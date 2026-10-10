# Responsibilities

## 1. Purpose

This document defines the responsibilities of the logical actors and system capabilities involved in the Equity / Business Research Agent.

It establishes:

* Who owns each major activity.
* Which decisions are deterministic and which require AI-assisted reasoning.
* Where responsibilities begin and end.
* Which outputs each responsibility must produce.
* How failures, uncertainty, and incomplete work are handled.

This document defines **responsibilities, not implementation architecture**. Technology choices, deployment topology, component boundaries, and communication mechanisms will be documented separately.

---

## 2. Actors and Responsibility Owners

### 2.1 User

The user is the individual investor requesting research on a publicly listed Indian company.

Responsibilities:

* Provide the company name or ticker.
* Resolve ambiguity when the requested company cannot be identified confidently.
* Optionally provide an annual report PDF.
* Review the generated report, evidence, assumptions, risks, and limitations.
* Make their own investment decisions.

The user is not responsible for manually orchestrating research stages or validating every intermediate system operation.

### 2.2 Research Orchestrator

The Research Orchestrator owns the lifecycle of a research task.

Responsibilities:

* Accept a valid research request.
* Create and track a uniquely identifiable research task.
* Coordinate the required research activities.
* Maintain the task's current state and completed work.
* Enforce research-step, retry, API-call, and runtime limits.
* Determine which activities can proceed and which depend on earlier results.
* Trigger bounded follow-up research when evidence is insufficient.
* Stop when completion criteria are met or further research is no longer permitted.
* Distinguish completed, incomplete, failed, cancelled, and limited outcomes.
* Ensure the final status accurately reflects the work completed.

The orchestrator coordinates work; it does not independently establish the truth of financial or business claims.

### 2.3 Company Identity Resolver

The Company Identity Resolver determines which listed company the user intends to research.

Responsibilities:

* Interpret the supplied company name or ticker.
* Identify the corresponding Indian listed company.
* Detect ambiguous, incomplete, or conflicting identifiers.
* Request clarification when the identity cannot be established reliably.
* Preserve the confirmed company identity throughout the task.
* Prevent evidence from an incorrectly matched company from contaminating the report.

Output:

* Confirmed company identity and identifier.
* Relevant listing information.
* Resolution status.
* Any ambiguity requiring user clarification.

### 2.4 Research Planner

The Research Planner determines what information must be collected to produce the requested report.

Responsibilities:

* Translate the research objective into bounded research tasks.
* Identify required topics, such as business model, management, industry, financials, competitors, risks, and valuation.
* Define the evidence needed to support each topic.
* Identify required financial periods and relevant comparison data.
* Track completed, pending, blocked, and unsupported research tasks.
* Identify missing information and dependencies between research tasks.
* Prioritize follow-up work based on importance and evidence gaps.

The Research Planner must not expand the task into unrestricted research or unrelated company discovery.

Output:

* Research plan.
* Information requirements.
* Evidence requirements.
* Task dependencies.
* Research completion and gap status.

### 2.5 Source Discovery and Collection

This responsibility owns the discovery and collection of relevant source material.

Responsibilities:

* Retrieve information from available public sources.
* Prefer authoritative sources for material company and financial facts.
* Collect official company disclosures, regulatory filings, annual reports, historical financial information, share-price data, and relevant industry or competitor information.
* Record the source identity, publication date when available, reporting period, and retrieval metadata.
* Preserve the distinction between source-reported facts, third-party claims, estimates, and system-generated calculations.
* Report unavailable, inaccessible, stale, or incomplete sources.
* Avoid treating search-result snippets as sufficient evidence when the underlying source is needed.

Output:

* Source records.
* Retrieved documents or data.
* Source metadata.
* Collection status and failure details.
* Known source limitations.

### 2.6 Document Ingestion and Normalization

This responsibility prepares uploaded and retrieved documents for downstream analysis.

Responsibilities:

* Validate uploaded PDF files against configured file-size and page-count limits.
* Distinguish text-based PDFs from scanned PDFs.
* Extract text and relevant document structure.
* Apply OCR when required and available.
* Preserve page numbers and other location metadata where possible.
* Normalize extracted content without changing its meaning.
* Preserve tables, financial values, units, dates, and reporting periods as accurately as possible.
* Identify extraction failures, malformed documents, and low-confidence OCR results.
* Prevent duplicate processing of the same document.
* Quarantine malformed or unsafe documents rather than treating them as successfully processed.
* Associate extracted content with its source document.

Output:

* Validated document records.
* Extracted and normalized content.
* Page and location metadata.
* Extraction-quality indicators.
* Ingestion status and failure details.

### 2.7 Evidence Retrieval

Evidence Retrieval finds the source material relevant to a particular research question or claim.

Responsibilities:

* Retrieve relevant evidence from the permitted research collection.
* Use the research question and available context to identify useful passages or records.
* Preserve document, page, period, and source identifiers.
* Return evidence relevant to the requested claim rather than merely topically similar text.
* Identify when retrieval returns no useful evidence.
* Support evaluation of retrieval relevance and ranking quality.
* Respect collection boundaries and prevent cross-collection evidence access.

Output:

* Retrieved evidence items.
* Source and document references.
* Relevance information where available.
* Retrieval status.
* Evidence gaps.

Evidence Retrieval is responsible for finding candidate evidence, not deciding that every retrieved passage is sufficient to support a claim.

### 2.8 Evidence and Provenance Manager

This responsibility maintains the relationship between report claims and their supporting evidence.

Responsibilities:

* Assign stable identifiers to source documents and evidence items.
* Preserve the mapping between source documents, extracted content, and evidence locations.
* Associate claims with the evidence used to support them.
* Record whether a claim is directly sourced, calculated, inferred, estimated, or uncertain.
* Preserve calculation inputs and source references.
* Detect claims that lack adequate supporting evidence.
* Identify citations that do not support the associated claim.
* Retain enough metadata to reproduce or audit material findings.
* Preserve conflicting evidence instead of silently discarding it.

Output:

* Evidence records.
* Claim-to-evidence mappings.
* Citation metadata.
* Provenance information.
* Unsupported-claim and citation-validation findings.

### 2.9 Financial Data Analyst

The Financial Data Analyst extracts, reconciles, and interprets company financial information.

Responsibilities:

* Collect relevant income statement, balance sheet, and cash flow data.
* Organize financial data by reporting period and unit.
* Analyze historical financial performance, targeting five years of coverage where data is available.
* Calculate relevant growth rates, margins, returns, leverage, liquidity, and other fundamental metrics.
* Identify material changes in financial performance.
* Distinguish reported figures from calculated metrics and estimates.
* Check calculations for missing values, inconsistent units, incompatible periods, and division-by-zero cases.
* Preserve formulas, inputs, units, periods, and rounding rules.
* Identify financial inconsistencies that require further investigation.
* Avoid presenting unavailable or unreliable figures as established facts.

**Responsibility boundary:** Numerical calculations must follow explicit, testable calculation rules. AI-generated reasoning may interpret results, but it must not replace deterministic arithmetic for calculations that can be performed directly.

Output:

* Normalized financial data.
* Calculated financial metrics.
* Period-over-period comparisons.
* Financial findings.
* Calculation provenance.
* Data-quality warnings and missing-data records.

### 2.10 Business and Industry Analyst

The Business and Industry Analyst examines how the company operates and competes.

Responsibilities:

* Explain the company's business model, products, services, and revenue drivers.
* Analyze relevant industry structure and business conditions.
* Identify material competitive advantages and disadvantages.
* Examine relevant competitors and explain the basis for comparison.
* Consider differences in company scale, business mix, reporting periods, and data availability.
* Analyze management disclosures and governance-related information.
* Identify material business risks and dependencies.
* Distinguish reported facts from analytical interpretation.
* Support material findings with relevant evidence.

Output:

* Business model analysis.
* Industry analysis.
* Competitor comparisons.
* Management and governance findings.
* Business risks and opportunities.
* Supporting evidence and limitations.

### 2.11 Risk Analyst

The Risk Analyst identifies and evaluates material risks that could affect the company's business or valuation.

Responsibilities:

* Identify financial, operational, competitive, governance, regulatory, and industry risks where relevant.
* Assess the evidence supporting each material risk.
* Explain potential consequences for financial performance and valuation.
* Distinguish observed risks from hypothetical scenarios.
* Identify mitigating factors and counterevidence.
* Highlight information gaps that prevent reliable risk assessment.
* Ensure material risks are not omitted merely because they conflict with a positive investment thesis.

Output:

* Risk register.
* Evidence supporting each risk.
* Potential impact and relevant uncertainty.
* Mitigating factors.
* Unresolved risk questions.

### 2.12 Valuation Analyst

The Valuation Analyst estimates a defensible valuation range using an explicit methodology and documented assumptions.

Responsibilities:

* Determine which valuation methods are suitable given the available evidence.
* Collect the inputs required for the selected methods.
* Document assumptions, reference dates, units, and calculation steps.
* Calculate valuation outputs using deterministic arithmetic.
* Develop bull, base, and bear scenarios where supported.
* Perform sensitivity analysis on material assumptions.
* Explain which variables have the greatest effect on estimated value.
* Compare estimated value with an appropriately dated market-price reference when available.
* Identify when missing or unreliable data makes a valuation weak or speculative.
* Distinguish observed market data from assumptions and estimates.
* Avoid false precision and unsupported valuation claims.

Output:

* Valuation method and rationale.
* Documented assumptions and inputs.
* Calculated valuation range.
* Scenario analysis.
* Sensitivity analysis.
* Comparison with the dated market-price reference.
* Confidence assessment and limitations.

### 2.13 Thesis and Antithesis Analyst

This responsibility develops and tests the competing arguments about the company's investment merits.

Responsibilities:

* Construct the positive investment thesis from available evidence.
* Construct the negative thesis or antithesis using material risks and counterevidence.
* Identify assumptions on which each argument depends.
* Evaluate whether the evidence supports, weakens, or contradicts each argument.
* Identify conditions that could change the investment view.
* Distinguish factual observations from forward-looking judgments.
* Avoid treating a single favorable metric as sufficient evidence for an overall conclusion.
* Highlight unresolved questions and material uncertainty.

Output:

* Bull case.
* Bear case.
* Key supporting and opposing evidence.
* Important assumptions.
* Conditions that could change the view.
* Unresolved questions.

### 2.14 Investment Rating Evaluator

The Investment Rating Evaluator determines whether the available evidence supports the project's defined buy/hold/sell rating methodology.

Responsibilities:

* Apply the documented rating methodology consistently.
* Use the valuation result, evidence quality, business fundamentals, risks, and defined rating criteria.
* Verify that required evidence is available before assigning a rating.
* Identify when material assumptions or data limitations undermine the conclusion.
* Record the rationale, relevant evidence, confidence, and conditions that could change the rating.
* Return an explicit insufficient-evidence outcome when the methodology cannot be applied responsibly.
* Avoid presenting a rating as a personalized investment instruction or a guarantee of future performance.

Output:

* Rating or insufficient-evidence outcome.
* Rationale tied to the documented methodology.
* Supporting and opposing evidence.
* Confidence and limitations.
* Conditions that could change the rating.

The rating methodology and its thresholds must be defined separately before implementation and evaluation.

### 2.15 Conflict and Information-Gap Analyst

This responsibility identifies unresolved contradictions and missing information across the research task.

Responsibilities:

* Detect conflicting figures, statements, dates, units, definitions, and reporting periods.
* Compare source authority, relevance, recency, and context.
* Determine whether apparently conflicting values can be explained by different periods or definitions.
* Preserve material unresolved conflicts.
* Identify required information that could not be found or verified.
* Assess how missing information affects the analysis, valuation, and rating.
* Trigger bounded follow-up research when resolving a gap or conflict is important.
* Prevent unresolved uncertainty from being hidden in the final report.

Output:

* Conflict records.
* Missing-information records.
* Resolution status and rationale.
* Impact on findings and conclusions.
* Recommended follow-up tasks.

### 2.16 Report Generator

The Report Generator assembles validated research findings into the final structured report.

Responsibilities:

* Produce all required report sections.
* Present the executive summary and detailed analysis consistently.
* Integrate financial, business, industry, risk, competitor, valuation, and thesis findings.
* Include the rating or insufficient-evidence outcome.
* Attach citations to material claims.
* Explain calculations, assumptions, scenarios, conflicts, and missing information.
* Distinguish source-reported facts from calculations, estimates, and interpretations.
* Disclose limitations and uncertainty.
* Avoid introducing unsupported facts while combining findings.
* Preserve the report's relationship to the research task and its evidence.

Output:

* Structured research report.
* Material claims with supporting citations.
* Valuation and scenario results.
* Rating rationale.
* Limitations, conflicts, and missing-information disclosures.

### 2.17 Report Validator

The Report Validator checks whether the assembled report satisfies the defined quality and release requirements.

Responsibilities:

* Verify that mandatory report sections are present.
* Check citations for support and traceability.
* Identify unsupported material claims.
* Validate financial calculations against recorded inputs and formulas.
* Check consistency between financial analysis, valuation, scenarios, thesis, and rating.
* Verify that uncertainty and material conflicts are disclosed.
* Detect contradictions between the report and its evidence.
* Check that insufficient evidence is handled according to the defined policy.
* Return validation findings for correction or explicit limitation.
* Prevent a critical validation failure from being silently treated as a successful report.

Output:

* Validation result.
* Findings classified by severity.
* Unsupported-claim and citation issues.
* Calculation or consistency issues.
* Required corrections or explicit limitations.

### 2.18 Evaluation Owner

The Evaluation Owner measures system quality against the versioned benchmark and acceptance criteria.

Responsibilities:

* Maintain the evaluation dataset and its version.
* Preserve expected answers, relevant evidence, and question categories.
* Evaluate factual, multi-hop, unanswerable, and adversarial questions.
* Measure retrieval quality, factual correctness, evidence faithfulness, citation support, and financial calculation correctness.
* Evaluate valuation and rating quality using the defined rubric.
* Record latency, cost, failure behavior, and critical errors.
* Preserve per-question outputs and reproducible evaluation configurations.
* Run required retrieval and system experiments under comparable conditions.
* Report category-level results, limitations, and regressions.
* Block release when mandatory gates fail.

Output:

* Evaluation dataset and configuration versions.
* Baseline and evaluation results.
* Category-level metrics.
* Critical failure records.
* Experiment reports.
* Release-gate decision.

### 2.19 Security and Isolation Owner

This responsibility protects research inputs, documents, evidence, and stored results from defined security failures.

Responsibilities:

* Treat retrieved documents and uploaded files as untrusted data.
* Ensure instructions embedded in source documents cannot override system-defined rules.
* Maintain separation between source content and trusted instructions.
* Validate uploaded files and handle malformed content safely.
* Enforce collection-level evidence and retrieval boundaries.
* Prevent unauthorized cross-collection access.
* Minimize sensitive content in operational logs.
* Support explicit deletion of stored research data.
* Test defined prompt-injection and isolation attacks.
* Document residual risks and untested attack paths.

Output:

* Security validation results.
* Isolation-test results.
* Prompt-injection test findings.
* Data-handling and deletion evidence.
* Documented residual risks.

### 2.20 Task State and Recovery Owner

This responsibility ensures that long-running research tasks remain understandable and recoverable.

Responsibilities:

* Maintain task status, timestamps, and stage-level progress.
* Persist completed work and required checkpoints.
* Record errors, retries, and recovery attempts.
* Prevent duplicate processing from corrupting results.
* Resume eligible tasks after interruption.
* Respect cancellation requests and resource limits.
* Preserve completed work when a task is cancelled or fails.
* Ensure terminal task states reflect the actual outcome.
* Make failure reasons and incomplete work visible to the user.

Output:

* Current task state.
* Stage history.
* Checkpoint and recovery records.
* Retry and failure history.
* Accurate terminal status.

---

## 3. Responsibility Boundaries

The following boundaries prevent responsibilities from becoming mixed together.

| Responsibility                | Owns                                                | Does not own                                             |
| ----------------------------- | --------------------------------------------------- | -------------------------------------------------------- |
| Research Orchestrator         | Task lifecycle, coordination, bounded execution     | Establishing financial truth independently               |
| Research Planner              | Research tasks and evidence requirements            | Selecting deployment technologies                        |
| Source Discovery              | Finding and collecting source material              | Deciding that every source is reliable                   |
| Document Ingestion            | Extraction, normalization, document quality         | Interpreting the company's investment merits             |
| Evidence Retrieval            | Finding relevant evidence                           | Final claim verification                                 |
| Provenance Manager            | Traceability between claims and evidence            | Inventing or rewriting source facts                      |
| Financial Data Analyst        | Financial analysis and metric calculations          | Arbitrary valuation assumptions                          |
| Business and Industry Analyst | Business, industry, management, competitor analysis | Guaranteeing future performance                          |
| Risk Analyst                  | Risk identification and analysis                    | Hiding risks to support a preferred thesis               |
| Valuation Analyst             | Methodology, assumptions, valuation calculations    | Presenting uncertain estimates as facts                  |
| Thesis and Antithesis Analyst | Competing evidence-based arguments                  | Making unsupported claims to balance both sides          |
| Rating Evaluator              | Applying the documented rating methodology          | Personalized portfolio or allocation advice              |
| Conflict and Gap Analyst      | Missing information and conflicting evidence        | Silently deleting unresolved contradictions              |
| Report Generator              | Report assembly and presentation                    | Bypassing evidence requirements                          |
| Report Validator              | Quality checks and validation findings              | Silently waiving mandatory release gates                 |
| Evaluation Owner              | Benchmark, metrics, experiments, release evidence   | Changing thresholds after seeing results to force a pass |
| Security and Isolation Owner  | Defined security and isolation controls             | Claiming universal security from limited tests           |
| Task State and Recovery Owner | Progress, checkpoints, retries, accurate status     | Reporting failed or incomplete work as completed         |

---

## 4. Deterministic and AI-Assisted Responsibilities

The system must distinguish work that requires explicit deterministic rules from work that benefits from AI-assisted reasoning.

### 4.1 Primarily Deterministic

The following responsibilities should use explicit, testable rules wherever practical:

* Input and file validation.
* Company identifier matching against available records.
* Task state transitions.
* Retry and resource-limit enforcement.
* Financial arithmetic and metric calculations.
* Unit, date, and reporting-period checks.
* Provenance identifier preservation.
* Citation-reference integrity checks.
* Collection access enforcement.
* Duplicate-processing prevention.
* Report schema validation.
* Evaluation metric computation.
* Release-gate evaluation.
* Cancellation and terminal-status handling.

### 4.2 AI-Assisted

The following responsibilities may require language understanding, synthesis, or judgment:

* Research planning.
* Query formulation and follow-up prioritization.
* Business and industry interpretation.
* Competitor analysis.
* Risk identification.
* Conflict interpretation.
* Evidence sufficiency assessment.
* Thesis and antithesis development.
* Valuation-method selection where judgment is required.
* Scenario interpretation.
* Report drafting.
* Qualitative evaluation under a documented rubric.

AI-assisted outputs remain subject to evidence, validation, uncertainty, and evaluation requirements.

### 4.3 Shared Responsibilities

Some activities require both AI-assisted reasoning and deterministic validation.

Examples:

* An AI-assisted financial interpretation must reference validated metrics.
* An AI-generated claim must be linked to evidence and checked for support.
* An AI-proposed valuation method must use documented assumptions and reproducible calculations.
* An AI-generated rating must satisfy the documented rating methodology.
* An AI-generated report must pass required structural and evidence checks.

The system must not treat a model's confidence or fluent explanation as proof of correctness.

---

## 5. Cross-Responsibility Rules

All responsibility owners must follow these rules:

1. **Evidence before claims:** Material factual claims must have relevant supporting evidence or be explicitly marked as unsupported or uncertain.
2. **Preserve provenance:** Source and location metadata must remain available as findings move through the workflow.
3. **Distinguish fact from interpretation:** Reported facts, calculations, estimates, and judgments must not be presented as interchangeable.
4. **No fabricated completeness:** Missing data must remain missing; it must not be silently replaced with invented values.
5. **Explicit conflict handling:** Material unresolved contradictions must be disclosed.
6. **Bounded execution:** Research, retries, runtime, and external calls must remain within configured limits.
7. **Accurate status:** A task must not be marked complete unless required completion and validation conditions are satisfied.
8. **Security by boundary:** Untrusted source content must not override trusted instructions or cross collection boundaries.
9. **Auditable calculations:** Material numerical outputs must be reproducible from their recorded inputs and formulas.
10. **Critical failures are visible:** A failed mandatory check must result in correction, a blocked release, or an explicitly limited outcome according to the defined policy.
11. **No silent methodology changes:** Rating and valuation methodology changes must be documented and evaluated.
12. **Uncertainty remains visible:** Missing evidence, weak extraction, conflicting sources, and unsupported conclusions must be reflected in the final report.

---

## 6. Failure Ownership and Escalation

When a responsibility cannot complete its work, it must return a structured failure or limitation rather than silently substituting an unreliable result.

| Failure                                    | Primary responsibility owner                       | Required response                                                             |
| ------------------------------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------- |
| Ambiguous company identity                 | Company Identity Resolver                          | Request clarification or stop safely                                          |
| Source unavailable                         | Source Discovery and Collection                    | Record failure and identify alternatives                                      |
| Corrupt or unsupported PDF                 | Document Ingestion and Normalization               | Reject or quarantine the document                                             |
| OCR or extraction quality too low          | Document Ingestion and Normalization               | Flag affected content and limit dependent claims                              |
| No relevant evidence retrieved             | Evidence Retrieval                                 | Report the gap and allow bounded follow-up                                    |
| Citation does not support claim            | Evidence and Provenance Manager / Report Validator | Correct, remove, or qualify the claim                                         |
| Financial values conflict                  | Conflict and Information-Gap Analyst               | Investigate and disclose unresolved differences                               |
| Calculation invalid                        | Financial Data Analyst                             | Reject the invalid result and record the cause                                |
| Valuation cannot be supported              | Valuation Analyst                                  | Return a limited or speculative outcome with explicit uncertainty             |
| Rating criteria not satisfied              | Investment Rating Evaluator                        | Return insufficient evidence                                                  |
| Report contains critical unsupported claim | Report Validator                                   | Block successful completion until resolved or explicitly limited under policy |
| Research limit reached                     | Research Orchestrator                              | Stop further research and disclose incompleteness                             |
| Worker or task interrupted                 | Task State and Recovery Owner                      | Resume from a valid checkpoint or report failure                              |
| Cross-collection access violation          | Security and Isolation Owner                       | Block access, record the incident, and fail the relevant check                |
| Defined prompt-injection defense fails     | Security and Isolation Owner                       | Record the attack, block release, and require regression testing              |
| Mandatory evaluation gate fails            | Evaluation Owner                                   | Block release until corrected and retested                                    |

A responsibility owner may depend on another responsibility's output, but it must not silently assume that the output is valid when required validation has failed.

---

## 7. Responsibility-to-Workflow Mapping

| Workflow                                        | Primary responsibility owners                                |
| ----------------------------------------------- | ------------------------------------------------------------ |
| WF-01: End-to-end company research              | Research Orchestrator, Research Planner                      |
| WF-02: Company identity resolution              | Company Identity Resolver                                    |
| WF-03: Annual report ingestion                  | Document Ingestion and Normalization                         |
| WF-04: Evidence collection and retrieval        | Source Discovery and Collection, Evidence Retrieval          |
| WF-05: Evidence provenance                      | Evidence and Provenance Manager                              |
| WF-06: Missing information                      | Conflict and Information-Gap Analyst, Research Planner       |
| WF-07: Conflicting information                  | Conflict and Information-Gap Analyst                         |
| WF-08: Financial analysis                       | Financial Data Analyst                                       |
| WF-09: Valuation and scenarios                  | Valuation Analyst                                            |
| WF-10: Thesis, antithesis, and rating           | Thesis and Antithesis Analyst, Investment Rating Evaluator   |
| WF-11: Report generation and validation         | Report Generator, Report Validator                           |
| WF-12: Background progress                      | Task State and Recovery Owner, Research Orchestrator         |
| WF-13: Queue, cancellation, and recovery        | Task State and Recovery Owner, Research Orchestrator         |
| WF-14: Prompt injection and untrusted documents | Security and Isolation Owner                                 |
| WF-15: Benchmark evaluation                     | Evaluation Owner                                             |
| WF-16: A/B experiments                          | Evaluation Owner and relevant research responsibility owners |
| WF-17: Collection isolation                     | Security and Isolation Owner                                 |
| WF-18: Data deletion                            | Security and Isolation Owner, Task State and Recovery Owner  |

This mapping identifies primary ownership. Detailed component boundaries and interaction contracts will be defined in later documents.

---

## 8. Open Decisions for Later Design

The following decisions are intentionally not finalized in this document:

* Which responsibilities should be implemented as separate components.
* Which responsibilities can be grouped without creating excessive coupling.
* Which responsibilities require independent execution or background processing.
* How responsibility owners communicate and exchange structured data.
* Which state and evidence records must be persisted.
* How AI-assisted decisions are represented and validated.
* How responsibility failures are propagated across component boundaries.
* How rating methodology and valuation methods are formally specified.
* Which observability and evaluation tools will be used.

These decisions belong in the component-boundary, architecture, data-flow, contract, and ADR documents.

---

## 9. Completion Criteria

This document is complete when:

* Every major workflow has clearly identified responsibility owners.
* Each responsibility has explicit duties and outputs.
* Deterministic calculations and control rules are distinguished from AI-assisted reasoning.
* Responsibility boundaries and failure ownership are documented.
* Evidence, provenance, uncertainty, and security responsibilities are explicit.
* No technology or framework choice has been prematurely fixed.
* The responsibility mapping is consistent with `01_problem.md`, `02_requirements.md`, `03_scope.md`, `04_success_criteria.md`, and `05_workflows.md`.
