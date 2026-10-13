
import pytest

from app.ingestion.parsers import PdfParseError, parse_document


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("report.txt", "Plain text report content."),
        ("report.md", "# Report\nMarkdown content."),
        (
            "report.html",
            "<html><body>HTML report content.</body></html>",
        ),
    ],
)
def test_text_formats_reject_files_over_size_limit(
    tmp_path, filename, content
):
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    with pytest.raises(PdfParseError, match="(?i)file size"):

        parse_document(path, max_file_size_bytes=1)


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("report.txt", "Short text"),
        ("report.md", "# Short report"),
        ("report.html", "<p>Short report</p>"),
    ],
)
def test_text_formats_accept_files_under_size_limit(
    tmp_path, filename, content
):
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")

    result = parse_document(
        path,
        max_file_size_bytes=1024,
        low_text_threshold=1,
    )

    assert len(result.pages) == 1
    assert result.pages[0].text



import pytest

from app.ingestion.parsers import (
    PdfParseError,
    parse_html,
    parse_markdown,
    parse_txt,
)




@pytest.mark.parametrize(
    ("parser", "filename"),
    [
        (parse_txt, "invalid.txt"),
        (parse_markdown, "invalid.md"),
        (parse_html, "invalid.html"),
    ],
)
def test_text_parsers_report_invalid_utf8_clearly(
    tmp_path, parser, filename
):
    file_path = tmp_path / filename
    file_path.write_bytes(b"\x80\x81\xff")

    with pytest.raises(PdfParseError) as exc_info:
        parser(file_path)

    message = str(exc_info.value).lower()
    assert "encoding" in message or "utf-8" in message



@pytest.mark.parametrize(
    ("parser", "filename", "content"),
    [
        (parse_txt, "valid.txt", "Revenue: ₹500".encode("utf-8-sig")),
        (parse_markdown, "valid.md", "# Financial Report".encode("utf-8-sig")),
        (parse_html, "valid.html", "<html><body>Report</body></html>".encode("utf-8-sig")),
    ],
)
def test_text_parsers_accept_utf8_bom(tmp_path, parser, filename, content):
    file_path = tmp_path / filename
    file_path.write_bytes(content)

    result = parser(file_path)

    assert result is not None



@pytest.mark.parametrize(
    ("parser", "filename"),
    [
        (parse_txt, "empty.txt"),
        (parse_markdown, "empty.md"),
        (parse_html, "empty.html"),
    ],
)
def test_empty_documents_return_empty_text_with_warning(
    tmp_path, parser, filename
):
    path = tmp_path / filename
    path.write_text("", encoding="utf-8")

    result = parser(path, low_text_threshold=1)

    assert result.pages[0].text == ""
    assert "LOW_EXTRACTABLE_TEXT" in result.pages[0].warnings
