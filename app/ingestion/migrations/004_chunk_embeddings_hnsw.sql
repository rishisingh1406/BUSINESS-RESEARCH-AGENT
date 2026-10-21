-- 004_chunk_embeddings_hnsw.sql
-- HNSW cosine index for chunk embeddings.
--
-- Apply AFTER the first real batch of embeddings has been inserted.
-- For large datasets, run in the same session before this migration:
--   SET maintenance_work_mem = '512MB';
--
-- Parameters:
--   m = 16               connectivity; standard starting point
--   ef_construction=128  middle ground between speed and recall
--                        (raise to 200 later if recall is insufficient)

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_hnsw
    ON chunk_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 128);