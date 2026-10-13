import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.document import Document
from app.core.ai_provider import (
    BaseGenerationProvider,
    GeminiGenerationProvider,
    MockGenerationProvider,
)
from app.schemas.comparison import (
    ComparisonRequest,
    ComparisonResponse,
    DocumentFinding,
    ComparisonSynthesis,
)
from app.schemas.qa import ValidatedCitation
from app.services.retrieval_service import retrieval_service

logger = logging.getLogger("prooflens.comparison")


class ComparisonService:
    """Orchestrates per-document evidence retrieval, LLM synthesis, server-side citation validation, and relationship classification."""

    def __init__(self, provider: Optional[BaseGenerationProvider] = None):
        if provider is not None:
            self.provider = provider
            self.model_name = getattr(provider, "model", "custom-provider")
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() and not settings.GEMINI_API_KEY.startswith("your_"):
            try:
                self.provider = GeminiGenerationProvider()
                self.model_name = settings.GEMINI_CHAT_MODEL
                logger.info(f"Using GeminiGenerationProvider for comparison ({self.model_name})")
            except Exception as e:
                logger.warning(f"Could not initialize GeminiGenerationProvider: {e}. Falling back to MockGenerationProvider.")
                self.provider = MockGenerationProvider()
                self.model_name = "mock-generator-fallback"
        else:
            logger.info("No GEMINI_API_KEY found. Initializing MockGenerationProvider for offline comparison.")
            self.provider = MockGenerationProvider()
            self.model_name = "mock-generator"

    async def compare_documents(
        self,
        db: AsyncSession,
        workspace_id: str,
        payload: ComparisonRequest,
    ) -> ComparisonResponse:
        """Compare findings across multiple documents on a topic, verifying citations server-side."""
        # 1. Validate documents exist and belong to workspace
        doc_stmt = (
            select(Document)
            .where(Document.workspace_id == workspace_id, Document.id.in_(payload.document_ids))
        )
        docs = (await db.execute(doc_stmt)).scalars().all()
        docs_by_id = {d.id: d for d in docs}

        for did in payload.document_ids:
            if did not in docs_by_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{did}' was not found in this workspace.",
                )

        if len(docs_by_id) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least two distinct documents in this workspace are required for comparison.",
            )

        # 2. Retrieve top-k passages for each document independently
        documents_evidence = []
        chunks_by_doc_id = {}

        for doc_id in payload.document_ids:
            doc = docs_by_id[doc_id]
            chunks = await retrieval_service.retrieve(
                db=db,
                workspace_id=workspace_id,
                query=payload.topic,
                top_k=payload.top_k_per_document,
                document_ids=[doc_id],
            )
            chunks_by_doc_id[doc_id] = {c.chunk_id: c for c in chunks}
            documents_evidence.append({
                "document_id": doc_id,
                "filename": doc.filename,
                "passages": [
                    {
                        "chunk_id": c.chunk_id,
                        "content": c.content,
                        "page_number": c.page_number,
                    }
                    for c in chunks
                ],
            })

        # 3. Fast abstention if no passages were found in any document
        total_passages = sum(len(d["passages"]) for d in documents_evidence)
        if total_passages == 0:
            findings = [
                DocumentFinding(
                    document_id=d["document_id"],
                    filename=d["filename"],
                    status="INSUFFICIENT_EVIDENCE",
                    finding=f"No relevant passages were found in '{d['filename']}' for the topic.",
                    citations=[],
                )
                for d in documents_evidence
            ]
            synthesis = ComparisonSynthesis(
                relationship="INSUFFICIENT_EVIDENCE",
                summary="None of the selected documents contained sufficient evidence regarding the topic.",
                scope_warnings=["Zero relevant passages retrieved across all selected documents."],
            )
            return ComparisonResponse(
                workspace_id=workspace_id,
                topic=payload.topic,
                status="INSUFFICIENT_EVIDENCE",
                findings=findings,
                synthesis=synthesis,
                model_used=self.model_name,
            )

        # 4. Invoke LLM generation provider
        try:
            llm_result = self.provider.generate_cross_document_comparison(
                payload.topic, documents_evidence
            )
        except Exception as e:
            logger.error(f"Error during cross-document comparison: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while generating cross-document comparison.",
            )

        raw_findings = llm_result.get("findings", [])
        raw_relationship = str(llm_result.get("relationship", "DIFFERENCE")).strip().upper()
        raw_summary = str(llm_result.get("summary", "")).strip()
        raw_warnings = llm_result.get("scope_warnings", [])

        # 5. Server-Side Citation Validation Engine per Document
        findings_by_id = {f.get("document_id"): f for f in raw_findings}
        validated_findings: List[DocumentFinding] = []
        valid_findings_count = 0

        for doc_id in payload.document_ids:
            doc = docs_by_id[doc_id]
            doc_chunks = chunks_by_doc_id.get(doc_id, {})
            raw_item = findings_by_id.get(doc_id, {})

            raw_status = raw_item.get("status", "INSUFFICIENT_EVIDENCE")
            raw_text = raw_item.get("finding", "No specific finding extracted.")
            raw_cited_ids = raw_item.get("cited_chunk_ids", [])

            validated_citations: List[ValidatedCitation] = []
            seen_ids = set()

            for cid in raw_cited_ids:
                if cid in doc_chunks and cid not in seen_ids:
                    chk = doc_chunks[cid]
                    validated_citations.append(
                        ValidatedCitation(
                            chunk_id=chk.chunk_id,
                            document_id=chk.document_id,
                            filename=chk.filename,  # Server-derived
                            page_number=chk.page_number,  # Server-derived
                            chunk_index=chk.chunk_index,  # Server-derived
                            excerpt=chk.content[:250] + ("..." if len(chk.content) > 250 else ""),
                            similarity_score=chk.similarity_score,
                        )
                    )
                    seen_ids.add(cid)
                else:
                    logger.warning(
                        f"Comparison citation ID '{cid}' was rejected for document '{doc.filename}'."
                    )

            if raw_status == "FINDING_EXTRACTED" and validated_citations:
                status_final = "FINDING_EXTRACTED"
                valid_findings_count += 1
            else:
                status_final = "INSUFFICIENT_EVIDENCE"
                if raw_status == "FINDING_EXTRACTED" and not validated_citations:
                    raw_text = f"Findings from '{doc.filename}' could not be verified against actual retrieved document evidence."
                validated_citations = []

            validated_findings.append(
                DocumentFinding(
                    document_id=doc_id,
                    filename=doc.filename,
                    status=status_final,
                    finding=raw_text,
                    citations=validated_citations,
                )
            )

        # 6. Final Comparative Status and Relationship Reconciliation
        if valid_findings_count == 0:
            final_status = "INSUFFICIENT_EVIDENCE"
            final_relationship = "INSUFFICIENT_EVIDENCE"
            final_summary = "Neither document contained verifiable evidence to compare the topic."
        elif valid_findings_count < len(payload.document_ids):
            final_status = "PARTIAL"
            final_relationship = "DIFFERENCE"
            raw_warnings.append("One or more documents did not have sufficient evidence for comparison.")
            final_summary = raw_summary
            final_relationship = raw_relationship if raw_relationship in ["AGREEMENT", "DIFFERENCE", "CONTRADICTION"] else "DIFFERENCE"
        else:
            final_status = "COMPLETED"
            final_summary = raw_summary
            final_relationship = raw_relationship if raw_relationship in ["AGREEMENT", "DIFFERENCE", "CONTRADICTION"] else "DIFFERENCE"

        synthesis = ComparisonSynthesis(
            relationship=final_relationship,
            summary=final_summary,
            scope_warnings=raw_warnings,
        )

        return ComparisonResponse(
            workspace_id=workspace_id,
            topic=payload.topic,
            status=final_status,
            findings=validated_findings,
            synthesis=synthesis,
            model_used=self.model_name,
        )


comparison_service = ComparisonService()
