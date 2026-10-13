from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup
import pymupdf


DEFAULT_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


@dataclass
class ParsedPage:
    page_number: int
    text: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class PdfParseResult:
    source_path: str
    pages: list[ParsedPage]
    warnings: list[str] = field(default_factory=list)


class PdfParseError(Exception):
    """Raised when a document cannot be parsed safely."""


def _validate_file_size_limit(max_file_size_bytes: int) -> None:
    """Validate the configured maximum file size."""
    if max_file_size_bytes <= 0:
        raise ValueError("max_file_size_bytes must be greater than 0")


def _reject_oversized_file(
    path: Path,
    max_file_size_bytes: int,
) -> None:
    """Reject a file that exceeds the configured size limit."""
    file_size = path.stat().st_size

    if file_size > max_file_size_bytes:
        raise PdfParseError(
            f"File size {file_size} bytes exceeds "
            f"the limit of {max_file_size_bytes} bytes"
        )


def parse_pdf(
    file_path: str | Path,
    *,
    max_pages: int = 300,
    low_text_threshold: int = 40,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> PdfParseResult:
    """Extract PDF text, flag low-text pages, and warn about large files."""
    path = Path(file_path)

    if not path.is_file():
        raise PdfParseError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise PdfParseError("Expected a .pdf file")

    if max_pages < 1:
        raise ValueError("max_pages must be greater than 0")

    if low_text_threshold < 0:
        raise ValueError("low_text_threshold cannot be negative")

    if max_file_size_bytes < 0:
        raise ValueError("max_file_size_bytes cannot be negative")

    try:
        file_warnings = []

        if path.stat().st_size > max_file_size_bytes:
            file_warnings.append("LARGE_FILE_SIZE")

        with pymupdf.open(path) as document:
            if document.is_encrypted:
                raise PdfParseError("Encrypted PDFs are not supported")

            if len(document) == 0:
                raise PdfParseError("PDF contains no pages")

            if len(document) > max_pages:
                raise PdfParseError(
                    f"PDF has {len(document)} pages; maximum is {max_pages}"
                )

            pages: list[ParsedPage] = []

            for index, page in enumerate(document):
                text = page.get_text("text").strip()
                page_warnings = []

                if len(text) < low_text_threshold:
                    page_warnings.append("LOW_EXTRACTABLE_TEXT")

                pages.append(
                    ParsedPage(
                        page_number=index + 1,
                        text=text,
                        warnings=page_warnings,
                    )
                )

            result_warnings = list(file_warnings)

            if any(page.warnings for page in pages):
                result_warnings.append(
                    "ONE_OR_MORE_PAGES_HAVE_LOW_TEXT"
                )

            return PdfParseResult(
                source_path=str(path),
                pages=pages,
                warnings=result_warnings,
            )

    except PdfParseError:
        raise
    except Exception as exc:
        raise PdfParseError(f"Could not parse PDF: {exc}") from exc


def parse_html(
    file_path: str | Path,
    *,
    low_text_threshold: int = 40,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> PdfParseResult:
    """Extract readable text from HTML, excluding non-content elements."""
    path = Path(file_path)

    if not path.is_file():
        raise PdfParseError(f"HTML file not found: {path}")

    if path.suffix.lower() not in {".html", ".htm"}:
        raise PdfParseError("Expected an .html or .htm file")

    if low_text_threshold < 0:
        raise ValueError("low_text_threshold cannot be negative")

    _validate_file_size_limit(max_file_size_bytes)

    try:
        _reject_oversized_file(path, max_file_size_bytes)

        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")

        for element in soup(
            ["script", "style", "noscript", "template"]
        ):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)
        page_warnings = []

        if len(text) < low_text_threshold:
            page_warnings.append("LOW_EXTRACTABLE_TEXT")

        result_warnings = []
        if page_warnings:
            result_warnings.append("ONE_OR_MORE_PAGES_HAVE_LOW_TEXT")

        return PdfParseResult(
            source_path=str(path),
            pages=[
                ParsedPage(
                    page_number=1,
                    text=text,
                    warnings=page_warnings,
                )
            ],
            warnings=result_warnings,
        )

    except PdfParseError:
        raise
    except Exception as exc:
        raise PdfParseError(f"Could not parse HTML: {exc}") from exc


def parse_text_file(
    file_path: str | Path,
    *,
    expected_suffixes: set[str],
    low_text_threshold: int = 40,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> PdfParseResult:
    """Read a text-based document into the common parser result structure."""
    path = Path(file_path)

    if not path.is_file():
        raise PdfParseError(f"File not found: {path}")

    if path.suffix.lower() not in expected_suffixes:
        expected = ", ".join(sorted(expected_suffixes))
        raise PdfParseError(f"Expected one of these extensions: {expected}")

    if low_text_threshold < 0:
        raise ValueError("low_text_threshold cannot be negative")

    _validate_file_size_limit(max_file_size_bytes)

    try:
        _reject_oversized_file(path, max_file_size_bytes)

        text = path.read_text(encoding="utf-8-sig")
        page_warnings = []

        if len(text.strip()) < low_text_threshold:
            page_warnings.append("LOW_EXTRACTABLE_TEXT")

        result_warnings = []
        if page_warnings:
            result_warnings.append("ONE_OR_MORE_PAGES_HAVE_LOW_TEXT")

        return PdfParseResult(
            source_path=str(path),
            pages=[
                ParsedPage(
                    page_number=1,
                    text=text.strip(),
                    warnings=page_warnings,
                )
            ],
            warnings=result_warnings,
        )

    except PdfParseError:
        raise
    except Exception as exc:
        raise PdfParseError(
            f"Could not read text file: {exc}"
        ) from exc


def parse_markdown(
    file_path: str | Path,
    *,
    low_text_threshold: int = 40,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> PdfParseResult:
    """Parse Markdown while preserving its syntax."""
    return parse_text_file(
        file_path,
        expected_suffixes={".md", ".markdown"},
        low_text_threshold=low_text_threshold,
        max_file_size_bytes=max_file_size_bytes,
    )


def parse_txt(
    file_path: str | Path,
    *,
    low_text_threshold: int = 40,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> PdfParseResult:
    """Parse a plain-text document."""
    return parse_text_file(
        file_path,
        expected_suffixes={".txt"},
        low_text_threshold=low_text_threshold,
        max_file_size_bytes=max_file_size_bytes,
    )


def parse_document(
    file_path: str | Path,
    *,
    max_pages: int = 300,
    low_text_threshold: int = 40,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> PdfParseResult:
    """Dispatch a document to its format-specific parser."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf(
            path,
            max_pages=max_pages,
            low_text_threshold=low_text_threshold,
            max_file_size_bytes=max_file_size_bytes,
        )

    if suffix in {".html", ".htm"}:
        return parse_html(
            path,
            low_text_threshold=low_text_threshold,
            max_file_size_bytes=max_file_size_bytes,
        )

    if suffix in {".md", ".markdown"}:
        return parse_markdown(
            path,
            low_text_threshold=low_text_threshold,
            max_file_size_bytes=max_file_size_bytes,
        )

    if suffix == ".txt":
        return parse_txt(
            path,
            low_text_threshold=low_text_threshold,
            max_file_size_bytes=max_file_size_bytes,
        )

    raise PdfParseError(
        f"Unsupported document format: {suffix or '(no extension)'}"
    )
