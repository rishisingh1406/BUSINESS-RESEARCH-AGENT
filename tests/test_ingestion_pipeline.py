from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.registration import InMemoryRegistrationStore
from app.ingestion.storage import StorageResolutionError
from app.schema import DocumentIngestionRequest, IngestionStatus


class FakeChunkStore:
    """In-memory chunk store that records what the pipeline persists."""

    def __init__(self) -> None:
        self.replaced_chunks = []

    def replace_document_chunks(
        self,
        document_id: str,
        collection_id: str,
        chunks,
    ) -> int:
        self.replaced_chunks = list(chunks)
        return len(chunks)


def test_pipeline_delegates_registration_to_injected_store(
    tmp_path: Path,
):
    store = InMemoryRegistrationStore()
    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FakeChunkStore(),
    )

    document = tmp_path / "annual-report.pdf"
    document.write_bytes(b"%PDF-test")

    request = DocumentIngestionRequest(
        document_id="pipeline-doc-1",
        collection_id="pipeline-collection-1",
        original_filename="annual-report.pdf",
        content_sha256="a" * 64,
        content_type="application/pdf",
        file_size_bytes=document.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=document.as_uri(),
    )

    result = pipeline.register(request)

    assert result.document_id == "pipeline-doc-1"
    assert result.collection_id == "pipeline-collection-1"
    assert result.status == IngestionStatus.QUEUED


def test_pipeline_rejects_invalid_storage_uri_before_processing():
    store = InMemoryRegistrationStore()
    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FakeChunkStore(),
    )

    request = DocumentIngestionRequest(
        document_id="pipeline-doc-invalid",
        collection_id="pipeline-collection-1",
        original_filename="annual-report.pdf",
        content_sha256="b" * 64,
        content_type="application/pdf",
        file_size_bytes=1024,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri="s3://bucket/annual-report.pdf",
    )

    with pytest.raises(StorageResolutionError):
        pipeline.register(request)


def test_pipeline_processes_markdown_and_returns_chunk_metadata(
    tmp_path: Path,
):
    store = InMemoryRegistrationStore()
    chunk_store = FakeChunkStore()
    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=chunk_store,
    )

    document = tmp_path / "annual-report.md"
    document.write_text(
        "# Annual Report\n\nRevenue increased from 100 to 120.",
        encoding="utf-8",
    )

    request = DocumentIngestionRequest(
        document_id="pipeline-doc-process-1",
        collection_id="pipeline-collection-1",
        original_filename="annual-report.md",
        content_sha256="c" * 64,
        content_type="text/markdown",
        file_size_bytes=document.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=document.as_uri(),
    )

    registration = pipeline.register(request)
    assert registration.status == IngestionStatus.QUEUED

    result = pipeline.process(request)

    assert result.document_id == "pipeline-doc-process-1"
    assert result.collection_id == "pipeline-collection-1"
    assert result.extracted_pages == 1
    assert len(result.chunk_ids) >= 1
    assert result.status == IngestionStatus.COMPLETED

    # Verify that chunks were actually persisted before status flipped.
    assert len(chunk_store.replaced_chunks) == len(result.chunk_ids)
    assert [c.chunk_id for c in chunk_store.replaced_chunks] == result.chunk_ids

    # Verify that processing updated the canonical stored status.
    assert (
        store._statuses["pipeline-doc-process-1"]
        == IngestionStatus.COMPLETED
    )


def test_pipeline_quarantines_malformed_pdf(
    tmp_path: Path,
):
    store = InMemoryRegistrationStore()
    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FakeChunkStore(),
    )

    document = tmp_path / "malformed-report.pdf"
    document.write_bytes(b"This is not a valid PDF file.")

    request = DocumentIngestionRequest(
        document_id="pipeline-doc-malformed-1",
        collection_id="pipeline-collection-1",
        original_filename="malformed-report.pdf",
        content_sha256="d" * 64,
        content_type="application/pdf",
        file_size_bytes=document.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=document.as_uri(),
    )

    registration = pipeline.register(request)
    assert registration.status == IngestionStatus.QUEUED

    result = pipeline.process(request)

    assert result.status == IngestionStatus.QUARANTINED
    assert result.error_message
    assert (
        store._statuses["pipeline-doc-malformed-1"]
        == IngestionStatus.QUARANTINED
    )


def test_pipeline_moves_malformed_pdf_to_quarantine_and_records_location(
    tmp_path: Path,
):
    store = InMemoryRegistrationStore()
    quarantine_dir = tmp_path / "quarantine"

    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FakeChunkStore(),
        quarantine_dir=quarantine_dir,
    )

    document = tmp_path / "malformed-report.pdf"
    document.write_bytes(b"This is not a valid PDF file.")

    request = DocumentIngestionRequest(
        document_id="pipeline-doc-quarantine-move-1",
        collection_id="pipeline-collection-1",
        original_filename="malformed-report.pdf",
        content_sha256="e" * 64,
        content_type="application/pdf",
        file_size_bytes=document.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=document.as_uri(),
    )

    pipeline.register(request)
    result = pipeline.process(request)

    quarantined_file = quarantine_dir / document.name

    assert result.status == IngestionStatus.QUARANTINED
    assert not document.exists()
    assert quarantined_file.is_file()
    assert result.quarantine_uri == quarantined_file.as_uri()
    assert (
        store._statuses["pipeline-doc-quarantine-move-1"]
        == IngestionStatus.QUARANTINED
    )


def test_duplicate_registration_does_not_process_duplicate_file(
    tmp_path: Path,
):
    store = InMemoryRegistrationStore()
    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FakeChunkStore(),
    )

    original_file = tmp_path / "original.md"
    original_file.write_text(
        "# Annual Report\n\nRevenue increased.",
        encoding="utf-8",
    )

    duplicate_file = tmp_path / "duplicate.md"
    duplicate_file.write_text(
        "# Annual Report\n\nRevenue increased.",
        encoding="utf-8",
    )

    original_request = DocumentIngestionRequest(
        document_id="duplicate-test-original",
        collection_id="duplicate-test-collection",
        original_filename="original.md",
        content_sha256="e" * 64,
        content_type="text/markdown",
        file_size_bytes=original_file.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=original_file.as_uri(),
    )

    duplicate_request = DocumentIngestionRequest(
        document_id="duplicate-test-copy",
        collection_id="duplicate-test-collection",
        original_filename="duplicate.md",
        content_sha256="e" * 64,
        content_type="text/markdown",
        file_size_bytes=duplicate_file.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=duplicate_file.as_uri(),
    )

    original_registration = pipeline.register(original_request)
    assert original_registration.status == IngestionStatus.QUEUED

    duplicate_registration = pipeline.register(duplicate_request)
    assert duplicate_registration.status == IngestionStatus.DUPLICATE

    result = pipeline.process(
        duplicate_request,
        registration=duplicate_registration,
    )

    assert result.status == IngestionStatus.DUPLICATE
    assert result.document_id == "duplicate-test-original"
    assert (
        result.duplicate_of_document_id
        == "duplicate-test-original"
    )
    assert result.chunk_ids == []
    assert duplicate_file.exists()
    assert (
        store._statuses["duplicate-test-original"]
        == IngestionStatus.QUEUED
    )


def test_process_skips_duplicate_without_registration_argument(
    tmp_path: Path,
):
    store = InMemoryRegistrationStore()
    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FakeChunkStore(),
    )

    original_file = tmp_path / "original-no-arg.md"
    original_file.write_text("# Report\n\nRevenue increased.", encoding="utf-8")

    duplicate_file = tmp_path / "duplicate-no-arg.md"
    duplicate_file.write_text("# Report\n\nRevenue increased.", encoding="utf-8")

    original_request = DocumentIngestionRequest(
        document_id="no-arg-original",
        collection_id="no-arg-collection",
        original_filename=original_file.name,
        content_sha256="f" * 64,
        content_type="text/markdown",
        file_size_bytes=original_file.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=original_file.as_uri(),
    )

    duplicate_request = DocumentIngestionRequest(
        document_id="no-arg-duplicate",
        collection_id="no-arg-collection",
        original_filename=duplicate_file.name,
        content_sha256="f" * 64,
        content_type="text/markdown",
        file_size_bytes=duplicate_file.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=duplicate_file.as_uri(),
    )

    pipeline.register(original_request)
    pipeline.register(duplicate_request)

    # Intentionally omit the registration argument.
    result = pipeline.process(duplicate_request)

    assert result.status == IngestionStatus.DUPLICATE
    assert result.document_id == "no-arg-original"
    assert result.duplicate_of_document_id == "no-arg-original"
    assert result.chunk_ids == []
    assert duplicate_file.exists()
    assert store._statuses["no-arg-original"] == IngestionStatus.QUEUED


def test_process_does_not_reprocess_completed_document(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = InMemoryRegistrationStore()
    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FakeChunkStore(),
    )

    document = tmp_path / "completed-report.md"
    document.write_text("# Report\n\nRevenue increased.", encoding="utf-8")

    request = DocumentIngestionRequest(
        document_id="completed-doc-1",
        collection_id="completed-collection",
        original_filename=document.name,
        content_sha256="a" * 64,
        content_type="text/markdown",
        file_size_bytes=document.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=document.as_uri(),
    )

    pipeline.register(request)
    first_result = pipeline.process(request)
    assert first_result.status == IngestionStatus.COMPLETED

    def fail_if_parsed(*args, **kwargs):
        pytest.fail("Completed document was parsed again")

    monkeypatch.setattr(
        "app.ingestion.pipeline.parse_document",
        fail_if_parsed,
    )

    second_result = pipeline.process(request)

    assert second_result.status == IngestionStatus.COMPLETED
    assert second_result.document_id == first_result.document_id


def test_pipeline_does_not_mark_completed_when_chunk_store_fails(
    tmp_path: Path,
):
    """The invariant: no COMPLETED unless chunks are persisted."""

    store = InMemoryRegistrationStore()

    class FailingChunkStore:
        def replace_document_chunks(
            self,
            document_id: str,
            collection_id: str,
            chunks,
        ) -> int:
            raise RuntimeError("chunk store unavailable")

    pipeline = IngestionPipeline(
        registration_store=store,
        chunk_store=FailingChunkStore(),
    )

    document = tmp_path / "annual-report.md"
    document.write_text("# Report\n\nRevenue increased.", encoding="utf-8")

    request = DocumentIngestionRequest(
        document_id="failed-chunk-store-doc",
        collection_id="failed-chunk-store-collection",
        original_filename=document.name,
        content_sha256="9" * 64,
        content_type="text/markdown",
        file_size_bytes=document.stat().st_size,
        upload_timestamp=datetime(2026, 10, 13, tzinfo=timezone.utc),
        storage_uri=document.as_uri(),
    )

    pipeline.register(request)

    with pytest.raises(RuntimeError, match="chunk store unavailable"):
        pipeline.process(request)

    # Document must stay QUEUED so a retry can pick it up.
    assert (
        store._statuses["failed-chunk-store-doc"]
        == IngestionStatus.QUEUED
    )