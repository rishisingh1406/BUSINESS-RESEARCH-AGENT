-- 003_chunk_embeddings.sql
-- One current embedding per chunk.
-- Switching embedding models requires deleting existing rows first;
-- vectors from different models must never coexist in the same table.
-- Deleting a chunk cascades to its embedding.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    chunk_id text PRIMARY KEY
        REFERENCES document_chunks(chunk_id) ON DELETE CASCADE,
    embedding_model text NOT NULL,
    embedding vector(384) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT chunk_embeddings_model_nonblank
        CHECK (length(btrim(embedding_model)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_model
    ON chunk_embeddings (embedding_model)