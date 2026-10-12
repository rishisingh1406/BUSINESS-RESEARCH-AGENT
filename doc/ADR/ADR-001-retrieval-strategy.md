# ADR-001: Retrieval Strategy for Research Evidence

- **Status:** Accepted for MVP baseline; subject to benchmark validation
- **Date:** 2026-10-10
- **Decision owner:** Project engineer

## 1. Context

The research agent must retrieve evidence from annual reports, filings, and other company sources. Financial research includes both semantic questions and exact-match queries involving company names, dates, financial metrics, section names, and numerical terminology.

Retrieval errors can lead to unsupported claims, missing evidence, or incorrect conclusions. The strategy must therefore be evaluated independently of report fluency.

## 2. Decision drivers

- Relevant evidence must be retrievable from long documents.
- Exact terms and semantic similarity both matter.
- The system must preserve source and location metadata.
- Retrieval quality must be measurable on a fixed dataset.
- Added latency and cost must be measured.
- The system must support an explicit no-relevant-evidence outcome.

## 3. Options considered

### Option A — Vector-only retrieval

Retrieve passages using semantic similarity.

**Advantages**
- Simpler initial pipeline
- Useful for semantically phrased questions
- Fewer ranking components

**Disadvantages**
- May miss exact identifiers, uncommon financial terms, and specific wording
- Similarity scores alone do not establish that evidence answers the question

### Option B — Hybrid retrieval

Combine semantic retrieval with lexical retrieval and merge the rankings.

**Advantages**
- Covers semantic and exact-term queries
- Provides an alternative retrieval signal when one method ranks a relevant passage poorly
- Can be evaluated against vector-only retrieval

**Disadvantages**
- More components and configuration
- Ranking fusion needs tuning
- Additional indexing and retrieval cost

## 4. Decision

Use hybrid retrieval as the initial MVP baseline. Combine vector and lexical rankings using a documented fusion method.

Keep reranking and query rewriting independently configurable so their effects can be measured rather than assumed.

The retrieval contract must return evidence identifiers, source references, locations, ranking information, and an explicit empty-result outcome when no acceptable evidence is found.

## 5. Consequences

**Positive**
- Supports both semantic and exact-term research queries.
- Makes retrieval behavior measurable and reproducible.
- Allows later changes without changing the external retrieval contract.

**Negative**
- Adds implementation and evaluation complexity.
- May increase latency and resource use.
- Hybrid retrieval may not outperform a simpler approach on every query category.

## 6. Validation plan

Run the required experiments under the same benchmark conditions:

1. Hybrid retrieval versus vector-only retrieval.
2. Reranking enabled versus disabled.
3. Query rewriting enabled versus disabled.

Record dataset and configuration versions, relevant-source top-three rate, Precision@k, Recall@k, MRR, downstream evidence quality, latency, cost, failures, and limitations.

Do not assume a configuration is better merely because it produces higher similarity scores.

## 7. Revisit conditions

Reconsider the baseline if controlled evaluation shows that another configuration provides better evidence quality at acceptable latency and cost, or if the complexity of hybrid retrieval is not justified by measurable gains.

Update this ADR with the experimental result and final engineering verdict.