from posthog.test.base import BaseTest

from products.posthog_ai.backend.models.assistant import CoreMemory
from products.replay_vision.backend.temporal.team_context import (
    _MAX_EVENT_DESCRIPTION_LEN,
    _MAX_EVENT_DESCRIPTIONS,
    _MAX_PRODUCT_CONTEXT_LEN,
    fetch_product_context,
    select_event_descriptions,
    session_custom_event_names,
)


def _rows(*event_names: str) -> tuple[list[str], list[list[str]]]:
    return ["event_uuid", "event"], [[f"u{i}", name] for i, name in enumerate(event_names)]


class TestFetchProductContext(BaseTest):
    def test_prefers_core_memory_over_product_description(self):
        self.team.project.product_description = "Old description"
        self.team.project.save()
        CoreMemory.objects.create(team=self.team, text="Acme sells rockets to coyotes.")
        assert fetch_product_context(self.team) == "Acme sells rockets to coyotes."

    def test_falls_back_to_project_product_description(self):
        self.team.project.product_description = "A B2B invoicing tool."
        self.team.project.save()
        assert fetch_product_context(self.team) == "A B2B invoicing tool."

    def test_empty_when_neither_source_exists(self):
        assert fetch_product_context(self.team) == ""

    def test_sanitizes_control_chars_keeps_newlines_and_caps_length(self):
        CoreMemory.objects.create(team=self.team, text="fact one\x07\nfact two   spaced\n\n" + "x" * 9000)
        result = fetch_product_context(self.team)
        assert result.startswith("fact one\nfact two spaced\n")
        assert "\x07" not in result
        assert len(result) <= _MAX_PRODUCT_CONTEXT_LEN + 1  # cap plus the ellipsis


class TestSelectEventDescriptions(BaseTest):
    def _select(self, found: dict[str, str | None], *event_names: str) -> dict[str, str]:
        columns, rows = _rows(*event_names)
        return select_event_descriptions(session_custom_event_names(columns, rows), found)

    def test_returns_described_custom_events_ordered_by_session_frequency(self):
        found = {
            "checkout_completed": "User paid for their cart.",
            "quote_expired": "A saved quote passed its validity window.",
            "undescribed_event": "",
            "null_desc_event": None,
            "$pageview": "Customer override that must not surface.",
        }
        result = self._select(
            found,
            "quote_expired",
            "checkout_completed",
            "quote_expired",
            "$pageview",
            "undescribed_event",
            "null_desc_event",
            "unknown_event",
        )
        assert result == {
            "quote_expired": "A saved quote passed its validity window.",
            "checkout_completed": "User paid for their cart.",
        }
        assert list(result) == ["quote_expired", "checkout_completed"]

    def test_caps_count_and_description_length_and_strips_control_chars(self):
        names = [f"event_{i:03d}" for i in range(_MAX_EVENT_DESCRIPTIONS + 5)]
        result = self._select(dict.fromkeys(names, "desc\x07 `y`" + "y" * 600), *names)
        assert len(result) == _MAX_EVENT_DESCRIPTIONS
        sample = result[names[0]]
        assert sample.startswith("desc 'y'y")
        assert "\x07" not in sample
        assert len(sample) <= _MAX_EVENT_DESCRIPTION_LEN + 1  # cap plus the ellipsis

    def test_drops_names_containing_backticks(self):
        assert self._select({"bad`name": "Would escape the prompt's code fencing."}, "bad`name") == {}
