from typing import List, Dict, Any
from app.config import settings


class ChunkingService:
    def __init__(
        self,
        chunk_size_chars: int = 1800,  # ~450-500 tokens
        chunk_overlap_chars: int = 200, # ~50 tokens
    ):
        self.chunk_size = chunk_size_chars
        self.chunk_overlap = chunk_overlap_chars
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def _split_text(self, text: str) -> List[Dict[str, Any]]:
        """Recursively split text into overlapping chunks, tracking char offsets."""
        text = text.strip()
        if not text:
            return []

        chunks: List[Dict[str, Any]] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            if end < text_len:
                # Find best separator before end
                best_split = -1
                for sep in self.separators:
                    pos = text.rfind(sep, start + self.chunk_overlap, end)
                    if pos != -1:
                        best_split = pos + len(sep)
                        break

                if best_split != -1 and best_split > start:
                    end = best_split

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "char_start": start,
                    "char_end": end,
                })

            if end >= text_len:
                break

            # Advance by step size (chunk_size - overlap)
            start = max(start + 1, end - self.chunk_overlap)

        return chunks

    def chunk_document_pages(
        self, pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk text page-by-page.
        Crucial requirement: Chunks NEVER cross page boundaries.
        Returns a list of chunk dicts:
        {
            "page_number": int,
            "chunk_index": int,
            "content": str,
            "char_start": int,
            "char_end": int,
            "char_count": int,
            "word_count": int,
        }
        """
        all_chunks: List[Dict[str, Any]] = []
        global_index = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            splits = self._split_text(page_text)

            for s in splits:
                all_chunks.append({
                    "page_number": page_num,
                    "chunk_index": global_index,
                    "content": s["content"],
                    "char_start": s["char_start"],
                    "char_end": s["char_end"],
                    "char_count": len(s["content"]),
                    "word_count": len(s["content"].split()),
                })
                global_index += 1

        return all_chunks


chunking_service = ChunkingService()
