import os
from uuid import uuid4

import psycopg
import pytest

from app.ingestion.chunk_store import PostgresChunkStore
from app.ingestion.registration import PostgresRegistrationStore
from app.schema import DocumentIngestionRequest, ExtractedChunk

DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def make_request(*, collection_id: str):
    document_id = f"test-doc-{uuid4().hex}"

    return DocumentIngestionRequest(
        document_id=document_id,
        collection_id=collection_id,
        source_id=None,
        company_id=None,
        company_name="Integration Test Company",
        financial_year="2025",
        original_filename="test-report.txt",
        content_sha256=uuid4().hex + uuid4().hex,
        content_type="text/plain",
        file_size_bytes=100,
        upload_timestamp="2026-10-14T12:00:00+00:00",
        document_type="annual_report",
        storage_uri=f"local://documents/{document_id}",
        collection_idempotency_key=None,
    )


@pytest.fixture
def stores():
    """Create isolated test documents and clean up only their rows."""
    collection_id = f"chunk-test-{uuid4().hex}"
    registration_store = PostgresRegistrationStore(DATABASE_URL)
    chunk_store = PostgresChunkStore(DATABASE_URL)

    created_document_ids = []

    def register_document():
        request = make_request(collection_id=collection_id)
        registration_store.register(request)
        created_document_ids.append(request.document_id)
        return request.document_id

    yield chunk_store, register_document, collection_id

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE collection_id = %s",
                (collection_id,),
            )
            cur.execute(
                "DELETE FROM ingestion_request_keys WHERE collection_id = %s",
                (collection_id,),
            )
            cur.execute(
                "DELETE FROM ingestion_documents WHERE collection_id = %s",
                (collection_id,),
            )


def make_chunk(
    *,
    document_id: str,
    collection_id: str,
    chunk_id: str | None = None,
    chunk_text: str = "Example financial filing text.",
) -> ExtractedChunk:
    return ExtractedChunk(
        chunk_id=chunk_id or f"chunk-{uuid4().hex}",
        document_id=document_id,
        collection_id=collection_id,
        chunk_text=chunk_text,
        page_number=1,
        section_title="Financial Results",
        start_offset=0,
        end_offset=len(chunk_text),
        extraction_method="text",
        extraction_warnings=["test-warning"],
        metadata={"source": "test", "year": 2025},
    )


def test_insert_chunks_persists_fields_and_json(stores):
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    chunks = [
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
    ]

    inserted = chunk_store.insert_chunks(chunks)

    assert inserted == 2

    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            """
            SELECT chunk_id, chunk_text, page_number, section_title,
                   extraction_method, extraction_warnings, metadata
            FROM document_chunks
            WHERE collection_id = %s
            ORDER BY chunk_id
            """,
            (collection_id,),
        ).fetchall()

    assert len(rows) == 2
    assert all(row[1] == "Example financial filing text." for row in rows)
    assert all(row[2] == 1 for row in rows)
    assert all(row[3] == "Financial Results" for row in rows)
    assert all(row[4] == "text" for row in rows)
    assert all(row[5] == ["test-warning"] for row in rows)
    assert all(row[6] == {"source": "test", "year": 2025} for row in rows)


def test_duplicate_chunk_id_rolls_back_entire_batch(stores):
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    existing = make_chunk(
        document_id=document_id,
        collection_id=collection_id,
        chunk_id="duplicate-chunk-id",
    )
    new_chunk = make_chunk(
        document_id=document_id,
        collection_id=collection_id,
        chunk_id="new-chunk-id",
    )

    assert chunk_store.insert_chunks([existing]) == 1

    with pytest.raises(psycopg.IntegrityError):
        chunk_store.insert_chunks([new_chunk, existing])

    with psycopg.connect(DATABASE_URL) as conn:
        ids = conn.execute(
            "SELECT chunk_id FROM document_chunks WHERE collection_id = %s",
            (collection_id,),
        ).fetchall()

    assert {row[0] for row in ids} == {"duplicate-chunk-id"}


def test_missing_parent_rolls_back_entire_batch(stores):
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    valid_chunk = make_chunk(
        document_id=document_id,
        collection_id=collection_id,
        chunk_id="valid-chunk",
    )
    invalid_chunk = make_chunk(
        document_id="nonexistent-document",
        collection_id=collection_id,
        chunk_id="invalid-parent-chunk",
    )

    with pytest.raises(psycopg.IntegrityError):
        chunk_store.insert_chunks([valid_chunk, invalid_chunk])

    with psycopg.connect(DATABASE_URL) as conn:
        count = conn.execute(
            "SELECT count(*) FROM document_chunks WHERE collection_id = %s",
            (collection_id,),
        ).fetchone()[0]

    assert count == 0


def test_empty_batch_returns_zero_without_connecting():
    store = PostgresChunkStore("postgresql://invalid:invalid@127.0.0.1:1/invalid")

    def fail_if_connected():
        pytest.fail("An empty batch should not open a database connection.")

    store._connect = fail_if_connected

    assert store.insert_chunks([]) == 0


def test_replace_document_chunks_is_idempotent_across_retries(stores):
    """Calling replace twice leaves exactly one copy of the latest chunks."""
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    first_batch = [
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
    ]

    assert (
        chunk_store.replace_document_chunks(
            document_id, collection_id, first_batch
        )
        == 3
    )

    # Retry with freshly generated UUID4 chunk IDs, as a real retry would.
    second_batch = [
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
    ]

    assert (
        chunk_store.replace_document_chunks(
            document_id, collection_id, second_batch
        )
        == 2
    )

    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            "SELECT chunk_id FROM document_chunks WHERE document_id = %s",
            (document_id,),
        ).fetchall()

    remaining_ids = {row[0] for row in rows}
    expected_ids = {chunk.chunk_id for chunk in second_batch}

    assert remaining_ids == expected_ids
    assert len(remaining_ids) == 2


import os
from uuid import uuid4

import psycopg
import pytest

from app.ingestion.chunk_store import PostgresChunkStore
from app.ingestion.registration import PostgresRegistrationStore
from app.schema import DocumentIngestionRequest, ExtractedChunk

DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def make_request(*, collection_id: str):
    document_id = f"test-doc-{uuid4().hex}"

    return DocumentIngestionRequest(
        document_id=document_id,
        collection_id=collection_id,
        source_id=None,
        company_id=None,
        company_name="Integration Test Company",
        financial_year="2025",
        original_filename="test-report.txt",
        content_sha256=uuid4().hex + uuid4().hex,
        content_type="text/plain",
        file_size_bytes=100,
        upload_timestamp="2026-10-14T12:00:00+00:00",
        document_type="annual_report",
        storage_uri=f"local://documents/{document_id}",
        collection_idempotency_key=None,
    )


@pytest.fixture
def stores():
    """Create isolated test documents and clean up only their rows."""
    collection_id = f"chunk-test-{uuid4().hex}"
    registration_store = PostgresRegistrationStore(DATABASE_URL)
    chunk_store = PostgresChunkStore(DATABASE_URL)

    created_document_ids = []

    def register_document():
        request = make_request(collection_id=collection_id)
        registration_store.register(request)
        created_document_ids.append(request.document_id)
        return request.document_id

    yield chunk_store, register_document, collection_id

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE collection_id = %s",
                (collection_id,),
            )
            cur.execute(
                "DELETE FROM ingestion_request_keys WHERE collection_id = %s",
                (collection_id,),
            )
            cur.execute(
                "DELETE FROM ingestion_documents WHERE collection_id = %s",
                (collection_id,),
            )


def make_chunk(
    *,
    document_id: str,
    collection_id: str,
    chunk_id: str | None = None,
    chunk_text: str = "Example financial filing text.",
) -> ExtractedChunk:
    return ExtractedChunk(
        chunk_id=chunk_id or f"chunk-{uuid4().hex}",
        document_id=document_id,
        collection_id=collection_id,
        chunk_text=chunk_text,
        page_number=1,
        section_title="Financial Results",
        start_offset=0,
        end_offset=len(chunk_text),
        extraction_method="text",
        extraction_warnings=["test-warning"],
        metadata={"source": "test", "year": 2025},
    )


def test_insert_chunks_persists_fields_and_json(stores):
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    chunks = [
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
    ]

    inserted = chunk_store.insert_chunks(chunks)

    assert inserted == 2

    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            """
            SELECT chunk_id, chunk_text, page_number, section_title,
                   extraction_method, extraction_warnings, metadata
            FROM document_chunks
            WHERE collection_id = %s
            ORDER BY chunk_id
            """,
            (collection_id,),
        ).fetchall()

    assert len(rows) == 2
    assert all(row[1] == "Example financial filing text." for row in rows)
    assert all(row[2] == 1 for row in rows)
    assert all(row[3] == "Financial Results" for row in rows)
    assert all(row[4] == "text" for row in rows)
    assert all(row[5] == ["test-warning"] for row in rows)
    assert all(row[6] == {"source": "test", "year": 2025} for row in rows)


def test_duplicate_chunk_id_rolls_back_entire_batch(stores):
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    existing = make_chunk(
        document_id=document_id,
        collection_id=collection_id,
        chunk_id="duplicate-chunk-id",
    )
    new_chunk = make_chunk(
        document_id=document_id,
        collection_id=collection_id,
        chunk_id="new-chunk-id",
    )

    assert chunk_store.insert_chunks([existing]) == 1

    with pytest.raises(psycopg.IntegrityError):
        chunk_store.insert_chunks([new_chunk, existing])

    with psycopg.connect(DATABASE_URL) as conn:
        ids = conn.execute(
            "SELECT chunk_id FROM document_chunks WHERE collection_id = %s",
            (collection_id,),
        ).fetchall()

    assert {row[0] for row in ids} == {"duplicate-chunk-id"}


def test_missing_parent_rolls_back_entire_batch(stores):
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    valid_chunk = make_chunk(
        document_id=document_id,
        collection_id=collection_id,
        chunk_id="valid-chunk",
    )
    invalid_chunk = make_chunk(
        document_id="nonexistent-document",
        collection_id=collection_id,
        chunk_id="invalid-parent-chunk",
    )

    with pytest.raises(psycopg.IntegrityError):
        chunk_store.insert_chunks([valid_chunk, invalid_chunk])

    with psycopg.connect(DATABASE_URL) as conn:
        count = conn.execute(
            "SELECT count(*) FROM document_chunks WHERE collection_id = %s",
            (collection_id,),
        ).fetchone()[0]

    assert count == 0


def test_empty_batch_returns_zero_without_connecting():
    store = PostgresChunkStore("postgresql://invalid:invalid@127.0.0.1:1/invalid")

    def fail_if_connected():
        pytest.fail("An empty batch should not open a database connection.")

    store._connect = fail_if_connected

    assert store.insert_chunks([]) == 0


def test_replace_document_chunks_is_idempotent_across_retries(stores):
    """Calling replace twice leaves exactly one copy of the latest chunks."""
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    first_batch = [
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
    ]

    assert (
        chunk_store.replace_document_chunks(
            document_id, collection_id, first_batch
        )
        == 3
    )

    second_batch = [
        make_chunk(document_id=document_id, collection_id=collection_id),
        make_chunk(document_id=document_id, collection_id=collection_id),
    ]

    assert (
        chunk_store.replace_document_chunks(
            document_id, collection_id, second_batch
        )
        == 2
    )

    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            "SELECT chunk_id FROM document_chunks WHERE document_id = %s",
            (document_id,),
        ).fetchall()

    remaining_ids = {row[0] for row in rows}
    expected_ids = {chunk.chunk_id for chunk in second_batch}

    assert remaining_ids == expected_ids
    assert len(remaining_ids) == 2


def test_load_collection_chunks_returns_ids_and_texts(stores):
    chunk_store, register_document, collection_id = stores
    document_id = register_document()

    chunks = [
        make_chunk(
            document_id=document_id,
            collection_id=collection_id,
            chunk_text="first chunk",
        ),
        make_chunk(
            document_id=document_id,
            collection_id=collection_id,
            chunk_text="second chunk",
        ),
    ]
    chunk_store.insert_chunks(chunks)

    loaded = chunk_store.load_collection_chunks(collection_id)

    assert len(loaded) == 2
    assert sorted(loaded) == sorted(
        (c.chunk_id, c.chunk_text) for c in chunks
    )
    # Loader orders by chunk_id so BM25 scores are reproducible.
    assert [cid for cid, _ in loaded] == sorted(cid for cid, _ in loaded)


def test_load_collection_chunks_empty_for_unknown_collection(stores):
    chunk_store, _, _ = stores

    assert chunk_store.load_collection_chunks("unknown-collection-id") == []