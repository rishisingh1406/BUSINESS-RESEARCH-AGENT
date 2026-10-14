from typing import Protocol, runtime_checkable

from app.schema import (
    DocumentIngestionRequest,
    DocumentIngestionResult,
    IngestionStatus,
)


class IdempotencyKeyConflict(ValueError):
    """Raised when a request key is reused for different content."""


@runtime_checkable
class RegistrationStore(Protocol):
    """Contract for document registration and status updates."""

    def register(
        self,
        request: DocumentIngestionRequest,
    ) -> DocumentIngestionResult:
        """Register a document or resolve an existing registration."""
        ...

    def get_registered_document(
        self,
        document_id: str,
    ) -> tuple[DocumentIngestionRequest, IngestionStatus] | None:
        """Return a canonical request and its current status, if found."""
        ...

    def set_status(
        self,
        document_id: str,
        status: IngestionStatus,
    ) -> None:
        """Update the status of a registered document."""
        ...


class InMemoryRegistrationStore:
    """Test-only store without persistence or concurrency guarantees."""

    def __init__(self) -> None:
        # (collection_id, content_hash) -> canonical request
        self._documents: dict[
            tuple[str, str], DocumentIngestionRequest
        ] = {}

        # Canonical document ID -> current ingestion status
        self._statuses: dict[str, IngestionStatus] = {}

        # (collection_id, request_key) -> (content_hash, canonical_document_id)
        self._request_keys: dict[
            tuple[str, str], tuple[str, str]
        ] = {}

    def get_registered_document(
        self,
        document_id: str,
    ) -> tuple[DocumentIngestionRequest, IngestionStatus] | None:
        """Find a canonical document and its current status."""
        for request in self._documents.values():
            if request.document_id == document_id:
                return request, self._statuses[document_id]

        return None

    def set_status(
        self,
        document_id: str,
        status: IngestionStatus,
    ) -> None:
        """Update the status of an existing document."""
        if document_id not in self._statuses:
            raise KeyError(f"Unknown document_id: {document_id}")

        self._statuses[document_id] = status

    def register(
        self,
        request: DocumentIngestionRequest,
    ) -> DocumentIngestionResult:
        collection_id = request.collection_id
        content_hash = request.content_sha256.lower()
        request_key = request.collection_idempotency_key

        # 1. Recognize retries of the same request.
        if request_key:
            key = (collection_id, request_key)
            previous = self._request_keys.get(key)

            if previous is not None:
                previous_hash, canonical_document_id = previous

                if previous_hash != content_hash:
                    raise IdempotencyKeyConflict(
                        "The collection idempotency key was already used "
                        "for different content."
                    )

                return DocumentIngestionResult(
                    document_id=canonical_document_id,
                    collection_id=collection_id,
                    status=self._statuses[canonical_document_id],
                    content_sha256=content_hash,
                )

        # 2. Find existing content within the collection.
        content_key = (collection_id, content_hash)
        existing = self._documents.get(content_key)

        if existing is not None:
            canonical_id = existing.document_id

            if request_key:
                self._request_keys[(collection_id, request_key)] = (
                    content_hash,
                    canonical_id,
                )

            return DocumentIngestionResult(
                document_id=canonical_id,
                collection_id=collection_id,
                status=IngestionStatus.DUPLICATE,
                content_sha256=content_hash,
                duplicate_of_document_id=canonical_id,
            )

        # 3. Register new canonical content.
        self._documents[content_key] = request
        self._statuses[request.document_id] = IngestionStatus.QUEUED

        if request_key:
            self._request_keys[(collection_id, request_key)] = (
                content_hash,
                request.document_id,
            )

        return DocumentIngestionResult(
            document_id=request.document_id,
            collection_id=collection_id,
            status=IngestionStatus.QUEUED,
            content_sha256=content_hash,
        )
