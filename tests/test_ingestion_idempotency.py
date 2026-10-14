from datetime import datetime, timezone

from app.schema import DocumentIngestionRequest, IngestionStatus
from app.ingestion.registration import InMemoryRegistrationStore


NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
HASH_A = "a" * 64


def valid_request(**overrides):
    data = {
        "document_id": "doc-1",
        "collection_id": "collection-1",
        "original_filename": "annual-report.pdf",
        "content_sha256": HASH_A,
        "content_type": "application/pdf",
        "file_size_bytes": 1024,
        "upload_timestamp": NOW,
        "storage_uri": "local://documents/doc-1",
        "collection_idempotency_key": None,
    }
    data.update(overrides)
    return DocumentIngestionRequest(**data)


def test_first_upload_registers_new_document():
    store = InMemoryRegistrationStore()
    request = valid_request()

    result = store.register(request)

    assert result.document_id == request.document_id
    assert result.collection_id == request.collection_id
    assert result.content_sha256 == request.content_sha256
    assert result.status != IngestionStatus.DUPLICATE


def test_same_hash_in_same_collection_returns_duplicate():
    store = InMemoryRegistrationStore()
    original = valid_request(document_id="doc-original")
    retry = valid_request(document_id="doc-retry")

    store.register(original)
    result = store.register(retry)

    assert result.status == IngestionStatus.DUPLICATE
    assert result.duplicate_of_document_id == "doc-original"


import pytest

from app.ingestion.registration import IdempotencyKeyConflict


def test_same_key_and_hash_returns_original_registration():
    store = InMemoryRegistrationStore()

    original = valid_request(
        document_id="doc-original",
        collection_idempotency_key="request-123",
    )
    retry = valid_request(
        document_id="doc-retry",
        collection_idempotency_key="request-123",
    )

    first = store.register(original)
    second = store.register(retry)

    assert second.document_id == first.document_id
    assert second.status == first.status


def test_same_key_with_different_hash_is_rejected():
    store = InMemoryRegistrationStore()

    store.register(
        valid_request(collection_idempotency_key="request-123")
    )

    conflicting = valid_request(
        document_id="doc-other",
        content_sha256="b" * 64,
        collection_idempotency_key="request-123",
    )

    with pytest.raises(IdempotencyKeyConflict):
        store.register(conflicting)



def test_same_hash_in_different_collections_registers_independently():
    store = InMemoryRegistrationStore()

    first = store.register(
        valid_request(
            document_id="doc-collection-a",
            collection_id="collection-a",
        )
    )
    second = store.register(
        valid_request(
            document_id="doc-collection-b",
            collection_id="collection-b",
        )
    )

    assert first.status == IngestionStatus.QUEUED
    assert second.status == IngestionStatus.QUEUED
    assert first.document_id == "doc-collection-a"
    assert second.document_id == "doc-collection-b"


def test_same_key_in_different_collections_does_not_conflict():
    store = InMemoryRegistrationStore()

    first = store.register(
        valid_request(
            document_id="doc-a",
            collection_id="collection-a",
            collection_idempotency_key="request-123",
        )
    )
    second = store.register(
        valid_request(
            document_id="doc-b",
            collection_id="collection-b",
            content_sha256="b" * 64,
            collection_idempotency_key="request-123",
        )
    )

    assert first.status == IngestionStatus.QUEUED
    assert second.status == IngestionStatus.QUEUED
    assert first.document_id != second.document_id



def test_request_key_cannot_resolve_to_different_existing_content():
    store = InMemoryRegistrationStore()

    store.register(
        valid_request(
            document_id="doc-a",
            content_sha256="a" * 64,
            collection_idempotency_key="key-a",
        )
    )

    store.register(
        valid_request(
            document_id="doc-b",
            content_sha256="b" * 64,
            collection_idempotency_key="key-b",
        )
    )

    conflicting_retry = valid_request(
        document_id="doc-retry",
        content_sha256="a" * 64,
        collection_idempotency_key="key-b",
    )

    with pytest.raises(IdempotencyKeyConflict):
        store.register(conflicting_retry)


def test_request_retry_returns_original_current_status():
    store = InMemoryRegistrationStore()

    original = valid_request(
        document_id="doc-original",
        collection_idempotency_key="request-123",
    )
    first = store.register(original)

    # Simulate the original document progressing through ingestion.
    store.set_status("doc-original", IngestionStatus.INDEXED)

    retry = valid_request(
        document_id="doc-retry",
        collection_idempotency_key="request-123",
    )
    second = store.register(retry)

    assert first.document_id == "doc-original"
    assert second.document_id == "doc-original"
    assert second.status == IngestionStatus.INDEXED


def test_set_status_rejects_unknown_document():
    store = InMemoryRegistrationStore()

    with pytest.raises(KeyError, match="Unknown document_id"):
        store.set_status("missing-document", IngestionStatus.INDEXED)



def test_duplicate_with_different_request_key_returns_canonical_id():
    store = InMemoryRegistrationStore()

    original = valid_request(
        document_id="doc-original",
        collection_idempotency_key="request-original",
    )
    duplicate = valid_request(
        document_id="doc-duplicate",
        collection_idempotency_key="request-new",
    )

    first = store.register(original)
    second = store.register(duplicate)

    assert first.status == IngestionStatus.QUEUED
    assert second.status == IngestionStatus.DUPLICATE
    assert second.document_id == "doc-original"
    assert second.duplicate_of_document_id == "doc-original"
    assert second.content_sha256 == HASH_A




from app.ingestion.registration import RegistrationStore


def test_in_memory_store_satisfies_registration_protocol():
    store = InMemoryRegistrationStore()

    assert isinstance(store, RegistrationStore)
