
from app.ingestion.parsers import parse_html


def test_extracts_readable_text_and_removes_scripts(tmp_path):
    html_path = tmp_path / "report.html"
    html_path.write_text(
        """
        <html>
          <head>
            <style>.hidden { display: none; }</style>
            <script>alert('do not extract');</script>
          </head>
          <body>
            <h1>Company Report</h1>
            <p>Revenue increased this year.</p>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    result = parse_html(html_path)

    assert len(result.pages) == 1
    assert "Company Report" in result.pages[0].text
    assert "Revenue increased this year." in result.pages[0].text
    assert "alert(" not in result.pages[0].text
    assert ".hidden" not in result.pages[0].text


def test_flags_html_with_little_text(tmp_path):
    html_path = tmp_path / "empty.html"
    html_path.write_text("<html><body>x</body></html>", encoding="utf-8")

    result = parse_html(html_path, low_text_threshold=40)

    assert "LOW_EXTRACTABLE_TEXT" in result.pages[0].warnings
    assert "ONE_OR_MORE_PAGES_HAVE_LOW_TEXT" in result.warnings
