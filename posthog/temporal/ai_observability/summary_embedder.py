"""Queue LLM analytics documents for the embedding worker."""

from typing import Any

from posthog.api.embedding_worker import emit_embedding_request
from posthog.models.team import Team

# Trace clustering reads the 3072-dimension subtable.
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large-3072"

LLM_TRACES_SUMMARIES_PRODUCT = "llm-analytics"
LLM_TRACES_SUMMARIES_DOCUMENT_TYPE = "llm-trace-summary"


class LLMTracesSummarizerEmbedder:
    def __init__(self, team: Team, embedding_model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self._team = team
        self._model = embedding_model_name

    def embed_document(
        self,
        *,
        content: str,
        document_id: str,
        document_type: str,
        rendering: str,
        product: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        emit_embedding_request(
            content,
            team_id=self._team.id,
            product=product,
            document_type=document_type,
            rendering=rendering,
            document_id=document_id,
            models=[self._model],
            metadata=metadata,
        )
