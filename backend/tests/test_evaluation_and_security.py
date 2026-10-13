import pytest
import io
from pypdf import PdfWriter
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.main import app
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.qa import LLMAnswerOutput, QuestionRequest
from app.services.qa_service import qa_service
from tests.conftest import test_async_session


def create_blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_workspace_isolation_strictness():
    """Verify that retrieval and Q&A strictly respect workspace isolation and cannot leak chunks across workspaces."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Workspace A and Workspace B
        ws_a_res = await client.post("/api/v1/workspaces", json={"name": "Workspace A"})
        ws_b_res = await client.post("/api/v1/workspaces", json={"name": "Workspace B"})
        ws_a_id = ws_a_res.json()["id"]
        ws_b_id = ws_b_res.json()["id"]

        # Ingest real document into Workspace A
        with open("sample_docs/Assignment1.pdf", "rb") as f:
            upload_res = await client.post(
                f"/api/v1/workspaces/{ws_a_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        assert upload_res.status_code == 201

        # Query Workspace B for Workspace A's content
        query_res = await client.post(
            f"/api/v1/workspaces/{ws_b_id}/ask",
            json={"question": "What is the IP address of Google?", "top_k": 5},
        )
        assert query_res.status_code == 200
        data = query_res.json()
        assert data["status"] == "INSUFFICIENT_EVIDENCE"
        assert len(data["citations"]) == 0
        assert data["total_retrieved"] == 0


@pytest.mark.asyncio
async def test_citation_validation_filters_prompt_injected_citations():
    """Verify that if an adversarial prompt injection injects fake chunk IDs into LLM output, the server drops them."""
    async with test_async_session() as session:
        # Create Workspace, Document, and genuine DocumentChunk
        ws = Workspace(name="Injection Test Workspace")
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        doc = Document(
            workspace_id=ws.id,
            filename="genuine_manual.pdf",
            file_path="storage/test/genuine_manual.pdf",
            file_size_bytes=1024,
            page_count=1,
            status="COMPLETED",
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        real_chunk = DocumentChunk(
            document_id=doc.id,
            workspace_id=ws.id,
            page_number=1,
            chunk_index=0,
            content="Computer networks exchange packets over TCP/IP.",
            embedding=[0.1] * 768,
            char_count=45,
            word_count=7,
        )
        session.add(real_chunk)
        await session.commit()
        await session.refresh(real_chunk)

        # Mock LLM generation provider returning one genuine citation AND one injected malicious citation
        class InjectionAttackingProvider:
            def generate_grounded_answer(self, question: str, passages: list) -> dict:
                return {
                    "status": "ANSWERED",
                    "answer": "Computer networks exchange packets over TCP/IP.",
                    "cited_chunk_ids": [real_chunk.id, "fake-chunk-override-666"],
                }

        orig_provider = qa_service.provider
        qa_service.provider = InjectionAttackingProvider()

        try:
            response = await qa_service.answer_question(
                db=session,
                workspace_id=ws.id,
                payload=QuestionRequest(question="How do computer networks exchange packets?", top_k=5),
            )

            # Verification: Injected chunk MUST be dropped, only real chunk must be validated
            assert response.status == "ANSWERED"
            assert len(response.citations) == 1
            assert response.citations[0].chunk_id == real_chunk.id
            assert response.validated_citations_count == 1
            # Ensure fake chunk ID is completely absent
            assert not any(c.chunk_id == "fake-chunk-override-666" for c in response.citations)
        finally:
            qa_service.provider = orig_provider


@pytest.mark.asyncio
async def test_adversarial_abstention_when_all_citations_are_injected():
    """Verify that if an adversarial prompt causes the LLM to only cite fake chunk IDs, server forces abstention."""
    async with test_async_session() as session:
        ws = Workspace(name="Full Injection Workspace")
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        doc = Document(
            workspace_id=ws.id,
            filename="doc.pdf",
            file_path="storage/test/doc.pdf",
            file_size_bytes=500,
            page_count=1,
            status="COMPLETED",
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        real_chunk = DocumentChunk(
            document_id=doc.id,
            workspace_id=ws.id,
            page_number=1,
            chunk_index=0,
            content="Real text.",
            embedding=[0.2] * 768,
            char_count=10,
            word_count=2,
        )
        session.add(real_chunk)
        await session.commit()

        # Attacker injects exclusively hallucinated citations
        class TotalHallucinationProvider:
            def generate_grounded_answer(self, question: str, passages: list) -> dict:
                return {
                    "status": "ANSWERED",
                    "answer": "Fake answer bypassing constraints.",
                    "cited_chunk_ids": ["non-existent-chunk-1", "non-existent-chunk-2"],
                }

        orig_provider = qa_service.provider
        qa_service.provider = TotalHallucinationProvider()

        try:
            response = await qa_service.answer_question(
                db=session,
                workspace_id=ws.id,
                payload=QuestionRequest(question="Adversarial attack query?", top_k=5),
            )

            # Must abstain cleanly!
            assert response.status == "INSUFFICIENT_EVIDENCE"
            assert response.validated_citations_count == 0
            assert len(response.citations) == 0
            assert response.abstention_reason == "NO_VALID_CITATIONS_VERIFIED"
        finally:
            qa_service.provider = orig_provider


@pytest.mark.asyncio
async def test_document_deletion_cascades_completely():
    """Verify that deleting a document purges all related chunks and prevents subsequent retrieval."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create workspace and upload doc
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Cascade WS"})
        ws_id = ws_res.json()["id"]

        with open("sample_docs/Assignment1.pdf", "rb") as f:
            upload_res = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        assert upload_res.status_code == 201
        doc_id = upload_res.json()["id"]

        # Confirm chunks exist in DB
        async with test_async_session() as session:
            chunks = (
                await session.execute(
                    select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
                )
            ).scalars().all()
            assert len(chunks) >= 1

        # Delete document
        del_res = await client.delete(f"/api/v1/workspaces/{ws_id}/documents/{doc_id}")
        assert del_res.status_code == 204

        # Confirm chunks were deleted
        async with test_async_session() as session:
            chunks_after = (
                await session.execute(
                    select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
                )
            ).scalars().all()
            assert len(chunks_after) == 0

        # Query workspace should now return empty / abstention
        query_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/ask",
            json={"question": "What is the IP address of Google?"},
        )
        assert query_res.json()["status"] == "INSUFFICIENT_EVIDENCE"


@pytest.mark.asyncio
async def test_scanned_pdf_rejection():
    """Verify that uploading a blank/scanned PDF without extractable text is marked UNSUPPORTED_SCANNED_PDF."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Scanned PDF WS"})
        ws_id = ws_res.json()["id"]

        blank_bytes = create_blank_pdf_bytes()
        upload_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/documents/upload",
            files={"file": ("blank_scan.pdf", blank_bytes, "application/pdf")},
        )
        assert upload_res.status_code == 201
        data = upload_res.json()
        assert data["status"] == "UNSUPPORTED_SCANNED_PDF"
        assert "no extractable text" in data["error_message"].lower()
