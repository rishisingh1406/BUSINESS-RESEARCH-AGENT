import os
from collections.abc import Sequence

import psycopg
from psycopg.types.json import Jsonb

from app.schema import ExtractedChunk


class PostgresChunkStore:
    """PostgreSQL-backed storage for extracted document chunks."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        connect_timeout: int = 5,
    ) -> None:
        self._database_url = database_url or os.getenv("DATABASE_URL")

        if not self._database_url:
            raise ValueError(
                "A database URL is required. Pass database_url or set "
                "the DATABASE_URL environment variable."
            )

        if connect_timeout <= 0:
            raise ValueError("connect_timeout must be greater than zero.")

        self._connect_timeout = connect_timeout

    def _connect(self):
        """Open a database connection with a bounded timeout."""
        return psycopg.connect(
            self._database_url,
            connect_timeout=self._connect_timeout,
        )

    def insert_chunks(self, chunks: Sequence[ExtractedChunk]) -> int:
        """Insert a batch atomically; reject any conflicting chunk ID."""
        if not chunks:
            return 0

        rows = [
            (
                chunk.chunk_id,
                chunk.document_id,
                chunk.collection_id,
                chunk.chunk_text,
                chunk.page_number,
                chunk.section_title,
                chunk.start_offset,
                chunk.end_offset,
                chunk.extraction_method,
                Jsonb(chunk.extraction_warnings),
                Jsonb(chunk.metadata),
            )
            for chunk in chunks
        ]

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO document_chunks (
                        chunk_id,
                        document_id,
                        collection_id,
                        chunk_text,
                        page_number,
                        section_title,
                        start_offset,
                        end_offset,
                        extraction_method,
                        extraction_warnings,
                        metadata
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    rows,
                )

        return len(rows)

    def replace_document_chunks(
        self,
        document_id: str,
        collection_id: str,
        chunks: Sequence[ExtractedChunk],
    ) -> int:
        """Atomically replace all chunks for a document.

        Deletes any existing chunks for (document_id, collection_id) and
        inserts the new batch in a single transaction. Retrying ingestion
        for the same document is therefore idempotent even when UUID4
        chunk IDs differ between attempts.
        """
        rows = [
            (
                chunk.chunk_id,
                chunk.document_id,
                chunk.collection_id,
                chunk.chunk_text,
                chunk.page_number,
                chunk.section_title,
                chunk.start_offset,
                chunk.end_offset,
                chunk.extraction_method,
                Jsonb(chunk.extraction_warnings),
                Jsonb(chunk.metadata),
            )
            for chunk in chunks
        ]

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM document_chunks
                    WHERE document_id = %s AND collection_id = %s
                    """,
                    (document_id, collection_id),
                )

                if rows:
                    cur.executemany(
                        """
                        INSERT INTO document_chunks (
                            chunk_id,
                            document_id,
                            collection_id,
                            chunk_text,
                            page_number,
                            section_title,
                            start_offset,
                            end_offset,
                            extraction_method,
                            extraction_warnings,
                            metadata
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        rows,
                    )

        return len(rows)