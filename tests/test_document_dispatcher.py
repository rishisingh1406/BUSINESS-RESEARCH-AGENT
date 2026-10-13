
import pytest

from app.ingestion.parsers import PdfParseError, parse_document


@pytest.mark.parametrize(
    ("filename", "content", "expected_text"),
    [
        ("report.md", "# Annual Report", "# Annual Report"),
        ("report.txt", "Annual report content", "Annual report content"),
        (
            "report.html",
            "<html><body><h1>Annual Report</h1></body></html>",
            "Annual Report",
        ),
    ],
)
def test_dispatches_text_formats(
    tmp_path, filename, content, expected_text
):
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")

    result = parse_document(path, low_text_threshold=1)

    assert result.pages[0].text == expected_text


def test_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "report.docx"
    path.write_text("content", encoding="utf-8")

    with pytest.raises(PdfParseError, match="Unsupported document format"):
        parse_document(path)
