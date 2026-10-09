# Success Criteria

## 1. Purpose

This document defines how the Equity / Business Research Agent will be evaluated and when it can be considered ready for release.

The system is intended to produce structured, evidence-backed research on one Indian listed company per task. Success means that the system produces traceable and analytically useful reports, handles uncertainty and failures explicitly, and can be evaluated and operated reproducibly.

The thresholds below are acceptance targets, not claims about current system performance. They must be fixed before the final evaluation and must not be changed retrospectively merely to make a run pass.

## 2. Evaluation Principles

1. **Correctness and safety take precedence over aggregate scores.** Strong average performance cannot compensate for a critical failure.
2. **Separate release gates from diagnostic metrics and performance targets.** A diagnostic result helps explain system behavior but is not automatically a release blocker unless specified below.
3. **Report raw counts as well as percentages.** This is especially important for the small benchmark subsets.
4. **Preserve individual failure cases.** Every critical failure must be investigated and regression-tested where feasible.
5. **Make results reproducible.** Record dataset and configuration versions, test conditions, outputs, and relevant execution metadata.
6. **Do not overstate what the benchmark proves.** A 40-question benchmark is useful for detecting defects and comparing configurations, but is too small to establish broad statistical certainty.

## 3. Benchmark Design

The initial evaluation benchmark contains 40 questions:

| Category | Number of questions | Purpose |
|---|---:|---|
| Factual | 15 | Test direct factual questions grounded in available evidence |
| Multi-hop | 15 | Test questions requiring evidence from multiple passages or sources |
| Unanswerable | 5 | Test whether the system recognizes insufficient evidence and avoids unsupported answers |
| Adversarial / poisoned-document | 5 | Test behavior under adversarial inputs, including prompt-injection attempts |
| **Total** | **40** | |

The project’s defined prompt-injection security test also includes three poisoned documents. Record those test cases and their results explicitly; do not assume that the five adversarial benchmark questions and the three security tests are identical unless the test design says so.

For each evaluation run, preserve:
- Benchmark dataset version and question identifiers
- Relevant-source labels or answer keys, where available
- System, prompt, retrieval and evaluation configuration versions
- Per-question output and score
- Raw counts and percentages, both overall and by category
- Critical failures, error classifications and limitations
- Runtime, latency and cost observations

## 4. Mandatory Release Gates

Every mandatory gate in this section must pass before release. A failure cannot be offset by a high score elsewhere.

### 4.1 Evidence Faithfulness

**Target:** At least 80% on the defined evidence-faithfulness evaluation.

The scoring rubric must define what counts as a faithful answer and how material claims are assessed. Score individual material claims where appropriate, alongside question-level results. Report raw counts and percentages.

**Release condition:** The threshold is met and there is no unresolved critical failure involving materially unsupported claims.

### 4.2 Citation Support

**Target:** At least 90% citation-support rate.

A citation counts as supported only when the cited evidence actually supports the associated claim. A citation to a generally relevant document is not sufficient if it does not support the specific statement.

Report the numerator, denominator, and failures. Identify unsupported material claims separately.

**Release condition:** The threshold is met and there is no unresolved critical citation failure affecting a material financial or valuation conclusion.

### 4.3 Retrieval Source in Top Three

**Target:** At least 80% of applicable benchmark questions have a known relevant source retrieved in the top three results.

Calculate this metric only for questions with known relevant sources. Also record Precision@k, Recall@k and Mean Reciprocal Rank (MRR) at the configured k values.

**Release condition:** The defined top-three target is met on the applicable evaluation subset. Preserve category-level results and failures; do not imply that the small sample proves general retrieval reliability.

### 4.4 Factual Correctness

**Target:** At least 90% factual correctness across answerable benchmark questions.

Assess whether material factual claims agree with the available evidence. Record claim-level results where appropriate and question-level results as well. Report factual and multi-hop results separately.

**Release condition:** The threshold is met, with no unresolved critical factual error. A fabricated or materially incorrect financial figure must not be hidden by the aggregate score.

### 4.5 Deterministic Financial Calculations

**Target:** 100% correctness on the defined deterministic calculation test suite.

Tests must define the inputs, formula, units, financial period, and rounding rules. Include appropriate edge cases, such as:
- Negative or zero values
- Missing inputs
- Unit and scale conversions
- Financial-period mismatches
- Zero denominators
- Rounding and precision behavior

This criterion tests calculation logic; it does not by itself guarantee that a source-reported figure is correct.

**Release condition:** Every required deterministic calculation test passes.

### 4.6 Valuation and Rating Quality

**Target:** At least 80% on a predefined expert-review rubric.

The rubric must assess:
- Evidence quality and traceability
- Assumptions and their disclosure
- Calculation correctness and traceability
- Valuation and scenario logic
- Sensitivity and uncertainty handling
- Adherence to the documented rating methodology
- Appropriate use of an insufficient-evidence outcome

Do not score a rating as incorrect merely because a reviewer prefers a different investment conclusion. Evaluate the quality of its reasoning, evidence and methodology.

**Release condition:** The threshold is met and there is no unresolved critical failure involving a materially unsupported valuation or rating conclusion.

### 4.7 Prompt-Injection Resistance

**Target:** All three defined poisoned-document attacks are blocked in the defended configuration. Demonstrate the attack path in an unprotected baseline.

**Release condition:** All three defined attacks fail against the defended system. Document the attack setup, expected unsafe behavior, observed baseline behavior, defenses, defended results and residual risks.

Passing these cases demonstrates resistance to the tested attacks only. It does not establish immunity to all prompt injection.

### 4.8 Collection Isolation

**Target:** 100% pass rate on the defined collection-isolation regression suite.

Queries scoped to one collection must not retrieve or cite evidence from another collection.

**Release condition:** Every defined isolation test passes. Any confirmed cross-collection evidence leak blocks release until fixed and regression-tested.

### 4.9 Worker Crash and Recovery

**Target:** All defined worker crash, retry, checkpoint and duplicate-processing tests pass.

The system must resume from a valid checkpoint or fail clearly without corrupting completed work or duplicating side effects.

**Release condition:** All required tests pass, with state consistency and idempotency verified.

### 4.10 Dependency-Failure Handling

Required cases include:
- Redis interruption during ingestion
- Redis interruption during querying
- Malformed or corrupt PDF input
- Empty retrieval
- Exhausted retries
- Worker interruption and recovery

The two worst Redis failure paths identified during testing must be fixed and covered by tests.

**Release condition:** All defined required failure tests pass. Remaining limitations must be documented; the system must not falsely report a failed or incomplete task as successfully completed.

### 4.11 Bounded Execution and Runtime Limits

Runtime, research-step count, retries per stage and external API calls must have configurable limits.

When a limit is reached, the system must:
- Stop safely
- Identify which limit was reached
- Preserve completed work where possible
- Return an explicit incomplete or limited outcome
- Avoid presenting an incomplete report as a complete report

**Release condition:** Required limit, bounded-retry and runaway-loop tests pass.

### 4.12 Deployed End-to-End Workflow

The API, worker, PostgreSQL, Redis and Caddy must operate together in the deployed environment.

**Release condition:** A complete research task succeeds in the deployed environment and its report can be retrieved. Service startup or individual health checks alone are insufficient.

### 4.13 Evaluation Baseline and Traceability

The benchmark dataset and evaluation configuration must be versioned. Record a committed baseline, per-category results, raw counts, percentages, critical failures and known limitations.

For each report, preserve enough information to investigate the result, including:
- Task inputs and relevant timestamps/status
- Source references and evidence mappings
- Material assumptions and calculation inputs
- Relevant system/configuration versions
- Stage-level timings, cost and failure reasons

Logs should not contain unnecessary sensitive data.

**Release condition:** The baseline and required report-traceability evidence are recorded and reviewable.

## 5. Diagnostic Metrics and Targets

These measurements are required for understanding system behavior. Unless separately designated as a mandatory gate above, missing a target does not automatically block an MVP release; the miss and its cause must be reported.

### 5.1 Unanswerable-Question Handling

**Diagnostic target:** At least 80% of the five unanswerable questions are handled correctly.

Record raw counts as well as percentages. With five questions, one result changes the score by 20 percentage points.

Independently inspect unsupported factual answers. The system should disclose insufficient evidence rather than fabricate a factual answer. Any confirmed critical unsupported claim remains subject to the critical-failure policy.

### 5.2 End-to-End Report Latency

**Target:** Complete a research report within 20 minutes under documented test conditions.

Measure total latency from acceptance of a valid research task to availability of the completed report. Exclude time the user spends reviewing the report. Record stage-level timings, timeouts, failures and incomplete tasks. Report median and p95 when the run count supports useful interpretation.

Do not report latency only for successful runs without also disclosing failures and timeouts.

### 5.3 Variable Cost per Completed Report

**Target:** At or below ₹100 per completed report under documented workload and provider-pricing assumptions.

Record actual model/API and paid research-service usage where applicable. Track infrastructure/hosting cost separately and report failed-run costs separately. A cheap incomplete report does not count as a successful completed report.

### 5.4 PDF Ingestion Performance

**Target:** Ingest a text-based PDF of up to 300 pages in under five minutes under documented test conditions.

Use repeated runs, record stage-level timings, and inspect extraction quality, including numeric and table extraction where relevant. Report failures and variability.

Scanned PDFs requiring OCR must be measured separately, including extraction quality. Do not treat the text-PDF target as proof of OCR performance.

### 5.5 Retrieval Diagnostics

In addition to the top-three release target, record Precision@k, Recall@k and MRR for configured k values. Keep relevant-source labels and per-question retrieval outcomes so regressions can be investigated.

### 5.6 Reliability Diagnostics

Record, where applicable:
- Recovery success and recovery time
- Retry counts and exhausted retries
- Duplicate-processing observations
- State consistency after failures
- Failure frequency and degraded/failed outcomes
- Prompt-injection outcomes by attack case
- Known vulnerabilities and untested attack classes

These diagnostics do not replace the mandatory reliability and security gates.

## 6. Required A/B Experiments

Complete all three experiments and document the results:

1. **Hybrid retrieval vs. vector-only retrieval**
2. **Reranking enabled vs. disabled**
3. **Query rewriting enabled vs. disabled**

For each experiment, record:
- Dataset and relevant configuration versions
- Experimental setup and comparison conditions
- Retrieval and answer-quality results
- Latency and cost
- Failures and relevant limitations
- Engineering verdict and rationale
- Relevant ADR updates

Use the same benchmark conditions for each comparison. Repeat runs where appropriate and report variability when meaningful. An experiment does not have to show an improvement to count as complete; a measured negative result is valid evidence for an engineering decision.

**Project-completion condition:** All three experiments have documented results, an engineering verdict, and relevant ADR updates.

## 7. Critical-Failure Policy

Any confirmed critical failure blocks release until it is corrected and regression-tested. The failure must not be averaged away by aggregate scores.

Examples include:
- Fabricated or materially incorrect financial facts
- Materially unsupported valuation or rating conclusions
- Cross-collection evidence leakage
- A successful attack in the defined prompt-injection test suite
- Reporting an incomplete or failed task as successfully completed
- Incorrect deterministic financial calculations

For each confirmed critical failure:
1. Record the case and severity.
2. Investigate and document the root cause.
3. Implement a corrective action.
4. Add a regression test where feasible.
5. Rerun the relevant test and record the outcome.

The list is intended to guide severity decisions; it does not imply that every minor factual or presentation error is automatically critical. Materiality and consequences must be documented.

## 8. Overall Release Decision

Release is permitted only when every mandatory release gate in Section 4 passes and there are no unresolved critical failures.

The following are targets rather than automatic release blockers for the MVP:
- End-to-end report latency of 20 minutes or less
- Variable cost of ₹100 or less per completed report
- PDF ingestion under five minutes for a 300-page text PDF

If a latency or cost target is missed, record the measured result, cause, impact and limitation. The target must not be silently redefined. A release may proceed only if all mandatory quality, safety, reliability and traceability gates pass and the performance/cost limitation is documented.

The final release record must distinguish:
- Gates passed
- Gates failed
- Diagnostic results
- Performance/cost targets met or missed
- Critical failures and their resolution
- Known limitations and residual risks

## 9. Benchmark Reporting Format

For every benchmark run, report:
- Dataset version and evaluation configuration version
- Date/run identifier and relevant system versions
- Overall raw counts and percentages
- Results for factual, multi-hop, unanswerable and adversarial categories
- Claim-level and question-level scoring where appropriate
- Retrieval metrics and relevant-source top-three results
- Valuation/rating rubric score
- Deterministic calculation test results
- Security, isolation, recovery and dependency-failure test results
- Latency, cost and ingestion measurements
- Critical failures, failure analysis and known limitations
- Baseline comparison and links/references to per-question outputs

Do not imply statistical certainty from this 40-question benchmark. Treat it as a versioned engineering benchmark for defect detection, regression tracking and controlled comparisons.

## 10. Project Completion Evidence

The project is complete when the repository contains and demonstrates:
- A deployed end-to-end research workflow
- Report evidence and claim traceability
- Valuation and rating methodology, including an insufficient-evidence outcome
- Passing required security, isolation, recovery and dependency-failure tests
- Benchmark dataset, configuration, baseline and results
- Completed required A/B experiments and updated ADRs
- Performance and cost measurements with test conditions
- Security findings, known limitations and residual risks
- Setup, deployment and recovery documentation
- A project postmortem describing failures, lessons and next steps

A project completion claim must be supported by recorded test and deployment evidence. Planned criteria, unrun tests or unmeasured targets must not be described as achieved.
