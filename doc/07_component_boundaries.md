# Component Boundaries

## 1. Purpose

This document defines the major logical components of the Equity / Business Research Agent and establishes clear boundaries between them.

It specifies:

* The responsibility of each component.
* The capabilities each component owns.
* The inputs and outputs exchanged between components.
* The dependencies and permitted interactions between components.
* The boundaries between deterministic logic and AI-assisted reasoning.
* The rules for handling failures, state, evidence, and security.

This document defines the logical system design, not the final technology stack.

Implementation technologies, deployment topology, storage choices, and communication protocols will be decided separately through architecture decisions and ADRs.

---

## 2. Component Design Principles

The system must follow these principles.

### 2.1 Single Responsibility

Each component should have a clearly defined primary responsibility.

A component may contain multiple related operations, but it must not become responsible for unrelated research, orchestration, persistence, and validation concerns.

### 2.2 Explicit Contracts

Every component must define:

* Required inputs.
* Produced outputs.
* Preconditions.
* Postconditions.
* Possible errors.
* Relevant state changes.
* Validation requirements.

Components must not depend on undocumented assumptions about another component's internal behavior.

### 2.3 Evidence Traceability

Evidence identifiers and source metadata must survive every stage of the research workflow.

A material report claim must be traceable through:

`Report Claim → Supporting Evidence → Extracted Content → Source Document → Source Location`

For calculated claims, the trace must additionally include the calculation inputs, formula, units, reporting periods, and output.

### 2.4 Deterministic Financial Calculations

Financial calculations must be reproducible and independently testable.

Language-model reasoning may interpret financial results, but arithmetic, unit conversions, period comparisons, and formula-based metrics must follow explicit calculation rules.

### 2.5 Bounded Research

The system must not perform unrestricted autonomous research.

Research execution must respect configurable limits for:

* Total runtime.
* Research steps.
* Retries per stage.
* External API calls.
* Queue capacity.

When a limit is reached, the system must stop safely and report incomplete work or limitations.

### 2.6 Failure Isolation

A failure in one research stage must not automatically invalidate all previously completed work.

Where recovery is safe, the system should preserve completed outputs, record the failure, and resume from a valid checkpoint.

### 2.7 Security Boundaries

Uploaded documents and retrieved source content are untrusted data.

No component may treat instructions embedded in research documents as higher-priority instructions than the system's trusted rules.

Collection boundaries must be enforced independently of the language model's behavior.

### 2.8 Quality Before Completion

Generating text is not equivalent to completing a research task.

Completion requires the defined research outputs, evidence checks, financial validation, required report sections, and mandatory release conditions to be satisfied.

---

## 3. High-Level Logical Components

The system is divided into the following logical components.

| ID  | Component                         | Primary responsibility                                              |
| --- | --------------------------------- | ------------------------------------------------------------------- |
| C01 | Research Request Interface        | Accept requests and expose task status and reports                  |
| C02 | Research Orchestrator             | Coordinate the lifecycle and execution of research tasks            |
| C03 | Company Identity Resolver         | Resolve and validate the requested listed company                   |
| C04 | Research Planner                  | Define research tasks, information requirements, and follow-ups     |
| C05 | Source Acquisition                | Discover and retrieve relevant source material                      |
| C06 | Document Ingestion                | Validate, extract, normalize, and track documents                   |
| C07 | Evidence Repository and Retrieval | Manage research evidence and retrieve relevant content              |
| C08 | Provenance Manager                | Maintain claim-to-source and calculation traceability               |
| C09 | Financial Analysis                | Normalize financial data and calculate fundamental metrics          |
| C10 | Business and Industry Analysis    | Analyze business models, management, industry, and competitors      |
| C11 | Risk Analysis                     | Identify and assess material risks                                  |
| C12 | Valuation and Scenario Analysis   | Estimate valuation ranges and evaluate scenarios                    |
| C13 | Thesis and Rating Analysis        | Develop competing investment arguments and apply rating methodology |
| C14 | Report Assembly                   | Assemble research findings into the required report                 |
| C15 | Report Validation                 | Validate evidence, calculations, consistency, and completeness      |
| C16 | Task State and Recovery           | Track progress, checkpoints, retries, cancellation, and recovery    |
| C17 | Evaluation and Experimentation    | Evaluate quality and compare system configurations                  |
| C18 | Security and Data Governance      | Enforce input safety, collection isolation, and data deletion rules |

These are logical boundaries. They do not require eighteen separately deployed services. Multiple components may be implemented together if their interfaces and responsibilities remain distinct.

---

## 4. Component Specifications

### C01 — Research Request Interface

**Purpose:** Provide the entry point for research requests and the interface for retrieving progress and results.

Responsibilities:

* Accept a company name or ticker.
* Accept an optional annual report PDF.
* Accept the applicable research configuration and reference date.
* Validate basic request structure and input constraints.
* Submit a research task.
* Return a unique task identifier.
* Expose task status, stage progress, errors, and limitations.
* Allow authorized cancellation and deletion requests within the MVP's supported access model.
* Make the completed report available to the user.

Inputs:

* Company identifier.
* Optional PDF.
* Reference date and permitted configuration.
* Status, cancellation, or deletion request.

Outputs:

* Request validation result.
* Task identifier.
* Current task state.
* Progress information.
* Final report or explicit failure/limitation status.

Must not:

* Perform the entire research workflow itself.
* Calculate financial metrics directly.
* Bypass report validation.
* Claim that a task is complete merely because it was accepted.

Dependencies:

* Research Orchestrator.
* Task State and Recovery.
* Security and Data Governance.

### C02 — Research Orchestrator

**Purpose:** Coordinate the end-to-end research task.

Responsibilities:

* Create and initialize research tasks.
* Coordinate dependencies between components.
* Maintain the research execution plan.
* Trigger appropriate components in the correct order.
* Determine when further evidence collection is necessary.
* Enforce research limits and completion rules.
* Track stage outcomes.
* Initiate report assembly and validation.
* Return a final task outcome consistent with the actual work completed.

Inputs:

* Validated research request.
* Confirmed company identity.
* Research plan.
* Stage outputs and errors.
* Current task state and configured limits.

Outputs:

* Component execution requests.
* Updated task state.
* Follow-up research requests.
* Completion, limited-completion, cancellation, or failure outcome.

Must not:

* Contain every research capability internally.
* Replace evidence validation with its own unsupported judgment.
* Retry indefinitely.
* Mark an incomplete task as successfully completed.

Dependencies:

* Company Identity Resolver.
* Research Planner.
* Source Acquisition.
* Document Ingestion.
* Evidence Repository and Retrieval.
* Analysis components.
* Report Assembly and Validation.
* Task State and Recovery.

### C03 — Company Identity Resolver

**Purpose:** Establish the correct identity of the company being researched.

Responsibilities:

* Resolve a supplied company name or ticker against available company and listing information.
* Detect ambiguous or conflicting matches.
* Confirm the identity before company-specific research proceeds.
* Preserve the resolved company identifier throughout the task.
* Prevent similarly named companies from being mixed together.

Inputs:

* Company name or ticker.
* Available company/listing records.

Outputs:

* Resolved company identity.
* Resolution evidence or reference.
* Match status.
* Clarification requirement where applicable.

Must not:

* Discover or rank investment opportunities.
* Choose a company on the user's behalf.
* Silently choose between materially ambiguous matches.

Dependencies:

* Research Request Interface.
* Available company metadata through Source Acquisition.

### C04 — Research Planner

**Purpose:** Translate the research objective into a bounded, evidence-oriented plan.

Responsibilities:

* Define required report topics.
* Identify the financial periods and information categories needed.
* Establish evidence requirements for material findings.
* Identify dependencies between research tasks.
* Track outstanding information requirements.
* Prioritize follow-up research.
* Stop expanding the plan when configured limits or completion criteria are reached.

Inputs:

* Confirmed company identity.
* Required report structure.
* Available source inventory.
* Existing findings, evidence gaps, and conflicts.

Outputs:

* Research plan.
* Task dependencies.
* Evidence requirements.
* Research completion checklist.
* Prioritized follow-up tasks.

Must not:

* Execute unrestricted research.
* Treat every possible research question as mandatory.
* Change rating or valuation methodology without documented rules.

Dependencies:

* Research Orchestrator.
* Source Acquisition.
* Evidence Repository and Retrieval.
* Analysis components.
* Task State and Recovery.

### C05 — Source Acquisition

**Purpose:** Find and collect relevant public source material and data.

Responsibilities:

* Retrieve official company disclosures and annual reports.
* Retrieve relevant regulatory and stock-exchange filings.
* Retrieve available historical financial information and share-price data.
* Collect relevant industry and competitor information.
* Record source identity, dates, reporting periods, and retrieval metadata.
* Record unavailable or inaccessible sources.
* Preserve source material or stable references needed for subsequent evidence extraction.

Inputs:

* Confirmed company identity.
* Research plan.
* Required information categories.
* Source and external-access configuration.

Outputs:

* Source records.
* Retrieved documents and structured data.
* Source metadata.
* Collection status and errors.
* Source coverage information.

Must not:

* Treat unverified search snippets as established facts.
* Silently reconcile contradictory figures.
* Invent missing financial history.
* Interpret source acquisition success as proof of research quality.

Dependencies:

* Research Planner.
* Document Ingestion.
* Evidence Repository and Retrieval.
* Security and Data Governance.

### C06 — Document Ingestion

**Purpose:** Convert supported documents into validated, searchable, traceable content.

Responsibilities:

* Validate PDF type, file size, page count, and basic integrity.
* Detect text-based versus scanned PDFs.
* Extract text and relevant structure.
* Apply OCR where required and available.
* Preserve page numbers and source locations.
* Normalize text without altering the intended meaning.
* Preserve financial tables, units, dates, and reporting periods as accurately as possible.
* Identify extraction-quality problems.
* Prevent duplicate ingestion.
* Quarantine malformed or unsafe documents.
* Track document-processing status and failures.

Inputs:

* Uploaded PDF or acquired document.
* Source metadata.
* Ingestion constraints.

Outputs:

* Validated document record.
* Extracted and normalized content.
* Page and location metadata.
* Extraction-quality information.
* Processing status and errors.

Must not:

* Treat low-quality OCR output as unquestionably accurate.
* Remove source-location metadata required for citations.
* Mark a document as successfully indexed before required processing finishes.

Dependencies:

* Research Request Interface or Source Acquisition.
* Evidence Repository and Retrieval.
* Security and Data Governance.
* Task State and Recovery.

### C07 — Evidence Repository and Retrieval

**Purpose:** Store and retrieve research evidence within the correct collection boundary.

Responsibilities:

* Maintain source-linked document content and evidence records.
* Make relevant content retrievable by research question.
* Return evidence with stable source and location references.
* Identify retrieval failures and empty-result cases.
* Preserve collection-level separation.
* Support evaluation of retrieval quality.
* Allow evidence to be traced back to its originating document.

Inputs:

* Normalized document content.
* Source metadata.
* Research questions.
* Collection scope and retrieval constraints.

Outputs:

* Retrieved evidence items.
* Source and location references.
* Retrieval status.
* Relevant metadata for downstream analysis.

Must not:

* Decide that retrieved evidence necessarily supports a claim.
* Generate unsupported company facts.
* Return evidence outside the permitted collection.
* Hide retrieval failures.

Dependencies:

* Document Ingestion.
* Source Acquisition.
* Provenance Manager.
* Security and Data Governance.

### C08 — Provenance Manager

**Purpose:** Preserve traceability from research conclusions back to the evidence and calculations supporting them.

Responsibilities:

* Assign and maintain stable evidence references.
* Link material claims to supporting source locations.
* Preserve reporting period, units, source date, and source identity.
* Record the origin of a finding: sourced, calculated, estimated, inferred, or uncertain.
* Link financial outputs to their calculation inputs and formulas.
* Identify missing evidence mappings.
* Support citation validation and report auditing.

Inputs:

* Evidence items.
* Source metadata.
* Analysis findings.
* Financial calculation records.
* Draft report claims.

Outputs:

* Claim-to-evidence mappings.
* Calculation provenance.
* Citation metadata.
* Traceability validation findings.

Must not:

* Invent citations.
* Treat citation presence as proof that a claim is supported.
* Change the meaning of a source to fit a conclusion.

Dependencies:

* Evidence Repository and Retrieval.
* Financial Analysis.
* Business and Industry Analysis.
* Risk Analysis.
* Valuation and Scenario Analysis.
* Thesis and Rating Analysis.
* Report Assembly and Validation.

### C09 — Financial Analysis

**Purpose:** Produce reproducible fundamental and financial analysis.

Responsibilities:

* Normalize financial statements and metrics.
* Analyze historical performance, targeting five years where available.
* Calculate growth, margins, returns, leverage, liquidity, and other relevant measures.
* Compare financial periods consistently.
* Detect incompatible units, missing values, and inconsistent definitions.
* Record inputs, formulas, periods, units, and rounding rules.
* Separate reported figures from calculated metrics and estimates.
* Explain material financial trends with reference to the underlying data.

Inputs:

* Financial statements and source data.
* Reporting periods.
* Metric definitions.
* Evidence references.

Outputs:

* Normalized financial data.
* Calculated metrics.
* Financial trends and findings.
* Calculation records.
* Data-quality warnings.

Must not:

* Fabricate missing values.
* Compare incompatible financial periods without qualification.
* Rely on language-model arithmetic when a deterministic calculation is required.
* Hide calculation failures.

Dependencies:

* Source Acquisition.
* Evidence Repository and Retrieval.
* Provenance Manager.

### C10 — Business and Industry Analysis

**Purpose:** Explain the company's business model and competitive environment.

Responsibilities:

* Analyze business segments, products, services, and revenue drivers.
* Examine relevant industry structure and trends.
* Identify competitors and explain why they are comparable.
* Analyze management disclosures and governance information.
* Identify material competitive strengths and weaknesses.
* Distinguish evidence from interpretation.
* Record missing information and limitations.

Inputs:

* Company disclosures.
* Industry and competitor sources.
* Retrieved evidence.
* Research plan.

Outputs:

* Business model analysis.
* Industry analysis.
* Competitor comparisons.
* Management and governance findings.
* Evidence-linked qualitative conclusions.

Must not:

* Present speculation as a reported fact.
* Make unsupported claims about management intent.
* Treat companies as directly comparable without considering material differences.

Dependencies:

* Source Acquisition.
* Evidence Repository and Retrieval.
* Provenance Manager.

### C11 — Risk Analysis

**Purpose:** Identify material risks and assess their implications.

Responsibilities:

* Analyze financial, business, competitive, operational, governance, regulatory, and industry risks where relevant.
* Link risks to supporting evidence.
* Explain potential effects on financial performance and valuation.
* Consider mitigating factors and counterevidence.
* Identify unresolved questions.
* Preserve material negative findings even when they weaken the investment thesis.

Inputs:

* Financial findings.
* Business and industry findings.
* Management disclosures.
* Retrieved evidence.
* Conflict and information-gap records.

Outputs:

* Evidence-linked risk register.
* Risk implications.
* Mitigating factors.
* Uncertainty and unresolved questions.

Must not:

* Invent risk events.
* Present hypothetical scenarios as events that have occurred.
* Suppress material risks to support a preferred conclusion.

Dependencies:

* Financial Analysis.
* Business and Industry Analysis.
* Evidence Repository and Retrieval.
* Provenance Manager.

### C12 — Valuation and Scenario Analysis

**Purpose:** Estimate a valuation range and examine how assumptions affect the result.

Responsibilities:

* Select a suitable valuation approach based on available information and documented methodology.
* Identify and record required inputs.
* Calculate valuation outputs using reproducible rules.
* Build bull, base, and bear scenarios where supported.
* Perform sensitivity analysis.
* Compare estimated value with an appropriately dated market-price reference when available.
* Record assumptions, limitations, and confidence.
* Flag estimates that are speculative or not decision-grade.

Inputs:

* Validated financial data.
* Market-price reference data.
* Documented valuation methodology.
* Business and risk findings.
* Evidence references.

Outputs:

* Valuation method and rationale.
* Assumptions and input records.
* Valuation range.
* Scenario and sensitivity results.
* Confidence assessment.
* Limitations and supporting evidence.

Must not:

* Hide assumptions.
* Present speculative estimates as reliable targets.
* Use missing data without disclosure.
* Claim a valuation is reliable merely because the calculation is numerically correct.

Dependencies:

* Financial Analysis.
* Business and Industry Analysis.
* Risk Analysis.
* Evidence Repository and Retrieval.
* Provenance Manager.

### C13 — Thesis and Rating Analysis

**Purpose:** Synthesize the evidence into competing investment arguments and apply the documented rating methodology.

Responsibilities:

* Construct the bull case and bear case.
* Identify the most important drivers and assumptions.
* Evaluate counterevidence and unresolved risks.
* Apply the documented buy/hold/sell criteria when the evidence is sufficient.
* Return an insufficient-evidence outcome when mandatory evidence or methodology requirements are not met.
* Explain conditions that could change the conclusion.
* Record the evidence and assumptions behind the conclusion.

Inputs:

* Financial findings.
* Business and industry findings.
* Risk register.
* Valuation and scenario results.
* Evidence and provenance records.
* Rating methodology.

Outputs:

* Bull and bear cases.
* Investment thesis and antithesis.
* Rating or insufficient-evidence outcome.
* Rationale and confidence.
* Conditions that could change the conclusion.

Must not:

* Invent a rating methodology during report generation.
* Present a rating as a guarantee or personalized investment instruction.
* Ignore material counterevidence.
* Assign a confident rating when evidence requirements are not met.

Dependencies:

* Financial Analysis.
* Business and Industry Analysis.
* Risk Analysis.
* Valuation and Scenario Analysis.
* Provenance Manager.

### C14 — Report Assembly

**Purpose:** Assemble validated research findings into a coherent report.

Responsibilities:

* Generate the required report structure.
* Integrate findings from the analysis components.
* Include executive summary, company overview, management, industry, financial analysis, competitors, risks, valuation, scenarios, technical analysis where data is available, thesis/antithesis, rating, and limitations.
* Preserve citations and calculation references.
* Distinguish facts, calculations, estimates, and judgments.
* Disclose missing information and unresolved conflicts.
* Avoid adding claims not present in validated findings.

Inputs:

* Analysis outputs.
* Evidence and provenance records.
* Valuation and rating outputs.
* Report structure requirements.
* Task metadata.

Outputs:

* Draft research report.
* Structured report sections.
* Claim and citation references.
* Report metadata.

Must not:

* Invent new financial facts during synthesis.
* Remove material caveats for readability.
* Treat missing report sections as complete without an explicit limitation.

Dependencies:

* Financial Analysis.
* Business and Industry Analysis.
* Risk Analysis.
* Valuation and Scenario Analysis.
* Thesis and Rating Analysis.
* Provenance Manager.

### C15 — Report Validation

**Purpose:** Determine whether the report satisfies the required structural, evidence, calculation, and consistency checks.

Responsibilities:

* Check required section coverage.
* Validate citation references and support for material claims.
* Identify unsupported claims.
* Verify financial calculation records.
* Check consistency across financial findings, valuation, scenarios, thesis, and rating.
* Verify disclosure of material conflicts and missing information.
* Identify contradictions and critical errors.
* Return actionable validation findings.
* Block successful completion when mandatory requirements fail.

Inputs:

* Draft report.
* Evidence and provenance records.
* Financial calculation records.
* Rating and valuation methodology.
* Defined quality and release criteria.

Outputs:

* Validation status.
* Findings and severity.
* Required corrections.
* Explicit limitations where permitted.
* Final validation decision.

Must not:

* Silently waive mandatory gates.
* Assume that a fluent report is correct.
* Approve a material claim solely because it contains a citation.

Dependencies:

* Report Assembly.
* Provenance Manager.
* Financial Analysis.
* Valuation and Scenario Analysis.
* Thesis and Rating Analysis.
* Evaluation and Experimentation.

### C16 — Task State and Recovery

**Purpose:** Maintain accurate task state and support bounded recovery from interruptions.

Responsibilities:

* Track task and stage status.
* Preserve completed outputs and checkpoints.
* Record errors, retry attempts, and recovery history.
* Enforce safe retry and idempotency behavior.
* Support queued and running task cancellation.
* Recover interrupted work where possible.
* Preserve completed work when a task fails or is cancelled.
* Expose accurate status and failure details.

Inputs:

* Task creation and status events.
* Stage outputs and failures.
* Retry and runtime limits.
* Cancellation requests.

Outputs:

* Current task state.
* Stage history.
* Checkpoint records.
* Recovery outcome.
* Accurate terminal status.

Must not:

* Mark failed work as complete.
* Retry indefinitely.
* Lose already completed results without a documented reason.

Dependencies:

* Research Orchestrator.
* Document Ingestion.
* Report Assembly and Validation.
* Research Request Interface.

### C17 — Evaluation and Experimentation

**Purpose:** Measure research quality and verify that system changes improve or preserve required behavior.

Responsibilities:

* Maintain the versioned 40-question benchmark.
* Measure retrieval, factual correctness, evidence faithfulness, citation support, and financial calculation correctness.
* Evaluate valuation and rating using the documented rubric.
* Test unanswerable and adversarial cases.
* Record latency, cost, failures, and critical errors.
* Run required retrieval experiments.
* Preserve baseline results and configuration versions.
* Report category-level outcomes.
* Enforce mandatory release gates.

Required experiments:

1. Hybrid retrieval versus vector-only retrieval.
2. Reranking enabled versus disabled.
3. Query rewriting enabled versus disabled.

Inputs:

* Versioned evaluation dataset.
* System configuration.
* Generated reports and intermediate outputs.
* Defined success criteria.

Outputs:

* Evaluation results.
* Baseline comparisons.
* Experiment reports.
* Regression findings.
* Release-gate outcome.

Must not:

* Change evaluation thresholds after observing results merely to obtain a pass.
* Hide category-specific failures behind aggregate scores.
* Claim general reliability from a small benchmark without qualification.

Dependencies:

* All components that produce evaluated outputs.
* Report Validation.
* Documented success criteria and experiment methodology.

### C18 — Security and Data Governance

**Purpose:** Enforce defined security, collection-isolation, and data-lifecycle requirements.

Responsibilities:

* Validate untrusted file inputs.
* Maintain separation between trusted instructions and source content.
* Enforce collection-scoped access to evidence and reports.
* Prevent cross-collection retrieval or disclosure.
* Support explicit data deletion.
* Minimize sensitive information in logs.
* Test the defined prompt-injection attack set.
* Record security failures and residual risks.
* Verify that deletion and isolation behavior meets documented requirements.

Inputs:

* User requests and uploaded files.
* Collection identifiers.
* Data-access requests.
* Deletion requests.
* Security test cases.

Outputs:

* Validation and access decisions.
* Isolation-test results.
* Deletion outcomes.
* Security findings.
* Documented residual risks.

Must not:

* Trust source-document instructions as system instructions.
* Claim complete prompt-injection immunity based on limited tests.
* Allow retrieval boundaries to depend solely on model compliance.

Dependencies:

* Research Request Interface.
* Document Ingestion.
* Evidence Repository and Retrieval.
* Task State and Recovery.
* Evaluation and Experimentation.

---

## 5. Component Interaction Rules

### 5.1 Research Execution

The normal research path is:

1. The Research Request Interface submits a request.
2. The Research Orchestrator creates the task.
3. The Company Identity Resolver confirms the company.
4. The Research Planner defines the research plan.
5. Source Acquisition and Document Ingestion collect and prepare source material.
6. Evidence Repository and Retrieval provide relevant evidence.
7. Financial Analysis, Business and Industry Analysis, and Risk Analysis produce findings.
8. Valuation and Scenario Analysis produces valuation outputs.
9. Thesis and Rating Analysis synthesizes the evidence and applies the documented rating methodology.
10. Report Assembly builds the draft report.
11. Report Validation checks the report.
12. The Research Orchestrator finalizes the task only when the required conditions are satisfied.

The exact ordering of independent research activities may change during architecture design. Dependencies and completion requirements must remain explicit.

### 5.2 Bounded Follow-up

Follow-up research may be triggered when:

* A mandatory report topic lacks evidence.
* A material claim has insufficient support.
* Financial figures conflict.
* A key valuation input is missing.
* A citation cannot be verified.
* A material risk requires further investigation.

Each follow-up must identify:

* The unresolved question.
* Why it matters.
* The evidence needed.
* The responsible component.
* The applicable resource limits.

Follow-up research must stop when the issue is resolved, the configured limits are reached, or additional research is no longer justified.

### 5.3 Failure Propagation

Components must return explicit success, limitation, or failure outcomes.

The orchestrator must distinguish:

* Recoverable failures.
* Non-recoverable failures.
* Missing or weak evidence.
* Validation failures.
* Resource-limit exhaustion.
* Cancellation.

A recoverable failure may trigger a bounded retry or resume operation. A material evidence or validation failure must not be treated as a successful result simply because the component returned output.

### 5.4 Completion Ownership

Only the Research Orchestrator may finalize the overall task state.

It must rely on:

* Required stage outcomes.
* Report validation.
* Mandatory completion conditions.
* Security and isolation requirements where applicable.
* Accurate recovery and task-state information.

The Report Generator cannot independently declare the task complete.

---

## 6. Data Ownership Boundaries

Each component may consume data produced by other components, but ownership of authoritative records must remain clear.

| Data                               | Logical owner                     | Other components' permitted use                                            |
| ---------------------------------- | --------------------------------- | -------------------------------------------------------------------------- |
| Research request                   | Research Request Interface        | Orchestrator and planner may read validated inputs                         |
| Company identity                   | Company Identity Resolver         | Research components may reference the confirmed identifier                 |
| Research plan                      | Research Planner                  | Orchestrator coordinates execution against it                              |
| Source records                     | Source Acquisition                | Analysis and provenance components may reference sources                   |
| Extracted document content         | Document Ingestion                | Retrieval and evidence processing may consume it                           |
| Evidence records                   | Evidence Repository and Retrieval | Analysis components may use returned evidence                              |
| Claim and citation mappings        | Provenance Manager                | Report assembly and validation may read and verify mappings                |
| Financial metrics and calculations | Financial Analysis                | Valuation and report components may consume validated outputs              |
| Business and industry findings     | Business and Industry Analysis    | Risk, valuation, thesis, and report components may consume them            |
| Risk register                      | Risk Analysis                     | Valuation, thesis, and report components may consume it                    |
| Valuation assumptions and outputs  | Valuation and Scenario Analysis   | Rating and report components may consume them                              |
| Thesis and rating output           | Thesis and Rating Analysis        | Report assembly and validation may consume it                              |
| Draft report                       | Report Assembly                   | Report Validation may inspect it                                           |
| Validation findings                | Report Validation                 | Orchestrator decides whether correction or finalization is permitted       |
| Task state and checkpoints         | Task State and Recovery           | Interface and orchestrator may read and update state through defined rules |
| Evaluation results                 | Evaluation and Experimentation    | Release decisions use the recorded results                                 |
| Security and deletion records      | Security and Data Governance      | Relevant components use them to enforce and audit required controls        |

A component must not silently overwrite another component's authoritative data. Corrections must preserve enough history to understand the change where auditability requires it.

---

## 7. AI and Deterministic Execution Boundaries

### 7.1 Deterministic Responsibilities

Use explicit rules and testable logic for:

* Input and document validation.
* Task state transitions.
* Retry limits and resource enforcement.
* Financial arithmetic.
* Formula-based metrics.
* Date, period, and unit validation.
* Evidence-reference integrity.
* Report schema validation.
* Collection access enforcement.
* Idempotency and duplicate-processing prevention.
* Evaluation metric computation.
* Mandatory release-gate checks.

### 7.2 AI-Assisted Responsibilities

AI-assisted reasoning may be used for:

* Research planning and follow-up selection.
* Qualitative business and industry interpretation.
* Risk identification.
* Evidence relevance and sufficiency assessment.
* Interpretation of conflicting disclosures.
* Thesis and antithesis development.
* Selection among permitted valuation approaches.
* Report synthesis.

AI-generated outputs must be constrained by explicit inputs, evidence requirements, and validation rules.

### 7.3 Combined Responsibilities

For work requiring both AI reasoning and deterministic validation:

* The AI-assisted stage proposes a finding or decision.
* The relevant component records the evidence and assumptions.
* Deterministic checks validate required structures and calculations.
* Provenance links the output to its supporting sources.
* Report Validation evaluates the final claim in context.

A language model must not be the sole authority for verifying its own factual or numerical correctness.

---

## 8. Security and Collection Isolation

### 8.1 Untrusted Source Content

All uploaded PDFs, retrieved pages, extracted text, and external content must be treated as untrusted data.

The system must:

* Keep source content separate from trusted instructions.
* Avoid executing instructions embedded in documents.
* Validate structured outputs before passing them to downstream components.
* Preserve evidence references for investigation.
* Record and test defined prompt-injection attacks.

### 8.2 Collection Isolation

Evidence retrieval and report access must respect the requested collection scope.

Required behavior:

* Each task operates within an explicit collection context.
* Retrieval returns only evidence permitted for that collection.
* Evidence references cannot be used to bypass collection boundaries.
* Isolation tests verify that one collection cannot expose another collection's evidence.
* Cross-collection access failures are treated as security failures.

The MVP does not require full multi-user authentication or enterprise role-based access control. Collection isolation is nevertheless mandatory and must not depend solely on the user interface.

### 8.3 Data Deletion

When deletion is requested:

* Identify the data associated with the deletion target.
* Remove the applicable stored report, source content, evidence, and derived records according to the defined deletion policy.
* Handle dependent records and references consistently.
* Record the deletion outcome without retaining unnecessary deleted content.
* Verify that deleted data is no longer accessible through supported retrieval paths.

Detailed retention semantics, backup handling, and deletion guarantees must be documented before implementation.

---

## 9. Component Failure Contract

Every component must expose enough information for the orchestrator and evaluation process to distinguish successful output from failure or limitation.

At minimum, a component outcome must communicate:

* Outcome status.
* Produced output or output reference, if any.
* Relevant evidence references.
* Warnings or limitations.
* Error category, when applicable.
* Whether retry is safe.
* Whether partial work was preserved.
* Relevant timing or resource information.

The final contract schema will be defined in `09_contracts.md`. This section specifies the required behavior, not the final serialization format.

A component must not:

* Hide exceptions as empty successful results.
* Replace missing evidence with fabricated content.
* Retry indefinitely.
* Report completion when required postconditions have not been met.

---

## 10. Decisions Deferred to Architecture and ADRs

The following decisions remain open:

* Which logical components should share a process or deployment unit.
* Which components require independent background execution.
* The final component and service topology.
* Communication and data-exchange protocols.
* Persistence ownership and storage technology.
* Evidence indexing and retrieval strategy.
* Model selection and model invocation boundaries.
* Local versus hosted embedding generation.
* Hybrid versus vector-only retrieval.
* Reranking and query-rewriting strategies.
* Checkpoint and retry implementation.
* Observability and evaluation tooling.
* Valuation methodology and rating thresholds.
* Detailed deletion and retention semantics.

Each decision must be made in the relevant architecture document or recorded in an ADR when appropriate. The implementation must not introduce these decisions implicitly without documenting their impact.

---

## 11. Completion Criteria

The component-boundary design is complete when:

* Every major workflow has clear component ownership.
* Each component has defined responsibilities, inputs, outputs, and prohibited behavior.
* Dependencies between components are explicit.
* Evidence and provenance ownership is clear.
* Financial calculation responsibility is separated from qualitative interpretation.
* Report generation is separated from report validation.
* Overall task completion is controlled by the orchestrator.
* Task-state and recovery responsibilities are explicit.
* Security and collection isolation are enforced across relevant boundaries.
* Failure and limitation outcomes can be propagated without being mistaken for success.
* Technology decisions remain deferred to the appropriate architecture documents and ADRs.
* The design is consistent with `01_problem.md`, `02_requirements.md`, `03_scope.md`, `04_success_criteria.md`, `05_workflows.md`, and `06_responsibilities.md`.
