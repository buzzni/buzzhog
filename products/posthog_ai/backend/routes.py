from posthog.api.routing import RouterRegistry

from products.posthog_ai.backend.api import TurnSuggestionsViewSet
from products.posthog_ai.backend.presentation.terminal_ai import TerminalAIViewSet


def register_routes(routers: RouterRegistry) -> None:
    routers.projects.register(r"terminal_ai", TerminalAIViewSet, "project_terminal_ai", ["team_id"])
    routers.projects.register(
        r"turn_suggestions",
        TurnSuggestionsViewSet,
        "project_turn_suggestions",
        ["team_id"],
    )
