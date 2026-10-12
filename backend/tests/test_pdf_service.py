import os
import pytest
from app.services.pdf_service import pdf_service


def test_pdf_extraction_real_files():
    """Verify page extraction and provenance on actual sample documents."""
    pdf_path = "sample_docs/Assignment1.pdf"
    if os.path.exists(pdf_path):
        result = pdf_service.extract_text_from_file(pdf_path)
        assert result.page_count == 13
        assert result.is_scanned is False
        assert len(result.pages) == 13

        # Verify page sequence provenance is strictly preserved
        for i, page in enumerate(result.pages):
            assert page["page_number"] == i + 1
            assert page["char_count"] > 0
            assert page["word_count"] > 0

        # Check expected content on page 1
        assert "Google server" in result.pages[0]["text"] or "IP address" in result.pages[0]["text"]


def test_pdf_extraction_empty_bytes():
    """Empty PDF bytes should raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        pdf_service.extract_text_from_bytes(b"")


def test_pdf_extraction_corrupted_bytes():
    """Malformed non-PDF bytes should raise ValueError."""
    with pytest.raises(ValueError, match="Malformed"):
        pdf_service.extract_text_from_bytes(b"not a valid pdf content")
