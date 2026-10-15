import pytest

from app.ingestion.queue import RedisIngestionQueue


class FakeRedis:
    def __init__(self):
        self.items = []

    def rpush(self, name, *values):
        self.items.extend((name, value) for value in values)
        return len(self.items)

    def blpop(self, keys, timeout=0):
        for index, (name, value) in enumerate(self.items):
            if name == keys:
                self.items.pop(index)
                return name, value
        return None


def test_enqueue_and_dequeue_document_id():
    client = FakeRedis()
    queue = RedisIngestionQueue(client)

    queue.enqueue("doc-123")

    assert queue.dequeue() == "doc-123"


def test_queue_preserves_fifo_order():
    client = FakeRedis()
    queue = RedisIngestionQueue(client)

    queue.enqueue("doc-1")
    queue.enqueue("doc-2")

    assert queue.dequeue() == "doc-1"
    assert queue.dequeue() == "doc-2"


def test_dequeue_returns_none_when_queue_is_empty():
    queue = RedisIngestionQueue(FakeRedis())

    assert queue.dequeue() is None


@pytest.mark.parametrize("document_id", ["", "   "])
def test_enqueue_rejects_blank_document_id(document_id):
    queue = RedisIngestionQueue(FakeRedis())

    with pytest.raises(ValueError, match="document_id"):
        queue.enqueue(document_id)


def test_queue_rejects_blank_queue_name():
    with pytest.raises(ValueError, match="queue_name"):
        RedisIngestionQueue(FakeRedis(), queue_name="   ")


def test_queue_rejects_negative_timeout():
    with pytest.raises(ValueError, match="timeout"):
        RedisIngestionQueue(
            FakeRedis(),
            block_timeout_seconds=-1,
        )
