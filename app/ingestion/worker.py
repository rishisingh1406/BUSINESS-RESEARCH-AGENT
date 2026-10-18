
from __future__ import annotations

import logging
import threading

from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.queue import RedisIngestionQueue
from app.ingestion.registration import RegistrationStore
from app.schema import DocumentIngestionResult, IngestionStatus

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {
    IngestionStatus.COMPLETED,
    IngestionStatus.QUARANTINED,
    IngestionStatus.DUPLICATE,
}


class IngestionWorker:
    """Process claimed ingestion jobs with at-least-once delivery."""

    def __init__(
        self,
        queue: RedisIngestionQueue,
        pipeline: IngestionPipeline,
        registration_store: RegistrationStore,
        lease_renewal_interval_seconds: float = 20.0,
    ) -> None:
        if lease_renewal_interval_seconds <= 0:
            raise ValueError(
                "lease_renewal_interval_seconds must be positive."
            )

        self._queue = queue
        self._pipeline = pipeline
        self._registration_store = registration_store
        self._lease_renewal_interval_seconds = (
            lease_renewal_interval_seconds
        )

    def _start_lease_heartbeat(
        self,
        job_id: str,
    ) -> tuple[threading.Event, threading.Event, threading.Thread]:
        """Renew a claimed job's lease until the stop event is set."""
        stop_event = threading.Event()
        lease_lost_event = threading.Event()

        def heartbeat() -> None:
            while not stop_event.wait(
                self._lease_renewal_interval_seconds
            ):
                try:
                    renewed = self._queue.renew_lease(job_id)
                except Exception:
                    logger.exception(
                        "Lease renewal raised an exception for job %s",
                        job_id,
                    )
                    lease_lost_event.set()
                    return

                if not renewed:
                    logger.error(
                        "Lease renewal failed for job %s; "
                        "job ownership is no longer confirmed",
                        job_id,
                    )
                    lease_lost_event.set()
                    return

                logger.debug("Renewed lease for job %s", job_id)

        thread = threading.Thread(
            target=heartbeat,
            name=f"ingestion-lease-{job_id}",
            daemon=True,
        )
        thread.start()

        return stop_event, lease_lost_event, thread

    def process_one(self) -> DocumentIngestionResult | None:
        """Process at most one job.

        Returns None when no job is available.

        Processing errors propagate to the caller. Failed jobs are not
        acknowledged and can be recovered after their lease expires.
        """
        job = self._queue.claim_job()

        if job is None:
            return None

        job_id = job.get("job_id")
        document_id = job.get("document_id")

        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("Claimed job has an invalid job_id.")

        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(
                f"Claimed job {job_id} has an invalid document_id."
            )

        logger.info(
            "Processing ingestion job %s for document %s",
            job_id,
            document_id,
        )

        registered = self._registration_store.get_registered_document(
            document_id
        )

        if registered is None:
            raise LookupError(
                f"No registration found for document_id {document_id!r}."
            )

        request, current_status = registered

        allowed_start_statuses = {
            IngestionStatus.QUEUED,
            IngestionStatus.COMPLETED,
            IngestionStatus.QUARANTINED,
        }

        if current_status not in allowed_start_statuses:
            raise RuntimeError(
                f"Document {document_id!r} cannot be processed from "
                f"status {current_status.value!r}."
            )

        stop_event, lease_lost_event, heartbeat_thread = (
            self._start_lease_heartbeat(job_id)
        )

        try:
            result = self._pipeline.process(request)
        finally:
            stop_event.set()
            heartbeat_thread.join()

        if lease_lost_event.is_set():
            raise RuntimeError(
                f"Lease ownership was lost or could not be confirmed "
                f"for job {job_id!r}; refusing to acknowledge it."
            )

        if result.status not in TERMINAL_STATUSES:
            raise RuntimeError(
                f"Pipeline returned non-terminal status "
                f"{result.status.value!r} for document {document_id!r}."
            )

        if result.document_id != document_id:
            raise RuntimeError(
                f"Pipeline returned document_id {result.document_id!r} "
                f"for job targeting {document_id!r}."
            )

        acknowledged = self._queue.acknowledge(job_id)

        if not acknowledged:
            raise RuntimeError(
                f"Could not acknowledge job {job_id!r}; "
                "it may have been recovered or removed."
            )

        logger.info(
            "Completed ingestion job %s for document %s with status %s",
            job_id,
            document_id,
            result.status.value,
        )

        return result
