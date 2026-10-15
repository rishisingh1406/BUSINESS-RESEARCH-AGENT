
import os
from uuid import uuid4

import pytest

from app.ingestion.registration import (
    IdempotencyKeyConflict,
    PostgresRegistrationStore,
)
from app.schema import DocumentIngestionRequest, IngestionStatus


DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def make_request(
    *,
    collection_id: str,
    content_hash: str | None = None,
    idempotency_key: str | None = None,
) -> DocumentIngestionRequest:
    document_id = f"test-doc-{uuid4().hex}"
    return DocumentIngestionRequest(
        document_id=document_id,
        collection_id=collection_id,
        source_id=None,
        company_id=None,
        company_name="Integration Test Company",
        financial_year="2025",
        original_filename="test-report.txt",
        content_sha256=content_hash or uuid4().hex + uuid4().hex,
        content_type="text/plain",
        file_size_bytes=100,
        upload_timestamp="2026-10-14T12:00:00+00:00",
        document_type="annual_report",
        storage_uri=f"local://documents/{document_id}",
        collection_idempotency_key=idempotency_key,
    )


@pytest.fixture
def stores():
    assert DATABASE_URL is not None
    collection_id = f"test-collection-{uuid4().hex}"

    store_a = PostgresRegistrationStore(DATABASE_URL)
    store_b = PostgresRegistrationStore(DATABASE_URL)

    yield store_a, store_b, collection_id

    # Remove only records created for this test collection.
    with __import__("psycopg").connect(DATABASE_URL) as conn:
        conn.execute(
            "DELETE FROM ingestion_request_keys WHERE collection_id = %s",
            (collection_id,),
        )
        conn.execute(
            "DELETE FROM ingestion_documents WHERE collection_id = %s",
            (collection_id,),
        )


def test_document_persists_across_store_instances(stores):
    store_a, store_b, collection_id = stores
    request = make_request(collection_id=collection_id)

    result = store_a.register(request)
    found = store_b.get_registered_document(result.document_id)

    assert found is not None
    stored_request, status = found
    assert stored_request.document_id == result.document_id
    assert stored_request.collection_id == collection_id
    assert status == IngestionStatus.QUEUED


def test_status_update_persists_across_store_instances(stores):
    store_a, store_b, collection_id = stores
    request = make_request(collection_id=collection_id)
    result = store_a.register(request)

    store_a.set_status(result.document_id, IngestionStatus.INDEXED)

    found = store_b.get_registered_document(result.document_id)
    assert found is not None
    assert found[1] == IngestionStatus.INDEXED


def test_same_key_and_content_returns_original_status(stores):
    store_a, store_b, collection_id = stores
    content_hash = uuid4().hex + uuid4().hex
    key = f"retry-{uuid4().hex}"

    first = make_request(
        collection_id=collection_id,
        content_hash=content_hash,
        idempotency_key=key,
    )
    initial_result = store_a.register(first)
    store_a.set_status(initial_result.document_id, IngestionStatus.INDEXED)

    retry = make_request(
        collection_id=collection_id,
        content_hash=content_hash,
        idempotency_key=key,
    )
    retry_result = store_b.register(retry)

    assert retry_result.document_id == initial_result.document_id
    assert retry_result.status == IngestionStatus.INDEXED


def test_same_key_with_different_content_raises_conflict(stores):
    store_a, _, collection_id = stores
    key = f"retry-{uuid4().hex}"

    store_a.register(
        make_request(
            collection_id=collection_id,
            content_hash=uuid4().hex + uuid4().hex,
            idempotency_key=key,
        )
    )

    with pytest.raises(IdempotencyKeyConflict):
        store_a.register(
            make_request(
                collection_id=collection_id,
                content_hash=uuid4().hex + uuid4().hex,
                idempotency_key=key,
            )
        )
