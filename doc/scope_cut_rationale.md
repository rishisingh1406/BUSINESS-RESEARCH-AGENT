# Scope-Cut Rationale — Equity / Business Research Agent

## 1. Purpose

This document records why the MVP includes selected capabilities and defers others. The objective is to build a credible, testable research system without expanding into a full investment platform.

## 2. Core product bet

The MVP tests one central hypothesis:

> A bounded AI research workflow can turn fragmented public company information and uploaded annual reports into a structured, traceable research report while explicitly exposing missing evidence, conflicts, uncertainty, and calculation assumptions.

The MVP should prove this workflow before adding user personalization, broad portfolio functionality, continuous monitoring, or autonomous financial actions.

## 3. Included capabilities and rationale

| Capability | Why it is included |
|---|---|
| One Indian listed company per task | Limits identity resolution and research complexity while preserving a meaningful end-to-end use case |
| Company fundamentals and business model | Establishes the core research value |
| Industry and competitor context | Helps interpret company performance rather than reporting financial figures in isolation |
| Annual-report PDF ingestion | Tests document processing, retrieval, provenance, and long-document handling |
| Public filings and company sources | Provides evidence for important claims and financial disclosures |
| Historical financial analysis | Enables comparison across reporting periods and supports fundamental analysis |
| Valuation scenarios and assumptions | Tests deterministic calculations, uncertainty handling, and evidence-backed reasoning |
| Thesis and antithesis | Requires the system to consider supporting and opposing evidence |
| Source citations and conflict disclosure | Makes the report auditable and helps the user verify material claims |
| Background execution and recovery | Research may involve multiple slow or failure-prone stages; operational reliability is part of the engineering objective |
| Evaluation and security tests | Prevents a polished report from being mistaken for a reliable system without measured evidence |

## 4. Deferred capabilities and rationale

| Deferred capability | Reason for deferral | Trade-off accepted |
|---|---|---|
| Authentication, full multi-user support, and RBAC | Not required to validate the single-user MVP workflow | The MVP is not suitable for unrestricted public or multi-user deployment |
| Portfolio allocation and personalized investment planning | Requires personal financial context and a different decision boundary | The system does not decide how much an individual should invest |
| Broker integration and autonomous trading | Adds financial-action risk and is outside the research problem | Reports inform research only; no orders are placed |
| Continuous real-time monitoring | Requires scheduling, freshness policies, and ongoing operational costs | Reports are snapshots as of a stated date |
| Advanced multi-company research | Adds cross-company comparability and coordination complexity | The initial task analyzes one company, with limited competitor context |
| Non-PDF uploads | Expands ingestion, validation, and evaluation surfaces | Other formats must be converted externally or are unsupported in v1 |
| Complex long-term memory and user preferences | Not necessary to validate one research task | No persistent personalization is promised |
| Fine-tuning | Adds dataset preparation, training cost, and another evaluation surface | Start with a measured baseline using existing models and deterministic logic |
| Kafka, Celery, and distributed-scale infrastructure | Premature before measured throughput needs justify the operational burden | Use a simpler bounded execution design; revisit only if evidence demands it |
| Custom report templates and mobile applications | Presentation expansion is not the core technical risk | Prioritize correctness, traceability, and reproducibility over interface breadth |
| Broad macroeconomic research and company discovery/ranking | Expands the research problem beyond a user-selected company | The user provides the company; the system resolves identity and researches it |

## 5. Deliberate constraints

### Authentication and access

Full authentication and multi-user authorization are out of scope. This does not remove the need for safe file handling, secret protection, collection isolation, deletion, and prompt-injection defenses.

The MVP must not be represented as a secure multi-tenant service.

### Document limits and formats

Initial ingestion supports PDF files, including scanned PDFs through OCR. The initial limits are 300 pages and 20 MB per file. The file-size limit must be confirmed before implementation.

These limits constrain resource use and create a reproducible test boundary. They do not guarantee that every PDF within the limits can be parsed correctly.

### Data sources

Prioritize official company disclosures, relevant exchange/regulatory filings, uploaded annual reports, and suitable financial-data sources. Broader web research may add context, but source authority, publication date, reporting period, and conflicts must be recorded.

The MVP does not promise that every source will be available or that all data will be real-time.

### Evaluation

Use the initial 40-question benchmark as a versioned engineering baseline. Treat category-specific scores as diagnostic evidence, not proof of general reliability. Mandatory safety, evidence, calculation, recovery, and isolation gates cannot be offset by a high aggregate score.

### Valuation and ratings

The system may produce a buy/hold/sell rating only when its documented methodology and evidence requirements are satisfied. Otherwise it must report insufficient evidence. It must not force a rating or imply personalized financial advice.

## 6. Costs of these cuts

The MVP sacrifices breadth, personalization, and commercial readiness in exchange for a smaller system whose important behaviors can be tested and explained.

Expected limitations include:
- No multi-user security guarantee
- Limited file-format coverage
- No guarantee of complete or current source data
- Limited benchmark coverage
- No automatic monitoring after a report is generated
- No portfolio or trading capabilities

These are intentional limitations, not hidden features.

## 7. Revisit conditions

Reopen a scope cut only when there is evidence that:
- The core workflow passes mandatory release gates.
- A real user need justifies the added capability.
- The added work has explicit acceptance criteria.
- Its effect on security, evaluation, cost, and operations is understood.

Do not add a deferred feature solely because it is technically interesting.

## 8. Decision

The MVP prioritizes a single-company, evidence-backed research workflow with transparent uncertainty, auditable calculations, bounded execution, and reproducible evaluation.

Features that do not directly validate this core hypothesis remain deferred.