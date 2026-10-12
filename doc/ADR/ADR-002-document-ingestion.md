# ADR-002: Bounded PDF Ingestion Pipeline

- **Status:** Accepted for MVP
- **Date:** 2026-10-10
- **Decision owner:** Project engineer

## 1. Context

Annual reports can be long, structurally complex, and inconsistent in quality. Some PDFs contain extractable text; others are scanned images. Documents may be malformed, duplicated, or contain untrusted instructions.

The research workflow needs reliable extraction, traceability, repeatable processing, and controlled resource consumption.

## 2. Decision drivers

- Support PDF files only in v1.
- Support text-based and scanned PDFs through separate extraction paths.
- Preserve document and page provenance.
- Detect duplicate uploads.
- Isolate malformed documents.
- Recover from interrupted processing without duplicating completed work.
- Respect configured file and processing limits.

## 3. Options considered

### Option A — Synchronous upload and processing

Process the document in the request that uploads it.

**Advantages**
- Simpler initial request flow
- Immediate completion feedback for small files

**Disadvantages**
- Long reports may exceed request timeouts
- Failures are harder to recover from independently
- Upload responsiveness is coupled to processing duration

### Option B — Background ingestion with explicit states

Accept the upload, create an ingestion task, and process it through bounded stages.

**Advantages**
- Separates upload acceptance from extraction duration
- Supports progress reporting and retries
- Allows failures to be isolated and inspected
- Better supports large documents

**Disadvantages**
- Requires persistent task state and recovery logic
- Introduces additional operational behavior to test

## 4. Decision

Use background ingestion with explicit task states and bounded processing stages.

The initial pipeline is:

1. Validate file type and configured size/page limits.
2. Record document metadata and calculate a content hash.
3. Check for an existing document with the same content hash within the applicable collection.
4. Extract text and page-level locations where possible.
5. Use OCR for scanned pages or documents when required.
6. Normalize extracted content while preserving traceability.
7. Produce chunks with stable document and location references.
8. Make successfully processed chunks available to retrieval.
9. Mark the task indexed, failed, or quarantined with a recorded reason.

Processing must be idempotent: retrying the same upload must not create duplicate indexed content for the same collection and content identity.

## 5. Failure behavior

- Invalid or unsupported files are rejected with an explicit reason.
- Corrupt or malformed files are quarantined or marked failed; they are not silently treated as successfully indexed.
- OCR failure must not be presented as successful extraction.
- Worker interruption must preserve valid completed work and allow safe recovery.
- Partial extraction quality must be recorded where it materially affects research reliability.
- Uploaded content is untrusted data and must never be treated as system instructions.

## 6. Consequences

**Positive**
- Supports repeatable ingestion and recovery.
- Provides a stable basis for provenance and evaluation.
- Separates document-processing failures from research-generation failures.

**Negative**
- Requires task-state management and idempotency tests.
- OCR can increase processing time and cost.
- Correct extraction of tables and financial figures remains a measurable risk.

## 7. Validation plan

Test:
- Text-based PDFs and scanned PDFs separately
- A document at the configured page and size limits
- Corrupt and malformed files
- Duplicate uploads
- OCR quality on selected numeric and table content
- Worker interruption and restart
- Retry behavior and partial-progress preservation
- Source/page traceability from extracted content to final evidence

Measure text-PDF ingestion time under documented conditions. Evaluate OCR extraction quality separately; passing a runtime target alone is not proof of correct extraction.

## 8. Revisit conditions

Reconsider the pipeline if measured throughput, extraction quality, operational complexity, or resource use fails the documented requirements.

Update the ADR when experiments support a materially different processing strategy.