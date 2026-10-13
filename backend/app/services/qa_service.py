import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.ai_provider import (
    BaseGenerationProvider,
    GeminiGenerationProvider,
    MockGenerationProvider,
)
from app.schemas.qa import (
    QuestionRequest,
    GroundedAnswerResponse,
    ValidatedCitation,
)
from app.services.retrieval_service import retrieval_service

logger = logging.getLogger("prooflens.qa")


class QAService:
    """Orchestrates evidence retrieval, LLM synthesis, server-side citation validation, and strict abstention."""

    def __init__(self, provider: Optional[BaseGenerationProvider] = None):
        if provider is not None:
            self.provider = provider
            self.model_name = getattr(provider, "model", "custom-provider")
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() and not settings.GEMINI_API_KEY.startswith("your_"):
            try:
                self.provider = GeminiGenerationProvider()
                self.model_name = settings.GEMINI_CHAT_MODEL
                logger.info(f"Using GeminiGenerationProvider ({self.model_name})")
            except Exception as e:
                logger.warning(f"Could not initialize GeminiGenerationProvider: {e}. Falling back to MockGenerationProvider.")
                self.provider = MockGenerationProvider()
                self.model_name = "mock-generator-fallback"
        else:
            logger.info("No GEMINI_API_KEY found. Initializing MockGenerationProvider for offline/testing mode.")
            self.provider = MockGenerationProvider()
            self.model_name = "mock-generator"

    async def answer_question(
        self,
        db: AsyncSession,
        workspace_id: str,
        payload: QuestionRequest,
    ) -> GroundedAnswerResponse:
        """Answer a user question strictly grounded in retrieved workspace documents."""
        # 1. Retrieve top candidate chunks from database within workspace scope
        retrieved = await retrieval_service.retrieve(
            db=db,
            workspace_id=workspace_id,
            query=payload.question,
            top_k=payload.top_k,
            document_ids=payload.document_ids,
        )

        # 2. Fast abstention if no passages exist in the workspace
        if not retrieved:
            return GroundedAnswerResponse(
                question=payload.question,
                workspace_id=workspace_id,
                status="INSUFFICIENT_EVIDENCE",
                answer="No relevant document passages were found in this workspace to answer the question.",
                citations=[],
                total_retrieved=0,
                validated_citations_count=0,
                model_used=self.model_name,
                abstention_reason="NO_PASSAGES_FOUND",
            )

        # 3. Assemble evidence passages for generation provider
        passages = [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "similarity_score": c.similarity_score,
            }
            for c in retrieved
        ]

        # 4. Invoke LLM generation provider
        try:
            llm_result = self.provider.generate_grounded_answer(payload.question, passages)
        except Exception as e:
            logger.error(f"Error during grounded answer generation: {e}")
            return GroundedAnswerResponse(
                question=payload.question,
                workspace_id=workspace_id,
                status="ERROR",
                answer="An error occurred while generating the answer from AI provider.",
                citations=[],
                total_retrieved=len(retrieved),
                validated_citations_count=0,
                model_used=self.model_name,
                abstention_reason=f"PROVIDER_ERROR: {str(e)}",
            )

        raw_status = str(llm_result.get("status", "INSUFFICIENT_EVIDENCE")).strip().upper()
        raw_answer = str(llm_result.get("answer", "")).strip()
        raw_cited_ids = llm_result.get("cited_chunk_ids", [])

        # 5. Server-Side Citation Validation Engine
        # STRICT RULE: No citation metadata is accepted solely because LLM supplied it.
        # Verify citation IDs against real retrieved database records and derive metadata server-side.
        chunks_by_id = {c.chunk_id: c for c in retrieved}
        validated_citations: List[ValidatedCitation] = []
        seen_chunk_ids = set()

        for cid in raw_cited_ids:
            if cid in chunks_by_id and cid not in seen_chunk_ids:
                chk = chunks_by_id[cid]
                validated_citations.append(
                    ValidatedCitation(
                        chunk_id=chk.chunk_id,
                        document_id=chk.document_id,
                        filename=chk.filename,  # Server-derived from database record
                        page_number=chk.page_number,  # Server-derived from database record
                        chunk_index=chk.chunk_index,  # Server-derived from database record
                        excerpt=chk.content[:250] + ("..." if len(chk.content) > 250 else ""),
                        similarity_score=chk.similarity_score,
                    )
                )
                seen_chunk_ids.add(cid)
            else:
                logger.warning(
                    f"Citation ID '{cid}' was rejected because it does not match any retrieved chunk in scope."
                )

        # 6. Apply Strict Abstention Policy
        if raw_status == "INSUFFICIENT_EVIDENCE":
            final_status = "INSUFFICIENT_EVIDENCE"
            final_citations = []
            abstention_reason = "MODEL_REPORTED_INSUFFICIENT_EVIDENCE"
        elif raw_status == "ANSWERED":
            if not validated_citations:
                # Model claimed an answer but provided zero valid citations; abstain immediately!
                logger.warning("Model claimed 'ANSWERED' but zero citations were validated. Forcing abstention.")
                final_status = "INSUFFICIENT_EVIDENCE"
                raw_answer = "The system abstained because the generated answer could not be verified against actual retrieved document evidence."
                final_citations = []
                abstention_reason = "NO_VALID_CITATIONS_VERIFIED"
            else:
                final_status = "ANSWERED"
                final_citations = validated_citations
                abstention_reason = None
        else:
            final_status = "INSUFFICIENT_EVIDENCE"
            final_citations = []
            abstention_reason = f"UNRECOGNIZED_STATUS_{raw_status}"

        return GroundedAnswerResponse(
            question=payload.question,
            workspace_id=workspace_id,
            status=final_status,
            answer=raw_answer,
            citations=final_citations,
            total_retrieved=len(retrieved),
            validated_citations_count=len(final_citations),
            model_used=self.model_name,
            abstention_reason=abstention_reason,
        )


qa_service = QAService()
