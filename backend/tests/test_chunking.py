from app.services.chunking_service import chunking_service


def test_chunking_preserves_page_boundaries():
    """Verify that chunks never span across multiple pages."""
    pages = [
        {"page_number": 1, "text": "This is page one text. " * 50},
        {"page_number": 2, "text": "This is page two text. " * 50},
    ]

    chunks = chunking_service.chunk_document_pages(pages)
    assert len(chunks) >= 2

    for c in chunks:
        # Every chunk belongs to exactly one page
        assert c["page_number"] in [1, 2]
        if c["page_number"] == 1:
            assert "page two" not in c["content"]
        if c["page_number"] == 2:
            assert "page one" not in c["content"]


def test_chunking_metadata():
    """Verify chunk indices and word counts."""
    pages = [
        {"page_number": 1, "text": "Short intro on page one."},
        {"page_number": 2, "text": "Second page with more details."},
    ]
    chunks = chunking_service.chunk_document_pages(pages)
    assert len(chunks) == 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1
    assert chunks[0]["word_count"] == 5
