import pytest

from posthog.models import Organization, Team

from products.tasks.backend.logic.services.compute_quota import (
    ComputeQuotaDenialReason,
    get_compute_quota_denial_reason,
    is_billable_compute,
    is_compute_quota_exhausted,
    is_task_billable_compute,
)
from products.tasks.backend.models import Task, TaskClientProvenance


@pytest.mark.django_db
class TestComputeQuota:
    @pytest.fixture(autouse=True)
    def setup(self):
        organization = Organization.objects.create(name="test")
        self.team = Team.objects.create(organization=organization, name="test")

    def task(self, **overrides):
        defaults = {
            "team": self.team,
            "title": "task",
            "description": "task",
            "origin_product": Task.OriginProduct.USER_CREATED,
            "client_provenance": TaskClientProvenance.POSTHOG_DESKTOP,
        }
        defaults.update(overrides)
        return Task.objects.create(**defaults)

    def test_active_org_is_never_blocked(self):
        assert not is_compute_quota_exhausted(self.task())

    def test_deactivated_org_blocks(self):
        self.team.organization.is_active = False
        self.team.organization.save(update_fields=["is_active"])

        assert is_compute_quota_exhausted(self.task())
        assert get_compute_quota_denial_reason(self.task()) == ComputeQuotaDenialReason.ORGANIZATION_DEACTIVATED

    @pytest.mark.parametrize(
        "origin,provenance",
        [
            (Task.OriginProduct.SLACK, TaskClientProvenance.POSTHOG_DESKTOP),
            (Task.OriginProduct.SIGNAL_REPORT, TaskClientProvenance.POSTHOG_DESKTOP),
            (Task.OriginProduct.USER_CREATED, None),
        ],
    )
    def test_non_billable_origins_are_ineligible(self, origin, provenance):
        assert not is_task_billable_compute(self.task(origin_product=origin, client_provenance=provenance))

    @pytest.mark.parametrize("origin", [Task.OriginProduct.USER_CREATED, Task.OriginProduct.SPACE_SETUP])
    @pytest.mark.parametrize("provenance", list(TaskClientProvenance))
    def test_first_party_client_origins_are_billable(self, origin, provenance):
        assert is_task_billable_compute(self.task(origin_product=origin, client_provenance=provenance))

    def test_unknown_origin_is_ineligible(self):
        assert not is_billable_compute(origin_product=None, client_provenance=TaskClientProvenance.POSTHOG_DESKTOP)
