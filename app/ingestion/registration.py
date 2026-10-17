import os
import logging
from typing import Protocol, runtime_checkable

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.schema import (
    DocumentIngestionRequest,
    DocumentIngestionResult,
    IngestionStatus,
)

logger = logging.getLogger(__name__)


class IdempotencyKeyConflict(ValueError):
    """Raised when a request key is reused for different content."""


@runtime_checkable
class RegistrationStore(Protocol):
    """Contract for document registration and status updates."""

    def register(
        self,
        request: DocumentIngestionRequest,
    ) -> DocumentIngestionResult:
        """Register a document or resolve an existing registration."""
        ...

    def get_registered_document(
        self,
        document_id: str,
    ) -> tuple[DocumentIngestionRequest, IngestionStatus] | None:
        """Return a canonical request and its current status, if found."""
        ...

    def set_status(
        self,
        document_id: str,
        status: IngestionStatus,
    ) -> None:
        """Update the status of a registered document."""
        ...


class InMemoryRegistrationStore:
    """Test-only store without persistence or concurrency guarantees."""

    def __init__(self) -> None:
        # (collection_id, content_hash) -> canonical request
        self._documents: dict[
            tuple[str, str], DocumentIngestionRequest
        ] = {}

        # Canonical document ID -> current ingestion status
        self._statuses: dict[str, IngestionStatus] = {}

        # (collection_id, request_key) -> (content_hash, canonical_document_id)
        self._request_keys: dict[
            tuple[str, str], tuple[str, str]
        ] = {}

    def get_registered_document(
        self,
        document_id: str,
    ) -> tuple[DocumentIngestionRequest, IngestionStatus] | None:
        """Find a canonical document and its current status."""
        for request in self._documents.values():
            if request.document_id == document_id:
                return request, self._statuses[document_id]

        return None

    def set_status(
        self,
        document_id: str,
        status: IngestionStatus,
    ) -> None:
        """Update the status of an existing document."""
        if document_id not in self._statuses:
            raise KeyError(f"Unknown document_id: {document_id}")

        self._statuses[document_id] = status

    def register(
        self,
        request: DocumentIngestionRequest,
    ) -> DocumentIngestionResult:
        collection_id = request.collection_id
        content_hash = request.content_sha256.lower()
        request_key = request.collection_idempotency_key

        # 1. Recognize retries of the same request.
        if request_key:
            key = (collection_id, request_key)
            previous = self._request_keys.get(key)

            if previous is not None:
                previous_hash, canonical_document_id = previous

                if previous_hash != content_hash:
                    raise IdempotencyKeyConflict(
                        "The collection idempotency key was already used "
                        "for different content."
                    )

                return DocumentIngestionResult(
                    document_id=canonical_document_id,
                    collection_id=collection_id,
                    status=self._statuses[canonical_document_id],
                    content_sha256=content_hash,
                )

        # 2. Find existing content within the collection.
        content_key = (collection_id, content_hash)
        existing = self._documents.get(content_key)

        if existing is not None:
            canonical_id = existing.document_id

            if request_key:
                self._request_keys[(collection_id, request_key)] = (
                    content_hash,
                    canonical_id,
                )

            return DocumentIngestionResult(
                document_id=canonical_id,
                collection_id=collection_id,
                status=IngestionStatus.DUPLICATE,
                content_sha256=content_hash,
                duplicate_of_document_id=canonical_id,
            )

        # 3. Register new canonical content.
        normalized_request = request.model_copy(
            update={"content_sha256": content_hash}
        )

        self._documents[content_key] = normalized_request
        self._statuses[request.document_id] = IngestionStatus.QUEUED

        if request_key:
            self._request_keys[(collection_id, request_key)] = (
                content_hash,
                request.document_id,
            )

        return DocumentIngestionResult(
            document_id=request.document_id,
            collection_id=collection_id,
            status=IngestionStatus.QUEUED,
            content_sha256=content_hash,
        )


class PostgresRegistrationStore:
    """PostgreSQL-backed registration store with transactional writes."""

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
        """Open a database connection with a bounded connection timeout."""
        return psycopg.connect(
            self._database_url,
            row_factory=dict_row,
            connect_timeout=self._connect_timeout,
        )

    def get_registered_document(
        self,
        document_id: str,
    ) -> tuple[DocumentIngestionRequest, IngestionStatus] | None:
        """Load a canonical request and its current status."""
        logger.debug("Loading registered document %s", document_id)

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT request_data, status
                FROM ingestion_documents
                WHERE document_id = %s
                """,
                (document_id,),
            ).fetchone()

        if row is None:
            return None

        request = DocumentIngestionRequest.model_validate(
            row["request_data"]
        )
        status = IngestionStatus(row["status"])

        return request, status

    def set_status(
        self,
        document_id: str,
        status: IngestionStatus,
    ) -> None:
        """Persist the status of a canonical document."""
        logger.debug(
            "Updating document %s to status %s",
            document_id,
            status.value,
        )

        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE ingestion_documents
                SET status = %s
                WHERE document_id = %s
                """,
                (status.value, document_id),
            )

            if cursor.rowcount == 0:
                raise KeyError(f"Unknown document_id: {document_id}")

    def register(
        self,
        request: DocumentIngestionRequest,
    ) -> DocumentIngestionResult:
        """Register content atomically or resolve its canonical document."""
        collection_id = request.collection_id
        content_hash = request.content_sha256.lower()
        request_key = request.collection_idempotency_key

        normalized_request = request.model_copy(
            update={"content_sha256": content_hash}
        )

        logger.debug(
            "Registering document %s in collection %s",
            request.document_id,
            collection_id,
        )

        try:
            with self._connect() as conn:
                logger.debug("Registration database connection opened")

                # Serialize registrations within this collection.
                logger.debug("Acquiring collection advisory lock")

                conn.execute(
                    """
                    SELECT pg_advisory_xact_lock(
                        hashtextextended(%s, 0)
                    )
                    """,
                    (collection_id,),
                )

                logger.debug("Collection advisory lock acquired")

                # 1. Check the idempotency key before checking content.
                if request_key:
                    previous = conn.execute(
                        """
                        SELECT content_sha256, canonical_document_id
                        FROM ingestion_request_keys
                        WHERE collection_id = %s
                          AND idempotency_key = %s
                        """,
                        (collection_id, request_key),
                    ).fetchone()

                    if previous is not None:
                        if previous["content_sha256"] != content_hash:
                            raise IdempotencyKeyConflict(
                                "The collection idempotency key was already "
                                "used for different content."
                            )

                        canonical = conn.execute(
                            """
                            SELECT status
                            FROM ingestion_documents
                            WHERE document_id = %s
                            """,
                            (previous["canonical_document_id"],),
                        ).fetchone()

                        if canonical is None:
                            raise RuntimeError(
                                "Idempotency mapping references a missing "
                                "canonical document."
                            )

                        return DocumentIngestionResult(
                            document_id=previous["canonical_document_id"],
                            collection_id=collection_id,
                            status=IngestionStatus(canonical["status"]),
                            content_sha256=content_hash,
                        )

                # 2. Look for existing content in this collection.
                existing = conn.execute(
                    """
                    SELECT document_id
                    FROM ingestion_documents
                    WHERE collection_id = %s
                      AND content_sha256 = %s
                    """,
                    (collection_id, content_hash),
                ).fetchone()

                if existing is not None:
                    canonical_id = existing["document_id"]

                    if request_key:
                        conn.execute(
                            """
                            INSERT INTO ingestion_request_keys (
                                collection_id,
                                idempotency_key,
                                content_sha256,
                                canonical_document_id
                            )
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                collection_id,
                                request_key,
                                content_hash,
                                canonical_id,
                            ),
                        )

                    return DocumentIngestionResult(
                        document_id=canonical_id,
                        collection_id=collection_id,
                        status=IngestionStatus.DUPLICATE,
                        content_sha256=content_hash,
                        duplicate_of_document_id=canonical_id,
                    )

                # 3. Register new canonical content.
                conn.execute(
                    """
                    INSERT INTO ingestion_documents (
                        document_id,
                        collection_id,
                        content_sha256,
                        request_data,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        normalized_request.document_id,
                        collection_id,
                        content_hash,
                        Jsonb(normalized_request.model_dump(mode="json")),
                        IngestionStatus.QUEUED.value,
                    ),
                )

                if request_key:
                    conn.execute(
                        """
                        INSERT INTO ingestion_request_keys (
                            collection_id,
                            idempotency_key,
                            content_sha256,
                            canonical_document_id
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            collection_id,
                            request_key,
                            content_hash,
                            normalized_request.document_id,
                        ),
                    )

            # The transaction has committed successfully.
            logger.debug(
                "Registered document %s successfully",
                normalized_request.document_id,
            )

        except Exception:
            logger.exception(
                "Registration failed for document %s",
                request.document_id,
            )
            raise

        return DocumentIngestionResult(
            document_id=normalized_request.document_id,
            collection_id=collection_id,
            status=IngestionStatus.QUEUED,
            content_sha256=content_hash,
        )
