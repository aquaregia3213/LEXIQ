import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models.models import Chunk, Contract, Document
from backend.app.services.embedding import get_embedding_service, EmbeddingService


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class SearchService:
    """Service handling semantic vector search and metadata filtering."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()

    def semantic_search(
        self,
        db: Session,
        query: str,
        contract_id: Optional[str] = None,
        contract_type: Optional[str] = None,
        section: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search over document chunks.
        Supports metadata filtering by contract_id, contract_type, and section.
        Returns ordered top-K results with complete source references.
        """
        if not query or not query.strip():
            return []

        # 1. Generate query vector
        query_vector = self.embedding_service.embed_text(query)

        # 2. Build base query joining Chunk, Contract, Document
        stmt = (
            select(Chunk, Contract, Document)
            .join(Contract, Chunk.contract_id == Contract.id)
            .join(Document, Chunk.document_id == Document.id)
        )

        # 3. Apply metadata filters
        if contract_id:
            stmt = stmt.where(Chunk.contract_id == contract_id)
        if contract_type:
            stmt = stmt.where(Contract.contract_type.ilike(f"%{contract_type}%"))
        if section:
            from sqlalchemy import cast, String
            stmt = stmt.where(cast(Chunk.metadata_json, String).ilike(f"%{section}%"))

        results = db.execute(stmt).all()

        # 4. Score and rank results
        scored_results = []
        is_postgres = db.bind is not None and db.bind.dialect.name == "postgresql"

        for chunk, contract, document in results:
            if not chunk.embedding:
                continue

            # Calculate similarity score
            score = 0.0
            if isinstance(chunk.embedding, list):
                score = cosine_similarity(query_vector, chunk.embedding)
            elif isinstance(chunk.embedding, str):
                import json
                try:
                    vec = json.loads(chunk.embedding)
                    score = cosine_similarity(query_vector, vec)
                except Exception:
                    score = 0.0
            else:
                # pgvector Vector object handling
                try:
                    score = cosine_similarity(query_vector, list(chunk.embedding))
                except Exception:
                    score = 0.0

            # Filter by minimum score threshold
            if score < min_score:
                continue

            section_name = "General"
            if chunk.metadata_json and isinstance(chunk.metadata_json, dict):
                section_name = chunk.metadata_json.get("section", "General")

            if section and section.lower() not in section_name.lower():
                continue

            scored_results.append({
                "chunk_id": chunk.id,
                "contract_id": contract.id,
                "contract_name": contract.name,
                "contract_type": contract.contract_type,
                "document_id": document.id,
                "file_name": document.file_name,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "section": section_name,
                "similarity_score": round(float(score), 4),
                "metadata": chunk.metadata_json or {}
            })

        # 5. Sort descending by similarity score
        scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Return top_k results
        return scored_results[:top_k]


# Singleton instance
_search_service = SearchService()


def get_search_service() -> SearchService:
    """Return default SearchService instance."""
    return _search_service
