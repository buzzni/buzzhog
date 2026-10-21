"""Query-count guard for the usage-report aggregator, plus the in-memory object storage helper the other usage-report tests share."""

import io
from datetime import UTC, datetime
from typing import Any

import pytest

from django.db import connection
from django.test.utils import CaptureQueriesContext

from posthog.models import Organization, Team
from posthog.temporal.usage_report.queries import QUERIES
from posthog.temporal.usage_report.types import WorkflowContext


def _all_destination_keys() -> list[str]:
    """Every key `_get_team_report` reads, derived from the registry so we
    don't have to keep the test in sync with the spec list by hand.
    """
    keys: list[str] = []
    for spec in QUERIES:
        if spec.output == "multi":
            keys.extend(spec.multi_keys_mapping.values())
        else:
            keys.append(spec.name)
    return keys


def _install_in_memory_object_storage(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    """Patch the S3 helpers used by the Temporal flow to read/write a dict.

    Returns the dict so the test can read what was written and pre-seed
    keys for `load_all_data` to read back.
    """
    s3: dict[str, bytes] = {}

    def _write(key: str, content: Any, extras: Any = None, bucket: Any = None) -> None:
        s3[key] = content.encode("utf-8") if isinstance(content, str) else content

    def _write_stream(key: str, fileobj: io.IOBase, extras: Any = None, bucket: Any = None) -> None:
        s3[key] = fileobj.read()

    def _read_bytes(key: str, bucket: Any = None, *, missing_ok: bool = False) -> bytes | None:
        if key not in s3:
            if missing_ok:
                return None
            raise FileNotFoundError(key)
        return s3[key]

    monkeypatch.setattr("posthog.storage.object_storage.write", _write)
    monkeypatch.setattr("posthog.storage.object_storage.write_stream", _write_stream)
    monkeypatch.setattr("posthog.storage.object_storage.read_bytes", _read_bytes)
    return s3


@pytest.mark.django_db(transaction=True)
def test_temporal_org_reports_do_not_run_per_org_membership_queries() -> None:
    """The Temporal `aggregator.iter_org_reports` must fetch organization
    membership counts in bulk. The legacy Celery facade still runs one
    `OrganizationMembership.count()` per organization inside its team loop,
    and the `aggregate-and-chunk-org-reports` activity must not.
    """
    from posthog.temporal.usage_report.aggregator import get_org_user_counts, iter_org_reports

    # Create a meaningful number of fresh orgs/teams so the per-org N+1
    # would have clear daylight from the bulk-fetch path. Without this,
    # query counts are low enough that any reasonable cap would pass.
    fresh_orgs: list[Organization] = []
    for i in range(20):
        org = Organization.objects.create(name=f"Bulk Org {i}")
        Team.objects.create(organization=org, name=f"Team {i}")
        fresh_orgs.append(org)

    period_start = datetime(2026, 5, 4, 0, 0, 0, tzinfo=UTC)
    ctx = WorkflowContext(
        run_id="membership-queries",
        period_start=period_start,
        period_end=datetime(2026, 5, 4, 23, 59, 59, 999999, tzinfo=UTC),
        date_str="2026-05-04",
    )
    all_data: dict[str, dict[int, int]] = {key: {} for key in _all_destination_keys()}

    with CaptureQueriesContext(connection) as captured:
        org_user_counts = get_org_user_counts()
        list(iter_org_reports(all_data, ctx, org_user_counts))

    # The Temporal path runs ~2 queries (teams + bulk memberships)
    # regardless of org count. The legacy Celery path runs 1 + N. Cap
    # well below `1 + N` so any per-org N+1 here blows the test, while
    # leaving slack for harmless query-count drift (savepoints etc.).
    assert len(captured.captured_queries) <= 5, (
        f"Temporal iter_org_reports issued {len(captured.captured_queries)} "
        f"queries — with {len(fresh_orgs)} fresh orgs this looks like a "
        f"per-org N+1, which dominates wall-clock for the aggregation activity."
    )
