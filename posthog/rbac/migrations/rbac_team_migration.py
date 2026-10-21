import structlog

from posthog.models.organization import Organization

logger = structlog.get_logger(__name__)


class RBACTeamMigrationUnsupportedError(Exception):
    pass


# Teams that still use the legacy project access control kept their per-member grants in explicit
# team memberships. That model is gone, so those grants cannot be read. Moving such a team to the RBAC
# system would give it a default of "none" and no member grants, which locks out its non-admin
# members. So the migration refuses to touch a team in that state instead of half-migrating it.
def rbac_team_access_control_migration(organization_id: int) -> None:
    logger.info("Starting RBAC team migrations", organization_id=organization_id)

    organization = Organization.objects.get(id=organization_id)
    legacy_team_ids = list(organization.teams.filter(access_control=True).values_list("id", flat=True))
    if legacy_team_ids:
        error_message = (
            f"Refusing to migrate organization {organization_id}: teams {legacy_team_ids} still use legacy "
            "project access control, and their per-member permissions cannot be migrated."
        )
        logger.error(error_message, organization_id=organization_id, team_ids=legacy_team_ids)
        raise RBACTeamMigrationUnsupportedError(error_message)

    logger.info("Finished RBAC team migrations", organization_id=organization_id)
