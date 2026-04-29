from app.schemas.common import RetrievalMetrics


class EvaluationService:
    """Computes retrieval metrics for offline and operator-driven evaluation."""

    @staticmethod
    def retrieval_metrics(retrieved_chunk_ids: list[str], relevant_chunk_ids: list[str], top_k: int) -> RetrievalMetrics:
        retrieved = retrieved_chunk_ids[:top_k]
        relevant = {item for item in relevant_chunk_ids if item}
        if not retrieved or not relevant:
            return RetrievalMetrics(precision_at_k=0.0, recall_at_k=0.0, matched_chunk_ids=[])

        matched = [chunk_id for chunk_id in retrieved if chunk_id in relevant]
        precision = len(matched) / max(1, len(retrieved))
        recall = len(matched) / max(1, len(relevant))
        return RetrievalMetrics(
            precision_at_k=round(precision, 4),
            recall_at_k=round(recall, 4),
            matched_chunk_ids=matched,
        )