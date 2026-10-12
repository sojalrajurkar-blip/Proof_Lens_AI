import os
import re
from pathlib import Path
from app.config import settings


class StorageService:
    def __init__(self, root_dir: str = settings.STORAGE_ROOT):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        # Strip path traversal attempts and keep alphanumeric, dashes, dots, underscores
        clean = os.path.basename(filename)
        clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean)
        return clean

    def get_document_path(self, workspace_id: str, document_id: str) -> Path:
        ws_dir = self.root_dir / workspace_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        target_path = (ws_dir / f"{document_id}.pdf").resolve()
        # Ensure path is strictly within self.root_dir
        if not str(target_path).startswith(str(self.root_dir)):
            raise ValueError("Invalid storage path traversal detected.")
        return target_path

    async def save_pdf(self, workspace_id: str, document_id: str, content: bytes) -> str:
        target_path = self.get_document_path(workspace_id, document_id)
        with open(target_path, "wb") as f:
            f.write(content)
        return str(target_path)

    def delete_document(self, workspace_id: str, document_id: str) -> bool:
        try:
            target_path = self.get_document_path(workspace_id, document_id)
            if target_path.exists():
                target_path.unlink()
                return True
        except Exception:
            pass
        return False


storage_service = StorageService()
