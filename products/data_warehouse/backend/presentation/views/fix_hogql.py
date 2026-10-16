import uuid

from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from posthog.api.documentation import _FallbackSerializer, extend_schema
from posthog.api.routing import TeamAndOrgViewSetMixin


class FixHogQLViewSet(TeamAndOrgViewSetMixin, viewsets.ModelViewSet):
    scope_object = "INTERNAL"
    serializer_class = _FallbackSerializer

    @extend_schema(operation_id="fix_hogql_list")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request: Request, *args, **kwargs) -> Response:
        if request.data.get("query", None) is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "No query provided"},
            )

        trace_id = f"fix_hogql_query_{uuid.uuid4()}"
        return Response({"trace_id": trace_id, "error": "Could not fix the query"}, status=400)
