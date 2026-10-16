"""Tests for `enqueue_pointer_message` — the activity that would send the
single SQS pointer to billing.
"""

from datetime import UTC, datetime

import pytest

from django.conf import settings

from posthog.temporal.usage_report.activities import SQS_QUEUE_NAME, enqueue_pointer_message
from posthog.temporal.usage_report.types import AggregateResult, EnqueuePointerInputs, WorkflowContext


def _ctx() -> WorkflowContext:
    return WorkflowContext(
        run_id="run-test",
        workflow_started_at=datetime(2026, 5, 5, 1, 45, 0, tzinfo=UTC),
        period_start=datetime(2026, 5, 4, 0, 0, 0, tzinfo=UTC),
        period_end=datetime(2026, 5, 4, 23, 59, 59, 999999, tzinfo=UTC),
        date_str="2026-05-04",
        report_completeness="complete",
    )


def _agg() -> AggregateResult:
    return AggregateResult(
        chunk_keys=[
            "tasks/billing/usage_reports/2026-05-04/run-test/chunks/chunk_0000.jsonl.gz",
            "tasks/billing/usage_reports/2026-05-04/run-test/chunks/chunk_0001.jsonl.gz",
        ],
        manifest_key="tasks/billing/usage_reports/2026-05-04/run-test/manifest.json",
        total_orgs=12345,
        total_orgs_with_usage=678,
    )


@pytest.mark.asyncio
async def test_pointer_is_skipped_without_billing(activity_environment) -> None:
    await activity_environment.run(
        enqueue_pointer_message,
        EnqueuePointerInputs(ctx=_ctx(), aggregate=_agg()),
    )


def test_v2_queue_is_configured_in_settings() -> None:
    queues = getattr(settings, "SQS_QUEUES", {})
    assert SQS_QUEUE_NAME in queues, (
        f"Queue {SQS_QUEUE_NAME!r} must be declared in settings.SQS_QUEUES — "
        f"otherwise the pointer activity raises after S3 work is done"
    )
