# Ingestion Observability

## Objective

Define how the document ingestion pipeline records lifecycle events, processing outcomes, and failures so that ingestion behavior can be debugged and evaluated.

## Scope

Observability covers the following stages:

1. Document registration
2. Document parsing
3. Text chunking
4. Successful completion
5. Quarantine after parsing failure

## Required Event Fields

Each lifecycle event should contain:

- `event`: Name of the lifecycle event.
- `document_id`: Identifier of the document being processed.
- `collection_id`: Collection associated with the document.
- `stage`: Current ingestion stage.
- `status`: Current processing status.
- `duration_ms`: Processing duration when measurable.
- `error_type`: Exception class or failure category when applicable.

## Event Design

| Event | When it occurs |
|---|---|
| `ingestion.registered` | A new document is registered |
| `ingestion.parse_started` | Parsing begins |
| `ingestion.parse_failed` | Parsing fails |
| `ingestion.chunking_completed` | Chunking finishes successfully |
| `ingestion.completed` | The document finishes ingestion |
| `ingestion.quarantined` | The document is moved to quarantine |

## Failure Handling

- Parsing failures must be distinguishable from registration and chunking failures.
- Failure events should provide enough context to identify the failing stage.
- A parsing failure must not be reported as successful ingestion.
- Existing quarantine behavior must remain unchanged.
- Logging failures must not silently change the ingestion result.

## Security Requirements

- Never log database credentials, API keys, or access tokens.
- Do not log complete document contents or extracted financial text.
- Avoid logging sensitive source data.
- Use document and collection identifiers for correlation.

## Testing Requirements

- Verify that successful ingestion records a completion event.
- Verify that malformed PDFs produce failure and quarantine events.
- Verify that event fields identify the relevant document and stage.
- Verify that sensitive document contents and credentials are not included in logs.
- Verify that existing ingestion behavior and tests remain unchanged.

## Definition of Done

- Lifecycle events are consistently named.
- Failures can be traced to an ingestion stage.
- Processing duration is recorded where measurable.
- Automated tests cover successful and failed ingestion.
- Existing tests pass.

## Out of Scope

- External monitoring platforms
- Distributed tracing infrastructure
- Dashboards and alerting
- Changes to the ingestion queue architecture