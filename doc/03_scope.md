# 03 — Project Scope: Equity / Business Research Agent

## 1. Project Overview

### 1.1 Objective

Build an AI-powered equity and business research platform that produces structured, evidence-backed research reports on Indian listed companies.

The system should help individual investors understand a company's business model, financial performance, competitive position, management, risks, valuation, and investment thesis.

The target is research approaching the quality of a professional equity research analyst report. This is an objective to validate through evaluation, not a claim of guaranteed analyst-level accuracy.

### 1.2 Target User

Individual investors who want to research publicly listed Indian companies but have limited time to collect, interpret, compare, and validate information from multiple sources.

### 1.3 Core Use Case

The user supplies a company name or ticker and requests a comprehensive research report.

The system collects relevant public information, processes available annual reports, analyzes financial and business performance, identifies gaps and conflicting evidence, estimates valuation scenarios, evaluates historical price trends, and produces a traceable research conclusion.

The report supports the user's own research and judgment. The system does not execute trades or determine portfolio allocation.

---

## 2. MVP Scope

The MVP focuses on researching **one Indian listed company per research task**.

It must support the following capabilities.

### 2.1 Research Initiation

* Accept a company name or ticker.
* Ask the user to confirm the company when the input is ambiguous.
* Establish the research question and an as-of date for the analysis.
* Identify the information required to complete the research.
* Track the status and progress of each research task.

### 2.2 Company and Business Research

* Retrieve publicly available company information.
* Explain the company's history, business model, revenue sources, and major business segments where information is available.
* Research management and corporate governance.
* Analyze the company's industry, competitive position, and business risks.
* Suggest relevant competitors and explain the selection based primarily on industry and business similarity.
* Consider scale and data comparability when interpreting competitor comparisons.

### 2.3 Financial and Fundamental Analysis

* Analyze income statements, balance sheets, and cash flow statements.
* Cover up to five years of financial history where reliable data is available.
* Calculate relevant financial ratios, growth rates, and other fundamental metrics.
* Identify important financial trends and potential concerns.
* Preserve traceability between reported figures, source inputs, and calculated metrics.
* Clearly disclose missing financial periods and unreliable inputs.

### 2.4 Valuation and Scenarios

* Produce a valuation range as part of the report.
* Explain valuation methods, assumptions, estimates, and limitations.
* Present bull, base, and bear scenarios with their assumptions and uncertainty.
* Explain important valuation sensitivities.
* Distinguish reported financial figures from calculated metrics and estimated inputs.
* If the evidence cannot support a meaningful valuation, provide an explicitly speculative, high-uncertainty range and label it as **not decision-grade**.

### 2.5 Historical Price and Technical Analysis

* Retrieve historical share-price data where available.
* Analyze up to five years of historical prices.
* Calculate relevant technical indicators and describe historical price trends.
* Disclose incomplete price history or unavailable indicators.
* Keep technical analysis distinct from fundamental analysis and valuation.
* Do not require live prices or real-time market monitoring.

### 2.6 Evidence and Source Management

* Extract relevant evidence from company filings and public sources.
* Preserve source references and source locations where available.
* Link material factual claims to their supporting evidence.
* Track evidence provenance from a reported claim to the supporting source and document location, where available.
* Identify conflicting figures, missing information, and uncertainty.
* Prefer authoritative sources for reported company figures without silently suppressing material disagreements.
* Record enough research state to support auditing and recovery.

### 2.7 Report Generation

Generate a structured report containing:

1. Executive summary
2. Company history and business model
3. Management and corporate governance
4. Industry overview
5. Five-year financial and fundamental analysis
6. Competitor comparison and competitive positioning
7. Risks and uncertainties
8. Valuation range, assumptions, and sensitivities
9. Bull, base, and bear scenarios
10. Historical price trends and technical indicators
11. Investment thesis and antithesis
12. Buy/hold/sell rating or an explicit insufficient-evidence outcome
13. Missing information, source conflicts, and limitations
14. Sources and supporting evidence

When a section cannot be adequately supported, the report must disclose the limitation rather than fabricate completeness.

---

## 3. Supported Inputs and Data Sources

### 3.1 Company Universe

* Indian listed companies only.
* One company per research task.
* Company identified by name or ticker.

### 3.2 Financial Information

Required financial categories:

* Income statement
* Balance sheet
* Cash flow statement
* Financial ratios
* Growth trends
* Relevant historical financial metrics

The target coverage is five years, subject to source availability and reliability.

### 3.3 Company Filings

Supported filing sources:

* Official company websites
* Stock exchange and regulatory filings
* User-uploaded annual reports

Third-party websites that merely reproduce filings are not a primary source requirement.

### 3.4 User-Uploaded Documents

* PDF files only.
* Text-based and scanned PDFs.
* OCR must be supported for scanned documents.
* Maximum page count: 300 pages.
* Initial maximum file size: 20 MB, to be confirmed before implementation.

Malformed or unreadable files must be reported and quarantined where appropriate.

OCR-extracted figures, especially financial tables and numeric values, must be validated where possible or explicitly flagged as uncertain.

### 3.5 Market Information

* Historical share prices, with five years as the target period.
* Historical price trends and technical indicators.
* No requirement for real-time prices or continuous market feeds.

### 3.6 Competitor Research

The system suggests relevant competitors and explains why they were selected. Industry and business similarity are the primary criteria.

Comparability limitations, including differences in scale and available financial information, must be disclosed where material.

### 3.7 Missing or Conflicting Data

* Continue research with available reliable evidence when a source is unavailable.
* Disclose missing information and its impact on conclusions.
* Prefer authoritative sources for reported financial figures.
* Compare reporting periods, units, and metric definitions when sources disagree.
* Disclose material unresolved conflicts and explain the figure selected for analysis.
* Never invent missing historical figures or imply that incomplete coverage is complete.

---

## 4. Investment Conclusion and Valuation Boundaries

### 4.1 Valuation

The system must attempt to provide a valuation range, even when the available evidence is incomplete.

However:

* Assumptions and estimates must be explicitly identified.
* Source-derived values must be distinguished from calculated and estimated values.
* The valuation range must reflect uncertainty.
* Missing inputs and sensitivity to assumptions must be disclosed.
* Unsupported estimates must not be presented as reliable valuations.
* When a meaningful estimate cannot be supported, the range must be labelled speculative and not decision-grade.

### 4.2 Investment Rating

The report must provide a buy, hold, or sell rating when the methodology and evidence permit.

The rating methodology must define:

* Investment horizon
* Valuation reference
* Rating criteria and thresholds
* Evidence requirements
* Factors driving the rating
* Conditions that could change the rating

When evidence is insufficient for a defensible classification, the report must retain the rating field but return an explicit **insufficient evidence / low confidence** outcome.

The conclusion must include supporting and opposing arguments, important risks, unresolved questions, and relevant assumptions.

The system does not execute trades, determine portfolio allocations, or decide how much the user should invest.

---

## 5. Operational Boundaries

### 5.1 Research Execution

Research runs as a background job.

* Each research request receives a unique ID.
* The user receives the ID and initial status without waiting for the entire report.
* The system persists job status and stage progress.
* Long-running work does not depend on the original HTTP connection remaining open.

### 5.2 Progress Reporting

Expose the current research stage, such as:

* Queued
* Retrieving sources
* Processing documents
* Analyzing financials
* Performing valuation
* Generating report
* Completed
* Failed
* Cancelled

Do not display a percentage unless it reflects measurable progress.

Partial findings are not required in the MVP.

### 5.3 Checkpoints and Recovery

* Persist valid checkpoints for long-running research.
* Resume interrupted jobs from the last valid checkpoint where possible.
* Retry failed stages safely.
* Avoid duplicate document ingestion, evidence records, and repeated side effects.
* Record failures and recovery attempts.
* Never mark an interrupted or failed run as successfully completed.

### 5.4 Concurrency and Queue

* Allow only one active research job at a time in the MVP.
* Queue additional jobs.
* Set a configurable maximum queue size.
* Reject new submissions clearly when the queue is full.
* Do not silently discard previously queued jobs.

### 5.5 Cancellation

* Allow queued and running jobs to be cancelled.
* Cancel queued jobs immediately.
* Stop running jobs safely at appropriate checkpoints where possible.
* Preserve completed results.
* Record cancellation state and do not mark cancelled jobs as completed.
* Recognize that external requests already in flight may not be reversible.

### 5.6 Resource and Cost Limits

Provide configurable limits for:

* Maximum research runtime
* Maximum research steps
* Maximum retries per stage
* Maximum external API calls

The exact numerical values must be defined before implementation.

When a limit is reached, the system must record which limit was triggered, identify incomplete work, and disclose that limitation to the user.

### 5.7 Persistence and Retention

Persist research until the user explicitly deletes it. Automatic expiration is not required for the MVP.

Persist enough information for audit and recovery, including:

* Final report
* Research status and timestamps
* Source references and document locations
* Evidence-to-claim mappings
* Financial inputs and calculation assumptions
* Relevant intermediate stage results
* Failure and recovery details

Support explicit deletion of a research run and its associated stored data, subject to documented storage dependencies.

### 5.8 Research Collections

Support multiple research collections with per-collection retrieval scope.

The MVP must demonstrate at least two collections containing distinct documents. Queries scoped to one collection must not retrieve evidence belonging exclusively to another collection.

Automated regression tests must verify isolation after relevant changes.

This is a retrieval boundary, not a full multi-user authorization system.

---

## 6. Quality and Security Boundaries

### 6.1 Evidence Sufficiency

* Do not present unsupported claims as facts.
* Explicitly identify missing evidence and uncertainty.
* Continue producing useful report sections when only some information is unavailable.
* Do not fabricate figures or conceal material evidence gaps.

### 6.2 Citation Standard

Every material factual claim must link to supporting evidence and a source location where available.

Claims that cannot be adequately supported must be flagged.

Calculated values must be traceable to their inputs, units, periods, and formulas. Estimates and analytical judgments must be distinguishable from reported facts.

### 6.3 Financial Calculation Validation

* Use deterministic logic for financial calculations.
* Preserve calculation inputs, units, reporting periods, formulas, and outputs.
* Test calculations against known cases and edge cases.
* Handle missing values and invalid denominators explicitly.
* Recognize that deterministic calculations can still be wrong if the source data or formula is wrong.

### 6.4 Source Conflict Handling

* Prefer authoritative sources for reported figures.
* Compare periods, units, and definitions before interpreting disagreements.
* Disclose material unresolved conflicts.
* Explain which figure was used and why.
* Do not average conflicting values merely to manufacture agreement.

### 6.5 Prompt-Injection Defense

Retrieved documents and external source content must be treated as untrusted data, not instructions.

The MVP must include:

* Instruction hierarchy enforcement
* Isolation of untrusted source content
* Output validation and filtering
* Three deliberately poisoned documents in the security test suite
* A demonstration of the attacks against the unprotected behavior
* Defense implementation and repeat testing until the defined attacks fail
* A security note describing tested coverage and residual risks

Passing the defined attack suite is evidence of resistance to those tested attacks, not proof of universal immunity.

### 6.6 File and Data Security

* Validate uploaded file type and size.
* Use path-safe file handling and storage.
* Quarantine malformed documents where appropriate.
* Avoid logging unnecessary document contents or sensitive material.
* Support explicit deletion of research data.
* Full authentication, role-based access control, and multi-user isolation are outside the MVP scope.

### 6.7 Release Evaluation

Before the final release evaluation:

* Define measurable acceptance thresholds.
* Commit a reproducible benchmark baseline.
* Report performance by question category.
* Document critical failures and limitations.
* Do not claim that a critical release gate passed if its required threshold failed.

---

## 7. Evaluation and Experimentation

### 7.1 Benchmark Dataset

The benchmark must contain 40 questions:

| Category                        | Questions |
| ------------------------------- | --------: |
| Factual                         |        15 |
| Multi-hop                       |        15 |
| Unanswerable                    |         5 |
| Adversarial / poisoned-document |         5 |
| **Total**                       |    **40** |

The dataset must be versioned and committed so that evaluation results can be reproduced.

### 7.2 Retrieval Evaluation

Measure:

* Precision@k
* Recall@k
* Mean Reciprocal Rank (MRR)

The benchmark should track whether known relevant sources appear in the top three retrieved results.

### 7.3 Answer Evaluation

Evaluate:

* Faithfulness to retrieved evidence
* Answer correctness
* Appropriate fallback behavior
* Citation support
* Latency
* Cost

Use claim-versus-context evaluation for faithfulness where appropriate, including LLM-as-judge evaluation with documented limitations.

### 7.4 Mandatory A/B Experiments

Run and document:

1. Hybrid retrieval versus vector-only retrieval.
2. Reranking enabled versus disabled.
3. Query rewriting enabled versus disabled.

Each experiment must record:

* Configuration and dataset version
* Retrieval and answer-quality results
* Latency
* Cost
* One-paragraph engineering verdict

Update relevant architecture decision records (ADRs) based on measured results.

Numerical acceptance thresholds must be established in the evaluation documentation before the final release evaluation; they must not be chosen retrospectively to make results pass.

---

## 8. Performance and Reliability Completion Targets

### 8.1 PDF Ingestion

For a text-based PDF containing up to 300 pages:

* Target ingestion time: under five minutes.
* Document the hardware, file characteristics, and test conditions.
* Measure scanned-PDF OCR separately.
* Record OCR timing and extraction quality.
* Validate financial tables and numeric extraction where possible.

The target is a defined benchmark condition, not a universal guarantee for every PDF.

### 8.2 Failure-Injection Requirements

Demonstrate and document:

* Malformed or corrupt PDF handling
* Empty retrieval and insufficient-evidence behavior
* Duplicate document upload without duplicate ingestion
* Worker crash and checkpoint recovery
* Redis interruption during ingestion
* Redis interruption during research queries
* Runtime, retry, and API-call limit handling
* Prompt-injection defense behavior

For Redis failures, identify the two worst failure paths, implement fixes, and verify those fixes with automated tests. Document remaining limitations.

### 8.3 Deployment

Deploy a usable multi-service application consisting of:

* API service
* Research worker
* PostgreSQL
* Redis
* Caddy

Document setup, configuration, health checks, deployment, and recovery procedures. Verify the deployed end-to-end workflow.

Production-scale autoscaling, high availability, and distributed infrastructure are not required.

---

## 9. MVP Completion Criteria

The MVP is complete only when the required functionality and engineering evidence are demonstrably present.

### 9.1 End-to-End Workflow

* [ ] Accept an Indian listed company name or ticker.
* [ ] Resolve ambiguous company identification.
* [ ] Run a background research job and expose stage-level progress.
* [ ] Process an annual-report PDF and retrieve available public company and financial information.
* [ ] Analyze fundamentals, competitors, risks, valuation, scenarios, and historical prices where data is available.
* [ ] Generate the complete structured report.
* [ ] Provide evidence-backed findings and traceable calculations.
* [ ] Provide a rating or explicit insufficient-evidence outcome.
* [ ] Disclose missing information, source conflicts, and limitations.

### 9.2 Ingestion and Source Handling

* [ ] Test text-based and scanned PDFs.
* [ ] Verify the 300-page, under-five-minute text-based ingestion target under documented conditions.
* [ ] Measure scanned-PDF OCR timing and extraction quality separately.
* [ ] Demonstrate missing-source and conflicting-source handling.
* [ ] Demonstrate duplicate-upload idempotency.

### 9.3 Evaluation

* [ ] Commit the 40-question benchmark and baseline.
* [ ] Measure retrieval metrics and answer-quality metrics.
* [ ] Report results by question category.
* [ ] Complete all three mandatory A/B experiments.
* [ ] Record latency, cost, results, and engineering verdicts.
* [ ] Define acceptance thresholds before final release evaluation.
* [ ] Document unresolved failures and limitations.

### 9.4 Reliability and Security

* [ ] Demonstrate checkpoint-based worker recovery.
* [ ] Test Redis interruptions during ingestion and queries.
* [ ] Patch and test the two worst Redis failure paths.
* [ ] Test empty retrieval, malformed documents, and resource limits.
* [ ] Run the three-document prompt-injection test suite.
* [ ] Document the security tests and residual risks.
* [ ] Verify collection-level retrieval isolation with automated regression tests.

### 9.5 Deployment

* [ ] Deploy the API, worker, PostgreSQL, Redis, and Caddy.
* [ ] Verify health checks and the deployed end-to-end workflow.
* [ ] Document setup and recovery procedures.

### 9.6 Repository Evidence

The repository must contain:

* [ ] README and setup/deployment instructions
* [ ] Architecture and component documentation
* [ ] Unit and integration tests
* [ ] Evaluation benchmark, baseline, and results
* [ ] Versioned benchmark data
* [ ] ADRs recording measured architecture experiments
* [ ] Prompt-injection defense security note
* [ ] Failure-injection results and postmortem
* [ ] Evidence of collection-level retrieval isolation
* [ ] Documented limitations and unresolved issues

Passing individual tests or generating one convincing report does not independently establish MVP completion.

---

## 10. Out of Scope

The following capabilities are explicitly excluded from the MVP.

### 10.1 Investment and Trading

* Autonomous trade execution
* Broker integration
* Portfolio allocation
* Personalized financial planning
* Determining how much a user should invest
* Autonomous buy/sell execution
* Finding and ranking new companies independently of the user's research target

The system may generate a research rating under its documented methodology, but it does not execute or manage investment decisions.

### 10.2 Research Expansion

* Broad macroeconomic research as a separate research capability
* Unrestricted autonomous research across arbitrary topics
* Advanced multi-company research in a single task
* Continuous or real-time market monitoring
* Scheduled recurring reports
* Complex long-term conversational memory
* Custom report templates

Company and industry context required for the target company's analysis remains in scope.

### 10.3 Platform Expansion

* Full authentication and multi-user support
* Role-based access control
* Multi-tenant authorization
* Mobile applications
* Production-scale distributed infrastructure
* Autoscaling and high availability
* Kafka or Celery-based infrastructure
* Fine-tuning custom models for the MVP
* File formats beyond PDF

These exclusions may be reconsidered after the MVP demonstrates measurable research quality and reliability.

---

## 11. Scope Constraints and Assumptions

### 11.1 Resource Constraints

The project is designed as a single-user MVP with limited compute, storage, and API budgets.

Accordingly:

* Only one research job runs at a time.
* Additional work is queued with a configurable limit.
* Research runtime and external API usage are bounded.
* The system may disclose incomplete coverage when limits are reached.
* The architecture should avoid unnecessary infrastructure complexity.

### 11.2 Data Availability

The project assumes that relevant public information and historical market data can be obtained from available sources.

It does not guarantee complete five-year coverage for every company, every financial metric, or every market-data source.

Unavailable or unreliable data must be disclosed.

### 11.3 Quality Expectations

A comprehensive report is the goal, but completeness must not be confused with correctness.

The system must prioritize:

1. Evidence-backed claims
2. Traceable calculations
3. Explicit uncertainty
4. Disclosure of conflicts and missing information
5. Reproducible evaluation
6. Reliable failure handling

A report may contain explicitly incomplete sections when supporting evidence is unavailable.

### 11.4 Implementation Flexibility

The scope defines observable system behavior and completion requirements. Specific implementation technologies and architecture choices are to be documented separately.

Technology choices, component boundaries, interfaces, and orchestration details belong in the architecture and contract documents. Choices that require empirical validation must be evaluated through documented experiments and ADRs.

### 11.5 Deferred Decisions

The following values must be finalized before implementation or final release evaluation:

* Confirmation of the initial 20 MB PDF file-size limit
* Maximum queue size
* Maximum research runtime
* Maximum research steps
* Retry limits
* External API-call limits
* Numerical retrieval and answer-quality acceptance thresholds
* Rating methodology and its explicit criteria
* Detailed valuation methodology and assumptions
* Reproducible ingestion test environment

These decisions must be documented rather than silently assumed.

---

## 12. Scope Completion Definition

This scope is complete when the MVP can demonstrate a deployed, end-to-end company research workflow with:

* Structured and evidence-backed company reports
* Financial analysis and traceable calculations
* Valuation scenarios and a documented rating methodology
* Source conflict and missing-data disclosure
* Background execution, progress reporting, and recovery
* Prompt-injection defenses and failure-injection tests
* Collection-level retrieval isolation
* Reproducible benchmark results and controlled A/B experiments
* Documented deployment, architecture decisions, limitations, and postmortem evidence

The project's success is determined by measured behavior and engineering evidence, not by the number of features or the appearance of the final report.
