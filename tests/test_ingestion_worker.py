
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.ingestion.worker import IngestionWorker
from app.schema import (
    DocumentIngestionRequest,
    DocumentIngestionResult,
    IngestionStatus,
)


def make_request() -> DocumentIngestionRequest:
    return DocumentIngestionRequest(
        document_id="worker-doc-1",
        collection_id="worker-collection-1",
        original_filename="annual-report.md",
        content_sha256="a" * 64,
        content_type="text/markdown",
        file_size_bytes=100,
        upload_timestamp=datetime(2026, 10, 17, tzinfo=timezone.utc),
        storage_uri="file:///tmp/annual-report.md",
    )



def make_result(
    status: IngestionStatus = IngestionStatus.COMPLETED,
) -> DocumentIngestionResult:
    result_data = {
        "document_id": "worker-doc-1",
        "collection_id": "worker-collection-1",
        "status": status,
        "content_sha256": "a" * 64,
        "extracted_pages": 1,
        "chunk_ids": ["chunk-1"],
        "warnings": [],
    }

    if status == IngestionStatus.QUARANTINED:
        result_data["error_message"] = "Document parsing failed."

    return DocumentIngestionResult(**result_data)



def make_worker(
    *,
    job=None,
    registration=("request", IngestionStatus.QUEUED),
    result=None,
):
    queue = Mock()
    queue.claim_job.return_value = job
    queue.acknowledge.return_value = True

    store = Mock()
    store.get_registered_document.return_value = registration

    pipeline = Mock()
    pipeline.process.return_value = result or make_result()

    worker = IngestionWorker(
        queue=queue,
        pipeline=pipeline,
        registration_store=store,
    )

    return worker, queue, store, pipeline


def test_process_one_returns_none_when_queue_is_empty():
    worker, queue, store, pipeline = make_worker(job=None)

    assert worker.process_one() is None

    queue.acknowledge.assert_not_called()
    store.get_registered_document.assert_not_called()
    pipeline.process.assert_not_called()


def test_process_one_processes_and_acknowledges_completed_job():
    request = make_request()
    job = {
        "job_id": "job-1",
        "document_id": request.document_id,
        "lease_until": 1_800_000_000,
    }
    result = make_result()

    worker, queue, store, pipeline = make_worker(
        job=job,
        registration=(request, IngestionStatus.QUEUED),
        result=result,
    )

    actual = worker.process_one()

    assert actual == result
    store.get_registered_document.assert_called_once_with(
        request.document_id
    )
    pipeline.process.assert_called_once_with(request)
    queue.acknowledge.assert_called_once_with("job-1")


def test_process_one_acknowledges_quarantined_document():
    request = make_request()
    job = {
        "job_id": "job-quarantine",
        "document_id": request.document_id,
        "lease_until": 1_800_000_000,
    }
    result = make_result(IngestionStatus.QUARANTINED)

    worker, queue, _, _ = make_worker(
        job=job,
        registration=(request, IngestionStatus.QUEUED),
        result=result,
    )

    actual = worker.process_one()

    assert actual.status == IngestionStatus.QUARANTINED
    queue.acknowledge.assert_called_once_with("job-quarantine")


def test_process_one_raises_when_registration_is_missing():
    job = {
        "job_id": "job-missing",
        "document_id": "missing-doc",
        "lease_until": 1_800_000_000,
    }

    worker, queue, store, pipeline = make_worker(
        job=job,
        registration=None,
    )

    with pytest.raises(LookupError, match="No registration found"):
        worker.process_one()

    queue.acknowledge.assert_not_called()
    pipeline.process.assert_not_called()


def test_process_one_leaves_job_unacknowledged_on_pipeline_error():
    request = make_request()
    job = {
        "job_id": "job-error",
        "document_id": request.document_id,
        "lease_until": 1_800_000_000,
    }

    worker, queue, _, pipeline = make_worker(
        job=job,
        registration=(request, IngestionStatus.QUEUED),
    )
    pipeline.process.side_effect = RuntimeError("temporary processing error")

    with pytest.raises(RuntimeError, match="temporary processing error"):
        worker.process_one()

    queue.acknowledge.assert_not_called()


def test_process_one_raises_if_acknowledgement_fails():
    request = make_request()
    job = {
        "job_id": "job-ack-fail",
        "document_id": request.document_id,
        "lease_until": 1_800_000_000,
    }

    worker, queue, _, _ = make_worker(
        job=job,
        registration=(request, IngestionStatus.QUEUED),
    )
    queue.acknowledge.return_value = False

    with pytest.raises(RuntimeError, match="Could not acknowledge"):
        worker.process_one()

    queue.acknowledge.assert_called_once_with("job-ack-fail")



import threading


def test_heartbeat_renews_lease_during_processing():
    request = make_request()
    job = {
        "job_id": "job-heartbeat",
        "document_id": request.document_id,
        "lease_until": 1_800_000_000,
    }

    worker, queue, _, pipeline = make_worker(
        job=job,
        registration=(request, IngestionStatus.QUEUED),
    )
    worker._lease_renewal_interval_seconds = 0.01

    renewal_observed = threading.Event()

    def slow_process(_request):
        if renewal_observed.wait(timeout=1):
            return make_result()
        raise AssertionError("Heartbeat did not renew the lease in time.")

    def renew_lease(_job_id):
        renewal_observed.set()
        return True

    pipeline.process.side_effect = slow_process
    queue.renew_lease.side_effect = renew_lease

    result = worker.process_one()

    assert result.status == IngestionStatus.COMPLETED
    queue.renew_lease.assert_called()
    queue.acknowledge.assert_called_once_with("job-heartbeat")


def test_worker_does_not_acknowledge_after_lease_renewal_fails():
    request = make_request()
    job = {
        "job_id": "job-lease-lost",
        "document_id": request.document_id,
        "lease_until": 1_800_000_000,
    }

    worker, queue, _, pipeline = make_worker(
        job=job,
        registration=(request, IngestionStatus.QUEUED),
    )
    worker._lease_renewal_interval_seconds = 0.01

    renewal_attempted = threading.Event()

    def slow_process(_request):
        assert renewal_attempted.wait(timeout=1)
        return make_result()

    def fail_renewal(_job_id):
        renewal_attempted.set()
        return False

    pipeline.process.side_effect = slow_process
    queue.renew_lease.side_effect = fail_renewal

    with pytest.raises(RuntimeError, match="Lease ownership was lost"):
        worker.process_one()

    queue.acknowledge.assert_not_called()
