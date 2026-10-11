# Business Research Agent — System Architecture

- **Status:** Proposed MVP architecture
- **Date:** 2026-10-11
- **Related decisions:** ADR-001, ADR-002, ADR-003, ADR-004, ADR-005

## 1. Purpose

Design a bounded, evidence-backed research system for Indian listed companies. The system accepts company research requests and PDF documents, gathers and retrieves evidence, performs reproducible financial calculations, and produces a cited research report with explicit limitations.

The system is a research and analysis assistant. It does not execute trades or autonomously allocate a portfolio.

## 2. Architectural principles

1. Evidence must be traceable to a source and location.
2. Retrieval scores are ranking signals, not proof that a claim is correct.
3. Financial arithmetic must be deterministic and reproducible.
4. Untrusted document text must never override system instructions.
5. Long-running work must survive supported worker interruptions.
6. Retries, research steps, runtime, and external calls must be bounded.
7. A report is complete only after required validation succeeds.
8. Missing or conflicting evidence must be reported, not concealed.
9. Collection boundaries must be enforced before evidence is returned.
10. Architectural alternatives must be evaluated under controlled conditions.

## 3. Deployment topology

### 3.1 API service

Responsibilities:
- Validate research and upload requests.
- Resolve or request clarification for ambiguous company identities.
- Create task records and return task identifiers.
- Expose task status, progress, reports, and supported cancellation.
- Enforce request limits and collection boundaries.

The API must not synchronously execute the entire research workflow.

### 3.2 Worker

Responsibilities:
- Consume queued ingestion and research work.
- Execute bounded workflow stages.
- Coordinate planning, source acquisition, retrieval, analysis, and report validation.
- Persist stage results and recovery checkpoints.
- Apply retry policies and resource limits.

The worker is a deployment boundary. Ingestion and research may initially share the worker process while remaining logically separate workflows.

### 3.3 PostgreSQL

Authoritative storage for:
- Tasks and their lifecycle state.
- Document metadata and collection ownership.
- Extracted evidence, source locations, and provenance.
- Research findings, calculations, conflicts, and information gaps.
- Reports, validation results, and evaluation records.
- Checkpoints and audit events.

PostgreSQL is the source of truth for durable application state.

### 3.4 Redis

Used for:
- Work queueing.
- Transient coordination where needed.

Redis data must be treated as recoverable operational state, not the only copy of a completed task or report. Queue loss or interruption must not silently lose durable work.

### 3.5 Retrieval engine

A logical component responsible for:
- Query preparation and optional rewriting.
- Lexical and vector retrieval.
- Ranking fusion when hybrid retrieval is enabled.
- Optional reranking.
- Collection and metadata filtering.
- Returning evidence identifiers, source locations, and ranking information.

The initial retrieval baseline is hybrid, as recorded in ADR-001. ADR-004 defines the controlled comparison with vector-only retrieval.

### 3.6 Research planner

A bounded decision component that:
- Converts the research request into required topics and questions.
- Identifies relevant reporting periods and evidence requirements.
- Tracks dependencies between research stages.
- Prioritizes material information gaps.
- Requests additional research only within configured limits.

The planner proposes research actions. It does not bypass resource limits, validation rules, or access controls.

### 3.7 Evaluation harness

An offline evaluation component that:
- Runs versioned benchmark cases against fixed configurations.
- Measures retrieval quality, evidence support, correctness, latency, and cost.
- Compares controlled experiments.
- Records failures and category-level results.
- Supports release decisions using predefined acceptance criteria.

Evaluation results must not be inferred from report fluency or similarity scores alone.

### 3.8 Supporting deployment components

- **Caddy:** reverse proxy and HTTPS termination where configured.
- **Embedding backend:** local sentence-transformers or a hosted embedding API, selected and validated under ADR-005.
- **Document extraction:** PDF text extraction and OCR for scanned pages when required.
- **Source adapters:** controlled access to permitted financial data providers and web sources.

The embedding backend and source adapters are dependencies, not independent business-logic authorities.

## 4. Logical component boundaries

The system separates these responsibilities:

1. Request validation and task lifecycle.
2. Company identity resolution.
3. Research planning and bounded orchestration.
4. Source acquisition and PDF ingestion.
5. Evidence storage, provenance, and retrieval.
6. Financial calculations.
7. Business, industry, and risk analysis.
8. Valuation and scenario analysis.
9. Thesis and rating analysis.
10. Report assembly and validation.
11. Checkpoint recovery and security enforcement.
12. Evaluation and experimentation.

These are logical responsibilities. They do not require twelve separate deployed services.

## 5. Data flow A — Upload to searchable evidence

1. The client submits a PDF and collection context to the API.
2. The API validates the request and configured upload limits.
3. The system creates or identifies the document record and ingestion task.
4. The worker calculates a content hash and checks for a duplicate within the applicable collection.
5. The worker extracts text and page locations; OCR is used where required.
6. Extraction quality and processing errors are recorded.
7. The worker normalizes extracted content and creates traceable chunks.
8. Chunks receive stable identifiers and source-location metadata.
9. The embedding backend creates vectors; the configured lexical and vector indexes are updated.
10. Indexing is verified before the document is marked searchable.
11. The task becomes indexed, failed, or quarantined with a recorded reason.

### Upload invariants

- Repeated uploads of identical content within the same collection must not create duplicate indexed content.
- A failed extraction or indexing operation must not be reported as successful.
- Every searchable chunk must retain document identity and location provenance.
- Partially completed work must be safe to retry.
- Content from one collection must not become visible to another collection through retrieval.
- Document instructions are untrusted input, never system instructions.

## 6. Data flow B — Question to cited research report

1. The client submits a company research request.
2. The API validates the request and resolves the company identity.
3. A durable task is created and queued; the client receives its task identifier.
4. The worker establishes the research as-of date and required report topics.
5. The planner produces bounded questions, dependencies, and evidence requirements.
6. Source adapters collect permitted source records; their provenance is recorded.
7. The retrieval engine searches the applicable collection and relevant source records.
8. The system evaluates evidence sufficiency, conflicts, and missing information.
9. Deterministic financial calculations run on validated inputs with formulas and units recorded.
10. Analysis components create findings linked to evidence or calculations.
11. Valuation and rating analysis consider supporting evidence, opposing evidence, assumptions, and uncertainty.
12. The report assembler organizes the findings and citations.
13. Report validation checks evidence support, calculation reproducibility, contradictions, and required sections.
14. The system persists the report, validation outcome, provenance, and limitations.
15. The task becomes completed, completed_with_limitations, failed, or cancelled according to the task-state contract.

### Research invariants

- Material factual claims must have supporting evidence or an explicit limitation.
- Calculated claims must reference reproducible calculations and their inputs.
- A citation must identify the source and location that support the associated claim.
- Conflicting evidence must remain visible until resolved or disclosed.
- Insufficient evidence must lead to an explicit limitation or insufficient-evidence outcome.
- Report generation alone does not establish task completion.

## 7. State, persistence, and recovery

PostgreSQL owns durable task and report state. Redis supports queueing and transient coordination.

The worker persists completed-stage outputs and checkpoints at documented boundaries. After interruption, it resumes from a valid checkpoint or safely repeats an idempotent stage.

Retry policy:
- Retry eligible transient failures only within configured limits.
- Do not endlessly retry deterministic validation failures.
- Record attempts, errors, and recovery decisions.
- Preserve valid completed work.
- Do not mark a task successful if a required stage or release gate fails.

Initial runtime, queue, retry, research-step, external-call, PDF-size, and PDF-page limits must be configuration-driven and documented before implementation.

## 8. Failure behavior

| Failure | Required behavior |
|---|---|
| Redis unavailable | Do not claim new work was queued unless durable acceptance is established; recover pending work after service returns. |
| Worker crashes | Recover from durable state and checkpoints without duplicating completed work. |
| PostgreSQL unavailable | Fail safely; do not claim durable state changes succeeded. |
| Embedding backend unavailable | Retry eligible transient errors within limits; otherwise fail or defer indexing explicitly. |
| OCR or PDF extraction fails | Record the failure or quarantine the document; do not mark it indexed. |
| Retrieval returns no useful evidence | Return an explicit no-evidence outcome; do not manufacture citations. |
| External source unavailable | Record the unavailable source and its effect on report coverage. |
| Conflicting financial figures | Preserve both sources and record the conflict; do not silently choose one. |
| Calculation validation fails | Reject the affected calculation or block report release when material. |
| Report validation fails | Do not mark the report fully completed; retain diagnostics and valid intermediate work. |
| Resource limit is exhausted | Stop additional work and return an explicit limited, incomplete, or failed outcome. |
| Cancellation requested | Stop at a supported safe boundary and preserve valid completed work. |

## 9. Security and trust boundaries

- Treat uploaded documents, retrieved passages, web content, and tool outputs as untrusted data.
- Keep system instructions separate from retrieved content.
- Enforce collection scope before returning evidence.
- Validate external inputs and tool arguments.
- Restrict source adapters to approved operations.
- Avoid logging secrets or unnecessary raw document content.
- Apply explicit retention and deletion behavior to source files, chunks, reports, and derived records.
- Ensure citations reference actual stored or retrieved sources.

## 10. Evaluation and release gates

Use the versioned 40-question benchmark defined in project scope:
- 15 factual questions.
- 15 multi-hop questions.
- 5 unanswerable questions.
- 5 adversarial or poisoned-document questions.

Required controlled comparisons:
1. Hybrid versus vector-only retrieval.
2. Reranking enabled versus disabled.
3. Query rewriting enabled versus disabled.
4. Local versus hosted embeddings.

Measure retrieval Precision@k, Recall@k, MRR, relevant-source top-three rate, citation support, answer correctness, faithfulness, fallback behavior, latency, cost, and failures. Report results by question category as well as overall.

Freeze the dataset, corpus, and relevant configuration for each comparison. Define acceptance thresholds before final evaluation. Record negative results and material limitations.

## 11. Initial deployment boundary

The initial deployment consists of:
- API service
- Worker process
- PostgreSQL
- Redis
- Caddy

The retrieval engine, planner, and evaluation harness are logical components. They do not need separate network services in the MVP.

No Kafka or Celery dependency is introduced by this architecture.

## 12. Open decisions

The following require explicit decisions or measurements:
- Exact queue implementation and recovery semantics.
- Local versus hosted embedding backend.
- Final hybrid fusion and retrieval settings.
- Reranking and query-rewriting thresholds.
- OCR quality requirements for financial tables and numbers.
- Source authority and conflict-resolution rules.
- Initial resource-limit values.
- Rating methodology and report release thresholds.

These decisions must be recorded in the relevant ADR or configuration documentation rather than assumed by the architecture.

## 13. Acceptance criteria for this architecture

- Both data flows have defined success and failure outcomes.
- Every component has a defined responsibility and interface contract.
- Durable state is separated from transient queue state.
- Retrieval and report claims preserve evidence provenance.
- Worker interruption and retry behavior are testable.
- Resource limits and collection isolation are explicit.
- Retrieval and embedding choices have measurable validation plans.
