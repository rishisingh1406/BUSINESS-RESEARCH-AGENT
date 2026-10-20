CREATE UNIQUE INDEX IF NOT EXISTS uq_ingestion_documents_document_collection
    ON ingestion_documents (document_id, collection_id);

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id TEXT PRIMARY KEY,

    document_id TEXT NOT NULL,
    collection_id TEXT NOT NULL,

    chunk_text TEXT NOT NULL
        CHECK (length(btrim(chunk_text)) > 0),

    page_number INTEGER
        CHECK (page_number IS NULL OR page_number >= 1),

    section_title TEXT,

    start_offset INTEGER
        CHECK (start_offset IS NULL OR start_offset >= 0),

    end_offset INTEGER
        CHECK (end_offset IS NULL OR end_offset >= 0),

    extraction_method TEXT NOT NULL DEFAULT 'unknown'
        CHECK (
            extraction_method IN ('text', 'ocr', 'mixed', 'unknown')
        ),

    extraction_warnings JSONB NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(extraction_warnings) = 'array'),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(metadata) = 'object'),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_document_chunks_offsets
        CHECK (
            start_offset IS NULL
            OR end_offset IS NULL
            OR end_offset >= start_offset
        ),

    CONSTRAINT fk_document_chunks_document_collection
        FOREIGN KEY (document_id, collection_id)
        REFERENCES ingestion_documents (document_id, collection_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_collection
    ON document_chunks (collection_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document
    ON document_chunks (document_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_collection_document
    ON document_chunks (collection_id, document_id);
