# Workflows — Equity / Business Research Agent

## 1. Purpose

This document defines the primary user and system workflows for the Equity / Business Research Agent.

The system helps an individual investor research one Indian listed company at a time. It gathers and analyzes public information, evaluates financial performance and valuation, tracks evidence and uncertainty, and generates a structured research report.

The workflows define **what happens and in what order**, not the implementation architecture. Component responsibilities, interfaces, contracts, and technology choices will be documented separately.

## 2. Actors

| Actor                        | Responsibility                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------------ |
| Investor                     | Selects a company, optionally supplies an annual report, starts research, and reviews the result |
| Research System              | Coordinates research, evidence collection, analysis, validation, and report generation           |
| External Information Sources | Provide public company, financial, industry, competitor, and market information                  |
| Evaluation System            | Measures retrieval, answer quality, financial correctness, security, latency, and cost           |
| Operator / Developer         | Investigates failures, reviews evaluations, manages configuration, and improves the system       |

## 3. Primary End-to-End Workflow

### WF-01: Research a Listed Company

**Goal:** Generate a structured, evidence-backed research report for one Indian listed company.

**Trigger:** The investor submits a company name or ticker and starts a research task.

**Preconditions:**

* The company is within the supported Indian listed-company scope.
* Required configuration and external services are available.
* The task is within configured workload and resource limits.

**Workflow:**

1. Investor submits the company name or ticker.
2. System validates the input.
3. System resolves the company identity.
4. If the company identity is ambiguous, the system asks the investor to select or confirm the intended company.
5. System establishes the research as-of date.
6. System creates a research task and returns a unique task identifier.
7. System identifies the information required to complete the report.
8. System gathers relevant company, financial, industry, competitor, governance, risk, and market evidence.
9. System processes any user-supplied annual report.
10. System organizes retrieved information and links evidence to its sources.
11. System checks which information requirements are satisfied, missing, contradictory, or insufficiently supported.
12. System performs bounded follow-up research where necessary and permitted by configured limits.
13. System analyzes the business model, management, industry, financial performance, competitors, and risks.
14. System calculates financial metrics using explicit inputs, formulas, units, and periods.
15. System develops valuation assumptions and bull, base, and bear scenarios.
16. System evaluates the investment thesis and antithesis.
17. System determines whether the available evidence supports a buy, hold, or sell rating under the documented methodology.
18. If evidence is insufficient for a defensible rating, system reports an insufficient-evidence outcome with reasons.
19. System validates factual claims, calculations, citations, uncertainty disclosures, and required report sections.
20. System generates the structured research report.
21. System persists the report and relevant evidence mappings, assumptions, execution metadata, and final task status.
22. Investor retrieves and reviews the report.

**Success outcome:**

* The report is available to the investor.
* Material claims can be traced to supporting evidence.
* Calculations and valuation assumptions are inspectable.
* Missing information, conflicts, uncertainty, and limitations are disclosed.
* The task status accurately reflects the outcome.

**Failure outcome:**

* The task is marked failed, incomplete, or limited as appropriate.
* The system records the failure reason.
* Completed work is preserved where possible.
* The system does not present an incomplete report as a successfully completed report.

## 4. Company Input and Identity Resolution

### WF-02: Validate and Resolve Company Identity

**Goal:** Ensure that the research task targets the intended company.

**Workflow:**

1. Investor submits a company name or ticker.
2. System checks whether the input is present and valid.
3. System searches for a matching Indian listed company.
4. System checks whether the result is sufficiently unambiguous.
5. If exactly one suitable company is identified, system records the resolved identity.
6. If multiple plausible companies match, system asks the investor to clarify.
7. If no supported company can be identified, system explains the problem and does not start full research.
8. System records the resolved company identifier and as-of date with the task.

**Success outcome:** The research task has an unambiguous company identity.

**Failure and edge cases:**

* Empty company input
* Invalid ticker
* Company name shared by multiple entities
* Delisted or unsupported company
* Missing or conflicting identity information

The system must not silently choose among materially ambiguous companies.

## 5. Annual Report Upload and Ingestion

### WF-03: Upload and Process an Annual Report

**Goal:** Make a user-supplied annual report available as traceable research evidence.

**Preconditions:**

* The upload is a supported PDF.
* The file satisfies configured size and page limits.
* The file is associated with the intended research task or evidence collection.

**Workflow:**

1. Investor uploads a PDF.
2. System validates the file type, size, and page count.
3. System rejects files that exceed configured limits or are not supported.
4. System checks whether the file is malformed, corrupt, empty, or unreadable.
5. System creates an ingestion record and reports its status.
6. System extracts text and document structure.
7. If the PDF is scanned, system attempts OCR when supported.
8. System preserves useful structural information, including page locations and relevant table content where possible.
9. System identifies extraction failures or low-quality output.
10. System divides extracted content into retrievable units and attaches source metadata.
11. System records document identity and content hash.
12. System checks whether the same content has already been processed.
13. If identical content has already been indexed, system avoids duplicate ingestion and reuses the existing result where valid.
14. If processing succeeds, system marks the document indexed and makes it available for retrieval.
15. If processing fails, system records the failure and quarantines malformed or unsafe documents as appropriate.

**Success outcome:**

* The report is available for retrieval.
* Retrieved evidence can be traced to its source document and location.
* Duplicate uploads do not create duplicate indexed content.
* Extraction limitations are visible.

**Failure and edge cases:**

* Unsupported file type
* File size or page limit exceeded
* Corrupt or encrypted PDF that cannot be processed
* Empty extracted text
* OCR failure
* Poor extraction of tables or financial figures
* Worker interruption during processing
* Duplicate upload
* Storage or queue dependency unavailable

A failed ingestion must not be reported as successfully indexed.

## 6. Evidence Collection and Retrieval

### WF-04: Collect Evidence for Research Requirements

**Goal:** Obtain sufficient, relevant evidence to support the report's required sections.

**Workflow:**

1. System establishes the information requirements for the company research task.
2. System identifies which requirements need evidence from official filings, annual reports, company sources, financial data, industry research, competitors, or market history.
3. System retrieves candidate evidence from the permitted sources.
4. System associates each candidate with source metadata and a retrievable location.
5. System evaluates whether retrieved evidence is relevant to the specific information requirement.
6. System identifies missing requirements and weak evidence coverage.
7. System identifies whether additional retrieval or follow-up research is justified.
8. System continues research within configured step, runtime, retry, and API-call limits.
9. System records which requirements are satisfied and which remain incomplete.
10. System passes the evidence and remaining gaps to the analysis workflow.

**Success outcome:** The research process has a traceable set of relevant evidence and a visible record of remaining gaps.

**Failure and edge cases:**

* No relevant evidence found
* Search returns irrelevant or duplicate sources
* Source is unavailable
* Required source is inaccessible
* Evidence covers the wrong reporting period
* Retrieval results omit a known relevant source
* External service fails or reaches its limit

The system must distinguish between a fact not found and a fact that does not exist.

### WF-05: Verify Evidence and Preserve Provenance

**Goal:** Ensure material claims in the report can be traced to evidence.

**Workflow:**

1. System receives candidate evidence.
2. System records the source identity and relevant document location or source reference.
3. System associates evidence with the research requirement and relevant claims.
4. System checks whether the evidence directly supports the intended claim.
5. System identifies weak, incomplete, indirect, or contradictory support.
6. System retains source and evidence references through analysis and report generation.
7. System validates that material report claims have appropriate supporting evidence.
8. System discloses unsupported or unresolved claims as uncertain, incomplete, or omitted as appropriate.

**Success outcome:** A reviewer can move from a material report claim to its supporting evidence and source location.

**Failure and edge cases:**

* Citation points to a relevant document but not to supporting evidence
* Source reference cannot be resolved
* Evidence is stale or relates to a different period
* Claim is stronger than the evidence supports
* Multiple sources disagree

The system must not invent citations or imply that a source supports a claim when it does not.

## 7. Missing Information and Conflicting Sources

### WF-06: Detect and Handle Missing Information

**Goal:** Avoid presenting an incomplete evidence base as complete research.

**Workflow:**

1. System compares available evidence against required report sections and information requirements.
2. System identifies missing, incomplete, or weakly supported information.
3. System determines whether bounded follow-up research may resolve the gap.
4. If additional research is justified and limits permit, system searches for additional evidence.
5. System reassesses whether the requirement is satisfied.
6. If the information remains unavailable, system records the gap.
7. System explains how the missing information affects the analysis or confidence of the conclusion.
8. System continues with the supported portions of the report where possible.

**Success outcome:** The report distinguishes supported conclusions from gaps and uncertainty.

**Failure and edge cases:**

* Important financial period unavailable
* Missing competitor data
* Insufficient evidence for a valuation assumption
* Incomplete annual report extraction
* External sources unavailable
* Research limits reached before the gap is resolved

The system should continue with available evidence when possible, but must not invent missing facts.

### WF-07: Resolve Conflicting Evidence

**Goal:** Handle material disagreements between sources without silently selecting a convenient value.

**Workflow:**

1. System detects conflicting values or statements.
2. System identifies each source and its publication or reporting period.
3. System compares units, currencies, definitions, accounting periods, and measurement methods.
4. System checks source authority and whether the values refer to the same underlying concept.
5. System determines whether the apparent conflict can be explained by period, unit, or definition differences.
6. If the conflict is resolved, system records the reason and uses the appropriate value with traceable support.
7. If the conflict remains unresolved, system discloses it and explains its significance.
8. System avoids using an unresolved value as a certain fact in calculations or valuation.

**Success outcome:** Material conflicts are explained, resolved with evidence, or explicitly disclosed.

**Failure and edge cases:**

* Two sources report different values for the same period
* Consolidated versus standalone financials
* Different fiscal-year definitions
* Different units or currencies
* Restated historical financials
* Conflicting management statements and regulatory filings

Where appropriate, the system should prefer authoritative evidence, but it must still explain material unresolved conflicts.

## 8. Financial Analysis and Valuation

### WF-08: Analyze Financial Performance

**Goal:** Produce traceable analysis of the company's historical financial performance.

**Workflow:**

1. System gathers available financial statements and related source evidence.
2. System identifies the periods and financial measures available.
3. System checks whether the periods and units are comparable.
4. System calculates relevant financial metrics using explicit formulas and inputs.
5. System validates calculations and handles missing values or invalid denominators.
6. System examines historical trends, growth, profitability, leverage, cash generation, and other relevant measures.
7. System links material findings to source figures and calculation details.
8. System identifies missing periods, inconsistencies, and limitations.
9. System produces a financial analysis with appropriate qualifications.

**Success outcome:** Financial trends are understandable, reproducible, and traceable to source figures.

**Failure and edge cases:**

* Missing historical periods
* Inconsistent financial units
* Invalid or unavailable denominator
* Source figure conflicts
* Incorrect table extraction
* Incomparable standalone and consolidated data

The system must not silently treat missing values as zero or compare incompatible periods as if they were equivalent.

### WF-09: Estimate Valuation and Build Scenarios

**Goal:** Produce an inspectable valuation range and explain the assumptions that influence it.

**Workflow:**

1. System collects relevant financial, business, industry, and market evidence.
2. System identifies which valuation inputs are available and which are missing.
3. System selects valuation methods supported by the documented methodology and available evidence.
4. System records the assumptions and their evidence or rationale.
5. System performs calculations and validates the arithmetic.
6. System estimates a valuation range.
7. System constructs bull, base, and bear scenarios.
8. System performs sensitivity analysis on material assumptions.
9. System distinguishes sourced facts, calculated values, and analyst-style estimates.
10. System evaluates whether the range is sufficiently supported for decision-grade use.
11. If evidence is weak, system labels the estimate as speculative and high uncertainty, or reports that a decision-grade valuation cannot be supported.
12. System records limitations and the assumptions that could materially change the result.

**Success outcome:** The valuation range and scenarios are traceable to inputs, formulas, and assumptions.

**Failure and edge cases:**

* Missing valuation inputs
* Unreliable source figures
* Sensitivity to a small change in assumptions
* Contradictory financial evidence
* Unsupported growth assumptions
* Calculation or unit errors

The system should attempt a valuation range, but it must clearly label an unsupported range as not decision-grade rather than presenting it as reliable.

### WF-10: Form Thesis, Antithesis, and Rating

**Goal:** Produce a balanced investment analysis using the documented rating methodology.

**Workflow:**

1. System summarizes the strongest evidence supporting the investment thesis.
2. System identifies counterevidence and the strongest antithesis.
3. System identifies business, financial, governance, industry, and valuation risks.
4. System compares the thesis and antithesis against the available evidence.
5. System evaluates the valuation range and scenarios under the documented methodology.
6. System checks whether the methodology's evidence requirements are satisfied.
7. If sufficient evidence exists, system produces a buy, hold, or sell rating according to the methodology.
8. If evidence is insufficient, system returns an insufficient-evidence outcome with the reasons.
9. System identifies the conditions or new evidence that could change the rating.
10. System ensures the report does not present the rating as a personalized instruction to trade or allocate capital.

**Success outcome:** The rating is reasoned, traceable, appropriately qualified, and consistent with the documented methodology.

**Failure and edge cases:**

* Evidence supports neither a clear positive nor negative conclusion
* Valuation is highly sensitive to uncertain assumptions
* Important risks are insufficiently researched
* Contradictory evidence remains unresolved
* Rating methodology requirements are not met

## 9. Report Generation and Validation

### WF-11: Generate and Validate the Research Report

**Goal:** Produce a complete report with clear structure, evidence, calculations, uncertainty, and limitations.

**Expected report sections:**

1. Executive summary
2. Company history and business model
3. Management and governance
4. Industry analysis
5. Five-year financial and fundamental analysis, where evidence is available
6. Competitor analysis
7. Risks
8. Valuation range, assumptions, and sensitivities
9. Bull, base, and bear scenarios
10. Historical share-price trends and technical indicators, where data is available
11. Investment thesis and antithesis
12. Buy, hold, sell, or insufficient-evidence outcome
13. Missing information, conflicts, and limitations
14. Sources and evidence references

**Workflow:**

1. System assembles the findings from completed research stages.
2. System checks that all required sections are present or explicitly marked unavailable/not supported.
3. System checks material factual claims against their evidence.
4. System validates citation support.
5. System validates financial calculations and displayed units/periods.
6. System checks that assumptions, estimates, scenarios, and sourced facts are distinguishable.
7. System checks that missing information, conflicts, uncertainty, and limitations are disclosed.
8. System checks for unsupported claims and inappropriate certainty.
9. If a correctable issue is found, system performs bounded correction and revalidation.
10. If a critical issue remains unresolved, system does not mark the report as successfully completed.
11. System persists the validated report and relevant metadata.
12. System updates the task status and makes the result available.

**Success outcome:** A structured, validated report is available with traceable evidence and transparent limitations.

**Failure and edge cases:**

* Required section has no supporting evidence
* Citation validation fails
* Financial calculation validation fails
* Report generation is interrupted
* Correction attempts are exhausted
* Output validation fails

The system must not manufacture missing information merely to fill a required section.

## 10. Background Execution and Task Status

### WF-12: Track Research Progress

**Goal:** Let the investor understand whether a research task is queued, running, completed, failed, or incomplete.

**Workflow:**

1. System accepts a valid research request.
2. System creates a task identifier and records the initial status.
3. System places the task into the execution process.
4. System updates status as the task advances through meaningful stages.
5. System exposes the current stage and available progress information.
6. If the task completes, system marks it completed and makes the report available.
7. If the task fails, system records the failure reason and final status.
8. If the task reaches a configured limit, system marks it incomplete or limited and preserves completed work where possible.

Progress percentages should be shown only if they can be measured meaningfully. Otherwise, report the current stage.

### WF-13: Queue, Cancel, and Recover Tasks

**Goal:** Handle queued or interrupted work without misreporting task outcomes.

**Workflow:**

1. System accepts a task if capacity and configured limits permit.
2. If another task is active, the new task is queued within the configured queue limit.
3. If the queue is full, the system rejects the new task clearly.
4. If cancellation is requested, system determines whether the task is queued or running.
5. A queued task is cancelled without execution.
6. A running task is stopped at a safe point where possible.
7. Completed work is preserved when possible and the final status reflects cancellation.
8. If a worker crashes, the system identifies the interrupted task and checks its last valid checkpoint.
9. The task resumes from a valid checkpoint or transitions to an explicit failed state.
10. Retries follow configured bounds and avoid duplicate side effects.
11. The system records recovery outcome and relevant failure metadata.

**Success outcome:** Tasks have truthful states, bounded retries, and consistent recovery behavior.

**Failure and edge cases:**

* Worker crashes mid-stage
* Redis becomes unavailable
* Queue capacity is exceeded
* Cancellation arrives during a non-interruptible operation
* Checkpoint is invalid or unavailable
* Retry budget is exhausted

## 11. Prompt-Injection and Untrusted Documents

### WF-14: Process Potentially Malicious Document Content

**Goal:** Prevent instructions embedded in retrieved documents from overriding the system's intended task or security rules.

**Workflow:**

1. System accepts a document as an untrusted information source.
2. System validates the file and processes its content under the document-ingestion rules.
3. Retrieved content is treated as data to analyze, not as instructions that control system behavior.
4. System maintains the separation between trusted task instructions and untrusted document content.
5. System checks generated actions and outputs against permitted behavior and validation rules.
6. System records relevant security outcomes without unnecessarily logging sensitive content.
7. During evaluation, the system is tested against the defined poisoned documents.
8. The unprotected baseline is used to demonstrate the attack path.
9. The defended configuration is tested against the same defined cases.
10. Failures are investigated, defenses are improved, and regression tests are rerun.

**Success outcome:** The defined attacks do not cause the defended system to follow malicious document instructions or violate its permitted behavior.

**Failure and edge cases:**

* Document asks the system to ignore prior instructions
* Document attempts to extract secrets or unrelated data
* Document attempts to influence a rating without supporting evidence
* Document contains malicious instructions disguised as financial content
* Retrieved content attempts to trigger unauthorized tool use

Passing the defined tests does not establish universal prompt-injection resistance. Residual risks and untested attack classes must be documented.

## 12. Evaluation and Improvement

### WF-15: Run the Evaluation Benchmark

**Goal:** Measure research quality and detect regressions using a fixed, versioned benchmark.

**Workflow:**

1. Select the benchmark dataset and evaluation configuration versions.
2. Confirm that scoring rules and release thresholds were defined before the evaluation.
3. Run the benchmark questions.
4. Record per-question outputs and scores.
5. Calculate overall and category-level results.
6. Report raw counts and percentages.
7. Calculate applicable retrieval metrics, including Precision@k, Recall@k, MRR, and relevant-source top-three rate.
8. Evaluate faithfulness, citation support, factual correctness, fallback behavior, and valuation/rating quality.
9. Run required calculation, security, isolation, recovery, and dependency-failure tests.
10. Record latency, cost, and ingestion performance under documented conditions.
11. Compare results with the committed baseline.
12. Investigate critical failures and important regressions.
13. Record the evaluation verdict and known limitations.

**Success outcome:** Results are reproducible enough to compare configurations and identify failures. The report must not imply statistical certainty from the 40-question benchmark.

### WF-16: Run Controlled A/B Experiments

**Goal:** Determine whether retrieval and query-processing changes provide a worthwhile engineering trade-off.

Required experiments:

1. Hybrid retrieval versus vector-only retrieval
2. Reranking enabled versus disabled
3. Query rewriting enabled versus disabled

**Workflow:**

1. Select one experiment and define the configurations being compared.
2. Use the same benchmark and comparable test conditions.
3. Record configuration versions and relevant settings.
4. Run both variants.
5. Compare retrieval and answer quality.
6. Compare latency and cost.
7. Record failures, variability, and limitations where applicable.
8. Decide whether the change is justified.
9. Update the relevant Architecture Decision Record (ADR).
10. Preserve results so the decision can be reviewed later.

**Success outcome:** Each experiment has measured results, an engineering verdict, and an updated ADR. A negative result is acceptable if the experiment is valid and its conclusion is documented.

## 13. Cross-Collection Isolation

### WF-17: Verify Collection Boundaries

**Goal:** Ensure retrieval and citations remain within the collection selected for a task.

**Workflow:**

1. Prepare at least two separate evidence collections.
2. Add distinguishable test evidence to each collection.
3. Submit a query scoped to the first collection.
4. Inspect retrieved evidence and report citations.
5. Confirm that no evidence from the second collection appears.
6. Repeat with the collections reversed.
7. Run adversarial cross-collection test cases.
8. Record every pass and failure.
9. If leakage occurs, block release, fix the defect, and rerun the regression suite.

**Success outcome:** Every defined isolation test passes.

## 14. Deletion and Data Handling

### WF-18: Delete Research Data

**Goal:** Honor an explicit deletion request for retained research data within the supported system boundary.

**Workflow:**

1. Receive a deletion request identifying the relevant task, document, or collection.
2. Validate the requested target.
3. Identify associated persisted data and references within the supported deletion boundary.
4. Delete the requested data and applicable derived artifacts.
5. Record deletion completion without unnecessarily retaining deleted content in logs.
6. Report success or an explicit failure if deletion cannot be completed.
7. Verify that deleted data is no longer available through normal retrieval paths.

**Success outcome:** The requested data is deleted from the supported system boundary, and the result is reported truthfully.

**Failure and edge cases:**

* Target cannot be identified unambiguously
* A dependency is unavailable during deletion
* Some derived artifacts cannot be removed immediately
* Deletion fails partway through

Any limitations in deletion behavior must be documented. The system must not claim complete deletion if only part of the data was removed.

## 15. Cross-Workflow Invariants

The following rules apply across all workflows:

1. **Evidence integrity:** Material claims must not be presented as verified unless supporting evidence is available.
2. **Provenance:** Evidence references must remain connected to their source and location.
3. **Uncertainty disclosure:** Missing data, conflicts, weak evidence, and unsupported conclusions must be visible.
4. **Financial correctness:** Deterministic calculations must use explicit inputs, units, periods, formulas, and rounding rules.
5. **Bounded execution:** Research steps, retries, runtime, and external calls must respect configured limits.
6. **Truthful status:** A task that fails, is cancelled, or stops at a limit must not be marked completed.
7. **Safe failure:** Completed work should be preserved where possible, without corrupting task state.
8. **Isolation:** Evidence from another collection must not appear in retrieval or citations.
9. **Untrusted content:** Documents are evidence sources, not trusted system instructions.
10. **Reproducibility:** Evaluation runs and major engineering decisions must retain their relevant configurations and results.
11. **No invented evidence:** The system must not fabricate source material, citations, historical values, or missing facts.
12. **Scope discipline:** Each research task focuses on one supported Indian listed company. Portfolio allocation, personalized financial planning, and autonomous trade execution remain outside the workflow.

## 16. Workflow Completion Criteria

The workflow design is ready to proceed to responsibility and component-boundary design when:

* Primary and failure workflows are documented.
* Inputs, outputs, triggers, and major decision points are clear.
* Missing-information and conflict-handling paths are defined.
* Evidence traceability and report validation are explicit.
* Background execution, limits, cancellation, and recovery are addressed.
* Security, collection-isolation, and deletion workflows are documented.
* Evaluation and experiment workflows are defined.
* Remaining implementation choices are left for component boundaries, contracts, ADRs, and later implementation planning.
