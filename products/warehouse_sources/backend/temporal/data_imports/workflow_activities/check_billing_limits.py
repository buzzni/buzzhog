import typing
import dataclasses

from django.db import close_old_connections

from structlog.contextvars import bind_contextvars
from structlog.types import FilteringBoundLogger
from temporalio import activity

from posthog.temporal.common.logger import get_logger

from products.warehouse_sources.backend.models.external_data_job import ExternalDataJob
from products.warehouse_sources.backend.models.external_data_source import ExternalDataSource
from products.warehouse_sources.backend.temporal.data_imports.util import with_internal_db_retries

LOGGER = get_logger(__name__)


@dataclasses.dataclass
class CheckBillingLimitsActivityInputs:
    team_id: int
    job_id: str

    @property
    def properties_to_log(self) -> dict[str, typing.Any]:
        return {
            "team_id": self.team_id,
            "job_id": self.job_id,
        }


def billing_limit_reached(
    job: ExternalDataJob, source: ExternalDataSource, team_id: int, logger: FilteringBoundLogger
) -> bool:
    """Whether this run must stop because the team is over its synced-rows quota.

    A self-hosted install has no billing, so no run is ever limited. Callers keep asking so the
    workflow's activity sequence stays the same.
    """
    return False


@activity.defn
@with_internal_db_retries
def check_billing_limits_activity(inputs: CheckBillingLimitsActivityInputs) -> bool:
    bind_contextvars(team_id=inputs.team_id)
    logger = LOGGER.bind()
    close_old_connections()

    try:
        job = ExternalDataJob.objects.get(id=inputs.job_id)
    except ExternalDataJob.DoesNotExist:
        # job_id can be None (or point at a job that no longer exists) when this input came
        # from an older worker's create_external_data_job_model_activity result — that legacy
        # compatibility path doesn't guarantee a job was created. Nothing to bill for, so let
        # the sync proceed rather than fail the whole workflow.
        logger.info("Skipping billing limits check: job does not exist", job_id=inputs.job_id)
        return False

    return billing_limit_reached(job, job.pipeline, inputs.team_id, logger)
