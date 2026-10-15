
CREATE TABLE IF NOT EXISTS ingestion_documents (
    document_id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    request_data JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_ingestion_collection_content
        UNIQUE (collection_id, content_sha256)
);

CREATE TABLE IF NOT EXISTS ingestion_request_keys (
    collection_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    canonical_document_id TEXT NOT NULL
        REFERENCES ingestion_documents(document_id),

    PRIMARY KEY (collection_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_ingestion_documents_collection
    ON ingestion_documents (collection_id);
