
from __future__ import annotations

import json
import time
import uuid
from typing import Protocol


class RedisListClient(Protocol):
    """Minimal Redis client interface required by the ingestion queue."""

    def rpush(self, name: str, *values: str) -> int: ...

    def blpop(
        self,
        keys: str,
        timeout: int = 0,
    ) -> tuple[str, str] | None: ...

    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: str | int | float,
    ) -> object: ...


class RedisIngestionQueue:
    """
    FIFO Redis queue with atomic claiming, acknowledgement,
    lease renewal, and abandoned-job recovery.

    Delivery is at least once. Consumers must be idempotent.
    """

    # RPUSH appends new jobs to the right; LPOP claims from the left.
    # This preserves FIFO order while atomically moving jobs to processing.
    CLAIM_SCRIPT = """
    local item = redis.call('LPOP', KEYS[1])
    if not item then
        return nil
    end

    local job = cjson.decode(item)
    local lease_until = tonumber(ARGV[1]) + tonumber(ARGV[2])
    job['lease_until'] = lease_until

    local encoded = cjson.encode(job)
    redis.call('LPUSH', KEYS[2], encoded)
    redis.call('ZADD', KEYS[3], lease_until, job['job_id'])

    return encoded
    """

    ACK_SCRIPT = """
    local items = redis.call('LRANGE', KEYS[1], 0, -1)

    for _, item in ipairs(items) do
        local job = cjson.decode(item)

        if job['job_id'] == ARGV[1] then
            redis.call('LREM', KEYS[1], 1, item)
            redis.call('ZREM', KEYS[2], ARGV[1])
            return 1
        end
    end

    return 0
    """

    RENEW_SCRIPT = """
    local items = redis.call('LRANGE', KEYS[1], 0, -1)

    for index, item in ipairs(items) do
        local job = cjson.decode(item)

        if job['job_id'] == ARGV[1] then
            local lease_until = tonumber(ARGV[2]) + tonumber(ARGV[3])
            job['lease_until'] = lease_until

            redis.call(
                'LSET',
                KEYS[1],
                index - 1,
                cjson.encode(job)
            )
            redis.call('ZADD', KEYS[2], lease_until, ARGV[1])

            return 1
        end
    end

    return 0
    """

    RECOVER_SCRIPT = """
    local expired = redis.call(
        'ZRANGEBYSCORE',
        KEYS[3],
        '-inf',
        ARGV[1],
        'LIMIT',
        0,
        tonumber(ARGV[2])
    )

    local expired_ids = {}
    for _, job_id in ipairs(expired) do
        expired_ids[job_id] = true
    end

    -- Processing is newest-first because claims use LPUSH.
    -- Scan backwards to recover expired jobs in original claim order.
    local items = redis.call('LRANGE', KEYS[2], 0, -1)
    local recovered_jobs = {}

    for index = #items, 1, -1 do
        local item = items[index]
        local job = cjson.decode(item)
        local job_id = job['job_id']

        if expired_ids[job_id] then
            redis.call('LREM', KEYS[2], 1, item)

            job['lease_until'] = nil
            table.insert(recovered_jobs, cjson.encode(job))
            redis.call('ZREM', KEYS[3], job_id)
        end
    end

    -- Remove stale lease entries even if their jobs are absent
    -- from the processing list.
    for _, job_id in ipairs(expired) do
        redis.call('ZREM', KEYS[3], job_id)
    end

    -- Recovered jobs go to the front of pending, ahead of newer jobs.
    -- Reverse iteration with LPUSH preserves their original order.
    for index = #recovered_jobs, 1, -1 do
        redis.call('LPUSH', KEYS[1], recovered_jobs[index])
    end

    return #recovered_jobs
    """

    def __init__(
        self,
        client: RedisListClient,
        queue_name: str = "business_research:ingestion",
        block_timeout_seconds: int = 5,
        lease_seconds: int = 60,
    ) -> None:
        if not queue_name.strip():
            raise ValueError("queue_name must not be blank")
        if block_timeout_seconds < 0:
            raise ValueError("timeout must be non-negative")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")

        self._client = client
        self._queue_name = queue_name
        self._pending_key = f"{queue_name}:pending"
        self._processing_key = f"{queue_name}:processing"
        self._leases_key = f"{queue_name}:leases"
        self._block_timeout_seconds = block_timeout_seconds
        self._lease_seconds = lease_seconds

    def enqueue(self, document_id: str) -> None:
        """Append a document to the pending queue."""
        if not document_id.strip():
            raise ValueError("document_id must not be blank")

        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": document_id,
        }

        self._client.rpush(
            self._pending_key,
            json.dumps(job, separators=(",", ":")),
        )

    def claim_job(self) -> dict[str, object] | None:
        """Atomically claim the oldest pending job."""
        deadline = time.monotonic() + self._block_timeout_seconds

        while True:
            result = self._client.eval(
                self.CLAIM_SCRIPT,
                3,
                self._pending_key,
                self._processing_key,
                self._leases_key,
                time.time(),
                self._lease_seconds,
            )

            if result is not None:
                if isinstance(result, bytes):
                    result = result.decode("utf-8")

                if not isinstance(result, str):
                    raise TypeError(
                        "Redis claim script returned an invalid job"
                    )

                return json.loads(result)

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None

            time.sleep(min(0.1, remaining))

    def acknowledge(self, job_id: str) -> bool:
        """Remove a claimed job and clear its lease."""
        if not job_id.strip():
            raise ValueError("job_id must not be blank")

        result = self._client.eval(
            self.ACK_SCRIPT,
            2,
            self._processing_key,
            self._leases_key,
            job_id,
        )

        return int(result or 0) == 1

    def renew_lease(self, job_id: str) -> bool:
        """Extend the lease for a job that is still processing."""
        if not job_id.strip():
            raise ValueError("job_id must not be blank")

        result = self._client.eval(
            self.RENEW_SCRIPT,
            2,
            self._processing_key,
            self._leases_key,
            job_id,
            time.time(),
            self._lease_seconds,
        )

        return int(result or 0) == 1

    def recover_abandoned(self, limit: int = 100) -> int:
        """Move expired claims back to pending, up to limit jobs."""
        if limit <= 0:
            raise ValueError("limit must be positive")

        result = self._client.eval(
            self.RECOVER_SCRIPT,
            3,
            self._pending_key,
            self._processing_key,
            self._leases_key,
            time.time(),
            limit,
        )

        return int(result or 0)

    def dequeue(self) -> str | None:
        """
        Legacy destructive dequeue API.

        This reads the pending list and does not provide reliable processing.
        Prefer claim_job() followed by acknowledge().
        """
        item = self._client.blpop(
            self._pending_key,
            timeout=self._block_timeout_seconds,
        )

        if item is None:
            return None

        _, raw_job = item

        if isinstance(raw_job, bytes):
            raw_job = raw_job.decode("utf-8")

        try:
            job = json.loads(raw_job)
        except (json.JSONDecodeError, TypeError):
            return raw_job

        return job["document_id"]
