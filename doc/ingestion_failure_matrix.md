# Ingestion Failure Matrix

## Purpose

Define expected system behavior when document ingestion encounters failures. The goal is to make failures predictable, prevent false success states, and identify which failures can be retried safely.

## Failure Scenarios

| Failure | Expected behavior | Retry policy |
|---|---|---|
| Unsupported file type | Reject the document with a clear error | No retry until input changes |
| Malformed PDF | Move the document to quarantine and record the failure | No automatic retry |
| Missing source file | Fail ingestion without reporting success | Retry only after the file becomes available |
| Duplicate content in the same collection | Return the existing canonical document | No reprocessing required |
| Same idempotency key with different content | Raise an idempotency conflict | Require a new key |
| Database unavailable during registration | Report registration failure | Retry with bounded backoff |
| Redis unavailable during enqueue | Do not claim successful queue submission | Retry after queue recovery |
| Worker crashes during processing | Preserve a recoverable document state | Recovery mechanism required |
| Chunking fails | Record the failing stage and avoid marking ingestion complete | Retry only when safe |
| Status update fails | Do not assume the status change persisted | Reconcile with the database |

## Invariants

1. A document must never be marked completed before parsing and chunking succeed.
2. Duplicate content within a collection must not create another canonical document.
3. Reusing an idempotency key with different content must produce a conflict.
4. A failure must not be silently converted into a successful result.
5. Database state is the source of truth for registered documents and their statuses.
6. Retries must not create duplicate documents or chunks.
7. Failure messages must not expose credentials or full document contents.

## Recovery Requirements

- Distinguish transient infrastructure failures from invalid input.
- Use bounded retries for transient failures.
- Preserve enough state to diagnose interrupted processing.
- Ensure retries are idempotent.
- Record the failure stage and relevant document identifier.
- Define an explicit recovery procedure for documents left in intermediate states.

## Testing Requirements

- Test each failure scenario independently.
- Verify the expected status and returned error.
- Verify that retries do not create duplicate registrations.
- Verify that failed processing never produces a false completed status.
- Test recovery behavior after simulated database, queue, and worker failures.

## Out of Scope

This document defines expected behavior. It does not claim that every recovery mechanism or retry policy has already been implemented.
