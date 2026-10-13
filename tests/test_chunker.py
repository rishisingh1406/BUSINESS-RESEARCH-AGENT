from django.core.serializers import python

from app.ingestion.chunker import chunk_document
from app.ingestion.parsers import ParsedPage, PdfParseResult


def test_short_page_produces_one_chunk_with_page_provenance():
    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text="Revenue increased by 12% during the year.",
                warnings=["LOW_EXTRACTABLE_TEXT"],
            )
        ],
        warnings=["ONE_OR_MORE_PAGES_HAVE_LOW_TEXT"],
    )

    chunks = chunk_document(
        parsed_document,
        document_id="doc-1",
        collection_id="collection-1",
    )

    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk.document_id == "doc-1"
    assert chunk.collection_id == "collection-1"
    assert chunk.page_number == 1
    assert chunk.chunk_text == "Revenue increased by 12% during the year."
    assert chunk.start_offset == 0
    assert chunk.end_offset == len(chunk.chunk_text)
    assert "LOW_EXTRACTABLE_TEXT" in chunk.extraction_warnings


def test_oversized_page_is_split_with_word_overlap():
    words = [f"word{i}" for i in range(25)]
    page_text = " ".join(words)

    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(
                page_number=3,
                text=page_text,
                warnings=[],
            )
        ],
        warnings=[],
    )

    chunks = chunk_document(
        parsed_document,
        document_id="doc-1",
        collection_id="collection-1",
        target_words=10,
        overlap_words=2,
    )

    assert len(chunks) > 1
    assert all(len(chunk.chunk_text.split()) <= 10 for chunk in chunks)
    assert all(chunk.page_number == 3 for chunk in chunks)

    for previous, current in zip(chunks, chunks[1:]):
        previous_words = previous.chunk_text.split()
        current_words = current.chunk_text.split()

        assert previous_words[-2:] == current_words[:2]


def test_chunk_offsets_match_original_page_text():
    words = [f"word{i}" for i in range(25)]
    page_text = " ".join(words)

    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text=page_text,
                warnings=[],
            )
        ],
        warnings=[],
    )

    chunks = chunk_document(
        parsed_document,
        document_id="doc-1",
        collection_id="collection-1",
        target_words=10,
        overlap_words=2,
    )

    for chunk in chunks:
        original_page = parsed_document.pages[chunk.page_number - 1].text

        assert (
            original_page[chunk.start_offset:chunk.end_offset]
            == chunk.chunk_text
        )


def test_chunks_from_multiple_pages_keep_independent_offsets():
    page_one = " ".join(f"first{i}" for i in range(15))
    page_two = " ".join(f"second{i}" for i in range(15))

    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(page_number=1, text=page_one, warnings=[]),
            ParsedPage(page_number=2, text=page_two, warnings=[]),
        ],
        warnings=[],
    )

    chunks = chunk_document(
        parsed_document,
        document_id="doc-1",
        collection_id="collection-1",
        target_words=10,
        overlap_words=2,
    )

    page_one_chunks = [chunk for chunk in chunks if chunk.page_number == 1]
    page_two_chunks = [chunk for chunk in chunks if chunk.page_number == 2]

    assert page_one_chunks
    assert page_two_chunks
    assert page_one_chunks[0].start_offset == 0
    assert page_two_chunks[0].start_offset == 0

    for chunk in chunks:
        original_page = (
            page_one if chunk.page_number == 1 else page_two
        )
        assert (
            original_page[chunk.start_offset:chunk.end_offset]
            == chunk.chunk_text
        )

def test_empty_and_whitespace_only_pages_produce_no_chunks():
    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(page_number=1, text="", warnings=[]),
            ParsedPage(page_number=2, text="   \n\t  ", warnings=[]),
        ],
        warnings=[],
    )

    chunks = chunk_document(
        parsed_document,
        document_id="doc-1",
        collection_id="collection-1",
    )

    assert chunks == []


def test_invalid_chunk_settings_raise_value_error():
    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text="Revenue increased during the year.",
                warnings=[],
            )
        ],
        warnings=[],
    )

    invalid_settings = [
        {"target_words": 0, "overlap_words": 0},
        {"target_words": -1, "overlap_words": 0},
        {"target_words": 10, "overlap_words": -1},
        {"target_words": 10, "overlap_words": 10},
        {"target_words": 10, "overlap_words": 11},
    ]

    for settings in invalid_settings:
        try:
            chunk_document(
                parsed_document,
                document_id="doc-1",
                collection_id="collection-1",
                **settings,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Expected ValueError for settings: {settings}"
            )



def test_single_word_page_produces_one_chunk():
    page_text = "Revenue"
    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text=page_text,
                warnings=[],
            )
        ],
        warnings=[],
    )

    chunks = chunk_document(
        parsed_document,
        document_id="doc-1",
        collection_id="collection-1",
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_text == "Revenue"
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == len(page_text)


def test_exact_chunk_size_produces_one_chunk():
    words = [f"word{i}" for i in range(10)]
    page_text = " ".join(words)
    parsed_document = PdfParseResult(
        source_path="annual-report.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text=page_text,
                warnings=[],
            )
        ],
        warnings=[],
    )

    chunks = chunk_document(
        parsed_document,
        document_id="doc-1",
        collection_id="collection-1",
        target_words=10,
        overlap_words=2,
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_text == page_text
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == len(page_text)
