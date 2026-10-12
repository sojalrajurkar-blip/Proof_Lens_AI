import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_workspace_and_document_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a workspace
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Computer Networks Workspace"})
        assert ws_res.status_code == 201
        ws_data = ws_res.json()
        ws_id = ws_data["id"]
        assert ws_data["name"] == "Computer Networks Workspace"

        # 2. Upload Assignment1.pdf
        sample_path = "sample_docs/Assignment1.pdf"
        assert os.path.exists(sample_path), "Sample PDF must exist for integration test"

        with open(sample_path, "rb") as f:
            files = {"file": ("Assignment1.pdf", f, "application/pdf")}
            up_res = await client.post(f"/api/v1/workspaces/{ws_id}/documents/upload", files=files)

        assert up_res.status_code == 201
        doc_data = up_res.json()
        doc_id = doc_data["id"]
        assert doc_data["filename"] == "Assignment1.pdf"
        assert doc_data["status"] == "COMPLETED"
        assert doc_data["page_count"] == 13

        # 3. List documents in workspace
        list_res = await client.get(f"/api/v1/workspaces/{ws_id}/documents")
        assert list_res.status_code == 200
        docs = list_res.json()
        assert len(docs) == 1
        assert docs[0]["id"] == doc_id

        # 4. Inspect document details with extracted pages
        detail_res = await client.get(f"/api/v1/workspaces/{ws_id}/documents/{doc_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert len(detail_data["pages"]) == 13
        assert detail_data["pages"][0]["page_number"] == 1
        assert len(detail_data["pages"][0]["text"]) > 0

        # 5. Delete document
        del_res = await client.delete(f"/api/v1/workspaces/{ws_id}/documents/{doc_id}")
        assert del_res.status_code == 204

        # 6. Verify document no longer exists
        get_res = await client.get(f"/api/v1/workspaces/{ws_id}/documents/{doc_id}")
        assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_upload_invalid_file_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create workspace
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Invalid File Test"})
        ws_id = ws_res.json()["id"]

        # Try to upload a text file instead of PDF
        files = {"file": ("notes.txt", b"plain text content", "text/plain")}
        res = await client.post(f"/api/v1/workspaces/{ws_id}/documents/upload", files=files)
        assert res.status_code == 400
        assert "Only PDF documents" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_file():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ws_res = await client.post("/api/v1/workspaces", json={"name": "Empty File Test"})
        ws_id = ws_res.json()["id"]

        files = {"file": ("empty.pdf", b"", "application/pdf")}
        res = await client.post(f"/api/v1/workspaces/{ws_id}/documents/upload", files=files)
        assert res.status_code == 400
        assert "empty" in res.json()["detail"]
