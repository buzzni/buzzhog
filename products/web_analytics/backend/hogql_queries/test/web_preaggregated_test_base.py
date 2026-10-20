import uuid
from abc import ABC, abstractmethod

from posthog.test.base import APIBaseTest, ClickhouseTestMixin, _create_person


class WebAnalyticsPreAggregatedTestBase(ClickhouseTestMixin, APIBaseTest, ABC):
    """Abstract base class for testing web analytics pre-aggregated queries"""

    STANDARD_EVENT_PROPERTIES = {
        "$host": "example.com",
        "$device_type": "Desktop",
        "$browser": "Chrome",
        "$os": "Windows",
        "$viewport_width": 1920,
        "$viewport_height": 1080,
    }

    def setUp(self):
        super().setUp()
        self._setup_test_data()

    @abstractmethod
    def _setup_test_data(self):
        pass

    def _generate_random_distinct_id(self, prefix: str = "user") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def _create_test_person(self, distinct_id: str | None = None) -> str:
        if distinct_id is None:
            distinct_id = self._generate_random_distinct_id()
        _create_person(distinct_ids=[distinct_id], team_id=self.team.pk)
        return distinct_id

    def _sort_results(self, results, key=lambda x: str(x[0])):
        return sorted(results, key=key)
