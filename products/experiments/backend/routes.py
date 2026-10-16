from posthog.api.routing import RouterRegistry
from posthog.settings import EE_AVAILABLE


def register_routes(routers: RouterRegistry) -> None:
    # The experiments viewset lives in `products/experiments/backend/presentation/views.py`
    # and is unavailable without EE installed, so the entire surface is EE-gated.
    if not EE_AVAILABLE:
        return

    from products.experiments.backend.presentation.views import EnterpriseExperimentsViewSet

    routers.projects.register(r"experiments", EnterpriseExperimentsViewSet, "project_experiments", ["project_id"])
