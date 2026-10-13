from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from app.schema import (
    DocumentIngestionRequest,
    DocumentIngestionResult,
    ExtractedChunk,
    IngestionStatus,
)

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
HASH = "a" * 64


def valid_request(**overrides):
    data = {
        "document_id": "doc-1",
        "collection_id": "collection-1",
        "original_filename": "annual-report.pdf",
        "content_sha256": HASH,
        "content_type": "application/pdf",
        "file_size_bytes": 1024,
        "upload_timestamp": NOW,
        "storage_uri": "s3://bucket/doc-1",
    }
    data.update(overrides)
    return DocumentIngestionRequest(**data)


def test_valid_pdf_request_passes():
    model = valid_request()
    assert model.content_type == "application/pdf"
    assert model.original_filename == "annual-report.pdf"


@pytest.mark.parametrize(
    ("raw_type", "expected"),
    [
        ("application/pdf", "application/pdf"),
        ("text/markdown", "text/markdown"),
        ("text/x-markdown", "text/markdown"),
        ("text/html; charset=utf-8", "text/html"),
        ("text/plain", "text/plain"),
    ],
)
def test_supported_content_types_are_normalized(raw_type, expected):
    assert valid_request(content_type=raw_type).content_type == expected


def test_unsupported_content_type_is_rejected():
    with pytest.raises(ValidationError):
        valid_request(content_type="application/zip")


def test_whitespace_filename_is_rejected():
    with pytest.raises(ValidationError):
        valid_request(original_filename="   ")


def test_invalid_sha256_is_rejected():
    with pytest.raises(ValidationError):
        valid_request(content_sha256="not-a-hash")


def test_blank_storage_uri_is_rejected():
    with pytest.raises(ValidationError):
        valid_request(storage_uri="   ")


def valid_result(**overrides):
    data = {
        "document_id": "doc-1",
        "collection_id": "collection-1",
        "status": IngestionStatus.COMPLETED,
        "content_sha256": HASH,
        "started_at": NOW,
        "completed_at": NOW + timedelta(seconds=3),
    }
    data.update(overrides)
    return DocumentIngestionResult(**data)


def test_duplicate_result_requires_reference():
    with pytest.raises(ValidationError):
        valid_result(status=IngestionStatus.DUPLICATE)


def test_duplicate_reference_not_allowed_for_non_duplicate():
    with pytest.raises(ValidationError):
        valid_result(duplicate_of_document_id="doc-original")


@pytest.mark.parametrize("status", [IngestionStatus.FAILED, IngestionStatus.QUARANTINED, IngestionStatus.REJECTED])
def test_failure_and_rejection_states_require_reason(status):
    with pytest.raises(ValidationError):
        valid_result(status=status)


def test_failure_state_accepts_error_message():
    result = valid_result(status=IngestionStatus.QUARANTINED, error_message="PDF cannot be parsed")
    assert result.status == IngestionStatus.QUARANTINED


def test_completed_timestamp_cannot_precede_started_timestamp():
    with pytest.raises(ValidationError):
        valid_result(completed_at=NOW - timedelta(seconds=1))


def valid_chunk(**overrides):
    data = {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "collection_id": "collection-1",
        "chunk_text": "Revenue increased during the year.",
        "start_offset": 10,
        "end_offset": 45,
    }
    data.update(overrides)
    return ExtractedChunk(**data)


def test_valid_chunk_offsets_pass():
    assert valid_chunk().end_offset == 45


def test_end_offset_before_start_offset_is_rejected():
    with pytest.raises(ValidationError):
        valid_chunk(start_offset=45, end_offset=10)


def test_chunk_offsets_can_be_omitted_for_non_text_aligned_extraction():
    chunk = valid_chunk(start_offset=None, end_offset=None)
    assert chunk.start_offset is None
    assert chunk.end_offset is None


def test_chunk_rejects_blank_text():
    with pytest.raises(ValidationError):
        valid_chunk(chunk_text="   ")
