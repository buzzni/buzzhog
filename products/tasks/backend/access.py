from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from django.conf import settings

import structlog

from posthog.models.user import User
from posthog.ph_client import feature_enabled_or_false, get_feature_flag_or_none

from products.tasks.backend.facade.contracts import DesktopAccessReason
from products.tasks.backend.metrics import DesktopAccessOutcome, observe_desktop_access_decision

if TYPE_CHECKING:
    from posthog.models.organization import Organization
    from posthog.models.team.team import Team

logger = structlog.get_logger(__name__)

DESKTOP_ACCESS_OVERRIDE_FLAG = "posthog-desktop-access-override"
DESKTOP_SIGNUP_GATE_FLAG = "posthog-desktop-signup-gate"


class DesktopAccessResolutionError(Exception):
    pass


class DesktopAccessDecision(StrEnum):
    ALLOWED = "allowed"
    STARTUP_PLAN = "startup_plan"
    PREPAID_CREDITS = "prepaid_credits"
    SIGNUPS_PAUSED = "signups_paused"

    @property
    def allowed(self) -> bool:
        return self == self.ALLOWED

    @property
    def reason(self) -> DesktopAccessReason | None:
        if self == self.STARTUP_PLAN:
            return DesktopAccessReason.STARTUP_PLAN
        if self == self.PREPAID_CREDITS:
            return DesktopAccessReason.PREPAID_CREDITS
        return None


_DECISION_OUTCOMES: dict[DesktopAccessDecision, DesktopAccessOutcome] = {
    DesktopAccessDecision.ALLOWED: "allowed",
    DesktopAccessDecision.STARTUP_PLAN: "startup_plan",
    DesktopAccessDecision.PREPAID_CREDITS: "prepaid_credits",
    DesktopAccessDecision.SIGNUPS_PAUSED: "signups_paused",
}


_DECISION_VALUES = frozenset(decision.value for decision in DesktopAccessDecision)


def _signup_cutoff() -> datetime | None:
    raw_cutoff = settings.DESKTOP_SIGNUP_CUTOFF
    if not raw_cutoff:
        return None
    try:
        cutoff = datetime.fromisoformat(raw_cutoff)
    except ValueError as error:
        raise DesktopAccessResolutionError("DESKTOP_SIGNUP_CUTOFF is not an ISO 8601 datetime") from error
    return cutoff if cutoff.tzinfo is not None else cutoff.replace(tzinfo=UTC)


def _signed_up_after_cutoff(user: User) -> bool:
    cutoff = _signup_cutoff()
    return cutoff is not None and user.date_joined >= cutoff


def _flag_enabled(flag_key: str, user: User, organization: "Organization") -> bool:
    organization_id = str(organization.id)
    enabled = get_feature_flag_or_none(
        flag_key,
        str(user.distinct_id),
        groups={"organization": organization_id},
        group_properties={"organization": {"id": organization_id}},
        only_evaluate_locally=False,
        send_feature_flag_events=False,
    )
    if not isinstance(enabled, bool):
        raise DesktopAccessResolutionError(f"Could not evaluate the {flag_key} flag")
    return enabled


def get_desktop_access_decision(user: User, organization: "Organization") -> DesktopAccessDecision:
    """The per-user override flag is evaluated on every call."""
    if not user or not user.is_authenticated or not user.distinct_id:
        raise DesktopAccessResolutionError("Authentication is required to evaluate Desktop access")

    if settings.DEBUG:
        observe_desktop_access_decision(outcome="override")
        return DesktopAccessDecision.ALLOWED

    try:
        if _flag_enabled(DESKTOP_ACCESS_OVERRIDE_FLAG, user, organization):
            observe_desktop_access_decision(outcome="override")
            return DesktopAccessDecision.ALLOWED
        # The gate flag is evaluated only for users past the cutoff, so existing users pay no extra flag call.
        if _signed_up_after_cutoff(user) and _flag_enabled(DESKTOP_SIGNUP_GATE_FLAG, user, organization):
            decision = DesktopAccessDecision.SIGNUPS_PAUSED
        else:
            decision = DesktopAccessDecision.ALLOWED
    except DesktopAccessResolutionError:
        observe_desktop_access_decision(outcome="resolution_failure")
        raise

    observe_desktop_access_decision(outcome=_DECISION_OUTCOMES[decision])
    return decision


def has_loops_access(user: User, team: "Team | None" = None) -> bool:
    if not user.distinct_id:
        return False

    organization = team.organization if team is not None else getattr(user, "organization", None)
    organization_id = str(organization.id) if organization is not None else None
    return feature_enabled_or_false(
        "loops",
        str(user.distinct_id),
        groups={"organization": organization_id} if organization_id is not None else None,
        group_properties={"organization": {"id": organization_id}} if organization_id is not None else None,
        only_evaluate_locally=False,
        send_feature_flag_events=False,
    )
