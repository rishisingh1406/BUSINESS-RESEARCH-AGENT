
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.ingestion.registration import InMemoryRegistrationStore
from app.ingestion.service import IngestionSubmissionService
from app.schema import IngestionStatus


def make_service():
    store = InMemoryRegistrationStore()
    queue = Mock()
    service = IngestionSubmissionService(store, queue)
    return service, store, queue


def submit_file(service, file_path, **overrides):
    options = {
        "file_path": file_path,
        "collection_id": "collection-1",
        "content_type": "text/markdown",
    }
    options.update(overrides)
    return service.submit(**options)


def test_new_file_is_registered_and_enqueued_once(tmp_path):
    service, store, queue = make_service()
    file_path = tmp_path / "annual-report.md"
    content = b"# Annual Report\nRevenue increased."
    file_path.write_bytes(content)

    result = submit_file(service, file_path)

    assert result.status == IngestionStatus.QUEUED
    assert result.content_sha256 is not None
    assert len(result.content_sha256) == 64

    registered = store.get_registered_document(result.document_id)
    assert registered is not None

    request, status = registered
    assert request.content_sha256 == result.content_sha256
    assert request.file_size_bytes == len(content)
    assert request.original_filename == file_path.name
    assert status == IngestionStatus.QUEUED

    queue.enqueue.assert_called_once_with(result.document_id)


def test_duplicate_content_does_not_enqueue_another_job(tmp_path):
    service, store, queue = make_service()
    file_path = tmp_path / "annual-report.md"
    file_path.write_bytes(b"# Annual Report\nRevenue increased.")

    first = submit_file(service, file_path)
    second = submit_file(service, file_path)

    assert first.document_id == second.document_id
    assert second.status == IngestionStatus.DUPLICATE
    queue.enqueue.assert_called_once_with(first.document_id)


def test_idempotency_retry_does_not_enqueue_another_job(tmp_path):
    service, store, queue = make_service()
    file_path = tmp_path / "annual-report.md"
    file_path.write_bytes(b"# Annual Report\nRevenue increased.")

    first = submit_file(
        service,
        file_path,
        collection_idempotency_key="upload-request-123",
    )
    second = submit_file(
        service,
        file_path,
        collection_idempotency_key="upload-request-123",
    )

    assert first.document_id == second.document_id
    assert first.status == IngestionStatus.QUEUED
    assert second.status == IngestionStatus.QUEUED
    queue.enqueue.assert_called_once_with(first.document_id)



def test_missing_file_is_rejected_before_registration(tmp_path):
    service, store, queue = make_service()
    missing_file = tmp_path / "missing.md"

    with pytest.raises(ValueError, match="does not exist"):
        submit_file(service, missing_file)

    assert store.get_registered_document("unused") is None
    queue.enqueue.assert_not_called()


def test_empty_file_is_rejected_before_registration(tmp_path):
    service, store, queue = make_service()
    empty_file = tmp_path / "empty.md"
    empty_file.write_bytes(b"")

    with pytest.raises(ValueError, match="must not be empty"):
        submit_file(service, empty_file)

    assert store.get_registered_document("unused") is None
    queue.enqueue.assert_not_called()


def test_queue_failure_propagates_after_registration(tmp_path):
    service, store, queue = make_service()
    file_path = tmp_path / "annual-report.md"
    file_path.write_bytes(b"# Annual Report\nRevenue increased.")
    queue.enqueue.side_effect = RuntimeError("Redis unavailable")

    with pytest.raises(RuntimeError, match="Redis unavailable"):
        submit_file(service, file_path)

    # Registration happened before the queue operation failed.
    # This exposes the recovery gap we need to address next.
    queue.enqueue.assert_called_once()

    # The test double lets us verify the document remains registered.
    # Capture its ID from the attempted enqueue.
    document_id = queue.enqueue.call_args.args[0]
    registered = store.get_registered_document(document_id)

    assert registered is not None
    assert registered[1] == IngestionStatus.QUEUED
