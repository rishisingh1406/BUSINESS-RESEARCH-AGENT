
import pymupdf
import pytest

from app.ingestion.parsers import PdfParseError, parse_pdf


def create_pdf(path, page_texts):
    """Create a test PDF with the supplied text on each page."""
    document = pymupdf.open()

    for text in page_texts:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)

    document.save(path)
    document.close()
    return path


def test_extracts_text_and_preserves_page_numbers(tmp_path):
    pdf_path = create_pdf(
        tmp_path / "annual_report.pdf",
        [
            "Revenue increased during the reporting period.",
            "Operating expenses also increased.",
        ],
    )

    result = parse_pdf(pdf_path)

    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert "Revenue increased" in result.pages[0].text
    assert result.pages[1].page_number == 2
    assert "Operating expenses" in result.pages[1].text


def test_flags_low_text_page_without_dropping_it(tmp_path):
    pdf_path = create_pdf(
        tmp_path / "mixed_report.pdf",
        [
            "This page contains enough extractable text for testing.",
            "",
        ],
    )

    result = parse_pdf(pdf_path)

    assert len(result.pages) == 2
    assert result.pages[1].text == ""
    assert "LOW_EXTRACTABLE_TEXT" in result.pages[1].warnings
    assert "ONE_OR_MORE_PAGES_HAVE_LOW_TEXT" in result.warnings


def test_missing_file_raises_parse_error(tmp_path):
    with pytest.raises(PdfParseError, match="not found"):
        parse_pdf(tmp_path / "missing.pdf")


def test_non_pdf_extension_is_rejected(tmp_path):
    text_file = tmp_path / "report.txt"
    text_file.write_text("Not a PDF", encoding="utf-8")

    with pytest.raises(PdfParseError, match="Expected a .pdf file"):
        parse_pdf(text_file)


def test_page_limit_is_enforced(tmp_path):
    pdf_path = create_pdf(
        tmp_path / "three_pages.pdf",
        ["Page one", "Page two", "Page three"],
    )

    with pytest.raises(PdfParseError, match="maximum is 2"):
        parse_pdf(pdf_path, max_pages=2)


def test_invalid_pdf_content_raises_parse_error(tmp_path):
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_bytes(b"This is not a valid PDF")

    with pytest.raises(PdfParseError, match="Could not parse PDF"):
        parse_pdf(invalid_pdf)



def test_large_pdf_is_parsed_with_warning(tmp_path):
    pdf_path = create_pdf(
        tmp_path / "large_report.pdf",
        ["This PDF should still be parsed despite exceeding the configured limit."],
    )

    result = parse_pdf(pdf_path, max_file_size_bytes=1)

    assert len(result.pages) == 1
    assert "This PDF should still be parsed" in result.pages[0].text
    assert "LARGE_FILE_SIZE" in result.warnings
