# ADR-004: Hybrid Retrieval Versus Vector-Only Retrieval

- **Status:** Experiment pending; hybrid remains the initial baseline under ADR-001
- **Date:** 2026-10-11
- **Decision owner:** Project engineer
- **Related:** ADR-001, architecture.md, component_contracts.md

## 1. Context

Business research queries combine semantic questions with exact identifiers and terminology. Examples include company names, tickers, reporting periods, financial statement labels, and uncommon terms in annual reports.

Vector retrieval ranks passages by embedding similarity. Lexical retrieval ranks passages using term matching. Hybrid retrieval combines both ranking signals but adds indexing, configuration, and operational complexity.

ADR-001 already establishes hybrid retrieval as the initial MVP baseline. This ADR defines the prediction and controlled experiment needed to verify whether that additional complexity is justified.

## 2. Prediction

**Prediction, not a measured result:** hybrid retrieval will likely improve retrieval for queries that depend on exact company identifiers, financial terminology, reporting periods, and specific wording. Vector-only retrieval may remain competitive for semantic questions phrased differently from the source.

The expected advantage is a higher rate of retrieving relevant evidence in the top results, particularly for exact-term queries. The expected cost is additional indexing and ranking complexity, with potentially higher latency and resource use.

This prediction may be wrong. It must be tested against the fixed benchmark.

## 3. Options

### Option A — Vector-only

Retrieve candidates using dense-vector similarity.

Advantages:
- Simpler ranking pipeline.
- One primary retrieval index.
- Potentially lower operational complexity.

Disadvantages:
- May miss exact terms and identifiers.
- Semantic similarity may rank a related but non-answering passage highly.

### Option B — Hybrid

Retrieve candidates using vector and lexical search, then combine their rankings using a documented fusion method.

Advantages:
- Combines semantic and exact-term signals.
- May improve coverage across different query types.
- Supports a controlled comparison against vector-only retrieval.

Disadvantages:
- Requires a lexical index and ranking fusion.
- Adds configuration and debugging complexity.
- May increase latency and storage or compute costs.

## 4. Experiment design

### Hypothesis

Under equivalent corpus, chunking, embedding, and evaluation conditions, hybrid retrieval will improve relevant-evidence retrieval compared with vector-only retrieval without exceeding the documented latency and resource budget.

### Controlled variables

Keep these equivalent between the two arms:
- Benchmark questions and reference evidence.
- Corpus and document versions.
- Chunking configuration.
- Embedding model and version.
- Metadata and collection filters.
- Candidate and final result limits where comparable.
- Evaluation code and acceptance thresholds.

Record any unavoidable differences.

### Independent variable

- Arm A: vector-only retrieval.
- Arm B: hybrid lexical and vector retrieval with the fusion method recorded.

Keep reranking and query rewriting disabled for the primary comparison, or hold each at exactly the same setting in both arms. Evaluate their effects independently as required by ADR-001.

### Metrics

- Precision@k.
- Recall@k.
- MRR.
- Relevant-source top-three rate.
- Citation support and downstream evidence quality.
- Latency, resource use, and cost.
- Failure rate and no-relevant-evidence behavior.

Break results down by factual, multi-hop, unanswerable, and adversarial categories.

## 5. Decision rule

Retain hybrid retrieval if the measured evidence-quality improvement justifies its added operational cost and it satisfies predefined latency, reliability, and resource thresholds.

Prefer vector-only if it meets the evidence-quality requirements and hybrid's incremental benefit does not justify the additional complexity.

Return an inconclusive verdict if the benchmark is insufficient, the comparison is not controlled, or results are within uncertainty that the evaluation cannot resolve.

Define the numerical acceptance thresholds before the final benchmark run.

## 6. Risks and validity threats

- A small benchmark may not represent real research traffic.
- Reference labels may omit valid evidence.
- Different candidate limits can bias the comparison.
- Overall averages can conceal weak performance on exact-term or adversarial queries.
- Retrieval improvements may not translate into better cited answers.
- Index configuration and query preprocessing may affect the result.

Record these limitations with the results.

## 7. Consequences

The system retains a stable retrieval interface regardless of which strategy wins. The implementation can change without forcing the planner or report assembler to depend on a particular ranking algorithm.

## 8. Status update required after evaluation

After running the controlled experiment, append:
- Benchmark and corpus versions.
- Exact retrieval configurations.
- Numerical results and category breakdowns.
- Latency and cost comparison.
- Critical failures and limitations.
- Final decision and rationale.

Do not change the status to validated or claim hybrid superiority before this evidence exists.
