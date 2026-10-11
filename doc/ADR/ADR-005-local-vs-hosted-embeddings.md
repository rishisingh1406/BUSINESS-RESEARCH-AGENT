# ADR-005: Local Sentence-Transformers Versus Hosted Embeddings

- **Status:** Decision pending controlled evaluation
- **Date:** 2026-10-11
- **Decision owner:** Project engineer
- **Related:** ADR-001, ADR-002, ADR-004, architecture.md, component_contracts.md

## 1. Context

The research system must embed extracted document chunks during ingestion and embed queries during retrieval. The embedding backend affects retrieval quality, latency, operating cost, deployment complexity, availability, and data handling.

The MVP needs a backend that can be evaluated under the intended deployment conditions rather than selected solely from model reputation or a single latency measurement.

## 2. Prediction

**Prediction, not a measured result:** a local sentence-transformers model may provide more predictable marginal cost and keep embedding inputs within the controlled deployment environment. It will consume local CPU, memory, and possibly GPU resources, and its latency may be poor under concurrent ingestion or retrieval workloads.

A hosted embedding API may reduce local compute requirements and simplify model serving. It introduces network latency, provider availability and rate-limit dependencies, usage-based cost, and external data-transfer considerations.

Neither option is assumed to produce better retrieval quality. Quality depends on the specific model, corpus, chunking, language, query types, and retrieval configuration.

## 3. Options

### Option A — Local sentence-transformers

Advantages:
- No per-request embedding-provider charge after deployment, though compute and operations still cost money.
- Inputs can remain inside the deployment boundary.
- Model version and execution environment can be controlled.
- Can operate without an external embedding API when dependencies are locally available.

Disadvantages:
- Consumes CPU and memory; throughput depends on hardware and batching.
- Model installation, updates, and serving become operational responsibilities.
- Concurrent embedding work may compete with other worker tasks.
- Local inference can have high latency on constrained hardware.

### Option B — Hosted embedding API

Advantages:
- Minimal local model-serving responsibility.
- Provider-managed inference infrastructure.
- May offer higher throughput or better latency under some workloads.
- Easier to scale embedding requests independently of the application host.

Disadvantages:
- Usage-based cost and possible pricing changes.
- Network latency, rate limits, and provider outages.
- External data-transfer and retention terms require review.
- Model availability and version changes can affect reproducibility.

## 4. Experiment design

### Objective

Choose an embedding backend that meets the required evidence-quality, latency, cost, reliability, and data-handling constraints for the MVP.

### Controlled variables

Keep these equivalent:
- Document corpus and benchmark version.
- Chunking and text preprocessing.
- Retrieval filters and result limits.
- Retrieval method and ranking configuration.
- Evaluation questions and reference evidence.
- Measurement environment and workload definition where feasible.

Each embedding model may require its own vector index. Do not mix vectors from incompatible embedding models in the same index or compare results without recording model and index compatibility.

### Independent variable

- Arm A: a named and versioned local sentence-transformers model.
- Arm B: a named hosted embedding model and provider configuration.

Record model identity, vector dimensions, normalization behavior, token limits, batch settings, and relevant API or runtime configuration.

### Metrics

- Precision@k, Recall@k, MRR, and relevant-source top-three rate.
- Citation support and downstream answer quality.
- Embedding latency and end-to-end retrieval latency.
- Throughput under the documented workload.
- CPU and memory use for local inference.
- Hosted usage charges and estimated cost per research task.
- Rate-limit, timeout, and dependency-failure rates.
- Recovery behavior and operational complexity.
- Data-transfer, retention, and privacy constraints.

Measure ingestion embeddings and query embeddings separately; their workload characteristics differ.

## 5. Decision rule

Choose local embeddings if retrieval quality satisfies the predefined requirements and local resource use, latency, and operational burden fit the target deployment.

Choose hosted embeddings if their measured quality or performance benefits justify the ongoing cost and external dependency, and data-handling requirements permit their use.

If neither option meets requirements, evaluate another model or revise the deployment plan rather than claiming a successful selection.

Define numerical thresholds and the workload before the final comparison.

## 6. Reproducibility and index migration

- Record the exact model identifier and version.
- Record preprocessing and vector-normalization behavior.
- Associate each index with its embedding configuration.
- Re-embed the corpus when changing to an incompatible model or vector space.
- Evaluate a replacement model before routing production queries to its index.
- Keep the previous valid index available until migration and validation succeed, where resources permit.

## 7. Failure behavior

Local backend failure must produce an explicit failed or deferred embedding task; it must not silently create invalid vectors.

Hosted backend failure must follow bounded retry rules for eligible transient errors. Exhausted rate limits, authentication errors, and provider failures must be recorded distinctly.

A model change must not silently mix incompatible document and query embeddings.

## 8. Risks and validity threats

- Different model dimensions or preprocessing may invalidate a naive comparison.
- Low-volume tests may hide concurrency and rate-limit issues.
- Provider latency varies with network and service conditions.
- Local measurements depend on hardware, batching, and concurrent workload.
- Price estimates can change; record the price source and evaluation date.
- Retrieval metrics do not by themselves prove financial correctness or citation support.

## 9. Status update required after evaluation

Append:
- Exact local and hosted model identifiers.
- Hardware and workload conditions.
- Benchmark and corpus versions.
- Retrieval-quality results.
- Latency, throughput, and cost results.
- Failure and data-handling assessment.
- Selected backend, rationale, and limitations.

Until these measurements are recorded, the embedding decision remains pending.
