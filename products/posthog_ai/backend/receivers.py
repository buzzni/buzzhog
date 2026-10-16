"""Task hooks for PostHog AI.

Every hook connects through the tasks facade so no model class crosses the product boundary.

- After a turn completes: the end-of-turn suggestion is queued (``turn_suggestions/dispatch.py``).
"""

from products.posthog_ai.backend.turn_suggestions.dispatch import enqueue_turn_suggestion_on_turn_completed
from products.tasks.backend.facade.task_run_signals import connect_task_run_turn_completed


def connect() -> None:
    connect_task_run_turn_completed(
        enqueue_turn_suggestion_on_turn_completed, dispatch_uid="posthog_ai_turn_suggestion_on_turn_completed"
    )
