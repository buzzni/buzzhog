from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal, Optional, TypedDict, Union

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import IntegrityError, models, transaction
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

import structlog
import dateutil.parser
from rest_framework import exceptions

from posthog.cloud_utils import is_cloud
from posthog.constants import INVITE_DAYS_VALIDITY, MAX_SLUG_LENGTH, AvailableFeature
from posthog.dataclasses import frozen
from posthog.models.activity_logging.model_activity import ModelActivityMixin
from posthog.models.personal_api_key import PersonalAPIKey
from posthog.models.utils import LowercaseSlugField, UUIDTModel, create_with_slug, generate_slug_candidates, sane_repr

if TYPE_CHECKING:
    from posthog.models import Team, User


logger = structlog.get_logger(__name__)


class OrganizationUsageResource(TypedDict):
    usage: int | None
    limit: int | None
    todays_usage: int | None


# The "usage" field is essentially cached info from the Billing Service to be used for visual reporting to the user
# as well as for enforcing limits.
# These keys must match QuotaResource and UsageCounters (except for `period`).
class OrganizationUsageInfo(TypedDict):
    events: OrganizationUsageResource | None
    exceptions: OrganizationUsageResource | None
    recordings: OrganizationUsageResource | None
    survey_responses: OrganizationUsageResource | None
    rows_synced: OrganizationUsageResource | None
    cdp_trigger_events: OrganizationUsageResource | None
    rows_exported: OrganizationUsageResource | None
    feature_flag_requests: OrganizationUsageResource | None
    api_queries_read_bytes: OrganizationUsageResource | None
    llm_events: OrganizationUsageResource | None
    ai_credits: OrganizationUsageResource | None
    signals_credits: OrganizationUsageResource | None
    posthog_code_credits: OrganizationUsageResource | None
    posthog_code_token_credits: OrganizationUsageResource | None
    sandbox_compute_credits: OrganizationUsageResource | None
    sandbox_compute_cpu_millicore_seconds: OrganizationUsageResource | None
    sandbox_compute_memory_mib_seconds: OrganizationUsageResource | None
    workflow_emails: OrganizationUsageResource | None
    workflow_push: OrganizationUsageResource | None
    workflow_destinations_dispatched: OrganizationUsageResource | None
    logs_mb_ingested: OrganizationUsageResource | None
    replay_vision_credits: OrganizationUsageResource | None
    period: list[str] | None


@frozen
class BillingPeriod:
    start: datetime
    end: datetime


class ProductFeature(TypedDict):
    key: str
    name: str
    description: str
    unit: str | None
    limit: int | None
    note: str | None
    is_plan_default: bool


class OrganizationManager(models.Manager):
    def create(self, *args: Any, **kwargs: Any):
        # Set default_anonymize_ips based on deployment if not explicitly provided
        if "default_anonymize_ips" not in kwargs:
            kwargs["default_anonymize_ips"] = default_anonymize_ips()
        if "is_ai_training_opted_in" not in kwargs:
            kwargs["is_ai_training_opted_in"] = default_is_ai_training_opted_in()
        # New organizations start on the most-specific resolution. Existing ones opt in.
        if "uses_most_specific_access_resolution" not in kwargs:
            kwargs["uses_most_specific_access_resolution"] = True
        return create_with_slug(super().create, *args, **kwargs)

    def bootstrap(
        self,
        user: Optional["User"],
        *,
        team_fields: dict[str, Any] | None = None,
        **kwargs,
    ) -> tuple["Organization", Optional["OrganizationMembership"], "Team"]:
        """Instead of doing the legwork of creating an organization yourself, delegate the details with bootstrap."""
        from .project import Project  # Avoiding circular import

        with transaction.atomic(using=self.db):
            # Set default_anonymize_ips based on deployment if not explicitly provided
            if "default_anonymize_ips" not in kwargs:
                kwargs["default_anonymize_ips"] = default_anonymize_ips()
            if "is_ai_training_opted_in" not in kwargs:
                kwargs["is_ai_training_opted_in"] = default_is_ai_training_opted_in()
            organization = Organization.objects.create(**kwargs)
            _, team = Project.objects.create_with_team(
                initiating_user=user, organization=organization, team_fields=team_fields
            )
            organization_membership: OrganizationMembership | None = None
            if user is not None:
                organization_membership = OrganizationMembership.objects.create(
                    organization=organization,
                    user=user,
                    level=OrganizationMembership.Level.OWNER,
                )
                user.current_organization = organization
                user.organization = user.current_organization  # Update cached property
                user.current_team = team
                user.team = user.current_team  # Update cached property
                user.save()

        return organization, organization_membership, team


def default_anonymize_ips():
    """Default to True for EU cloud deployments to comply with stricter privacy requirements"""
    return getattr(settings, "CLOUD_DEPLOYMENT", None) == "EU"


def default_is_ai_training_opted_in():
    """Default to False (opted out) for EU cloud deployments to comply with stricter privacy requirements"""
    return getattr(settings, "CLOUD_DEPLOYMENT", None) != "EU"


class Organization(ModelActivityMixin, UUIDTModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["for_internal_metrics"],
                condition=Q(for_internal_metrics=True),
                name="single_for_internal_metrics",
            )
        ]

    class PluginsAccessLevel(models.IntegerChoices):
        # None means the organization can't use plugins at all. They're hidden. Cloud default.
        NONE = 0, "none"
        # Config means the organization can only enable/disable/configure globally managed plugins.
        # This prevents config orgs from running untrusted code, which the next levels can do.
        CONFIG = 3, "config"
        # Install means the organization has config capabilities + can install own editor/GitHub/GitLab/npm plugins.
        # The plugin repository is off limits, as repository installations are managed by root orgs to avoid confusion.
        INSTALL = 6, "install"
        # Root means the organization has unrestricted plugins access on the instance. Self-hosted default.
        # This includes installing plugins from the repository and managing plugin installations for all other orgs.
        ROOT = 9, "root"

    class DefaultExperimentStatsMethod(models.TextChoices):
        BAYESIAN = "bayesian", "Bayesian"
        FREQUENTIST = "frequentist", "Frequentist"

    class DeactivationReason(models.TextChoices):
        UNPAID_BALANCE = "Access revoked due to unpaid balance.", "Unpaid balance"
        COMPLIANCE_REVIEW = "Access disabled for compliance review.", "Compliance review"
        TERMS_OF_SERVICE_VIOLATION = (
            "Access revoked due to terms of service violation.",
            "Terms of service violation",
        )
        DESKTOP_ABUSE = (
            "Suspected PostHog Desktop abuse. Contact PostHog support if you think this is a mistake.",
            "Desktop abuse",
        )

    members = models.ManyToManyField(
        "posthog.User",
        through="posthog.OrganizationMembership",
        through_fields=("organization", "user"),
        related_name="organizations",
        related_query_name="organization",
    )

    # General settings
    name = models.CharField(max_length=64)
    # Name this instance last saw in the DB; save() compares it to self.name to detect a rename.
    _loaded_name: Optional[str] = None
    slug: LowercaseSlugField = LowercaseSlugField(unique=True, max_length=MAX_SLUG_LENGTH)
    logo_media = models.ForeignKey("posthog.UploadedMedia", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        null=True,
        blank=True,
        help_text=_("Set this to 'No' to temporarily disable an organization."),
    )
    is_not_active_reason = models.TextField(
        _("de-activated reason"),
        null=True,
        blank=True,
        help_text=_(
            "(optional) reason for why the organization has been de-activated. This will be displayed to users on the web app."
        ),
        max_length=200,
    )
    # Transient flag set by the pre_save signal to communicate active-state changes to post_save.
    _is_active_changed: bool = False
    _has_active_subscription_changed: bool = False

    # Security / management settings
    session_cookie_age = models.IntegerField(
        null=True,
        blank=True,
        help_text="Custom session cookie age in seconds. If not set, the global setting SESSION_COOKIE_AGE will be used.",
    )

    is_member_join_email_enabled = models.BooleanField(
        default=True
    )  # DEPRECATED in favor of User.partial_notification_settings
    is_ai_data_processing_approved = models.BooleanField(null=True, blank=True, default=True)
    is_ai_training_opted_in = models.BooleanField(
        default=True,
        null=True,
        blank=True,
        help_text="When True, this organization allows its data to be used to train PostHog AI models.",
    )
    is_ai_training_locked = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="When True, the AI training opt-out setting cannot be modified through the UI or API.",
    )
    is_ai_training_cta_shown = models.BooleanField(
        default=True,
        null=True,
        blank=True,
        help_text="When True, in-app callouts inviting members to enable AI training are shown.",
    )
    enforce_2fa = models.BooleanField(null=True, blank=True)
    enforce_verified_domains = models.BooleanField(
        null=True,
        blank=True,
        help_text="When True, logins, signups, and invites for this organization are restricted to email addresses on its verified domains.",
    )
    members_can_invite = models.BooleanField(default=True, null=True, blank=True)
    members_can_create_projects = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="When True, organization members (below admin) are allowed to create new projects. Admins and owners can always create projects.",
    )
    members_can_use_personal_api_keys = models.BooleanField(default=True)
    members_can_see_org_members = models.BooleanField(
        default=True,
        db_default=True,
        help_text="When False, members (below admin) only see themselves in the members list and only project members in access control.",
    )
    uses_most_specific_access_resolution = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="When True, access controls resolve with the most specific matching rule. When False, the legacy resolution order applies.",
    )
    allow_publicly_shared_resources = models.BooleanField(default=True)
    member_notice = models.JSONField(
        null=True,
        blank=True,
        help_text="Notice shown in a banner to every member of the organization, with an optional link button.",
    )
    read_only_mcp_access = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="When True, requests through the PostHog MCP server can read but not change this organization's data.",
    )
    default_role = models.ForeignKey(
        "access_control.Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_organizations",
        help_text="Role automatically assigned to new members joining the organization",
    )

    # Misc
    plugins_access_level = models.PositiveSmallIntegerField(
        default=PluginsAccessLevel.CONFIG,
        choices=PluginsAccessLevel,
    )
    for_internal_metrics = models.BooleanField(default=False)
    default_anonymize_ips = models.BooleanField(
        default=False,
        help_text="Default setting for 'Discard client IP data' for new projects in this organization.",
    )
    is_pending_deletion = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="Set to True when org deletion has been initiated. Blocks all UI access until the async task completes.",
    )

    ## Managed by Billing
    customer_id = models.CharField(max_length=200, null=True, blank=True)

    # looking for feature? check: is_feature_available, get_available_feature
    available_product_features = ArrayField(models.JSONField(blank=False), null=True, blank=True)
    # Managed by Billing, cached here for usage controls
    # Like {
    #   'events': { 'usage': 10000, 'limit': 20000, 'todays_usage': 1000 },
    #   'recordings': { 'usage': 10000, 'limit': 20000, 'todays_usage': 1000 }
    #   'feature_flags_requests': { 'usage': 10000, 'limit': 20000, 'todays_usage': 1000 }
    #   'api_queries_read_bytes': { 'usage': 123456789, 'limit': 1000000000000, 'todays_usage': 1234 }
    #   'period': ['2021-01-01', '2021-01-31']
    # }
    # Also currently indicates if the organization is on billing V2 or not
    usage = models.JSONField(null=True, blank=True)
    never_drop_data = models.BooleanField(default=False, null=True, blank=True)

    if TYPE_CHECKING:
        oauth_applications: models.Manager[Any]
    # Scoring levels defined in billing::customer::TrustScores
    customer_trust_scores = models.JSONField(default=dict, null=True, blank=True)
    # Managed by Billing: whether the org had an active subscription (or active trial)
    # at last customer sync. NULL = never synced = unknown; consumers must fail open on NULL.
    has_active_subscription = models.BooleanField(null=True, blank=True)

    # DEPRECATED attributes (should be removed on next major version)
    setup_section_2_completed = models.BooleanField(default=True)
    personalization = models.JSONField(default=dict, null=False, blank=True)
    domain_whitelist: ArrayField = ArrayField(
        models.CharField(max_length=256, blank=False), blank=True, default=list
    )  # DEPRECATED in favor of `OrganizationDomain` model; previously used to allow self-serve account creation based on social login (#5111)

    objects: OrganizationManager = OrganizationManager()

    is_platform = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return self.name

    __repr__ = sane_repr("name")

    @classmethod
    def from_db(cls, db: Any, field_names: Any, values: Any) -> "Organization":
        instance = super().from_db(db, field_names, values)
        instance._loaded_name = instance.__dict__.get("name")
        return instance

    def refresh_from_db(self, using: Any = None, fields: Any = None, from_queryset: Any = None) -> None:
        super().refresh_from_db(using=using, fields=fields, from_queryset=from_queryset)
        if fields is None or "name" in fields:
            self._loaded_name = self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        update_fields = kwargs.get("update_fields")
        name_is_written = update_fields is None or "name" in update_fields
        renamed = (
            not self._state.adding
            and name_is_written
            and self._loaded_name is not None
            and self._loaded_name != self.name
        )
        # Read self.name only after a rename is known, so a deferred name costs no query.
        base_slug = slugify(self.name)[:MAX_SLUG_LENGTH] if renamed else ""
        if renamed and base_slug != self.slug:
            if update_fields is not None:
                kwargs["update_fields"] = {*update_fields, "slug"}
            self._save_with_regenerated_slug(base_slug, *args, **kwargs)
        else:
            super().save(*args, **kwargs)
        if name_is_written and "name" in self.__dict__:
            self._loaded_name = self.name

    def _save_with_regenerated_slug(self, base_slug: str, *args: Any, **kwargs: Any) -> None:
        for candidate in generate_slug_candidates(base_slug):
            self.slug = candidate
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError:
                continue
        raise Exception("Could not save organization with a unique slug in 10 tries!")

    @property
    def _billing_plan_details(self) -> tuple[str | None, str | None]:
        """
        Obtains details on the billing plan for the organization.
        Returns a tuple with (billing_plan_key, billing_realm)
        """
        return (None, None)

    def update_available_product_features(self) -> list[ProductFeature]:
        """Updates field `available_product_features`. Does not `save()`."""
        if is_cloud() or self.usage:
            # Since billing V2 we just use the field which is updated when the billing service is called
            return self.available_product_features or []

        self.available_product_features = []
        return []

    def get_available_feature(self, feature: Union[AvailableFeature, str]) -> ProductFeature | None:
        return next(
            filter(lambda f: f and f.get("key") == feature, self.available_product_features or []),
            None,
        )

    def is_feature_available(self, feature: Union[AvailableFeature, str]) -> bool:
        return bool(self.get_available_feature(feature))

    def get_plan_tier(self) -> Literal["free", "paid", "enterprise"]:
        """Best-effort plan tier derived from `available_product_features`.

        "paid" if any feature is present, otherwise "free". Paid uses "any feature present"
        rather than an allow-list because the billing service grants features (alerts,
        surveys_styling, ...) that postdate any fixed list, and an allow-list silently
        downgrades those orgs to free.
        """
        available_keys = {
            feature.get("key") for feature in (self.available_product_features or []) if feature and feature.get("key")
        }
        if not available_keys:
            return "free"

        return "paid"

    @property
    def current_billing_period(self) -> BillingPeriod | None:
        """
        Returns the current billing period.
        Returns None if usage data is not available or period is not set.
        """
        if not self.usage or "period" not in self.usage:
            return None

        try:
            period = self.usage["period"]
            if not period or len(period) < 2:
                return None

            start = dateutil.parser.isoparse(period[0])
            end = dateutil.parser.isoparse(period[1])
            return BillingPeriod(start=start, end=end)
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Failed to parse billing period for organization {self.id}: {e}")
            return None

    @property
    def active_invites(self) -> QuerySet:
        return self.invites.filter(created_at__gte=timezone.now() - timedelta(days=INVITE_DAYS_VALIDITY))

    def get_analytics_metadata(self):
        return {
            "member_count": self.members.count(),
            "project_count": self.teams.count(),
            "name": self.name,
        }


@receiver(models.signals.pre_save, sender=Organization)
def organization_about_to_be_created(sender, instance: Organization, raw, using, **kwargs):
    if instance._state.adding:
        instance.update_available_product_features()
        if not is_cloud():
            instance.plugins_access_level = Organization.PluginsAccessLevel.ROOT


@receiver(models.signals.pre_save, sender=Organization)
def remember_organization_field_changes(sender, instance: Organization, **kwargs):
    instance._is_active_changed = False
    instance._has_active_subscription_changed = False
    if instance._state.adding:
        return

    tracked_fields = {"is_active", "has_active_subscription"}
    update_fields = kwargs.get("update_fields")
    if update_fields is not None:
        tracked_fields &= set(update_fields)
        if not tracked_fields:
            return

    previous = sender.objects.filter(pk=instance.pk).values("is_active", "has_active_subscription").first()
    if previous is None:
        return
    if "is_active" in tracked_fields:
        instance._is_active_changed = previous["is_active"] != instance.is_active
    if "has_active_subscription" in tracked_fields:
        instance._has_active_subscription_changed = (
            previous["has_active_subscription"] != instance.has_active_subscription
        )


class OrganizationMembership(ModelActivityMixin, UUIDTModel):
    class Level(models.IntegerChoices):
        """Keep in sync with TeamMembership.Level (only difference being projects not having an Owner)."""

        MEMBER = 1, "member"
        ADMIN = 8, "administrator"
        OWNER = 15, "owner"

    organization = models.ForeignKey(
        "posthog.Organization",
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
    )
    user = models.ForeignKey(
        "posthog.User",
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        related_query_name="organization_membership",
    )
    level = models.PositiveSmallIntegerField(default=Level.MEMBER, choices=Level)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Persisted at invite acceptance so the welcome dialog can attribute who invited the member —
    # the OrganizationInvite row itself is deleted during use() and can't be looked up afterwards.
    invited_by = models.ForeignKey(
        "posthog.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    # Transient flag set by the pre_save signal to communicate level changes to post_save.
    _level_changed: bool = False

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization_id", "user_id"],
                name="unique_organization_membership",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "-joined_at"],
                name="org_membership_org_joined_idx",
            ),
        ]

    def __str__(self):
        return str(self.Level(self.level))

    def validate_update(
        self,
        membership_being_updated: "OrganizationMembership",
        new_level: Level | None = None,
    ) -> None:
        if new_level is not None:
            if membership_being_updated.id == self.id:
                raise exceptions.PermissionDenied("You can't change your own access level.")
            if new_level == OrganizationMembership.Level.OWNER:
                if self.level != OrganizationMembership.Level.OWNER:
                    raise exceptions.PermissionDenied(
                        "You can only make another member owner if you're this organization's owner."
                    )
                self.save()
            elif new_level > self.level:
                raise exceptions.PermissionDenied(
                    "You can only change access level of others to lower or equal to your current one."
                )
        if membership_being_updated.id != self.id:
            if membership_being_updated.organization_id != self.organization_id:
                raise exceptions.PermissionDenied("You both need to belong to the same organization.")
            if self.level < OrganizationMembership.Level.ADMIN:
                raise exceptions.PermissionDenied("You can only edit others if you are an admin.")
            if membership_being_updated.level > self.level:
                raise exceptions.PermissionDenied("You can only edit others with level lower or equal to you.")

    def get_scoped_api_keys(self):
        """
        Get API keys that are scoped to this organization or its teams.
        Returns a dictionary with information about the keys.
        """
        from posthog.models.team import Team

        # Get teams that belong to this organization
        team_ids = list(Team.objects.filter(organization_id=self.organization_id).values_list("id", flat=True))

        # Find API keys scoped to either the organization or any of its teams
        # Also include keys with no scoped teams or orgs (they apply to all orgs/teams)

        personal_api_keys = PersonalAPIKey.objects.filter(user=self.user).filter(
            Q(scoped_organizations__contains=[str(self.organization_id)])
            | Q(scoped_teams__overlap=team_ids)
            | (
                (Q(scoped_organizations__isnull=True) | Q(scoped_organizations=[]))
                & (Q(scoped_teams__isnull=True) | Q(scoped_teams=[]))
            )
        )

        # Get keys with more details
        keys_data = []
        has_keys = personal_api_keys.exists()

        # Check if any keys were used in the last week
        one_week_ago = timezone.now() - timedelta(days=7)
        has_keys_active_last_week = personal_api_keys.filter(last_used_at__gte=one_week_ago).exists()

        # Get detailed information about each key
        for key in personal_api_keys:
            keys_data.append({"name": key.label, "last_used_at": key.last_used_at})

        return {
            "personal_api_keys": personal_api_keys,
            "has_keys": has_keys,
            "has_keys_active_last_week": has_keys_active_last_week,
            "keys": keys_data,
            "team_ids": team_ids,
        }

    def delete(self, *args, **kwargs):
        from posthog.models.activity_logging.model_activity import get_current_user, get_was_impersonated
        from posthog.models.signals import model_activity_signal

        model_activity_signal.send(
            sender=self.__class__,
            scope=self.__class__.__name__,
            before_update=self,
            after_update=None,
            activity="deleted",
            user=get_current_user(),
            was_impersonated=get_was_impersonated(),
        )

        return super().delete(*args, **kwargs)

    __repr__ = sane_repr("organization", "user", "level")


@receiver(models.signals.pre_delete, sender=OrganizationMembership)
def ensure_organization_membership_consistency(sender, instance: OrganizationMembership, **kwargs):
    save_user = False
    if instance.user.current_organization == instance.organization:
        # reset current_organization if it's the removed organization
        instance.user.current_organization = None
        save_user = True
    if instance.user.current_team is not None and instance.user.current_team.organization == instance.organization:
        # reset current_team if it belongs to the removed organization
        instance.user.current_team = None
        save_user = True
    if save_user:
        instance.user.save()


@receiver(models.signals.post_delete, sender=OrganizationMembership)
def clean_up_alert_subscriptions_on_membership_removal(sender, instance: OrganizationMembership, **kwargs):
    from products.alerts.backend.models.alert import AlertSubscription

    deleted_count, _ = AlertSubscription.objects.filter(
        user=instance.user,
        alert_configuration__team__organization_id=instance.organization_id,
    ).delete()

    if deleted_count > 0:
        logger.info(
            "Removed alert subscriptions for user removed from organization",
            user_id=instance.user_id,
            organization_id=str(instance.organization_id),
            deleted_count=deleted_count,
        )


@receiver(models.signals.post_delete, sender=OrganizationMembership)
def clean_up_event_streams_on_membership_removal(sender, instance: OrganizationMembership, **kwargs):
    from products.customer_analytics.backend.facade.api import delete_event_streams_for_user

    deleted_count = delete_event_streams_for_user(user_id=instance.user_id, organization_id=instance.organization_id)

    if deleted_count > 0:
        logger.info(
            "Removed customer analytics event streams for user removed from organization",
            user_id=instance.user_id,
            organization_id=str(instance.organization_id),
            deleted_count=deleted_count,
        )


@receiver(models.signals.pre_save, sender=OrganizationMembership)
def organization_membership_saved(sender: Any, instance: OrganizationMembership, **kwargs: Any) -> None:
    from posthog.event_usage import report_user_organization_membership_level_changed

    instance._level_changed = False
    try:
        old_instance = OrganizationMembership.objects.get(id=instance.id)
        if old_instance.level != instance.level:
            instance._level_changed = True
            report_user_organization_membership_level_changed(
                instance.user, instance.organization, instance.level, old_instance.level
            )
    except OrganizationMembership.DoesNotExist:
        # The instance is new, or we are setting up test data
        pass


@receiver(post_save, sender=Organization)
def project_llm_gateway_quota_on_active_state_change(sender, instance: Organization, created: bool, **kwargs):
    if created or not instance._is_active_changed or not settings.AI_GATEWAY_REDIS_URL:
        return

    organization_id = instance.pk

    def _project_gateway_quota():
        from posthog.tasks.team_llm_gateway_quota import project_org_llm_gateway_quota_task

        try:
            project_org_llm_gateway_quota_task.delay(str(organization_id))
        except Exception:
            # The reconcile re-derives a deactivated org's blobs; never fail the org save.
            logger.warning("llm_gateway_quota_projection_enqueue_failed", organization_id=str(organization_id))

    transaction.on_commit(_project_gateway_quota)


@receiver(post_save, sender=Organization)
def cache_organization_session_age(sender, instance, **kwargs):
    """Cache organization's session_cookie_age in Redis when it changes."""
    if instance.session_cookie_age is not None:
        cache.set(f"org_session_age:{instance.id}", instance.session_cookie_age)
    else:
        cache.delete(f"org_session_age:{instance.id}")
