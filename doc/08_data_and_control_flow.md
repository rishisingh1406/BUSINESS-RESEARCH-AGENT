# Data and Control Flow

## 1. Purpose

This document defines how information and control move through the Equity / Business Research Agent.

It describes:

* The end-to-end research execution flow.
* How information moves between logical components.
* How research evidence is collected, processed, and validated.
* How missing information and conflicting evidence trigger bounded follow-up research.
* How financial analysis, valuation, and investment ratings consume upstream results.
* How task state, cancellation, retries, and recovery work.
* How report validation determines whether a task can be completed.
* How security and collection isolation are maintained throughout execution.

This document defines logical data movement and control behavior. It does not finalize implementation technologies, APIs, database schemas, message formats, or deployment topology.

---

## 2. Core Principles

### 2.1 Evidence Must Flow With Findings

Research findings must retain references to the evidence supporting them.

A material factual claim must be traceable through:

`Report Claim → Finding → Evidence Reference → Extracted Content → Source Document → Source Location`

A calculated claim must additionally retain:

* Input values.
* Units and reporting periods.
* Formula or calculation method.
* Rounding rules where relevant.
* Source references for the inputs.
* Calculation output.

### 2.2 Control Flow and Data Flow Are Different

**Data flow** describes how information moves between components.

**Control flow** describes which component runs next, which condition determines the next action, and when execution stops.

For example:

* Data flow: Financial Analysis returns calculated margins.
* Control flow: The Research Orchestrator determines that the valuation stage can begin because the required financial outputs are available.

These flows must be documented separately even when they occur together.

### 2.3 Every Stage Has an Explicit Outcome

A component must return an identifiable outcome, such as:

* Success.
* Partial success with limitations.
* Recoverable failure.
* Non-recoverable failure.
* Blocked due to missing prerequisites.
* Cancelled.

An empty result must not automatically be interpreted as a successful result.

### 2.4 Research Must Be Bounded

Research may repeat when material information is missing or conflicting, but it must respect configured limits for:

* Total runtime.
* Research steps.
* Retries per stage.
* External API calls.
* Queue capacity.

Reaching a limit must produce an explicit outcome rather than an indefinite loop.

### 2.5 Completed Work Should Survive Recoverable Failures

Where safe, completed outputs and valid checkpoints must be preserved.

Recovery must not silently duplicate work, corrupt task state, or discard completed research.

### 2.6 Untrusted Content Must Remain Untrusted

Uploaded documents and external source content are evidence, not trusted instructions.

Security boundaries must remain active during ingestion, retrieval, analysis, report generation, and recovery.

---

## 3. High-Level End-to-End Flow

The main research flow is:

```text
User
  |
  v
Research Request Interface
  |
  v
Research Orchestrator
  |
  v
Company Identity Resolution
  |
  v
Research Planning
  |
  v
Source Acquisition and Document Ingestion
  |
  v
Evidence Repository and Retrieval
  |
  +---------------------+----------------------+
  |                     |                      |
  v                     v                      v
Financial Analysis   Business/Industry     Risk Analysis
  |                     Analysis               |
  +---------------------+----------------------+
                        |
                        v
              Information-Gap and
                Conflict Assessment
                        |
                        v
             Valuation and Scenarios
                        |
                        v
              Thesis and Rating Analysis
                        |
                        v
                  Report Assembly
                        |
                        v
                 Report Validation
                        |
              +---------+---------+
              |                   |
           Valid              Invalid
              |                   |
              v                   v
       Finalize Task       Correct / Reassess
              |                   |
              v                   +----> Bounded follow-up
         User Report
```

The diagram represents logical stages, not a requirement that all components run sequentially or as separate services.

Independent analysis stages may execute in parallel when their inputs are available. Final synthesis must wait for the required outputs or explicitly disclose missing ones.

---

## 4. WF-01 — Research Request and Task Creation

### 4.1 Input

The user supplies:

* Company name or ticker.
* Optional annual report PDF.
* Applicable reference date.
* Supported research configuration, if exposed.

### 4.2 Data Flow

1. The Research Request Interface receives the request.
2. Basic input validation checks required fields and supported limits.
3. If a PDF is supplied, the file is registered for validation and ingestion.
4. The Research Orchestrator creates a unique task identifier.
5. Task State and Recovery records the initial state and timestamps.
6. The interface returns the task identifier and current status.

### 4.3 Control Flow

* Invalid request: reject before research execution.
* Valid request: create the task and proceed.
* Invalid or oversized PDF: record the upload failure and apply the documented file-handling policy.
* Task creation failure: return an explicit failure without claiming that research has started.

### 4.4 Required State

The task record must distinguish:

* Request accepted.
* Task queued.
* Task running.
* Task completed.
* Task completed with limitations, where supported.
* Task failed.
* Task cancelled.

The exact state schema and transitions will be defined in `09_contracts.md`.

---

## 5. WF-02 — Company Identity Resolution

### 5.1 Data Flow

```text
Company Name / Ticker
        |
        v
Company Identity Resolver
        |
        v
Resolved Company Identity
        |
        v
Research Planner
```

The resolver returns the company identifier and resolution status.

### 5.2 Control Flow

* Identity confirmed: continue to research planning.
* Multiple plausible matches: request clarification.
* No reliable match: stop company-specific research and report the problem.
* Conflicting company metadata: preserve the conflict and avoid selecting an unsupported match.

### 5.3 Invariants

* Every research task must have a confirmed company identity before company-specific findings are produced.
* Evidence from a different company must not be silently reused.
* The confirmed identity must remain consistent across source acquisition, analysis, valuation, and reporting.

---

## 6. WF-03 — Research Planning

### 6.1 Data Flow

The Research Planner receives:

* Confirmed company identity.
* Required report sections.
* Existing source inventory.
* Available uploaded documents.
* Research constraints and resource limits.

It produces:

* A research plan.
* Required information categories.
* Evidence requirements.
* Stage dependencies.
* Initial and follow-up research tasks.

### 6.2 Control Flow

1. The Research Orchestrator requests a research plan.
2. The planner identifies the information needed for the report.
3. The orchestrator validates that the plan is within the supported scope.
4. The task enters source acquisition and ingestion.
5. The plan is updated only when new evidence, conflicts, or missing information justify additional work.

### 6.3 Invariants

* The plan must remain within the defined project scope.
* The system must not expand into unrestricted research.
* Follow-up tasks must have an identifiable purpose and bounded cost.
* The plan must distinguish required information from optional supporting information.

---

## 7. WF-04 — Source Acquisition and Document Ingestion

### 7.1 Data Flow

```text
Research Plan
     |
     v
Source Acquisition
     |
     +------------------------+
     |                        |
     v                        v
Retrieved Web/Data       Retrieved Documents
                              |
                              v
                       Document Ingestion
                              |
                              v
                     Normalized Content
                              |
                              v
                 Evidence Repository
```

An uploaded annual report follows the ingestion path after passing the applicable input checks.

### 7.2 Source Metadata

Each acquired source should preserve, where available:

* Stable source identifier.
* Source name and origin.
* Document title or data description.
* Publication date.
* Reporting period.
* Retrieval timestamp.
* Document version or URL.
* Source type.
* Relevant extraction or collection warnings.

### 7.3 Document Processing

For PDF documents:

1. Validate file type, file size, and page count.
2. Check document integrity.
3. Determine whether text extraction or OCR is needed.
4. Extract content.
5. Preserve page and location references.
6. Normalize the content.
7. assess extraction quality, particularly for financial figures and tables.
8. Record processing status.
9. Make successfully processed content available for retrieval.

### 7.4 Control Flow

* Valid document: process it.
* Duplicate document: apply idempotent behavior and avoid duplicate records.
* Corrupt document: reject or quarantine it.
* Extraction failure: record the failure and preserve any safe partial output if policy permits.
* Low-confidence OCR: flag affected content and prevent it from being treated as fully reliable.
* Source unavailable: record the gap and continue with other permitted sources when possible.

### 7.5 Invariants

* Source identity and document location metadata must be preserved.
* A document must not be marked fully processed before required processing succeeds.
* Extraction quality must not be confused with factual correctness.
* Failure to obtain one source must not automatically invalidate all other usable evidence.

---

## 8. WF-05 — Evidence Retrieval

### 8.1 Data Flow

```text
Research Question
       |
       v
Evidence Retrieval
       |
       v
Candidate Evidence
       |
       v
Evidence and Relevance Assessment
       |
       +-------------------------+
       |                         |
       v                         v
Useful Evidence              No Useful Evidence
       |                         |
       v                         v
Analysis Stage             Gap Assessment
```

Retrieved evidence must include stable source and location references.

### 8.2 Control Flow

* Relevant evidence found: return it to the requesting analysis responsibility.
* No useful evidence found: record an evidence gap.
* Evidence is topically relevant but does not support the requested claim: do not treat it as sufficient support.
* Retrieval fails: report a retrieval failure distinct from a legitimate empty result.

### 8.3 Invariants

* Retrieval must respect collection scope.
* Retrieved passages must retain source references.
* Relevance is not equivalent to claim support.
* An empty retrieval result must not cause the system to fabricate an answer.

---

## 9. WF-06 — Evidence Provenance and Claim Traceability

### 9.1 Data Flow

Every material finding carries evidence references into downstream analysis.

```text
Source Document
      |
      v
Extracted Content + Location
      |
      v
Evidence Record
      |
      v
Analysis Finding
      |
      v
Claim-to-Evidence Mapping
      |
      v
Report Claim + Citation
```

Calculated findings must also reference the recorded calculation and its source inputs.

### 9.2 Control Flow

1. An analysis component proposes a finding.
2. The Provenance Manager records its evidence references and origin.
3. Missing or invalid references are flagged.
4. Unsupported material claims are returned for correction, qualification, or removal.
5. Report Validation checks that the citation actually supports the claim.

### 9.3 Invariants

* A citation must identify the source used.
* Citation presence alone is not proof of support.
* Material claims must not lose provenance during report synthesis.
* Calculated values must be traceable to their inputs and formulas.
* The system must not create a source reference for evidence that was never obtained.

---

## 10. WF-07 — Financial Analysis

### 10.1 Data Flow

```text
Financial Statements / Records
              |
              v
      Data Normalization
              |
              v
      Period and Unit Checks
              |
              v
      Deterministic Calculations
              |
              v
       Metric Validation
              |
              v
      Financial Findings
              |
              v
    Provenance and Report
```

### 10.2 Processing Rules

Financial data must preserve:

* Reporting period.
* Currency and units.
* Consolidated or standalone basis where relevant.
* Source reference.
* Whether the value is reported, calculated, estimated, or unavailable.

### 10.3 Control Flow

* Valid input data: calculate the required metrics.
* Missing input: mark the metric unavailable or apply a documented alternative method.
* Incompatible units or periods: block the comparison until corrected or explicitly qualified.
* Invalid calculation: return an error and do not pass the invalid result downstream as valid.
* Conflicting source values: send the conflict for assessment.

### 10.4 Invariants

* Formula-based calculations must be deterministic and testable.
* Missing values must not be silently replaced with invented values.
* Metrics must not be compared without accounting for material differences in units, periods, and definitions.
* Calculation provenance must remain available to valuation and report validation.

---

## 11. WF-08 — Business, Industry, and Risk Analysis

### 11.1 Data Flow

These analysis stages consume:

* Confirmed company identity.
* Retrieved source evidence.
* Company disclosures.
* Industry and competitor information.
* Validated financial findings where relevant.

They produce:

* Business model findings.
* Industry and competitor analysis.
* Management and governance findings.
* Risk records.
* Supporting and opposing evidence.
* Missing-information records.

### 11.2 Control Flow

Independent analyses may proceed in parallel when their required inputs are available.

When one analysis depends on another:

1. The dependent stage waits for the required input.
2. The orchestrator determines whether a partial result is acceptable.
3. Missing prerequisites are recorded.
4. Any material limitation is carried into later stages and the final report.

### 11.3 Invariants

* Qualitative interpretations must be distinguishable from reported facts.
* Material risks and counterevidence must remain available to the thesis and rating stages.
* Competitor comparisons must explain material comparability limitations.
* Missing evidence must be disclosed rather than concealed.

---

## 12. WF-09 — Missing Information and Conflict Resolution

### 12.1 Missing Information Flow

```text
Required Information
        |
        v
Evidence Assessment
        |
        v
Information Missing?
        |
    +---+---+
    |       |
   No      Yes
    |       |
    v       v
 Continue  Assess Materiality
              |
              v
       Follow-up Justified?
          |         |
         Yes        No
          |         |
          v         v
   Bounded Research  Record Gap
          |
          v
   Reassess Evidence
```

### 12.2 Conflict Flow

```text
Conflicting Values or Claims
             |
             v
      Compare Sources
             |
             v
 Compare Periods / Units /
 Definitions / Context
             |
             v
     Conflict Explained?
          |        |
         Yes       No
          |        |
          v        v
 Record Rationale  Preserve Conflict
          |        |
          +----+---+
               |
               v
      Disclose Material Impact
```

### 12.3 Control Rules

For each material gap or conflict:

1. Record the unresolved question.
2. Determine its impact on the report, valuation, or rating.
3. Identify the evidence needed to resolve it.
4. Decide whether follow-up is justified.
5. Check remaining runtime, research-step, retry, and API-call budgets.
6. Execute bounded follow-up if permitted.
7. Reassess the evidence.
8. Record the final resolution or unresolved status.

### 12.4 Invariants

* Conflicting values must not be silently averaged or replaced.
* Differences caused by reporting periods, units, or definitions must be distinguished from genuine contradictions.
* An unresolved material conflict must be visible in the report.
* A missing input must not be represented as a verified zero.
* If follow-up is not possible, the limitation must be explicit.

---

## 13. WF-10 — Valuation and Scenario Analysis

### 13.1 Data Flow

```text
Validated Financial Findings
             |
             +--------------------+
             |                    |
             v                    v
    Business and Risk       Market-Price Data
       Findings                    |
             |                    |
             +---------+----------+
                       |
                       v
              Valuation Method
                       |
                       v
           Inputs and Assumptions
                       |
                       v
          Deterministic Calculations
                       |
                       v
            Scenario and Sensitivity
                       |
                       v
             Valuation Output
```

### 13.2 Control Flow

* Required inputs available: perform the documented valuation analysis.
* Some inputs missing: determine whether a defensible alternative method is available.
* Valuation possible only with weak assumptions: label the result as highly uncertain or not decision-grade.
* No meaningful valuation supported: preserve the required valuation outcome as unavailable or insufficiently supported, with an explanation.

The project scope requires an attempt to estimate a valuation range. That requirement does not justify fabricating inputs or presenting an unsupported estimate as reliable.

### 13.3 Invariants

* Assumptions must be explicit.
* Calculation outputs must be reproducible.
* Scenario assumptions must be internally consistent.
* Material sensitivities must be disclosed.
* Market-price references must be dated.
* Valuation uncertainty must flow into the rating and final report.

---

## 14. WF-11 — Thesis, Antithesis, and Rating

### 14.1 Data Flow

The rating stage receives:

* Validated financial findings.
* Business and industry findings.
* Risk analysis.
* Valuation range and scenarios.
* Evidence and provenance records.
* Documented rating methodology.
* Material conflicts and information gaps.

It produces:

* Bull case.
* Bear case.
* Main investment drivers.
* Important assumptions.
* Rating or insufficient-evidence outcome.
* Conditions that could change the conclusion.

### 14.2 Control Flow

1. Assemble the positive and negative evidence.
2. Identify material assumptions and unresolved issues.
3. Assess whether the rating methodology's evidence requirements are satisfied.
4. Apply the documented methodology when permitted.
5. Return insufficient evidence if required conditions are not met.
6. Pass the rating rationale and its evidence references to report assembly.

### 14.3 Invariants

* The rating must follow a documented methodology.
* The rating stage must not invent thresholds during execution.
* Material counterevidence must be considered.
* A confident rating must not be produced when mandatory evidence requirements fail.
* A rating is an analytical output, not a personalized instruction to buy or sell.

---

## 15. WF-12 — Report Assembly and Validation

### 15.1 Data Flow

```text
Analysis Findings
       |
       v
Evidence and Provenance
       |
       v
Report Assembly
       |
       v
Draft Report
       |
       v
Report Validation
       |
       +----------------------+
       |                      |
       v                      v
Mandatory Checks Pass    Mandatory Checks Fail
       |                      |
       v                      v
Finalize if all gates    Correct / Reassess /
are satisfied            Record permitted limitation
       |                      |
       v                      +----> Revalidation
Final Report
```

### 15.2 Required Report Content

The report should include:

1. Executive summary.
2. Company history and business model.
3. Management and governance.
4. Industry analysis.
5. Historical financial and fundamental analysis.
6. Competitor analysis.
7. Material risks.
8. Valuation range, assumptions, and sensitivities.
9. Bull, base, and bear scenarios.
10. Historical price trends and technical indicators where data is available.
11. Investment thesis and antithesis.
12. Buy/hold/sell rating or insufficient-evidence outcome.
13. Missing information, conflicts, and limitations.
14. Sources and evidence references.

### 15.3 Validation Rules

Validation must check:

* Required section coverage.
* Citation integrity and claim support.
* Financial calculation correctness.
* Consistency between financial findings and valuation.
* Consistency between risks, scenarios, thesis, and rating.
* Disclosure of material conflicts and missing information.
* Absence of critical unsupported claims.
* Accurate task status and completion metadata.

### 15.4 Control Flow

* Validation passes: continue to finalization if every other mandatory completion condition is satisfied.
* Correctable issue: return findings for correction and revalidate.
* Material issue cannot be resolved: use an explicitly limited outcome only where the documented policy permits it.
* Critical release failure: block successful completion until corrected and regression-tested.

The system must not enter an endless report-revision loop. Corrections and revalidation must respect the configured execution limits.

---

## 16. WF-13 — Task State and Progress

### 16.1 Logical State Flow

```text
CREATED
   |
   v
QUEUED
   |
   v
RUNNING
   |
   +-----------------------------+
   |              |              |
   v              v              v
COMPLETED       FAILED        CANCELLED
```

Additional internal stage states may include:

* Pending.
* Running.
* Succeeded.
* Partially succeeded.
* Blocked.
* Retrying.
* Failed.
* Skipped with a documented reason.

The final task-state schema and allowed transitions will be specified in `09_contracts.md`.

### 16.2 State Ownership

Task State and Recovery owns the authoritative task lifecycle record.

The Research Orchestrator requests state transitions according to defined rules. Components report their stage outcomes and must not independently declare the overall task complete.

### 16.3 Progress Data

The interface should expose:

* Task identifier.
* Current task status.
* Current stage.
* Completed and pending stages where available.
* Relevant warnings or limitations.
* Failure information where applicable.
* Final report reference when available.

A percentage must not be displayed unless it can be calculated from a meaningful and defined measure of progress.

### 16.4 Invariants

* Every task has a unique identifier.
* State transitions follow the permitted lifecycle.
* Terminal states reflect the actual outcome.
* A completed task has a validated report and satisfies mandatory completion requirements.
* A failed task must not be represented as successfully completed.

---

## 17. WF-14 — Queueing, Cancellation, and Recovery

### 17.1 Queueing

The MVP supports one active research job at a time.

Additional valid jobs may be queued up to a configurable queue limit.

Control flow:

1. Validate the request.
2. Check current execution and queue capacity.
3. Start the job if execution capacity is available.
4. Queue it if capacity is occupied and queue space remains.
5. Reject it with an explicit response if the queue is full.

### 17.2 Cancellation

A cancellation request must be handled according to task state.

* Queued task: remove it from pending execution and mark it cancelled.
* Running task: request a safe stop.
* Completed task: retain the completed outcome; cancellation must not retroactively change it.
* Failed task: preserve the failure record.

For a running task:

1. Stop scheduling new research work.
2. Allow safe cleanup of in-progress work where feasible.
3. Preserve valid completed outputs and checkpoints.
4. Record the cancellation outcome.
5. Expose the final state.

### 17.3 Recovery

When execution is interrupted:

1. Detect or record the interruption.
2. Inspect the last valid checkpoint.
3. Determine whether the stage is safe to retry.
4. Check whether retry and runtime budgets remain.
5. Resume from a valid checkpoint or restart the affected stage safely.
6. Prevent duplicate records or repeated side effects.
7. Record recovery attempts and their outcomes.

### 17.4 Invariants

* Retries must be bounded.
* Duplicate processing must not corrupt results.
* Recovery must preserve valid completed work where possible.
* An unrecoverable interruption must result in an explicit failure or incomplete outcome.
* A task must not appear completed if required work was interrupted.

---

## 18. WF-15 — Prompt Injection and Untrusted Documents

### 18.1 Threat Path

```text
Uploaded PDF / Retrieved Source
              |
              v
      Document Ingestion
              |
              v
       Untrusted Content
              |
              v
       Evidence Retrieval
              |
              v
      AI-Assisted Analysis
              |
              v
    Structured Output Validation
              |
              v
      Evidence and Report Checks
```

### 18.2 Security Behavior

The system must:

* Treat source documents as untrusted content.
* Keep document text separate from trusted system instructions.
* Prevent document-embedded instructions from authorizing tools or changing system policy.
* Validate AI outputs before they enter downstream stages.
* Maintain evidence provenance for suspicious content.
* Test the defined prompt-injection cases.
* Record whether the attack was blocked, partially successful, or successful.

### 18.3 Evaluation Requirements

The project must demonstrate:

1. The defined attack path in an unprotected baseline.
2. The behavior of the defended configuration.
3. Results for the three defined poisoned-document attacks.
4. Regression results after mitigation.

Passing these tests demonstrates performance against the defined test set, not universal immunity to prompt injection.

### 18.4 Invariants

* Untrusted documents cannot change collection permissions.
* Untrusted documents cannot override trusted instructions.
* A model's claim that an attack was blocked is not sufficient evidence that the attack failed.
* Security failures must remain visible to the evaluation and release process.

---

## 19. WF-16 — Evaluation and Experiments

### 19.1 Benchmark Flow

```text
Versioned Evaluation Dataset
             |
             v
      Execute Research Cases
             |
             v
     Preserve Per-Case Outputs
             |
             v
     Calculate Evaluation Metrics
             |
             v
      Category-Level Analysis
             |
             v
     Compare Against Gates
             |
             v
       Record Release Decision
```

### 19.2 Benchmark Composition

The benchmark contains 40 questions:

| Category                        |  Count |
| ------------------------------- | -----: |
| Factual                         |     15 |
| Multi-hop                       |     15 |
| Unanswerable                    |      5 |
| Adversarial / poisoned-document |      5 |
| **Total**                       | **40** |

Results must be reported by category and as raw counts as well as percentages. The small benchmark must not be presented as proof of statistical certainty.

### 19.3 Required Measurements

Evaluate:

* Evidence faithfulness.
* Citation support.
* Factual correctness.
* Relevant source retrieval in the top three results.
* Precision@k, Recall@k, and MRR where applicable.
* Deterministic financial calculation correctness.
* Valuation and rating quality.
* Unanswerable-question handling.
* Latency and variable cost.
* Critical failures and security behavior.

### 19.4 Required Experiments

Run and document:

1. Hybrid retrieval versus vector-only retrieval.
2. Reranking enabled versus disabled.
3. Query rewriting enabled versus disabled.

Each experiment must preserve:

* Dataset version.
* Configuration and conditions.
* Quality results.
* Latency and cost.
* Failure cases.
* Limitations.
* Engineering conclusion.
* Relevant ADR updates.

### 19.5 Control Rules

* Use comparable conditions for A/B comparisons.
* Preserve a committed baseline.
* Record negative results.
* Do not change release thresholds after seeing results merely to obtain a pass.
* Block release when a mandatory gate fails.
* Require regression testing after critical fixes.

---

## 20. WF-17 — Collection Isolation

### 20.1 Data Flow

Every evidence retrieval and report-access request must include a defined collection context.

```text
Research Task
     |
     v
Collection Context
     |
     v
Evidence Retrieval / Report Access
     |
     v
Collection Boundary Check
     |
     +-----------------------+
     |                       |
     v                       v
Permitted Access         Denied Access
     |                       |
     v                       v
Return Allowed Data      Record Security Failure
```

### 20.2 Control Rules

* The collection context must be explicit.
* Retrieval must not cross collection boundaries.
* A supplied evidence identifier must not bypass access checks.
* Access violations must be recorded and tested.
* Isolation must be enforced outside model-generated reasoning.

### 20.3 Required Tests

The defined collection isolation suite must pass completely, with zero cross-collection evidence leaks.

The MVP's collection isolation requirement does not imply full multi-user authentication or enterprise access control.

---

## 21. WF-18 — Data Deletion

### 21.1 Control Flow

1. Receive a valid deletion request.
2. Identify the data covered by the request.
3. Determine dependent documents, evidence records, derived findings, reports, and task metadata.
4. Apply the documented deletion policy.
5. Remove or invalidate the applicable records and references.
6. Verify that deleted content is no longer accessible through supported retrieval paths.
7. Record the deletion outcome without retaining unnecessary deleted content.

### 21.2 Invariants

* Deletion must not leave stale references that expose deleted content.
* Derived data covered by the deletion policy must be handled consistently.
* Deletion failures must be explicit.
* The system must not claim complete deletion if the required checks fail.

Backup retention, legal retention requirements, and the exact deletion guarantees must be defined before implementation.

---

## 22. Cross-Workflow Invariants

The following rules apply to every workflow.

### Evidence

* Material claims must have supporting evidence or an explicit limitation.
* Evidence references must remain traceable.
* Conflicting source values must not be silently discarded.
* Missing information must not be fabricated.

### Calculations

* Financial arithmetic must be reproducible.
* Calculation inputs, units, periods, and formulas must be recorded.
* Invalid calculations must not be treated as valid outputs.

### Control

* Research and retries must be bounded.
* Each stage must report an explicit outcome.
* Task state must reflect the actual execution result.
* The orchestrator owns final task completion.

### Security

* Source content remains untrusted.
* Collection boundaries must be enforced.
* Security failures must be observable and testable.

### Reporting

* The final report must preserve citations, assumptions, conflicts, and limitations.
* Report assembly must not bypass validation.
* Mandatory release failures must not be hidden by aggregate quality scores.

---

## 23. Open Decisions for Later Design

This document does not finalize:

* API endpoint definitions.
* Request and response schemas.
* Exact task-state enum values and transition rules.
* Persistent record schemas.
* Queue and checkpoint implementation.
* Component communication mechanisms.
* Retrieval and indexing algorithms.
* Model invocation and tool-execution contracts.
* Valuation formulas and rating thresholds.
* Detailed deletion and retention behavior.
* Deployment topology and observability implementation.

These decisions belong in `09_contracts.md`, architecture documentation, and relevant ADRs.

---

## 24. Completion Criteria

This document is complete when:

* The normal research flow is documented end to end.
* Data flow and control flow are distinguished.
* Source ingestion, retrieval, provenance, and analysis flows are defined.
* Missing-information and conflict-resolution loops are bounded.
* Financial calculations and valuation have explicit data dependencies.
* Report validation controls final completion.
* Task state, queueing, cancellation, and recovery are defined.
* Prompt-injection, collection-isolation, and deletion paths are documented.
* Benchmark evaluation and required experiments are represented.
* Every critical workflow has defined failure behavior.

* The document remains consistent with `01_problem.md`, `02_requirements.md`, `03_scope.md`, `04_success_criteria.md`, `05_workflows.md`, `06_responsibilities.md`, and `07_component_boundaries.md`.
