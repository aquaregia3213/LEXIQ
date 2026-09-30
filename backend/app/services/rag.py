from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.app.services.search import get_search_service, SearchService
from backend.app.services.llm import get_llm_service, LLMService


class RAGPipeline:
    """
    RAG Pipeline for grounded legal question-answering over contract documents.
    Handles query processing, vector retrieval, XML evidence wrapping, LLM generation,
    source citation formatting, and insufficient evidence handling.
    """

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        llm_service: Optional[LLMService] = None
    ):
        self.search_service = search_service or get_search_service()
        self.llm_service = llm_service or get_llm_service()

    def construct_evidence_prompt(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Construct structured RAG prompt enclosing evidence inside XML tags.
        Treats contract text strictly as untrusted data to prevent prompt injection.
        """
        evidence_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            block = (
                f"<chunk id=\"{chunk.get('chunk_id')}\" index=\"{idx}\">\n"
                f"  <contract_name>{chunk.get('contract_name')}</contract_name>\n"
                f"  <section>{chunk.get('section')}</section>\n"
                f"  <page>{chunk.get('page_start')}</page>\n"
                f"  <text>\n{chunk.get('text')}\n  </text>\n"
                f"</chunk>"
            )
            evidence_blocks.append(block)

        evidence_str = "\n\n".join(evidence_blocks)

        prompt = (
            f"Question:\n{question}\n\n"
            f"<untrusted_contract_evidence>\n"
            f"{evidence_str}\n"
            f"</untrusted_contract_evidence>\n\n"
            f"Instructions:\n"
            f"Answer the question strictly using the evidence provided above. "
            f"If the evidence does not contain sufficient details to answer, respond stating insufficient evidence. "
            f"Cite each supporting source contract name, section, and page."
        )

        return prompt

    def ask_question(
        self,
        db: Session,
        question: str,
        contract_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Execute full RAG workflow for a user question.
        """
        clean_question = question.strip() if question else ""
        if not clean_question:
            raise ValueError("Question cannot be empty.")

        # 1. Vector Retrieval
        retrieved_chunks = self.search_service.semantic_search(
            db=db,
            query=clean_question,
            contract_id=contract_id,
            top_k=top_k,
            min_score=0.0
        )

        # 2. Check for empty retrieval
        if not retrieved_chunks:
            return {
                "question": clean_question,
                "answer": "The available documents do not provide sufficient evidence to answer this question.",
                "sources": [],
                "has_sufficient_evidence": False,
                "confidence_notes": "No relevant contract documents were found matching your search query."
            }

        # 3. Generate Grounded Answer via LLM Service
        result = self.llm_service.generate_grounded_answer(
            question=clean_question,
            evidence_chunks=retrieved_chunks
        )

        return {
            "question": clean_question,
            "answer": result["answer"],
            "sources": result["sources"],
            "has_sufficient_evidence": result["has_sufficient_evidence"],
            "confidence_notes": result["confidence_notes"]
        }


# Default singleton instance
_rag_pipeline = RAGPipeline()


def get_rag_pipeline() -> RAGPipeline:
    """Return default RAGPipeline instance."""
    return _rag_pipeline
