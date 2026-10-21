from uuid import UUID, uuid4

from posthog.test.base import BaseTest

from products.business_knowledge.backend.llm_telemetry import RetrievalTrace
from products.business_knowledge.backend.logic import KnowledgeSearchResult, rerank_chunks


class TestRerankChunks(BaseTest):
    def _make_result(self, content: str, *, chunk_id: UUID | None = None) -> KnowledgeSearchResult:
        return KnowledgeSearchResult(
            chunk_id=chunk_id or uuid4(),
            source_id=uuid4(),
            source_name="Docs",
            source_type="text",
            document_id=uuid4(),
            document_title="Title",
            heading_path="",
            ordinal=0,
            content=content,
        )

    def test_empty_candidates_no_op(self) -> None:
        assert rerank_chunks(self.team, "refund policy", [], top_k=5, trace=RetrievalTrace(surface="api")) == []

    def test_keeps_input_order_trimmed_to_top_k(self) -> None:
        results = [self._make_result(f"content {index}") for index in range(5)]

        reranked = rerank_chunks(self.team, "query", results, top_k=2, trace=RetrievalTrace(surface="api"))

        assert [result.chunk_id for result in reranked] == [result.chunk_id for result in results[:2]]
