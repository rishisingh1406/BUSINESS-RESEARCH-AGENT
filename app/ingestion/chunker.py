import re
from uuid import uuid4

from app.ingestion.parsers import PdfParseResult
from app.schema import ExtractedChunk


def chunk_document(
    parsed_document: PdfParseResult,
    *,
    document_id: str,
    collection_id: str,
    target_words: int = 500,
    overlap_words: int = 100,
) -> list[ExtractedChunk]:
    """Split extracted page text into overlapping chunks with provenance."""
    if target_words <= 0:
        raise ValueError("target_words must be greater than 0")

    if overlap_words < 0:
        raise ValueError("overlap_words cannot be negative")

    if overlap_words >= target_words:
        raise ValueError("overlap_words must be less than target_words")

    chunks: list[ExtractedChunk] = []
    step = target_words - overlap_words

    for page in parsed_document.pages:
        text = page.text
        word_matches = list(re.finditer(r"\S+", text))

        if not word_matches:
            continue

        start_word = 0

        while start_word < len(word_matches):
            end_word = min(
                start_word + target_words,
                len(word_matches),
            )

            start_offset = word_matches[start_word].start()
            end_offset = word_matches[end_word - 1].end()
            chunk_text = text[start_offset:end_offset]

            chunks.append(
                ExtractedChunk(
                    chunk_id=str(uuid4()),
                    document_id=document_id,
                    collection_id=collection_id,
                    chunk_text=chunk_text,
                    page_number=page.page_number,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    extraction_method="unknown",
                    extraction_warnings=list(page.warnings),
                    metadata={},
                )
            )

            if end_word == len(word_matches):
                break

            start_word += step

    return chunks
