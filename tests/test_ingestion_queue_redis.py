
import os
import time
import uuid

import pytest
import redis

from app.ingestion.queue import RedisIngestionQueue


@pytest.fixture
def real_redis_client():
    client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
        decode_responses=True,
    )

    try:
        client.ping()
    except redis.RedisError as exc:
        client.close()
        pytest.skip(f"Redis is unavailable: {exc}")

    yield client
    client.close()


@pytest.fixture
def real_redis_queue(real_redis_client):
    queue_name = f"business_research:test:{uuid.uuid4().hex}"

    queue = RedisIngestionQueue(
        real_redis_client,
        queue_name=queue_name,
        block_timeout_seconds=1,
        lease_seconds=30,
    )

    yield queue

    real_redis_client.delete(
        queue._pending_key,
        queue._processing_key,
        queue._leases_key,
    )


def test_real_redis_claim_and_acknowledge(real_redis_queue):
    real_redis_queue.enqueue("doc-1")

    job = real_redis_queue.claim_job()

    assert job is not None
    assert job["document_id"] == "doc-1"
    assert real_redis_queue.acknowledge(job["job_id"]) is True
    assert real_redis_queue.claim_job() is None


def test_real_redis_lease_renewal(real_redis_queue):
    real_redis_queue.enqueue("doc-lease")
    job = real_redis_queue.claim_job()

    assert job is not None
    assert real_redis_queue.renew_lease(job["job_id"]) is True
    assert real_redis_queue.recover_abandoned() == 0
    assert real_redis_queue.acknowledge(job["job_id"]) is True


def test_real_redis_recovers_expired_job(real_redis_queue):
    real_redis_queue.enqueue("doc-recover")
    job = real_redis_queue.claim_job()

    assert job is not None

    # Expire the lease directly instead of waiting.
    real_redis_queue._client.zadd(
        real_redis_queue._leases_key,
        {job["job_id"]: time.time() - 10},
    )

    assert real_redis_queue.recover_abandoned() == 1

    recovered = real_redis_queue.claim_job()

    assert recovered is not None
    assert recovered["document_id"] == "doc-recover"
    assert real_redis_queue.acknowledge(recovered["job_id"]) is True


def test_real_redis_recovery_preserves_fifo(real_redis_queue):
    # Claim jobs in order so they are all in the processing list.
    for document_id in ("doc-1", "doc-2", "doc-3"):
        real_redis_queue.enqueue(document_id)

    claimed = [
        real_redis_queue.claim_job(),
        real_redis_queue.claim_job(),
        real_redis_queue.claim_job(),
    ]

    assert all(job is not None for job in claimed)

    # Expire all three leases.
    expired_at = time.time() - 10
    real_redis_queue._client.zadd(
        real_redis_queue._leases_key,
        {job["job_id"]: expired_at for job in claimed},
    )

    assert real_redis_queue.recover_abandoned() == 3

    # This new job should follow the recovered jobs.
    real_redis_queue.enqueue("doc-4")

    recovered_order = [
        real_redis_queue.claim_job()["document_id"]
        for _ in range(4)
    ]

    assert recovered_order == ["doc-1", "doc-2", "doc-3", "doc-4"]
