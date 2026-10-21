"""PostgreSQL storage for chunk embeddings."""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class ChunkEmbedding:
    chunk_id: str
    embedding: list[float]


class PostgresEmbeddingStore:
    """PostgreSQL-backed storage for chunk embeddings."""

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

    @staticmethod
    def _to_vector_literal(embedding: Sequence[float]) -> str:
        """Serialise a float sequence to pgvector's text input format."""
        return "[" + ",".join(str(float(x)) for x in embedding) + "]"

    def insert_embeddings(
        self,
        model_name: str,
        embeddings: Sequence[ChunkEmbedding],
    ) -> int:
        """Insert a batch of embeddings atomically.

        Each chunk_id must correspond to an existing document_chunks row.
        Inserting an embedding for an already-embedded chunk raises an
        integrity error rather than silently overwriting; the pipeline is
        expected to re-chunk (which cascades away stale embeddings) before
        re-embedding.
        """
        if not embeddings:
            return 0

        model_name = model_name.strip()
        if not model_name:
            raise ValueError("model_name must be non-blank.")

        rows = [
            (
                item.chunk_id,
                model_name,
                self._to_vector_literal(item.embedding),
            )
            for item in embeddings
        ]

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO chunk_embeddings (
                        chunk_id,
                        embedding_model,
                        embedding
                    )
                    VALUES (%s, %s, %s::vector)
                    """,
                    rows,
                )

        return len(rows)