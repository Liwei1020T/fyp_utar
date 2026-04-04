from __future__ import annotations

from ai_service.schemas.rag import RagMatch
from ai_service.schemas.rag import RagQueryRequest
from ai_service.schemas.rag import RagQueryResponse


def query_rag(payload: RagQueryRequest) -> RagQueryResponse:
    query_terms = {term for term in payload.query.lower().split() if term}
    ranked_documents: list[tuple[float, str, str | None, str]] = []

    for document in payload.documents:
        text_lower = document.text.lower()
        overlap = sum(1 for term in query_terms if term in text_lower)
        if overlap == 0:
            continue
        score = round(overlap / max(len(query_terms), 1), 2)
        excerpt = document.text[:220]
        ranked_documents.append((score, document.id, document.source, excerpt))

    ranked_documents.sort(key=lambda item: item[0], reverse=True)
    matches = [
        RagMatch(id=doc_id, source=source, score=score, excerpt=excerpt)
        for score, doc_id, source, excerpt in ranked_documents[: payload.top_k]
    ]

    if matches:
        answer = (
            "Retrieved supporting context from the provided documents. "
            "This is a lexical baseline, not a vector-search or generative RAG pipeline yet."
        )
    else:
        answer = "No supporting context matched the current query."

    return RagQueryResponse(
        query=payload.query,
        answer=answer,
        matches=matches,
        mode="lexical-baseline",
    )
