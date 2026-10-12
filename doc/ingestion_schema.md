# Ingestion Schema

## 1. Purpose

This document defines the data structures and processing behavior for ingesting annual reports into the Business Research Agent. It covers document metadata, chunk metadata, ingestion flow, duplicate detection, chunking, embeddings, retries, and failure handling.

## 2. Supported Inputs

The MVP supports **PDF files only**.

Other formats, including Markdown, HTML, and TXT, are outside the current implementation scope.

## 3. Document Schema

Each document represents an annual report uploaded for research.

| Field | Purpose |
|---|---|
| `document_id` | Unique identifier for the document record |
| `company_name` | Name of the company |
| `company_identifier` | Stable identifier for the company, when available |
| `financial_year` | Financial year covered by the report |
| `document_type` | Type of document, such as an annual report |
| `original_filename` | Name of the uploaded PDF |
| `content_hash` | SHA-256 hash of the file content for duplicate detection |
| `upload_timestamp` | Time when the document was uploaded |
| `collection_id` | Collection to which the document belongs |
| `status` | Current ingestion status |
| `error_message` | Description of a processing failure, when applicable |

## 4. Chunk Schema

Each chunk represents a section of extracted text from an annual report.

| Field | Purpose |
|---|---|
| `chunk_id` | Unique identifier for the chunk |
| `document_id` | Links the chunk to its source document |
| `chunk_text` | Extracted text used for retrieval |
| `page_number` | Page number in the original PDF |
| `section_title` | Heading associated with the chunk |
| `embedding` | Vector representation used for semantic search |

## 5. Ingestion Statuses

The document status uses one of the following values:

- `uploaded`: The file has been received.
- `processing`: The worker is processing the document.
- `completed`: Parsing, chunking, and embedding generation have completed.
- `failed`: Processing failed.

## 6. Ingestion Flow

1. The API receives a PDF.
2. The system calculates its SHA-256 content hash.
3. The system checks for an existing document with the same hash.
4. If a duplicate exists, the system returns the existing `document_id` and skips reprocessing. Under the current MVP decision, its `collection_id` is updated to the newly requested collection.
5. If the document is new, the API saves the PDF to the local filesystem.
6. The system creates an ingestion job and pushes it to Redis.
7. The API returns without waiting for the full ingestion process.
8. A separate worker retrieves the job.
9. The worker extracts text and identifies document sections.
10. The worker creates chunks using structure-aware chunking.
11. The worker generates an embedding for each chunk.
12. The worker stores chunk text, source metadata, and embeddings in PostgreSQL with pgvector.
13. The document status becomes `completed` if processing succeeds.

## 7. Chunking Strategy

The MVP uses structure-aware chunking.

- Split extracted text by headings and sections where possible.
- Divide oversized sections into smaller chunks.
- Target approximately 500 tokens per chunk.
- Use approximately 100 tokens of overlap.

These values are initial configuration choices and should be evaluated against retrieval quality and citation accuracy.

## 8. Embedding Generation

Embeddings are generated immediately after chunk creation.

Each embedding is associated with its chunk and stored in PostgreSQL using pgvector. The embedding model and vector dimensions must be defined in the implementation configuration.

## 9. Duplicate Detection

The system calculates a SHA-256 hash of the PDF content.

If an existing document has the same hash:

- Return the existing `document_id`.
- Skip parsing, chunking, and embedding generation.
- Update the existing document's `collection_id` to the requested collection.

This is global deduplication. Because each document has only one `collection_id`, uploading a duplicate into another collection moves the document's association rather than preserving membership in both collections.

## 10. Failure Handling and Retries

If parsing, chunking, or embedding generation fails:

1. Record the document status as `failed`.
2. Store an `error_message`.
3. Retry automatically up to three times.
4. Before each retry, remove partial chunks belonging to that document.
5. Restart ingestion from the beginning.

Cleanup must be scoped to the affected document so data belonging to other documents remains unchanged.

Malformed PDFs are deleted without retaining a document record or diagnostic information, according to the current MVP decision.

## 11. Storage

- **Original PDFs:** Local filesystem for the MVP.
- **Document metadata:** PostgreSQL.
- **Chunk text and metadata:** PostgreSQL.
- **Embeddings:** PostgreSQL with pgvector.
- **Asynchronous job queue:** Redis.
- **Future file storage:** Object storage, such as Amazon S3.

## 12. Scope and Limitations

- PDF is the only supported input format in the MVP.
- Each document belongs to one collection at a time.
- Global deduplication does not preserve membership in multiple collections.
- Malformed PDFs are deleted without an audit record.
- Chunk size and overlap are initial values that require evaluation.
- Redis job durability, worker crash recovery, and database transaction boundaries must be addressed in the implementation design.
