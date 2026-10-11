# Business Research Agent — Component Contracts

- **Status:** Proposed MVP interfaces
- **Date:** 2026-10-11
- **Related documents:** architecture.md, 09_contracts.md
- **Purpose:** Define the responsibilities, inputs, outputs, failure behavior, and invariants of five major component interfaces.

## 1. Contract conventions

These are logical interfaces. They do not require each component to run as a separate network service.

- IDs are opaque identifiers; callers must not assume a particular generation strategy.
- Timestamps use UTC.
- Collection scope must be explicit wherever document evidence is accessed.
- Errors must be structured and distinguish invalid input, unavailable dependencies, resource limits, and insufficient evidence.
- A successful response means the operation described by that interface succeeded; it does not guarantee the correctness of downstream research conclusions.
- Exact serialization schemas and implementation libraries remain implementation decisions unless specified elsewhere.

## 2. Contract C01 — API Service

### Responsibility

Validate client requests, establish task identity, persist accepted work, and expose task status and results. The API does not execute the entire long-running research workflow synchronously.

### Request: Create research task

Required logical fields:
- `company_identifier`: company name or ticker supplied by the client.
- `collection_id`: evidence collection to use, when applicable.
- `as_of_date`: optional requested research cutoff date.
- `research_options`: optional supported configuration.
- `idempotency_key`: optional client key to prevent duplicate task creation on retry.

### Response: Accepted task

- `task_id`
- `task_status`
- `created_at`
- `status_url` or equivalent status reference
- `resolved_company`, if identity resolution completed synchronously
- `warnings`, if clarification or limitations are already known

The API must not report a task as queued unless durable task acceptance and the queueing/recovery protocol have succeeded.

### Other operations

- Retrieve task state and progress by `task_id`.
- Retrieve a completed or limited report.
- Request cancellation where supported.
- Submit a PDF upload with collection context and configured limits.

### Failure behavior

- Invalid request: reject with a structured validation error.
- Ambiguous company: request clarification or return an explicit ambiguous-identity state.
- Persistence unavailable: do not claim that the task was accepted.
- Queue unavailable: use the documented durable enqueue/recovery protocol or return an explicit temporary failure.
- Unknown task: return a not-found outcome without exposing other task data.
- Cancellation after completion: return the documented conflict or terminal-state outcome.

### Invariants

- Every accepted task has a stable identifier.
- Task state is read from authoritative durable state.
- Collection access is checked before returning protected evidence or reports.
- Long-running research is performed by the worker, not held open in the request.
- Responses do not expose secrets or internal credentials.

## 3. Contract C02 — Ingestion Worker

### Responsibility

Validate and process accepted PDF ingestion tasks, preserve source provenance, and make evidence searchable only after required processing succeeds.

### Input

- `ingestion_task_id`
- `document_id`
- `collection_id`
- `source_file_reference`
- `content_hash`, if already calculated
- `configured_limits`
- `retry_context`, if the task is being resumed

### Output

- `document_id`
- `ingestion_status`
- `content_hash`
- `extraction_summary`
- `chunk_count`
- `indexing_status`
- `quality_warnings`
- `failure_reason`, when applicable

### Required stages

1. Validate file type, size, and page limits.
2. Calculate and verify the content hash.
3. Detect duplicates within the applicable collection.
4. Extract PDF text and page-level locations.
5. Use OCR where required.
6. Record extraction quality and material warnings.
7. Normalize content and create traceable chunks.
8. Generate embeddings and update configured indexes.
9. Verify indexing and persist the final state.

### Failure behavior

- Unsupported or oversized file: reject with a specific reason.
- Duplicate content: reuse or reference the existing indexed document according to the chosen duplicate policy.
- Extraction or OCR failure: record failure or quarantine; do not claim full indexing.
- Embedding backend failure: retry only eligible transient failures within limits.
- Indexing failure: preserve recoverable progress and leave the document non-searchable until consistency is restored.
- Worker interruption: resume from a durable checkpoint or safely repeat an idempotent stage.

### Invariants

- Reprocessing the same content in the same collection must not create duplicate indexed content.
- Every chunk retains document identity and source location.
- A document is marked indexed only after required index operations are verified.
- OCR-derived numeric content must not be assumed correct without quality checks.
- Document content is untrusted data and cannot modify system instructions.

## 4. Contract C03 — Retrieval Engine

### Responsibility

Return ranked, traceable evidence relevant to a research question while enforcing collection scope, metadata constraints, and configured resource limits.

### Request

- `query_id`
- `query_text`
- `collection_id`
- `top_k`
- `metadata_filters`
- `reporting_period`, when applicable
- `required_source_types`, when applicable
- `retrieval_configuration_version`

### Response

- `query_id`
- `retrieval_status`: `results_found`, `no_results`, `blocked`, or `failed`
- `results`: ordered evidence records containing:
  - `evidence_id`
  - `document_id`
  - `collection_id`
  - `source_reference`
  - `page_or_location`
  - `chunk_text` or an authorized evidence reference
  - `ranking_score`
  - `retrieval_method`
- `configuration_version`
- `latency_ms`
- `warnings`

### Failure behavior

- Invalid filters or query: return a validation error.
- Collection mismatch: block access; do not return evidence.
- No relevant evidence: return `no_results`.
- Index or embedding dependency unavailable: return a structured failure.
- Resource limit exceeded: stop within the configured budget and report the limitation.

### Invariants

- Collection filtering occurs before evidence is exposed to the caller.
- Every result identifies its source and location.
- Ranking scores are not confidence probabilities or proof of factual support.
- Results are reproducible against a recorded corpus and configuration version to the extent supported by the implementation.
- Reranking and query rewriting remain independently configurable for evaluation.
- The external contract remains stable when the underlying ranking implementation changes.

## 5. Contract C04 — Research Planner

### Responsibility

Convert a company research request into a bounded, dependency-aware plan, identify material evidence gaps, and propose follow-up research actions within configured limits.

### Input

- `task_id`
- `resolved_company`
- `as_of_date`
- `report_requirements`
- `available_source_types`
- `existing_findings`
- `known_conflicts`
- `known_information_gaps`
- `remaining_resource_budget`

### Output

- `plan_id`
- `plan_version`
- `research_questions`
- `planned_steps`, each containing:
  - `step_id`
  - `objective`
  - `required_evidence`
  - `dependencies`
  - `priority`
  - `completion_condition`
- `identified_gaps`
- `proposed_follow_up_actions`
- `estimated_resource_needs`
- `plan_warnings`

### Planning rules

- Prioritize material questions needed for the requested report.
- Specify reporting periods and units where relevant.
- Respect completed work and existing evidence.
- Distinguish missing evidence from contradictory evidence.
- Propose further retrieval only when it addresses a material gap.
- Keep actions within the remaining research-step, runtime, and external-call budgets.

### Failure behavior

- Ambiguous company identity: request clarification rather than plan for an assumed company.
- Insufficient remaining budget: produce a limited plan or explicit inability to continue.
- Dependency cycle: reject the invalid plan.
- Planner failure: record the stage failure and apply the bounded retry policy.
- Insufficient evidence after allowed research: report the gap instead of fabricating a finding.

### Invariants

- The planner cannot bypass deterministic validation or security checks.
- The planner cannot increase its own resource limits.
- Every planned step has an objective and completion condition.
- Additional research must be justified by an identified need.
- A plan is not proof that its questions have been answered.

## 6. Contract C05 — Evaluation Harness

### Responsibility

Run repeatable benchmark cases against specified system configurations and report retrieval quality, answer quality, reliability, latency, cost, and failure behavior.

### Input

- `evaluation_run_id`
- `benchmark_version`
- `corpus_version`
- `configuration_version`
- `experiment_id`
- `cases`
- `evaluation_limits`
- `acceptance_thresholds`

Each experiment must record the variables being compared and the variables held constant.

### Output

- `evaluation_run_id`
- `benchmark_version`
- `configuration_version`
- `case_results`
- `aggregate_metrics`
- `category_metrics`
- `latency_summary`
- `cost_summary`
- `failure_summary`
- `threshold_results`
- `limitations`
- `recommendation`: `accept`, `reject`, or `inconclusive`

### Required benchmark categories

Use the project's 40-question benchmark:
- 15 factual questions.
- 15 multi-hop questions.
- 5 unanswerable questions.
- 5 adversarial or poisoned-document questions.

### Required metrics

- Precision@k
- Recall@k
- Mean Reciprocal Rank (MRR)
- Relevant-source top-three rate
- Citation support
- Answer correctness and faithfulness
- Correct fallback behavior
- Latency and cost
- Failure and critical-error counts

### Required experiments

1. Hybrid retrieval versus vector-only retrieval.
2. Reranking enabled versus disabled.
3. Query rewriting enabled versus disabled.
4. Local sentence-transformers embeddings versus hosted embeddings.

### Failure behavior

- Invalid benchmark or configuration: reject the run.
- Missing reference evidence: mark affected cases invalid or incomplete; do not silently count them as successful.
- Evaluator failure: preserve partial results and mark the run incomplete.
- Threshold failure: report the failed threshold explicitly.
- Insufficient or incomparable data: return `inconclusive`.

### Invariants

- Acceptance thresholds are set before the final evaluation, not selected after seeing the results.
- Comparisons use equivalent benchmark and corpus versions.
- Configuration changes are recorded.
- Aggregate scores do not hide critical adversarial, citation, or correctness failures.
- Negative results and limitations are retained.
- A benchmark result supports a decision only for the tested conditions; it does not prove universal superiority.

## 7. Cross-contract guarantees

1. Every task and document operation has a traceable identifier.
2. Durable state changes are persisted before success is reported.
3. Collection boundaries are enforced at every evidence-access boundary.
4. Evidence references remain connected to source and location metadata.
5. Errors have explicit categories and bounded retry behavior.
6. Resource limits apply even when a component requests additional work.
7. Report completion requires the report-validation gate.
8. Evaluation records enough configuration information to reproduce the comparison.

## 8. Open implementation decisions

These contracts do not yet mandate:
- Exact Python class names or serialized schema libraries.
- REST endpoint paths.
- Internal queue message format.
- Database table layout.
- Embedding model identity or hosted provider.
- Exact lexical index and ranking-fusion implementation.
- Final retry, timeout, and resource-limit values.

Resolve these in implementation design and the relevant ADRs. Do not silently treat an unspecified detail as an accepted project decision.
