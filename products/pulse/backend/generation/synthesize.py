import datetime as dt

from posthog.models.team import Team
from posthog.models.user import User

from products.pulse.backend.config import BriefSettings
from products.pulse.backend.generation.schemas import BriefOut
from products.pulse.backend.models import BriefConfig
from products.pulse.backend.sources.base import SourceItem


class BriefSynthesisUnavailable(Exception):
    pass


def apply_say_less_gate(out: BriefOut, settings: BriefSettings) -> BriefOut:
    confident_opportunities = [o for o in out.opportunities if o.confidence >= settings.confidence_threshold]
    return BriefOut(
        sections=[s for s in out.sections if s.confidence >= settings.confidence_threshold],
        # Cap deterministically, because the model can return more than max_opportunities.
        opportunities=sorted(confident_opportunities, key=lambda o: o.confidence, reverse=True)[
            : settings.max_opportunities
        ],
    )


async def synthesize_brief(
    *,
    team: Team,
    user: User,
    config: BriefConfig | None,
    items: list[SourceItem],
    start_date: dt.date,
    end_date: dt.date,
    lookback_days: int,
) -> BriefOut:
    # Quiet periods must cost ~nothing: no items, no LLM call.
    if not items:
        return BriefOut(sections=[], opportunities=[])
    raise BriefSynthesisUnavailable("Brief synthesis needs an LLM client, which this install does not provide.")
