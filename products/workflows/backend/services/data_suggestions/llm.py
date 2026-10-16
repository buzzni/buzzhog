from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

from posthog.models import Team, User

Schema = TypeVar("Schema", bound=BaseModel)


def invoke_structured(
    *,
    team: Team,
    user: User,
    model: str,
    effort: Literal["low", "medium", "high"],
    feature: str,
    schema: type[Schema],
    system: str,
    human: str,
    excluded_values: frozenset[str],
    allowed_values: Mapping[str, Sequence[str]] | None = None,
    analytics_client: Any = None,
) -> Schema | None:
    """One Claude call that answers in `schema`, or None when the call fails or the answer does not fit.

    This install has no LLM client, so the call never succeeds and callers take their no-suggestion path.
    """
    return None
