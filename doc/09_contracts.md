# Component Contracts

## 1. Purpose

This document defines the data contracts exchanged between the logical components of the Equity / Business Research Agent.

It specifies:

* Required and optional fields.
* Input and output structures.
* Identifiers and relationships between records.
* Task and stage status values.
* Error categories and recovery behavior.
* Evidence and citation provenance.
* Financial calculation records.
* Report validation outcomes.
* Contract-level validation rules.

These contracts establish what components exchange, not how those contracts are implemented.

The contracts do not mandate a specific programming language, framework, database, serialization format, or communication protocol. Those decisions will be made during implementation and architecture design.

---

## 2. Contract Design Principles

### 2.1 Explicit Schemas

Every component boundary must have a defined input and output contract.

Required fields must not be silently omitted. Optional fields must have documented semantics.

### 2.2 Stable Identifiers

Records that need to be referenced by other components must have stable identifiers.

Identifiers must not depend on display names or mutable descriptions.

### 2.3 Explicit Outcomes

Every operation must distinguish success, partial success, failure, and blocked execution where relevant.

An empty result is not automatically a successful result.

### 2.4 Evidence Preservation

Research findings must preserve evidence references and relevant source metadata.

Material claims must not lose provenance during analysis or report assembly.

### 2.5 Reproducible Calculations

Financial calculations must retain sufficient inputs and metadata to reproduce and verify their outputs.

### 2.6 Bounded Execution

Contracts must carry or reference the applicable runtime, retry, research-step, and external-call limits.

### 2.7 Backward-Compatible Evolution

Changes to contracts must be reviewed for their effect on existing components, stored records, evaluation results, and recovery behavior.

Breaking changes must be documented and tested before deployment.

---

## 3. Common Contract Conventions

### 3.1 Identifier Types

The following logical identifiers are used throughout the system:

| Identifier          | Purpose                            |
| ------------------- | ---------------------------------- |
| `task_id`           | Identifies one research task       |
| `company_id`        | Identifies the resolved company    |
| `collection_id`     | Identifies the research collection |
| `source_id`         | Identifies an acquired source      |
| `document_id`       | Identifies a processed document    |
| `evidence_id`       | Identifies an evidence record      |
| `finding_id`        | Identifies an analysis finding     |
| `calculation_id`    | Identifies a financial calculation |
| `report_id`         | Identifies a generated report      |
| `stage_id`          | Identifies a stage execution       |
| `evaluation_run_id` | Identifies an evaluation run       |
| `experiment_id`     | Identifies an experiment           |
| `error_id`          | Identifies a recorded error        |

Identifiers must be unique within their documented scope. A component must not assume that an identifier from one namespace is interchangeable with another.

### 3.2 Timestamps

Timestamps must:

* Use a consistent, documented representation.
* Include timezone information.
* Distinguish event time from source publication time and data reporting period.
* Avoid using a timestamp as a substitute for a reporting period.

### 3.3 Missing Values

Missing values must have explicit meaning.

The system must distinguish between:

* Unknown.
* Not available from sources.
* Not applicable.
* Not yet collected.
* Extraction failed.
* Conflicting values.
* Intentionally omitted.

A missing value must not silently become zero, an empty string, or a fabricated estimate.

### 3.4 Units and Periods

Financial and market data must include units and relevant time context.

Where applicable, record:

* Currency.
* Scale or unit.
* Reporting period.
* Fiscal year.
* Consolidated or standalone basis.
* Market-price reference date.
* Whether the value is reported, calculated, estimated, or inferred.

### 3.5 Contract Examples

The structures in this document are logical schemas, not final implementation-specific models.

The notation uses:

* `string`: text value.
* `number`: numeric value.
* `integer`: whole number.
* `boolean`: true or false.
* `array`: ordered collection.
* `object`: structured record.
* `nullable`: value may be absent or explicitly null according to the field's defined semantics.

Exact field types, serialization constraints, and schema validation rules must be implemented and tested during the contract implementation stage.

---

## 4. Research Request Contract

### 4.1 Purpose

Represents a request to research one Indian listed company.

### 4.2 Request Fields

| Field                        | Type             | Required | Description                                      |
| ---------------------------- | ---------------- | -------- | ------------------------------------------------ |
| `company_identifier`         | string           | Yes      | Company name or ticker supplied by the user      |
| `reference_date`             | date             | Yes      | Date against which the research should be framed |
| `collection_id`              | string           | Yes      | Research collection to use                       |
| `annual_report_document_ids` | array of strings | No       | References to uploaded annual reports            |
| `research_options`           | object           | No       | Supported configuration options                  |
| `request_metadata`           | object           | No       | Non-sensitive metadata needed for traceability   |

### 4.3 Validation Rules

* The company identifier must not be empty.
* The reference date must be valid.
* The request must identify a permitted collection.
* Only supported document types and configuration options are accepted.
* The task must remain within the single-company MVP scope.
* Unsupported options must be rejected or explicitly reported as unsupported.
* Client-supplied identifiers must not be trusted as proof of authorization.

### 4.4 Request Acceptance Output

| Field               | Type      | Description                     |
| ------------------- | --------- | ------------------------------- |
| `task_id`           | string    | Unique research task identifier |
| `status`            | string    | Initial task status             |
| `accepted_at`       | timestamp | Time the task was accepted      |
| `message`           | string    | Human-readable result           |
| `validation_errors` | array     | Validation issues, if any       |

A request acceptance response means the request was accepted, not that research has completed.

---

## 5. Company Identity Contract

### 5.1 Purpose

Represents the result of resolving the supplied company identifier.

### 5.2 Output Fields

| Field                  | Type             | Required    | Description                                |
| ---------------------- | ---------------- | ----------- | ------------------------------------------ |
| `company_id`           | string           | Conditional | Stable identifier for the resolved company |
| `company_name`         | string           | Conditional | Official or best-supported company name    |
| `ticker`               | string           | Conditional | Relevant listed ticker                     |
| `exchange`             | string           | Conditional | Relevant listing exchange                  |
| `country`              | string           | Yes         | Country of listing                         |
| `resolution_status`    | string           | Yes         | Resolution outcome                         |
| `source_references`    | array of strings | No          | Evidence supporting the match              |
| `clarification_reason` | string           | No          | Why clarification is needed                |

### 5.3 Resolution Status Values

* `confirmed`
* `ambiguous`
* `not_found`
* `failed`

### 5.4 Invariants

* Company-specific research may proceed only after successful identity confirmation.
* An ambiguous match must not be treated as confirmed.
* The resolved identity must remain consistent throughout the task.
* If a company cannot be identified reliably, the task must stop or wait for clarification.

---

## 6. Research Plan Contract

### 6.1 Purpose

Defines the bounded research tasks needed to generate the report.

### 6.2 Plan Fields

| Field                   | Type             | Description                        |
| ----------------------- | ---------------- | ---------------------------------- |
| `task_id`               | string           | Parent research task               |
| `plan_version`          | integer          | Version of the plan                |
| `created_at`            | timestamp        | Plan creation time                 |
| `research_tasks`        | array            | Planned research activities        |
| `required_sections`     | array of strings | Mandatory report sections          |
| `resource_limits`       | object           | Applicable execution limits        |
| `completion_conditions` | array            | Conditions required for completion |

### 6.3 Research Task Fields

Each research task must include:

| Field                   | Type             | Description                            |
| ----------------------- | ---------------- | -------------------------------------- |
| `research_task_id`      | string           | Unique task-within-plan identifier     |
| `category`              | string           | Research category                      |
| `objective`             | string           | Question or information objective      |
| `required`              | boolean          | Whether the task is mandatory          |
| `dependencies`          | array of strings | Prerequisite research-task identifiers |
| `evidence_requirements` | array            | Required evidence characteristics      |
| `status`                | string           | Current research-task status           |
| `limitation_reason`     | string           | Explanation if blocked or incomplete   |

### 6.4 Research Task Status Values

* `pending`
* `running`
* `completed`
* `partially_completed`
* `blocked`
* `failed`
* `skipped`

A task may be marked `skipped` only when the reason is recorded and the skip is permitted by the scope and completion policy.

---

## 7. Source Record Contract

### 7.1 Purpose

Identifies an acquired source and preserves the metadata needed to assess its relevance and authority.

### 7.2 Fields

| Field              | Type              | Description                                   |
| ------------------ | ----------------- | --------------------------------------------- |
| `source_id`        | string            | Stable source identifier                      |
| `source_type`      | string            | Source category                               |
| `title`            | string            | Source title or descriptive label             |
| `origin`           | string            | URL, publisher, or source origin              |
| `publisher`        | string            | Publisher or issuing organization, when known |
| `published_at`     | timestamp or null | Publication timestamp when available          |
| `retrieved_at`     | timestamp         | Retrieval timestamp                           |
| `reporting_period` | string or null    | Financial or reporting period when applicable |
| `document_id`      | string or null    | Associated document, if applicable            |
| `authority_notes`  | string or null    | Notes supporting source-quality assessment    |
| `collection_id`    | string            | Collection that owns the source record        |
| `retrieval_status` | string            | Acquisition outcome                           |
| `limitations`      | array of strings  | Known source limitations                      |

### 7.3 Source Types

The initial logical categories are:

* `official_filing`
* `annual_report`
* `company_website`
* `financial_data`
* `market_price_data`
* `industry_source`
* `competitor_source`
* `other_public_source`
* `user_uploaded_document`

The exact taxonomy may be expanded when required, but categories must retain consistent meaning.

### 7.4 Retrieval Status Values

* `retrieved`
* `partially_retrieved`
* `unavailable`
* `failed`

A source record must not imply that its contents have been factually validated merely because retrieval succeeded.

---

## 8. Document Ingestion Contract

### 8.1 Purpose

Represents the processing state and output of an uploaded or acquired document.

### 8.2 Input Fields

| Field               | Type            | Description                                   |
| ------------------- | --------------- | --------------------------------------------- |
| `document_id`       | string          | Stable document identifier                    |
| `source_id`         | string          | Source associated with the document           |
| `collection_id`     | string          | Owning collection                             |
| `filename`          | string          | Original or normalized filename               |
| `content_type`      | string          | Detected content type                         |
| `file_size_bytes`   | integer         | File size                                     |
| `page_count`        | integer or null | Page count when known                         |
| `content_hash`      | string          | Content identity used for duplicate detection |
| `ingestion_options` | object          | Supported extraction configuration            |

### 8.3 Output Fields

| Field                  | Type             | Description                    |
| ---------------------- | ---------------- | ------------------------------ |
| `document_id`          | string           | Document identifier            |
| `ingestion_status`     | string           | Processing outcome             |
| `extraction_method`    | string           | Extraction approach used       |
| `extracted_page_count` | integer          | Number of pages processed      |
| `extraction_quality`   | object           | Extraction quality indicators  |
| `evidence_record_ids`  | array of strings | Created evidence references    |
| `warnings`             | array of strings | Quality or processing warnings |
| `error`                | object or null   | Failure details                |

### 8.4 Ingestion Status Values

* `uploaded`
* `queued`
* `processing`
* `indexed`
* `failed`
* `quarantined`

### 8.5 Validation Rules

* The file must satisfy configured type, size, and page-count limits.
* The content hash must be used consistently for duplicate detection.
* A duplicate upload must not create unintended duplicate evidence records.
* OCR-derived content must be distinguishable from directly extracted text.
* Low-quality extraction must be explicitly flagged.
* A quarantined document must not be treated as a normal searchable document.
* Source and page metadata must be preserved wherever available.

---

## 9. Evidence Record Contract

### 9.1 Purpose

Represents a retrievable unit of source content that can support research findings.

### 9.2 Fields

| Field                | Type             | Description                                  |
| -------------------- | ---------------- | -------------------------------------------- |
| `evidence_id`        | string           | Stable evidence identifier                   |
| `source_id`          | string           | Originating source                           |
| `document_id`        | string or null   | Originating document, if applicable          |
| `collection_id`      | string           | Owning collection                            |
| `content`            | string           | Extracted evidence content                   |
| `page_number`        | integer or null  | Source page number                           |
| `location_reference` | string or null   | Section, table, paragraph, or other location |
| `reporting_period`   | string or null   | Relevant reporting period                    |
| `content_hash`       | string           | Content identity                             |
| `extraction_method`  | string           | How content was extracted                    |
| `quality_flags`      | array of strings | Extraction or source-quality warnings        |
| `created_at`         | timestamp        | Evidence creation time                       |

### 9.3 Rules

* Every evidence record must reference its source.
* Document-derived evidence must reference its originating document.
* Page numbers must use a consistent convention and must not be confused with printed page labels.
* Extracted content must not be silently rewritten to change its meaning.
* Low-confidence extraction must remain flagged.
* Evidence records must remain within their owning collection.
* Evidence identity and content changes must be handled consistently so stored citations do not become silently invalid.

---

## 10. Retrieval Contract

### 10.1 Request Fields

| Field                   | Type           | Description                                   |
| ----------------------- | -------------- | --------------------------------------------- |
| `task_id`               | string         | Research task                                 |
| `collection_id`         | string         | Required retrieval scope                      |
| `query`                 | string         | Research question or retrieval query          |
| `filters`               | object         | Permitted metadata filters                    |
| `top_k`                 | integer        | Maximum number of candidate results requested |
| `required_source_types` | array          | Optional source-category constraints          |
| `reporting_period`      | string or null | Optional period constraint                    |

### 10.2 Response Fields

| Field              | Type             | Description                                      |
| ------------------ | ---------------- | ------------------------------------------------ |
| `retrieval_status` | string           | Retrieval outcome                                |
| `query`            | string           | Query actually used                              |
| `results`          | array            | Retrieved evidence references and relevance data |
| `result_count`     | integer          | Number of results returned                       |
| `warnings`         | array of strings | Relevant limitations                             |
| `error`            | object or null   | Failure details                                  |

Each result must contain:

* `evidence_id`
* `source_id`
* `document_id`, when applicable
* `collection_id`
* `relevance_score`, when available
* `location_reference`, when available

### 10.3 Retrieval Status Values

* `results_found`
* `no_results`
* `failed`
* `blocked`

### 10.4 Rules

* The collection boundary must be enforced before results are returned.
* A result score is not proof that the evidence supports a claim.
* `no_results` must be distinguishable from `failed`.
* Returned results must preserve their evidence identifiers.
* The requested result count must respect configured retrieval limits.

---

## 11. Analysis Finding Contract

### 11.1 Purpose

Represents a factual, numerical, or interpretive finding produced by a research responsibility.

### 11.2 Fields

| Field            | Type             | Description                                 |
| ---------------- | ---------------- | ------------------------------------------- |
| `finding_id`     | string           | Stable finding identifier                   |
| `task_id`        | string           | Parent research task                        |
| `category`       | string           | Finding category                            |
| `claim`          | string           | Finding or claim text                       |
| `claim_type`     | string           | Origin and nature of the claim              |
| `evidence_ids`   | array of strings | Supporting evidence references              |
| `calculation_id` | string or null   | Associated calculation, if applicable       |
| `confidence`     | number or null   | Confidence score, if defined and calibrated |
| `limitations`    | array of strings | Uncertainty or limitations                  |
| `status`         | string           | Finding validation status                   |
| `created_at`     | timestamp        | Creation time                               |

### 11.3 Claim Types

* `source_reported_fact`
* `calculated`
* `estimate`
* `inference`
* `interpretation`
* `uncertain`

### 11.4 Finding Status Values

* `draft`
* `supported`
* `partially_supported`
* `unsupported`
* `conflicted`
* `rejected`

### 11.5 Rules

* Material factual claims must have relevant evidence or an explicit limitation.
* Calculated claims must reference their calculation record.
* Estimates must identify material assumptions.
* Inferences must not be presented as directly reported facts.
* Confidence must not be interpreted as proof of correctness.
* Unsupported findings must not silently enter the final report as verified claims.

---

## 12. Conflict Record Contract

### 12.1 Purpose

Records contradictory values or claims that may affect research conclusions.

### 12.2 Fields

| Field                  | Type             | Description                              |
| ---------------------- | ---------------- | ---------------------------------------- |
| `conflict_id`          | string           | Stable conflict identifier               |
| `task_id`              | string           | Parent research task                     |
| `topic`                | string           | Subject of the conflict                  |
| `finding_ids`          | array of strings | Conflicting findings                     |
| `evidence_ids`         | array of strings | Relevant evidence                        |
| `conflict_type`        | string           | Type of disagreement                     |
| `materiality`          | string           | Impact classification                    |
| `resolution_status`    | string           | Resolution outcome                       |
| `resolution_rationale` | string or null   | Explanation of resolution                |
| `impact_on_conclusion` | string           | Effect on analysis, valuation, or rating |

### 12.3 Conflict Types

* `value_mismatch`
* `period_mismatch`
* `unit_mismatch`
* `definition_mismatch`
* `source_contradiction`
* `date_mismatch`
* `other`

### 12.4 Resolution Status Values

* `unresolved`
* `explained_by_context`
* `resolved_by_authoritative_evidence`
* `partially_resolved`
* `not_resolvable_with_available_evidence`

### 12.5 Rules

* Material conflicts must be preserved until resolved or explicitly disclosed.
* Different reporting periods must not automatically be treated as contradictory.
* Resolution rationale must reference the relevant evidence.
* A conflict must not be considered resolved merely because one value is more convenient for the report.

---

## 13. Information Gap Contract

### 13.1 Purpose

Represents required information that is missing, unavailable, unreliable, or unresolved.

### 13.2 Fields

| Field                 | Type    | Description                           |
| --------------------- | ------- | ------------------------------------- |
| `gap_id`              | string  | Stable gap identifier                 |
| `task_id`             | string  | Parent research task                  |
| `topic`               | string  | Missing information category          |
| `question`            | string  | Information that remains unresolved   |
| `importance`          | string  | Importance to the report              |
| `reason`              | string  | Why information is missing            |
| `follow_up_justified` | boolean | Whether further research is warranted |
| `follow_up_count`     | integer | Follow-up attempts                    |
| `status`              | string  | Current gap status                    |
| `impact_on_report`    | string  | Effect on findings or conclusions     |

### 13.3 Gap Status Values

* `open`
* `under_investigation`
* `resolved`
* `unavailable`
* `accepted_limitation`

### 13.4 Rules

* A gap must not be silently removed without resolution or a documented reason.
* Follow-up attempts must respect resource limits.
* Important unresolved gaps must be carried into the report.
* An accepted limitation must explain its impact on the conclusion.

---

## 14. Financial Calculation Contract

### 14.1 Purpose

Records deterministic financial calculations and makes them reproducible.

### 14.2 Fields

| Field                | Type           | Description                       |
| -------------------- | -------------- | --------------------------------- |
| `calculation_id`     | string         | Stable calculation identifier     |
| `task_id`            | string         | Parent research task              |
| `metric_name`        | string         | Name of the metric                |
| `formula`            | string         | Formula or calculation method     |
| `inputs`             | array          | Input values and their provenance |
| `output_value`       | number or null | Calculated result                 |
| `unit`               | string         | Output unit                       |
| `reporting_period`   | string or null | Applicable period                 |
| `currency`           | string or null | Currency when applicable          |
| `rounding_rule`      | string         | Rounding convention               |
| `calculation_status` | string         | Calculation outcome               |
| `validation_result`  | string         | Validation outcome                |
| `error`              | object or null | Calculation failure details       |

Each input must record:

* Input name.
* Value.
* Unit.
* Reporting period where applicable.
* Evidence reference or documented derivation.
* Whether it is reported, calculated, or estimated.

### 14.3 Calculation Status Values

* `valid`
* `invalid_input`
* `not_calculable`
* `failed`
* `requires_review`

### 14.4 Validation Rules

* Every required input must be present and valid.
* Units and reporting periods must be compatible.
* Division-by-zero and other invalid operations must be handled explicitly.
* Rounding rules must be consistent.
* Missing inputs must not be substituted with zero unless zero is supported by the data and the formula's semantics.
* Calculations must be reproducible from the stored inputs and formula.
* The required deterministic calculation test suite must pass completely before release.

---

## 15. Valuation Contract

### 15.1 Purpose

Represents the methodology, assumptions, calculations, and conclusions behind a valuation estimate.

### 15.2 Fields

| Field                 | Type             | Description                      |
| --------------------- | ---------------- | -------------------------------- |
| `valuation_id`        | string           | Stable valuation identifier      |
| `task_id`             | string           | Parent research task             |
| `method`              | string           | Valuation method                 |
| `methodology_version` | string           | Version of the documented method |
| `reference_date`      | date             | Valuation reference date         |
| `inputs`              | array            | Required valuation inputs        |
| `assumptions`         | array            | Explicit assumptions             |
| `scenarios`           | array            | Scenario results                 |
| `valuation_low`       | number or null   | Lower estimated value            |
| `valuation_base`      | number or null   | Base estimated value, if defined |
| `valuation_high`      | number or null   | Upper estimated value            |
| `currency`            | string or null   | Valuation currency               |
| `sensitivity_results` | array            | Sensitivity analysis             |
| `evidence_ids`        | array of strings | Supporting evidence              |
| `confidence_status`   | string           | Reliability assessment           |
| `limitations`         | array of strings | Missing inputs and uncertainty   |
| `valuation_status`    | string           | Outcome                          |

### 15.3 Valuation Status Values

* `supported`
* `limited`
* `speculative`
* `insufficient_evidence`
* `failed`

### 15.4 Rules

* Valuation methods must follow documented methodology.
* Material assumptions must be explicit.
* Numerical outputs must reference reproducible calculations.
* Scenario values must follow documented scenario definitions.
* Missing inputs and uncertain estimates must be disclosed.
* A speculative estimate must not be presented as decision-grade.
* A failed valuation must not be represented as a reliable numerical result.

---

## 16. Investment Rating Contract

### 16.1 Purpose

Represents the output of the documented investment-rating methodology.

### 16.2 Fields

| Field                           | Type             | Description                       |
| ------------------------------- | ---------------- | --------------------------------- |
| `rating_id`                     | string           | Stable rating identifier          |
| `task_id`                       | string           | Parent research task              |
| `methodology_version`           | string           | Version of the rating methodology |
| `rating`                        | string           | Rating outcome                    |
| `reference_date`                | date             | Date the assessment is based on   |
| `valuation_id`                  | string or null   | Associated valuation              |
| `supporting_finding_ids`        | array of strings | Supporting findings               |
| `opposing_finding_ids`          | array of strings | Counterevidence                   |
| `rationale`                     | string           | Explanation of the rating         |
| `confidence_status`             | string           | Confidence classification         |
| `conditions_that_change_rating` | array of strings | Material change conditions        |
| `limitations`                   | array of strings | Important gaps and caveats        |
| `rating_status`                 | string           | Evaluation outcome                |

### 16.3 Rating Values

* `buy`
* `hold`
* `sell`
* `insufficient_evidence`

### 16.4 Rating Status Values

* `valid`
* `limited`
* `blocked`
* `failed`

### 16.5 Rules

* Rating decisions must follow a documented methodology version.
* The reference date must be explicit.
* Material supporting and opposing evidence must be preserved.
* Missing evidence must be reflected in the rating status or outcome.
* The system must not invent rating thresholds at runtime.
* A rating is an analytical opinion under a defined methodology, not a guarantee or personalized investment instruction.

The methodology's investment horizon, valuation reference, criteria, thresholds, and evidence requirements must be finalized before the rating can be evaluated reliably.

---

## 17. Report Contract

### 17.1 Purpose

Defines the structured output delivered to the user.

### 17.2 Report Fields

| Field               | Type             | Description                |
| ------------------- | ---------------- | -------------------------- |
| `report_id`         | string           | Stable report identifier   |
| `task_id`           | string           | Parent research task       |
| `company_id`        | string           | Resolved company           |
| `reference_date`    | date             | Research reference date    |
| `report_version`    | integer          | Report revision            |
| `generated_at`      | timestamp        | Report generation time     |
| `report_status`     | string           | Report outcome             |
| `sections`          | array            | Structured report sections |
| `finding_ids`       | array of strings | Included findings          |
| `evidence_ids`      | array of strings | Referenced evidence        |
| `calculation_ids`   | array of strings | Referenced calculations    |
| `valuation_id`      | string or null   | Associated valuation       |
| `rating_id`         | string or null   | Associated rating          |
| `limitations`       | array of strings | Material caveats           |
| `validation_result` | object           | Validation summary         |

### 17.3 Required Report Sections

The report must support the following sections:

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
12. Rating or insufficient-evidence outcome.
13. Missing information, conflicts, and limitations.
14. Sources and evidence references.

### 17.4 Report Status Values

* `draft`
* `validating`
* `validated`
* `limited`
* `rejected`
* `failed`

### 17.5 Rules

* Required sections must be present or explicitly marked unavailable with an explanation where permitted.
* Material claims must retain evidence references.
* Calculated claims must retain calculation provenance.
* Material conflicts and uncertainty must be disclosed.
* A report marked `validated` must have passed the applicable mandatory validation checks.
* A draft report must not be presented as a completed report.

---

## 18. Report Validation Contract

### 18.1 Input Fields

* `task_id`
* `report_id`
* `report_version`
* `validation_profile`
* `required_sections`
* `evidence_records`
* `calculation_records`
* `rating_methodology_version`

### 18.2 Output Fields

| Field                  | Type      | Description                    |
| ---------------------- | --------- | ------------------------------ |
| `validation_id`        | string    | Stable validation identifier   |
| `task_id`              | string    | Parent task                    |
| `report_id`            | string    | Validated report               |
| `validation_status`    | string    | Overall outcome                |
| `checks`               | array     | Individual check results       |
| `critical_failures`    | array     | Critical issues                |
| `warnings`             | array     | Non-critical issues            |
| `required_corrections` | array     | Actions needed before approval |
| `validated_at`         | timestamp | Validation time                |

Each check should include:

* Check identifier.
* Check category.
* Result.
* Severity.
* Relevant claim, evidence, or calculation references.
* Explanation.
* Required corrective action, if applicable.

### 18.3 Validation Status Values

* `passed`
* `passed_with_limitations`
* `failed`
* `error`

### 18.4 Rules

* A critical failure must prevent successful finalization.
* Validation must check citation support, not merely citation presence.
* Financial calculations must be checked against their recorded inputs and formulas.
* Material inconsistencies between valuation and rating must be flagged.
* Permitted limitations must be explicit and must not override mandatory release gates.
* Validation failures must be retained for debugging and regression testing.

---

## 19. Task State Contract

### 19.1 Task Fields

| Field                  | Type              | Description                    |
| ---------------------- | ----------------- | ------------------------------ |
| `task_id`              | string            | Stable task identifier         |
| `company_id`           | string or null    | Resolved company               |
| `collection_id`        | string            | Owning collection              |
| `status`               | string            | Overall task state             |
| `current_stage`        | string or null    | Current stage                  |
| `created_at`           | timestamp         | Creation time                  |
| `started_at`           | timestamp or null | Start time                     |
| `completed_at`         | timestamp or null | Completion time                |
| `last_updated_at`      | timestamp         | Last state update              |
| `checkpoint_reference` | string or null    | Latest valid checkpoint        |
| `report_id`            | string or null    | Final report reference         |
| `error_id`             | string or null    | Terminal error reference       |
| `limitations`          | array of strings  | Incomplete or limited outcomes |

### 19.2 Task Status Values

* `created`
* `queued`
* `running`
* `completed`
* `completed_with_limitations`
* `failed`
* `cancelled`

### 19.3 Stage Status Values

* `pending`
* `running`
* `succeeded`
* `partially_succeeded`
* `blocked`
* `retrying`
* `failed`
* `skipped`
* `cancelled`

### 19.4 State Rules

* Every task must have one authoritative current status.
* Only permitted transitions may occur.
* A terminal state must not be silently overwritten by a conflicting terminal state.
* `completed` requires all mandatory completion conditions to pass.
* `completed_with_limitations` is permitted only where the completion policy allows it and the limitations are explicit.
* `failed` and `cancelled` must not be represented as successful completion.
* A task must not be marked completed merely because a report draft exists.

---

## 20. Error Contract

### 20.1 Purpose

Provides a consistent representation of component and workflow failures.

### 20.2 Error Fields

| Field               | Type           | Description                               |
| ------------------- | -------------- | ----------------------------------------- |
| `error_id`          | string         | Stable error identifier                   |
| `task_id`           | string or null | Associated task                           |
| `stage_id`          | string or null | Associated stage                          |
| `component`         | string         | Component reporting the error             |
| `error_category`    | string         | Error classification                      |
| `message`           | string         | Safe, human-readable explanation          |
| `retryable`         | boolean        | Whether retry may be appropriate          |
| `attempt_number`    | integer        | Current attempt number                    |
| `occurred_at`       | timestamp      | Error occurrence time                     |
| `impact`            | string         | Effect on the task                        |
| `recovery_action`   | string or null | Planned or completed recovery             |
| `details_reference` | string or null | Reference to protected diagnostic details |

### 20.3 Error Categories

* `invalid_input`
* `company_resolution_error`
* `source_unavailable`
* `document_validation_error`
* `document_extraction_error`
* `retrieval_error`
* `empty_evidence`
* `calculation_error`
* `validation_error`
* `model_output_error`
* `external_dependency_error`
* `resource_limit_exceeded`
* `timeout`
* `cancellation`
* `recovery_error`
* `security_violation`
* `collection_isolation_violation`
* `internal_error`

### 20.4 Error Handling Rules

* Retryable errors may be retried only within configured limits.
* Invalid input must not be retried without a meaningful change.
* Resource-limit exhaustion must stop further work.
* Security violations must not be treated as ordinary recoverable failures without review.
* Error messages shown to users must not expose secrets or unnecessary internal details.
* Diagnostic details must not unnecessarily retain sensitive document contents.
* The final task status must reflect the impact of the error.

---

## 21. Resource Limit Contract

### 21.1 Purpose

Defines the limits governing research execution.

### 21.2 Fields

| Field                    | Type    | Description                     |
| ------------------------ | ------- | ------------------------------- |
| `max_runtime_seconds`    | integer | Maximum permitted task runtime  |
| `max_research_steps`     | integer | Maximum research steps          |
| `max_retries_per_stage`  | integer | Maximum retries for one stage   |
| `max_external_api_calls` | integer | Maximum external API calls      |
| `max_queue_size`         | integer | Maximum queued jobs             |
| `max_pdf_size_bytes`     | integer | Maximum accepted PDF size       |
| `max_pdf_pages`          | integer | Maximum accepted PDF page count |

### 21.3 Rules

* Limits must be configurable.
* Limits must be validated before execution.
* Runtime and external-call budgets must be enforced during execution, not only at task creation.
* Reaching a limit must produce an explicit status or limitation.
* A retry must not reset the overall task budget.
* The final configured values must be established before implementation and recorded in the relevant configuration documentation.

The initial scope proposes a maximum of 20 MB and 300 pages per PDF. These values must be confirmed before implementation.

---

## 22. Checkpoint and Recovery Contract

### 22.1 Checkpoint Fields

| Field                 | Type           | Description                              |
| --------------------- | -------------- | ---------------------------------------- |
| `checkpoint_id`       | string         | Stable checkpoint identifier             |
| `task_id`             | string         | Parent task                              |
| `stage_id`            | string         | Associated stage                         |
| `checkpoint_version`  | integer        | Checkpoint schema version                |
| `completed_outputs`   | array          | References to completed outputs          |
| `stage_state`         | object         | Minimal state required to resume         |
| `created_at`          | timestamp      | Checkpoint creation time                 |
| `integrity_reference` | string or null | Mechanism to verify checkpoint integrity |

### 22.2 Recovery Rules

* A checkpoint must represent a valid and internally consistent state.
* Recovery must validate checkpoint compatibility before resuming.
* A stage may be retried only if its side effects can be handled safely.
* Duplicate processing must not create unintended duplicate records.
* If a checkpoint cannot be trusted, the system must not resume from it silently.
* Recovery failure must produce an explicit task outcome.

---

## 23. Evaluation Contract

### 23.1 Evaluation Run Fields

| Field                   | Type              | Description               |
| ----------------------- | ----------------- | ------------------------- |
| `evaluation_run_id`     | string            | Unique evaluation run     |
| `dataset_version`       | string            | Version of the benchmark  |
| `configuration_version` | string            | System configuration used |
| `started_at`            | timestamp         | Run start                 |
| `completed_at`          | timestamp or null | Run completion            |
| `case_results`          | array             | Per-question outcomes     |
| `aggregate_metrics`     | object            | Aggregate results         |
| `category_metrics`      | object            | Category-specific results |
| `critical_failures`     | array             | Critical failure records  |
| `release_gate_result`   | string            | Overall gate outcome      |

### 23.2 Per-Question Result

Each case result must preserve:

* Question identifier.
* Question category.
* Expected answer or evaluation criteria.
* Actual output or output reference.
* Relevant evidence references.
* Correctness result.
* Evidence-faithfulness result.
* Citation-support result.
* Retrieval metrics where applicable.
* Latency.
* Variable cost where measurable.
* Failure and limitation information.

### 23.3 Evaluation Rules

* The benchmark contains 40 questions: 15 factual, 15 multi-hop, 5 unanswerable, and 5 adversarial/poisoned-document.
* Results must include raw counts and percentages.
* Category-level performance must be reported.
* Critical failures must be reported separately from aggregate metrics.
* Evaluation dataset and configuration versions must be retained.
* A small benchmark must not be represented as proof of statistical certainty.

---

## 24. Experiment Contract

### 24.1 Experiment Fields

| Field                     | Type   | Description                    |
| ------------------------- | ------ | ------------------------------ |
| `experiment_id`           | string | Stable experiment identifier   |
| `name`                    | string | Experiment name                |
| `hypothesis`              | string | Expected effect                |
| `dataset_version`         | string | Evaluation dataset version     |
| `baseline_configuration`  | string | Baseline configuration         |
| `candidate_configuration` | string | Candidate configuration        |
| `quality_results`         | object | Quality comparison             |
| `latency_results`         | object | Latency comparison             |
| `cost_results`            | object | Cost comparison                |
| `failure_analysis`        | array  | Relevant failure cases         |
| `limitations`             | array  | Measurement limitations        |
| `engineering_verdict`     | string | Final interpretation           |
| `adr_references`          | array  | Related architecture decisions |

### 24.2 Required Experiments

1. Hybrid retrieval versus vector-only retrieval.
2. Reranking enabled versus disabled.
3. Query rewriting enabled versus disabled.

### 24.3 Rules

* Experiments must use comparable evaluation conditions.
* Negative results must be retained.
* Quality, latency, cost, and failure behavior must all be considered.
* Each experiment must document an engineering conclusion.
* Relevant ADRs must be updated based on the findings.
* Configuration changes must be traceable to the results that motivated them.

---

## 25. Data Deletion Contract

### 25.1 Request Fields

* `deletion_request_id`
* `collection_id`
* `target_type`
* `target_id`
* `requested_at`

### 25.2 Target Types

* `research_task`
* `report`
* `document`
* `collection`

Supported target types must be finalized before implementation.

### 25.3 Result Fields

* `deletion_request_id`
* `status`
* `deleted_record_categories`
* `remaining_dependencies`
* `completed_at`
* `error`, if applicable

### 25.4 Rules

* Deletion must follow the documented retention and dependency policy.
* Dependent evidence, derived outputs, and references must be handled consistently.
* A deletion operation must not claim success if required verification fails.
* Deletion records must not retain unnecessary deleted content.
* Backup retention and deletion guarantees must be documented separately.

---

## 26. Contract Validation Rules

Every contract implementation must validate the following categories where applicable.

### Structure

* Required fields are present.
* Field types are correct.
* Enum values are permitted.
* Collection sizes are within limits.

### Identity

* Identifiers reference the correct record type.
* Referenced records exist where required.
* Collection ownership is consistent.
* Company identity matches the active research task.

### Evidence

* Evidence references resolve.
* Material claims have supporting evidence or explicit limitations.
* Source and document provenance is preserved.
* Citations point to the intended source and location.

### Financial Data

* Units and periods are compatible.
* Calculation inputs are present.
* Formula and rounding rules are defined.
* Invalid operations are handled explicitly.
* Outputs are reproducible.

### Lifecycle

* State transitions are permitted.
* Retry limits are respected.
* Terminal states are accurate.
* Completed tasks satisfy mandatory completion requirements.

### Security

* Collection boundaries are enforced.
* Untrusted document content is never treated as trusted instructions.
* Secrets and unnecessary sensitive content are excluded from user-visible errors and ordinary logs.
* Deletion behavior is verified.

---

## 27. Contract Testing Strategy

The implementation must include tests at three levels.

### 27.1 Unit Contract Tests

Test each component's input and output validation independently.

Examples:

* Invalid company-resolution result.
* Missing evidence references.
* Incompatible financial units.
* Invalid valuation inputs.
* Malformed report sections.
* Invalid state transitions.
* Retry-limit enforcement.

### 27.2 Integration Contract Tests

Test that connected components exchange valid information.

Examples:

* Research Planner to Source Acquisition.
* Document Ingestion to Evidence Repository.
* Retrieval to analysis components.
* Financial Analysis to Valuation.
* Provenance Manager to Report Assembly.
* Report Assembly to Report Validation.
* Task State and Recovery to the Research Orchestrator.

### 27.3 Failure Contract Tests

Test how components behave when another component fails or returns incomplete data.

Examples:

* Empty retrieval.
* Unavailable external source.
* Corrupt PDF.
* Low-quality OCR.
* Invalid financial calculation.
* Unsupported material claim.
* Worker interruption.
* Retry exhaustion.
* Collection-isolation violation.
* Cancellation during execution.

A component must not return a successful outcome when its documented postconditions have failed.

---

## 28. Contract Versioning

Contracts will evolve during implementation.

Rules:

* Every persisted or externally exchanged contract must have a documented schema version where compatibility requires it.
* Additive optional fields should preserve compatibility when feasible.
* Changes to required fields, status meanings, identifier semantics, or calculation behavior must be treated as potentially breaking.
* Breaking changes must include migration or compatibility handling.
* Historical evaluation results must retain the contract and configuration versions under which they were produced.
* Contract changes that affect report quality, provenance, recovery, or security must trigger relevant regression tests.

---

## 29. Open Decisions

The following decisions remain unresolved and must be finalized during implementation design:

* Exact serialized schema format.
* Concrete data types and validation library.
* Identifier generation strategy.
* Task-state transition matrix.
* Report section schemas.
* Detailed valuation input schemas.
* Rating methodology and thresholds.
* Source-authority scoring policy.
* Evidence-confidence representation.
* Checkpoint persistence and recovery semantics.
* Deletion and retention guarantees.
* API and internal component interface definitions.

These decisions must be documented rather than introduced implicitly.

---

## 30. Completion Criteria

This document is complete when:

* Every major component exchange has a defined contract.
* Request, source, document, evidence, finding, and report records have explicit fields.
* Financial calculations preserve reproducibility and provenance.
* Valuation and rating outputs include methodology references and limitations.
* Task states, errors, retries, and recovery have defined semantics.
* Report validation outcomes are explicit.
* Evaluation and experiment records are reproducible.
* Security and collection-isolation requirements are represented.
* Contract testing requirements cover normal and failure paths.
* The document is consistent with `01_problem.md` through `08_data_and_control_flow.md`.

Implementation must not begin by treating these contracts as optional conventions. Components must validate and respect the contracts at their boundaries.
