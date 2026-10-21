import os
from uuid import uuid4

import psycopg
import pytest

from app.ingestion.chunk_store import PostgresChunkStore
from app.ingestion.embedding_store import ChunkEmbedding, PostgresEmbeddingStore
from app.ingestion.registration import PostgresRegistrationStore
from app.schema import DocumentIngestionRequest, ExtractedChunk

DATABASE_URL = os.getenv("TEST_DATABASE_URL")
EMBEDDING_DIM = 384
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

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


def make_chunk(*, document_id: str, collection_id: str) -> ExtractedChunk:
    text = "Example financial filing text."
    return ExtractedChunk(
        chunk_id=f"chunk-{uuid4().hex}",
        document_id=document_id,
        collection_id=collection_id,
        chunk_text=text,
        page_number=1,
        section_title="Financial Results",
        start_offset=0,
        end_offset=len(text),
        extraction_method="text",
        extraction_warnings=[],
        metadata={},
    )


@pytest.fixture
def stores():
    collection_id = f"emb-test-{uuid4().hex}"
    registration_store = PostgresRegistrationStore(DATABASE_URL)
    chunk_store = PostgresChunkStore(DATABASE_URL)
    embedding_store = PostgresEmbeddingStore(DATABASE_URL)

    def register_and_chunk(num_chunks: int = 2):
        request = make_request(collection_id=collection_id)
        registration_store.register(request)
        chunks = [
            make_chunk(
                document_id=request.document_id,
                collection_id=collection_id,
            )
            for _ in range(num_chunks)
        ]
        chunk_store.insert_chunks(chunks)
        return request.document_id, chunks

    yield embedding_store, register_and_chunk, collection_id

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM chunk_embeddings
                WHERE chunk_id IN (
                    SELECT chunk_id FROM document_chunks
                    WHERE collection_id = %s
                )
                """,
                (collection_id,),
            )
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


def test_insert_embeddings_persists_rows(stores):
    embedding_store, register_and_chunk, _ = stores
    _, chunks = register_and_chunk(num_chunks=2)

    vector = [0.1] * EMBEDDING_DIM
    embeddings = [
        ChunkEmbedding(chunk_id=c.chunk_id, embedding=vector) for c in chunks
    ]

    inserted = embedding_store.insert_embeddings(MODEL_NAME, embeddings)

    assert inserted == 2

    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            """
            SELECT chunk_id, embedding_model, embedding::text
            FROM chunk_embeddings
            WHERE chunk_id = ANY(%s)
            """,
            ([c.chunk_id for c in chunks],),
        ).fetchall()

    assert len(rows) == 2
    for row in rows:
        assert row[1] == MODEL_NAME
        assert row[2].startswith("[")
        assert row[2].endswith("]")


def test_insert_embeddings_empty_returns_zero_without_connecting():
    store = PostgresEmbeddingStore(
        "postgresql://invalid:invalid@127.0.0.1:1/invalid"
    )

    def fail_if_connected():
        pytest.fail("Empty batch must not open a database connection.")

    store._connect = fail_if_connected

    assert store.insert_embeddings(MODEL_NAME, []) == 0


def test_insert_embeddings_rejects_blank_model_name(stores):
    embedding_store, register_and_chunk, _ = stores
    _, chunks = register_and_chunk(num_chunks=1)

    vector = [0.1] * EMBEDDING_DIM
    embeddings = [
        ChunkEmbedding(chunk_id=chunks[0].chunk_id, embedding=vector)
    ]

    with pytest.raises(ValueError):
        embedding_store.insert_embeddings("   ", embeddings)


def test_insert_embeddings_missing_chunk_rolls_back_entire_batch(stores):
    embedding_store, register_and_chunk, _ = stores
    _, chunks = register_and_chunk(num_chunks=1)

    vector = [0.1] * EMBEDDING_DIM
    embeddings = [
        ChunkEmbedding(chunk_id=chunks[0].chunk_id, embedding=vector),
        ChunkEmbedding(chunk_id="nonexistent-chunk", embedding=vector),
    ]

    with pytest.raises(psycopg.IntegrityError):
        embedding_store.insert_embeddings(MODEL_NAME, embeddings)

    with psycopg.connect(DATABASE_URL) as conn:
        count = conn.execute(
            "SELECT count(*) FROM chunk_embeddings WHERE chunk_id = %s",
            (chunks[0].chunk_id,),
        ).fetchone()[0]

    assert count == 0


def test_deleting_chunks_cascades_to_embeddings(stores):
    embedding_store, register_and_chunk, collection_id = stores
    _, chunks = register_and_chunk(num_chunks=2)

    vector = [0.1] * EMBEDDING_DIM
    embedding_store.insert_embeddings(
        MODEL_NAME,
        [ChunkEmbedding(chunk_id=c.chunk_id, embedding=vector) for c in chunks],
    )

    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "DELETE FROM document_chunks WHERE collection_id = %s",
            (collection_id,),
        )

    with psycopg.connect(DATABASE_URL) as conn:
        count = conn.execute(
            "SELECT count(*) FROM chunk_embeddings WHERE chunk_id = ANY(%s)",
            ([c.chunk_id for c in chunks],),
        ).fetchone()[0]

    assert count == 0