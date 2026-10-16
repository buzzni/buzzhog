"""Cross-product write helpers for event definitions."""

from collections.abc import Sequence
from dataclasses import dataclass

from posthog.models import Team

from products.event_definitions.backend.models import EventDefinition, effective_project_id_expr


@dataclass(frozen=True)
class PlaceholderEventDefinition:
    name: str
    description: str | None = None


def create_placeholder_event_definitions(*, team_id: int, definitions: Sequence[PlaceholderEventDefinition]) -> None:
    """Create event definitions that ingestion can claim when the events are first seen."""
    if not definitions:
        return

    project_id = Team.objects.values_list("project_id", flat=True).get(id=team_id)
    names = [definition.name for definition in definitions]
    event_definitions_by_name: dict[str, EventDefinition] = {
        event_definition.name: event_definition
        for event_definition in EventDefinition.objects.alias(effective_project_id=effective_project_id_expr()).filter(
            effective_project_id=project_id, name__in=names
        )
    }

    for definition in definitions:
        if definition.name in event_definitions_by_name:
            continue
        event_definition, _ = EventDefinition.objects.get_or_create(
            project_id=project_id,
            name=definition.name,
            defaults={"team_id": team_id, "created_at": None, "last_seen_at": None},
        )
        event_definitions_by_name[definition.name] = event_definition
