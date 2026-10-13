import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_qa_grounded_answer_and_valid_citation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create workspace
        ws_res = await client.post("/api/v1/workspaces", json={"name": "QA Test Workspace"})
        assert ws_res.status_code == 201
        ws_id = ws_res.json()["id"]

        # 2. Upload Assignment1.pdf
        pdf_path = "sample_docs/Assignment1.pdf"
        assert os.path.exists(pdf_path)
        with open(pdf_path, "rb") as f:
            up_res = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        assert up_res.status_code == 201
        doc_id = up_res.json()["id"]

        # 3. Ask answerable question
        ask_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/ask",
            json={"question": "What is an IP address and how does it route packets?"},
        )
        assert ask_res.status_code == 200
        data = ask_res.json()

        assert data["workspace_id"] == ws_id
        assert data["status"] == "ANSWERED"
        assert len(data["answer"]) > 0
        assert data["total_retrieved"] > 0
        assert data["validated_citations_count"] >= 1
        assert len(data["citations"]) >= 1

        citation = data["citations"][0]
        assert citation["document_id"] == doc_id
        assert citation["filename"] == "Assignment1.pdf"
        assert citation["page_number"] >= 1
        assert citation["chunk_index"] >= 0
        assert len(citation["excerpt"]) > 0
        assert citation["similarity_score"] is not None


@pytest.mark.asyncio
async def test_qa_explicit_abstention_on_unsupported_question():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create workspace
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Abstention Test Workspace"})
        assert ws_res.status_code == 201
        ws_id = ws_res.json()["id"]

        # 2. Upload Assignment2.pdf
        with open("sample_docs/Assignment2.pdf", "rb") as f:
            up_res = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment2.pdf", f, "application/pdf")},
            )
        assert up_res.status_code == 201

        # 3. Ask unsupported question
        ask_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/ask",
            json={"question": "What is the unsupported orbital velocity of Saturn?"},
        )
        assert ask_res.status_code == 200
        data = ask_res.json()

        assert data["status"] == "INSUFFICIENT_EVIDENCE"
        assert data["validated_citations_count"] == 0
        assert len(data["citations"]) == 0
        assert "evidence" in data["answer"].lower() or "insufficient" in data["answer"].lower()


@pytest.mark.asyncio
async def test_qa_rejection_of_hallucinated_citations():
    """Verify that if the AI provider hallucinates a non-existent chunk ID, the server filters it out."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Hallucination Test Workspace"})
        ws_id = ws_res.json()["id"]

        with open("sample_docs/Assignment1.pdf", "rb") as f:
            await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )

        # Trigger mock provider's hallucination simulation via keyword
        ask_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/ask",
            json={"question": "Explain server response and hallucinate fake chunk"},
        )
        assert ask_res.status_code == 200
        data = ask_res.json()

        # Server must reject 'invented-fake-id-999'
        for citation in data["citations"]:
            assert citation["chunk_id"] != "invented-fake-id-999"


@pytest.mark.asyncio
async def test_qa_abstention_when_zero_valid_citations():
    """Verify that if the AI claims 'ANSWERED' but cites no valid passages, the server enforces abstention."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Zero Citations Workspace"})
        ws_id = ws_res.json()["id"]

        with open("sample_docs/Assignment1.pdf", "rb") as f:
            await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )

        # Trigger mock provider's no_citations simulation
        ask_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/ask",
            json={"question": "Test question with no_citations keyword"},
        )
        assert ask_res.status_code == 200
        data = ask_res.json()

        # Enforced abstention
        assert data["status"] == "INSUFFICIENT_EVIDENCE"
        assert data["citations"] == []
        assert data["validated_citations_count"] == 0
        assert data["abstention_reason"] == "NO_VALID_CITATIONS_VERIFIED"


@pytest.mark.asyncio
async def test_qa_empty_workspace_abstention():
    """Verify clean abstention when the workspace has no documents uploaded."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Empty Workspace"})
        ws_id = ws_res.json()["id"]

        ask_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/ask",
            json={"question": "What is Python programming?"},
        )
        assert ask_res.status_code == 200
        data = ask_res.json()

        assert data["status"] == "INSUFFICIENT_EVIDENCE"
        assert data["total_retrieved"] == 0
        assert data["citations"] == []
        assert data["abstention_reason"] == "NO_PASSAGES_FOUND"


@pytest.mark.asyncio
async def test_qa_workspace_not_found():
    """Verify HTTP 404 is returned if workspace ID does not exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ask_res = await client.post(
            "/api/v1/workspaces/non-existent-uuid/ask",
            json={"question": "Hello?"},
        )
        assert ask_res.status_code == 404
