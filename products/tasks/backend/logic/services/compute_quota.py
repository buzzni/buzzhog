from posthog.models import Team

from products.tasks.backend.facade.contracts import ComputeQuotaDenialReason
from products.tasks.backend.metrics import observe_compute_quota_check
from products.tasks.backend.models import Task, TaskClientProvenance

COMPUTE_QUOTA_DENIAL_CODE = ComputeQuotaDenialReason.COMPUTE_QUOTA_EXHAUSTED.value
ORGANIZATION_DEACTIVATED_DENIAL_CODE = ComputeQuotaDenialReason.ORGANIZATION_DEACTIVATED.value


POSTHOG_CODE_CLIENT_PROVENANCES = frozenset(TaskClientProvenance)


def organization_deactivated(team_id: int) -> bool:
    return Team.objects.filter(id=team_id, organization__is_active=False).exists()


def is_task_billable_compute(task: Task) -> bool:
    return is_billable_compute(origin_product=task.origin_product, client_provenance=task.client_provenance)


def is_billable_compute(*, origin_product: str | None, client_provenance: str | None) -> bool:
    if client_provenance not in POSTHOG_CODE_CLIENT_PROVENANCES:
        return False
    return origin_product in (Task.OriginProduct.USER_CREATED, Task.OriginProduct.SPACE_SETUP)


def get_compute_quota_denial_reason(task: Task) -> ComputeQuotaDenialReason | None:
    if organization_deactivated(task.team_id):
        observe_compute_quota_check("checked_blocked")
        return ComputeQuotaDenialReason.ORGANIZATION_DEACTIVATED
    return None


def is_compute_quota_exhausted(task: Task) -> bool:
    return get_compute_quota_denial_reason(task) is not None
