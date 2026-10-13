
from app.ingestion.parsers import parse_markdown, parse_txt


def test_markdown_preserves_syntax(tmp_path):
    path = tmp_path / "report.md"
    content = "# Company Report\n\n**Revenue** increased."
    path.write_text(content, encoding="utf-8")

    result = parse_markdown(path)

    assert result.pages[0].text == content
    assert result.pages[0].page_number == 1



def test_txt_reads_plain_text(tmp_path):
    path = tmp_path / "report.txt"
    content = "Company revenue increased this year."
    path.write_text(content, encoding="utf-8")

    result = parse_txt(path, low_text_threshold=10)

    assert result.pages[0].text == content
    assert result.pages[0].page_number == 1
    assert result.warnings == []



def test_empty_markdown_gets_low_text_warning(tmp_path):
    path = tmp_path / "empty.md"
    path.write_text("", encoding="utf-8")

    result = parse_markdown(path)

    assert "LOW_EXTRACTABLE_TEXT" in result.pages[0].warnings
    assert "ONE_OR_MORE_PAGES_HAVE_LOW_TEXT" in result.warnings
