
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.ingestion.hashing import sha256_file
from app.ingestion.queue import RedisIngestionQueue
from app.ingestion.registration import RegistrationStore
from app.ingestion.storage import resolve_storage_uri
from app.schema import DocumentIngestionRequest, DocumentIngestionResult


class IngestionSubmissionService:
    """Create, register, and enqueue file-ingestion requests."""

    def __init__(
        self,
        registration_store: RegistrationStore,
        queue: RedisIngestionQueue,
    ) -> None:
        self._registration_store = registration_store
        self._queue = queue

    def submit(
        self,
        *,
        file_path: str | Path,
        collection_id: str,
        content_type: str,
        document_type: str = "annual_report",
        source_id: str | None = None,
        company_id: str | None = None,
        company_name: str | None = None,
        financial_year: str | None = None,
        collection_idempotency_key: str | None = None,
    ) -> DocumentIngestionResult:
        """Register a file using its actual content hash and enqueue it."""
        path = Path(file_path).resolve()

        if not path.is_file():
            raise ValueError(f"Input file does not exist: {path}")

        # Resolve and validate the file using the existing storage contract.
        storage_uri = path.as_uri()
        resolved_path = resolve_storage_uri(storage_uri)

        content_hash = sha256_file(resolved_path)
        file_size = resolved_path.stat().st_size

        if file_size <= 0:
            raise ValueError("Input file must not be empty.")

        request = DocumentIngestionRequest(
            document_id=str(uuid4()),
            collection_id=collection_id,
            source_id=source_id,
            company_id=company_id,
            company_name=company_name,
            financial_year=financial_year,
            original_filename=path.name,
            content_sha256=content_hash,
            content_type=content_type,
            file_size_bytes=file_size,
            upload_timestamp=datetime.now(timezone.utc),
            document_type=document_type,
            storage_uri=storage_uri,
            collection_idempotency_key=collection_idempotency_key,
        )

        result = self._registration_store.register(request)

        # Only newly registered content should create a queue job.
        if result.document_id == request.document_id:
            self._queue.enqueue(request.document_id)

        return result
