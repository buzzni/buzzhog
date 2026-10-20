import structlog
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, viewsets

from posthog.api.routing import TeamAndOrgViewSetMixin
from posthog.api.shared import UserBasicSerializer
from posthog.models.integration import Integration
from posthog.models.organization_integration import OrganizationIntegration
from posthog.permissions import OrganizationAdminWritePermissions

logger = structlog.get_logger(__name__)


class OrganizationIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for organization-level integrations."""

    created_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = OrganizationIntegration
        fields = [
            "id",
            "kind",
            "integration_id",
            "config",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = fields


@extend_schema(extensions={"x-product": "integrations"})
class OrganizationIntegrationViewSet(
    TeamAndOrgViewSetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for organization-level integrations.

    Provides access to integrations that are scoped to the entire organization
    (vs. project-level integrations). Examples include Vercel, AWS Marketplace, etc.

    Creation is handled by the integration installation flows
    (e.g., Vercel marketplace installation). Users can disconnect integrations
    via the DELETE endpoint.
    """

    scope_object = "organization_integration"
    queryset = OrganizationIntegration.objects.select_related("created_by").all()
    serializer_class = OrganizationIntegrationSerializer
    permission_classes = [OrganizationAdminWritePermissions]

    def perform_destroy(self, instance: OrganizationIntegration) -> None:
        team_integrations_deleted, _ = Integration.objects.filter(
            team__organization=instance.organization,
            kind=Integration.IntegrationKind.VERCEL,
        ).delete()

        logger.info(
            "organization_integration.deleted",
            organization_id=str(instance.organization_id),
            integration_id=instance.integration_id,
            kind=instance.kind,
            team_integrations_deleted=team_integrations_deleted,
        )
        instance.delete()
