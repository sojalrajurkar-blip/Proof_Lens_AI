import io
from typing import List, Dict, Any
from pypdf import PdfReader


class PDFExtractionResult:
    def __init__(self, page_count: int, pages: List[Dict[str, Any]], is_scanned: bool = False):
        self.page_count = page_count
        self.pages = pages  # list of dicts: {"page_number": int, "text": str, "char_count": int, "word_count": int}
        self.is_scanned = is_scanned


class PDFService:
    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes) -> PDFExtractionResult:
        """Extract text from PDF bytes while strictly preserving page-level provenance."""
        if not pdf_bytes:
            raise ValueError("PDF content is empty.")

        stream = io.BytesIO(pdf_bytes)
        try:
            reader = PdfReader(stream)
        except Exception as e:
            raise ValueError(f"Malformed or unsupported PDF file: {e}")

        page_count = len(reader.pages)
        if page_count == 0:
            raise ValueError("PDF contains zero pages.")

        extracted_pages: List[Dict[str, Any]] = []
        total_text_length = 0

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            cleaned_text = page_text.strip()
            total_text_length += len(cleaned_text)

            extracted_pages.append({
                "page_number": page_num,
                "text": cleaned_text,
                "char_count": len(cleaned_text),
                "word_count": len(cleaned_text.split()) if cleaned_text else 0,
            })

        # Detection for scanned / image-only PDFs (less than 30 characters across the entire document)
        is_scanned = (total_text_length < 30 and page_count >= 1)

        return PDFExtractionResult(
            page_count=page_count,
            pages=extracted_pages,
            is_scanned=is_scanned,
        )

    @staticmethod
    def extract_text_from_file(file_path: str) -> PDFExtractionResult:
        with open(file_path, "rb") as f:
            return PDFService.extract_text_from_bytes(f.read())


pdf_service = PDFService()
