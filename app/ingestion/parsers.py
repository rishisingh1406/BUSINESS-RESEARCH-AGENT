from dataclasses import dataclass, field
from pathlib import Path

import pymupdf


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
    """Raised when a PDF cannot be parsed safely."""
 
def parse_pdf(
    file_path: str | Path,
    *,
    max_pages: int = 300,
    low_text_threshold: int = 40,
) -> PdfParseResult:
    """Extract text from every PDF page and flag pages with little text."""
    path = Path(file_path)

    if not path.is_file():
        raise PdfParseError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise PdfParseError("Expected a .pdf file")

    try:
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

            result_warnings = []
            if any(page.warnings for page in pages):
                result_warnings.append("ONE_OR_MORE_PAGES_HAVE_LOW_TEXT")

            return PdfParseResult(
                source_path=str(path),
                pages=pages,
                warnings=result_warnings,
            )

    except PdfParseError:
        raise
    except Exception as exc:
        raise PdfParseError(f"Could not parse PDF: {exc}") from exc
