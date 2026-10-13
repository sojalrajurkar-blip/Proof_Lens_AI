import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_passage_inspection_endpoint():
    """Verify that a user can inspect a specific cited passage and its context."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create workspace
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Passage Inspection Workspace"})
        assert ws_res.status_code == 201
        ws_id = ws_res.json()["id"]

        # 2. Upload Assignment1.pdf
        with open("sample_docs/Assignment1.pdf", "rb") as f:
            up_res = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        assert up_res.status_code == 201
        doc_id = up_res.json()["id"]

        # 3. Retrieve a passage to obtain a genuine chunk_id
        ret_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/retrieve",
            json={"query": "Google server IP address", "top_k": 1},
        )
        assert ret_res.status_code == 200
        chunk_id = ret_res.json()["chunks"][0]["chunk_id"]

        # 4. Inspect the specific passage
        inspect_res = await client.get(
            f"/api/v1/workspaces/{ws_id}/documents/{doc_id}/passages/{chunk_id}"
        )
        assert inspect_res.status_code == 200
        passage = inspect_res.json()

        assert passage["chunk_id"] == chunk_id
        assert passage["document_id"] == doc_id
        assert passage["workspace_id"] == ws_id
        assert passage["filename"] == "Assignment1.pdf"
        assert passage["page_number"] >= 1
        assert len(passage["content"]) > 0
        assert passage["char_count"] > 0
        assert passage["word_count"] > 0

        # 5. Non-existent chunk returns 404
        bad_res = await client.get(
            f"/api/v1/workspaces/{ws_id}/documents/{doc_id}/passages/fake-chunk-id"
        )
        assert bad_res.status_code == 404


@pytest.mark.asyncio
async def test_cross_document_comparison_success():
    """Verify comparison across two documents extracts findings with citations and comparative synthesis."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Comparison Workspace"})
        ws_id = ws_res.json()["id"]

        # Upload Assignment1.pdf
        with open("sample_docs/Assignment1.pdf", "rb") as f:
            up_1 = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        doc1_id = up_1.json()["id"]

        # Upload Assignment2.pdf
        with open("sample_docs/Assignment2.pdf", "rb") as f:
            up_2 = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment2.pdf", f, "application/pdf")},
            )
        doc2_id = up_2.json()["id"]

        # Compare documents on communication
        comp_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/compare",
            json={
                "topic": "How is network communication handled?",
                "document_ids": [doc1_id, doc2_id],
                "top_k_per_document": 2,
            },
        )
        assert comp_res.status_code == 200
        data = comp_res.json()

        assert data["workspace_id"] == ws_id
        assert data["status"] == "COMPLETED"
        assert len(data["findings"]) == 2

        # Check each document finding has its citations
        for finding in data["findings"]:
            assert finding["document_id"] in [doc1_id, doc2_id]
            assert finding["status"] == "FINDING_EXTRACTED"
            assert len(finding["finding"]) > 0
            assert len(finding["citations"]) >= 1
            for cit in finding["citations"]:
                assert cit["document_id"] == finding["document_id"]
                assert cit["filename"] in ["Assignment1.pdf", "Assignment2.pdf"]
                assert cit["page_number"] >= 1

        # Check synthesis
        synthesis = data["synthesis"]
        assert synthesis["relationship"] in ["AGREEMENT", "DIFFERENCE", "CONTRADICTION"]
        assert len(synthesis["summary"]) > 0


@pytest.mark.asyncio
async def test_cross_document_comparison_unsupported_abstention():
    """Verify that comparing documents on an unsupported topic results in clean abstention."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Comparison Abstention WS"})
        ws_id = ws_res.json()["id"]

        with open("sample_docs/Assignment1.pdf", "rb") as f:
            up_1 = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        doc1_id = up_1.json()["id"]

        with open("sample_docs/Assignment2.pdf", "rb") as f:
            up_2 = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment2.pdf", f, "application/pdf")},
            )
        doc2_id = up_2.json()["id"]

        comp_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/compare",
            json={
                "topic": "Unsupported recipe for making vanilla ice cream with missing evidence",
                "document_ids": [doc1_id, doc2_id],
            },
        )
        assert comp_res.status_code == 200
        data = comp_res.json()

        assert data["status"] == "INSUFFICIENT_EVIDENCE"
        assert data["synthesis"]["relationship"] == "INSUFFICIENT_EVIDENCE"
        for finding in data["findings"]:
            assert finding["status"] == "INSUFFICIENT_EVIDENCE"
            assert finding["citations"] == []


@pytest.mark.asyncio
async def test_cross_document_comparison_hallucinated_citations_rejected():
    """Verify that hallucinated citation IDs in comparison findings are filtered by the server."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Comparison Hallucination WS"})
        ws_id = ws_res.json()["id"]

        with open("sample_docs/Assignment1.pdf", "rb") as f:
            up_1 = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        doc1_id = up_1.json()["id"]

        with open("sample_docs/Assignment2.pdf", "rb") as f:
            up_2 = await client.post(
                f"/api/v1/workspaces/{ws_id}/documents/upload",
                files={"file": ("Assignment2.pdf", f, "application/pdf")},
            )
        doc2_id = up_2.json()["id"]

        # Keyword 'hallucinate' triggers mock provider to return a fake chunk ID
        comp_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/compare",
            json={
                "topic": "Compare protocols and hallucinate fake chunk",
                "document_ids": [doc1_id, doc2_id],
            },
        )
        assert comp_res.status_code == 200
        data = comp_res.json()

        for finding in data["findings"]:
            for cit in finding["citations"]:
                assert cit["chunk_id"] != "hallucinated-fake-chunk-id"


@pytest.mark.asyncio
async def test_cross_document_comparison_requires_at_least_two_documents():
    """Verify request validation fails if fewer than 2 documents are provided."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Validation WS"})
        ws_id = ws_res.json()["id"]

        # Only 1 document id provided
        comp_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/compare",
            json={
                "topic": "Network comparison",
                "document_ids": ["doc-1"],
            },
        )
        assert comp_res.status_code == 422


@pytest.mark.asyncio
async def test_cross_document_comparison_nonexistent_document():
    """Verify HTTP 404 when a provided document ID does not exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "404 WS"})
        ws_id = ws_res.json()["id"]

        comp_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/compare",
            json={
                "topic": "Compare networks",
                "document_ids": ["non-existent-doc-1", "non-existent-doc-2"],
            },
        )
        assert comp_res.status_code == 404
