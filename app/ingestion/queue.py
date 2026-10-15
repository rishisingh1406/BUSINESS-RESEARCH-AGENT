from typing import Protocol


class RedisListClient(Protocol):
    """Minimal Redis client interface required by the ingestion queue."""

    def rpush(self, name: str, *values: str) -> int: ...

    def blpop(
        self,
        keys: str,
        timeout: int = 0,
    ) -> tuple[str, str] | None: ...


class RedisIngestionQueue:
    """FIFO ingestion queue backed by a Redis list."""

    def __init__(
        self,
        client: RedisListClient,
        queue_name: str = "business_research:ingestion",
        block_timeout_seconds: int = 5,
    ) -> None:
        if not queue_name.strip():
            raise ValueError("queue_name must not be blank")

        if block_timeout_seconds < 0:
            raise ValueError("block_timeout_seconds must be non-negative")

        self._client = client
        self._queue_name = queue_name
        self._block_timeout_seconds = block_timeout_seconds

    def enqueue(self, document_id: str) -> None:
        """Append a document ID to the queue."""
        if not document_id.strip():
            raise ValueError("document_id must not be blank")

        self._client.rpush(self._queue_name, document_id)

    def dequeue(self) -> str | None:
        """Wait for a job and return its document ID, or None on timeout."""
        item = self._client.blpop(
            self._queue_name,
            timeout=self._block_timeout_seconds,
        )

        if item is None:
            return None

        _, document_id = item
        return document_id
