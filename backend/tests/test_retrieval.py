import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_semantic_retrieval_and_scope_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Workspace A
        res_a = await client.post("/api/v1/workspaces", json={"name": "Networks Workspace"})
        assert res_a.status_code == 201
        ws_a_id = res_a.json()["id"]

        # 2. Create Workspace B
        res_b = await client.post("/api/v1/workspaces", json={"name": "APIs Workspace"})
        assert res_b.status_code == 201
        ws_b_id = res_b.json()["id"]

        # 3. Upload Assignment1.pdf to Workspace A
        pdf_1_path = "sample_docs/Assignment1.pdf"
        assert os.path.exists(pdf_1_path)
        with open(pdf_1_path, "rb") as f:
            up_1 = await client.post(
                f"/api/v1/workspaces/{ws_a_id}/documents/upload",
                files={"file": ("Assignment1.pdf", f, "application/pdf")},
            )
        assert up_1.status_code == 201
        doc_a_id = up_1.json()["id"]

        # 4. Upload Assignment2.pdf to Workspace B
        pdf_2_path = "sample_docs/Assignment2.pdf"
        assert os.path.exists(pdf_2_path)
        with open(pdf_2_path, "rb") as f:
            up_2 = await client.post(
                f"/api/v1/workspaces/{ws_b_id}/documents/upload",
                files={"file": ("Assignment2.pdf", f, "application/pdf")},
            )
        assert up_2.status_code == 201
        doc_b_id = up_2.json()["id"]

        # 5. Retrieve from Workspace A
        ret_a = await client.post(
            f"/api/v1/workspaces/{ws_a_id}/retrieve",
            json={"query": "Google server IP address", "top_k": 3},
        )
        assert ret_a.status_code == 200
        data_a = ret_a.json()
        assert data_a["total_retrieved"] > 0
        for chunk in data_a["chunks"]:
            assert chunk["document_id"] == doc_a_id
            assert chunk["filename"] == "Assignment1.pdf"
            assert chunk["page_number"] >= 1
            assert chunk["similarity_score"] is not None

        # 6. Verify Workspace Isolation: Workspace A must NOT return Workspace B documents
        assert not any(c["document_id"] == doc_b_id for c in data_a["chunks"])

        # 7. Retrieve from Workspace B
        ret_b = await client.post(
            f"/api/v1/workspaces/{ws_b_id}/retrieve",
            json={"query": "REST API request and response", "top_k": 3},
        )
        assert ret_b.status_code == 200
        data_b = ret_b.json()
        assert data_b["total_retrieved"] > 0
        for chunk in data_b["chunks"]:
            assert chunk["document_id"] == doc_b_id
            assert chunk["filename"] == "Assignment2.pdf"
            assert chunk["page_number"] >= 1
