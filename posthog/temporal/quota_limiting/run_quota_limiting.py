import json
import logging
import dataclasses
from datetime import timedelta

import structlog
from temporalio import activity, common, workflow

from posthog.exceptions_capture import capture_exception
from posthog.temporal.common.base import PostHogWorkflow

logger = structlog.get_logger()
logging.basicConfig(level=logging.INFO)


@dataclasses.dataclass
class RunQuotaLimitingInputs:
    pass


@dataclasses.dataclass
class RunQuotaLimitingAllOrgsInputs:
    pass


@dataclasses.dataclass
class QuotaLimitingResult:
    duration_s: float = 0.0
    orgs_total: int = 0
    orgs_processed: int = 0
    orgs_limited: int = 0
    orgs_suspended: int = 0


@activity.defn(name="run-quota-limiting-all-orgs")
async def run_quota_limiting_all_orgs(
    _inputs: RunQuotaLimitingAllOrgsInputs,
) -> QuotaLimitingResult:
    # Quota limits come from billing data, which this installation does not have.
    return QuotaLimitingResult()


@workflow.defn(name="run-quota-limiting")
class RunQuotaLimitingWorkflow(PostHogWorkflow):
    @staticmethod
    def parse_inputs(inputs: list[str]) -> RunQuotaLimitingInputs:
        """Parse inputs from the management command CLI."""
        loaded = json.loads(inputs[0])
        return RunQuotaLimitingInputs(**loaded)

    @workflow.run
    async def run(self, _inputs: RunQuotaLimitingInputs) -> QuotaLimitingResult:
        try:
            return await workflow.execute_activity(
                run_quota_limiting_all_orgs,
                RunQuotaLimitingAllOrgsInputs(),
                start_to_close_timeout=timedelta(hours=12),
                retry_policy=common.RetryPolicy(
                    maximum_attempts=1,
                ),
                heartbeat_timeout=timedelta(minutes=2),
            )

        except Exception as e:
            capture_exception(e)
            raise
