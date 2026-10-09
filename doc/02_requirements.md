# Requirements

## 1. Functional Requirements

### 1.1 Research Input

The system must accept:

* Company name as a string.
* Company ticker.
* An optional annual report provided by the user.

### 1.2 Research Question Decomposition

The system must be able to:

* Decompose the user's research question into smaller research tasks.
* Identify the information required to complete each task.
* Create an ordered research plan.
* Track the completion status of each task.

### 1.3 Information Requirements

The system must be able to:

* Identify the information required to answer the research question.
* Determine whether the required information has been obtained.
* Identify information that is still missing.

### 1.4 Evidence Retrieval

The system must be able to:

* Generate appropriate search and retrieval queries for each research task.
* Retrieve relevant evidence for the generated queries.
* Associate retrieved evidence with the research task that requested it.

### 1.5 Evidence Analysis

The system must be able to:

* Analyze retrieved evidence.
* Extract relevant facts and information.
* Use the evidence to answer the corresponding research task.
* Distinguish supported information from unsupported information.

### 1.6 Gap Detection

The system must be able to:

* Identify gaps in the current research.
* Identify unanswered research requirements.
* Determine whether additional research is necessary.

### 1.7 Follow-up Research

The system must be able to:

* Perform follow-up research when important information is missing.
* Generate additional research tasks based on identified gaps.
* Stop follow-up research when sufficient evidence has been collected or the research limit has been reached.

### 1.8 Conflict Handling

The system must be able to:

* Identify conflicting information from different sources.
* Preserve the conflicting evidence.
* Compare the sources.
* Represent unresolved conflicts in the final findings instead of silently ignoring them.

### 1.9 Research Findings

The system must be able to:

* Generate structured findings from the collected evidence.
* Connect findings to their supporting evidence.
* Distinguish factual findings from analysis or interpretation.

### 1.10 Valuation Analysis

The system must be able to:

* Perform valuation analysis using available financial information.
* State the valuation methodology and assumptions.
* Produce an estimated valuation or valuation range when sufficient information is available.
* Identify important valuation sensitivities.
* Disclose limitations when available information does not support a reliable valuation.

### 1.11 Scenario Analysis

The system must be able to:

* Generate bull, base, and bear scenarios when sufficient information is available.
* Define the assumptions behind each scenario.
* Identify the conditions required for each scenario.
* Explain the major risks and uncertainties associated with each scenario.

### 1.12 Thesis and Antithesis

The system must be able to:

* Generate a thesis supported by evidence.
* Generate an antithesis that challenges the thesis.
* Identify evidence that could invalidate the thesis.
* Present unresolved questions and material contradictions that affect the overall assessment.

### 1.13 Missing Information

The system must be able to:

* Identify important information that could not be obtained.
* Clearly communicate what information is missing.
* Distinguish information that is unavailable from information that was searched for but not found.
* Prevent missing information from being presented as known facts.

### 1.14 Research Report

The system must be able to:

* Generate a structured company research report.
* Present findings in a format understandable to the user.
* Include evidence and citations for material factual claims.
* Clearly distinguish facts, analysis, assumptions, estimates, projections, and uncertainty.
* Identify material limitations and unresolved conflicts.

### 1.15 Research State

The system must be able to:

* Persist the current research state.
* Track completed and incomplete research tasks.
* Store collected evidence and findings.
* Resume an incomplete research process where possible.
* Avoid treating an interrupted or partially completed research task as a completed report.

---

## 2. Evidence and Provenance Requirements

### 2.1 Source Traceability

The system must:

* Maintain a reference to the original source for every piece of evidence used in the research.
* Track the source type, source name, document identifier, and relevant location when available.
* Allow a reviewer to trace a research finding back to its original source.
* Preserve source information throughout the research workflow.
* Preserve page-level or section-level references for uploaded documents when available.

### 2.2 Claim-to-Evidence Mapping

The system must:

* Associate every material factual claim in the final report with its supporting evidence.
* Allow a claim to be supported by multiple pieces of evidence when necessary.
* Distinguish claims supported by evidence from interpretations, assumptions, estimates, and hypotheses.
* Identify claims that lack sufficient supporting evidence.
* Avoid presenting unsupported claims as established facts.
* Preserve the relationship between a finding, its supporting evidence, and the original source location.

### 2.3 Citations

The system must:

* Provide citations for material factual claims in the final research report.
* Ensure that citations refer to the actual sources used to generate the claims.
* Include document page numbers, section names, URLs, or other source locations when available.
* Allow users to identify and inspect the evidence supporting a cited claim.
* Clearly indicate when a claim cannot be linked to a verifiable source.
* Avoid generating fabricated citations, page numbers, URLs, or source references.

### 2.4 Evidence Sufficiency

The system must:

* Determine whether the collected evidence is sufficient to support a research finding.
* Identify findings supported by strong, partial, conflicting, or insufficient evidence.
* Avoid generating definitive conclusions when the available evidence is insufficient.
* Attempt additional research when important evidence is missing and further research is appropriate.
* Explicitly report when sufficient evidence cannot be obtained.
* Avoid treating the quantity of retrieved evidence as proof of its quality or sufficiency.

### 2.5 Uncertainty

The system must:

* Distinguish verified facts from interpretations, estimates, assumptions, and projections.
* Communicate uncertainty when the available evidence does not support a definitive conclusion.
* Identify important assumptions that influence financial analysis and valuation.
* Explain material limitations in the available data or sources.
* Avoid presenting uncertain information or estimates as verified facts.
* Reflect uncertainty in the final findings, valuation scenarios, and research conclusions.

---

## 3. Output Requirements

### 3.1 Report Structure

The system must:

* Generate a structured company research report that is understandable to an individual investor.
* Organize the report into clearly defined sections.
* Present an executive summary, company overview, business model, industry analysis, management analysis, financial analysis, competitive analysis, risks, valuation, scenarios, thesis, and antithesis.
* Include relevant evidence and citations alongside material factual claims.
* Present key findings before supporting details where appropriate.
* Clearly distinguish factual information from analysis, assumptions, estimates, and projections.
* Identify important gaps, conflicting evidence, and limitations.

### 3.2 Financial Analysis

The system must:

* Analyze the company's income statement, balance sheet, and cash flow statement when relevant data is available.
* Identify historical trends in revenue, profitability, margins, cash flow, and other relevant financial metrics.
* Assess financial strength, liquidity, debt, and profitability.
* Calculate relevant financial ratios using available data.
* Explain significant changes in financial performance and their potential implications.
* Support material financial conclusions with evidence.
* Identify missing, inconsistent, outdated, or unreliable financial data.
* Distinguish figures reported directly by a source from figures calculated by the system.
* Preserve the source inputs, units, reporting periods, calculation method, and resulting value for derived financial metrics and valuation calculations.
* Identify missing calculation inputs, inconsistent units, incompatible reporting periods, and assumptions that materially affect a calculation.
* Distinguish calculated results from estimates and projections.
* Make financial calculations auditable so a reviewer can understand how a reported result was derived.

### 3.3 Competitive Analysis

The system must:

* Identify relevant competitors when sufficient information is available.
* Compare the target company with selected competitors using relevant business and financial metrics.
* Analyze competitive advantages, disadvantages, and market positioning.
* Assess relevant factors such as pricing power, market share, differentiation, and barriers to entry when evidence is available.
* Support important comparisons with sources and evidence.
* Identify limitations in competitor data that may affect the analysis.
* Make clear when competitor metrics are not directly comparable because of differences in reporting periods, accounting methods, business models, or available data.

### 3.4 Risk Analysis

The system must:

* Identify material risks affecting the company's business, financial position, and future performance.
* Consider relevant business, financial, operational, industry, regulatory, and management risks.
* Explain how each identified risk could affect the company's performance or valuation.
* Support material risk assessments with evidence.
* Distinguish disclosed risks from risks inferred through analysis.
* Identify important risks that cannot be adequately assessed because of missing information.
* Avoid presenting speculative risks as verified events or established facts.

### 3.5 Valuation Output

The system must:

* Present the valuation methodology used and explain why it is appropriate for the available data.
* State the assumptions, financial inputs, units, reporting periods, and calculations used in the valuation.
* Present an estimated valuation or valuation range when sufficient information is available.
* Compare the estimated valuation with a relevant current or reference valuation when reliable data is available.
* Identify the key variables and assumptions that materially affect the valuation.
* Present sensitivity analysis for important valuation assumptions.
* Support material assumptions with evidence or clearly identify them as estimates.
* Disclose limitations when available information does not support a reliable valuation.
* Preserve the calculation steps and inputs needed to audit the resulting valuation.
* Avoid presenting an estimated valuation as a guaranteed future market price.

### 3.6 Scenario Output

The system must:

* Present bull, base, and bear scenarios when sufficient information is available.
* State the key assumptions underlying each scenario.
* Explain the business and financial conditions required for each scenario to occur.
* Present the potential implications for business performance and valuation.
* Identify the major risks and uncertainties associated with each scenario.
* Explain which evidence supports or challenges each scenario.
* Avoid presenting scenario estimates as guaranteed outcomes.
* Clearly distinguish scenario assumptions from historical facts and reported financial results.

### 3.7 Thesis and Antithesis

The system must:

* Present a thesis summarizing the evidence supporting the company's potential business attractiveness.
* Present an antithesis identifying evidence and arguments that challenge the thesis.
* Support both sides with relevant evidence and citations.
* Identify assumptions on which the thesis depends.
* Explain what developments or evidence could invalidate the thesis.
* Highlight unresolved questions and material disagreements between supporting and opposing evidence.
* Avoid forcing a definitive conclusion when the evidence is insufficient or contradictory.

### 3.8 Limitations

The system must:

* Disclose important gaps in the available information.
* Identify material conflicts between sources that remain unresolved.
* Explain limitations in data quality, source reliability, and analysis.
* Disclose important assumptions and uncertainties affecting financial analysis and valuation.
* Distinguish unavailable information from information that was searched for but not found.
* Clearly state when the available evidence is insufficient to support a finding or conclusion.
* Avoid presenting the report as a guarantee of future business performance or investment returns.
* Make clear when parts of a report are incomplete because of failed retrieval, unavailable sources, or interrupted research.

---

## 4. Non-Functional Requirements

### 4.1 Performance

The system must:

* Prioritize research quality, factual correctness, evidence coverage, and reliability over response speed.
* Allow sufficient time for multi-step research, evidence verification, financial analysis, and valuation calculations.
* Measure the total time required to complete a research task and generate the final report.
* Measure the latency of individual stages to identify unnecessary delays and performance bottlenecks.
* Provide progress updates for long-running research tasks.
* Maintain reasonable response times without compromising evidence quality or report reliability.
* Measure the time required to ingest and prepare a 300-page annual report for retrieval, with an initial target of less than 5 minutes under defined test conditions.
* Record the conditions used for ingestion performance measurements, including document characteristics and the processing configuration.

### 4.2 Reliability

The system must:

* Handle missing, malformed, or incomplete input without crashing.
* Handle unavailable data sources and failed retrieval operations gracefully.
* Provide an explicit insufficient-evidence response when relevant information cannot be retrieved.
* Prevent failed research tasks from producing reports that appear complete and verified.
* Support retrying recoverable operations without creating duplicate records or evidence.
* Recover or resume interrupted ingestion and research tasks where possible.
* Handle dependency failures with a clear error or degraded mode rather than silently producing unreliable results.
* Distinguish completed, partially completed, failed, and interrupted research tasks.
* Preserve enough state to identify where a recoverable task failed.

### 4.3 Auditability

The system must:

* Preserve the evidence and source references used to generate research findings.
* Make material claims traceable to their supporting evidence.
* Record research task status and significant workflow events.
* Record relevant model, prompt, retrieval, and analysis configuration information for completed research runs.
* Allow a reviewer to investigate how a finding was produced.
* Preserve the calculation inputs and methods for derived financial metrics and valuations.
* Avoid recording sensitive information unnecessarily.

### 4.4 Reproducibility

The system must:

* Preserve the evaluation datasets and expected results used for regression testing.
* Version research datasets and evaluation configurations.
* Record the relevant model, prompt, retrieval, and processing configuration for each research run.
* Allow evaluation experiments to be repeated under the same recorded conditions.
* Track changes in evaluation results when prompts, models, retrieval methods, or other relevant configurations change.
* Document the limitations that prevent an identical result from being reproduced.

### 4.5 Cost

The system must:

* Measure the cost of model calls, embedding generation, and other metered external services where applicable.
* Track the estimated cost per completed research task and research report.
* Identify expensive workflow stages and unnecessary repeated operations.
* Support comparison of cost against research quality and latency during experiments.
* Avoid unnecessary model calls and repeated processing when existing results can be safely reused.
* Establish an acceptable cost target after measuring a representative set of research tasks.

---

## 5. Security Requirements

### 5.1 Document Validation

The system must:

* Accept only explicitly supported document formats.
* Enforce configurable file-size and page-count limits.
* Define the initial maximum upload size and page count before implementation.
* Validate uploaded files before processing them.
* Handle corrupted, malformed, empty, or unreadable documents without crashing.
* Reject files that violate validation rules and provide a clear explanation.
* Prevent unsafe filenames and file paths from accessing or overwriting unintended files.
* Isolate documents that fail processing so they cannot silently enter the research corpus.
* Ensure that document content is treated as untrusted input.
* Prevent incomplete document processing from being reported as successful ingestion.

### 5.2 Prompt Injection Protection

The system must:

* Treat instructions found inside uploaded documents, retrieved passages, and external web content as untrusted data.
* Prevent retrieved content from overriding trusted system instructions or security policies.
* Detect and resist attempts by malicious documents to manipulate research tasks, tool usage, or final outputs.
* Separate trusted instructions from untrusted source content during processing.
* Validate proposed tool actions before execution.
* Test prompt-injection defenses using a dedicated collection of benign and malicious documents.
* Record attack outcomes and verify that malicious content does not control the research workflow.
* Verify that malicious instructions cannot cause the system to fabricate evidence, bypass validation, or present unsupported claims as facts.

### 5.3 Source Isolation

The system must:

* Keep retrieved document content separate from trusted system instructions.
* Prevent external sources from independently triggering unauthorized tool calls or changing system configuration.
* Ensure that retrieved content cannot directly execute code or commands.
* Prevent one research collection from accessing documents belonging to another collection when collection-level isolation is enabled.
* Restrict access to tools and operations according to explicitly defined permissions.
* Treat information returned by external tools as untrusted until it has been validated for the intended use.

### 5.4 Output Validation

The system must:

* Validate generated research outputs against the required report structure.
* Verify that citations refer to evidence actually retrieved and stored by the system.
* Identify material claims that lack supporting evidence.
* Validate financial calculations and check that required inputs are available.
* Ensure that valuation assumptions, estimates, and projections are clearly distinguished from verified facts.
* Prevent malformed or incomplete model outputs from being presented as complete reports.
* Provide a clear failure, partial-result, or insufficient-evidence response when validation fails.
* Avoid silently removing unresolved conflicts, material risks, or important limitations from the final report.

### 5.5 Deployment Access Protection

The MVP does not require a full user authentication and account-management system. However:

* A deployed instance must remain private or use a minimal access-control mechanism to prevent unauthorized research requests and document uploads.
* Access to research operations and document-processing functionality must be restricted to authorized users or callers.
* The system must not rely on obscurity of its URL as its only access-control measure.
* The selected deployment protection must be documented before public deployment.

---

## 6. Evaluation Requirements

### 6.1 Evaluation Dataset

The system must:

* Maintain a versioned evaluation dataset containing representative company research questions.
* Include factual questions, multi-hop research questions, unanswerable questions, and adversarial questions.
* Store expected answers or evaluation criteria and the relevant supporting sources for each question.
* Cover financial analysis, company fundamentals, industry research, competitive analysis, risk analysis, and valuation.
* Include sufficient information to evaluate retrieval quality and final report quality separately.
* Preserve a baseline evaluation dataset for measuring changes in system performance over time.

### 6.2 Retrieval Evaluation

The system must:

* Evaluate whether retrieved evidence is relevant to the research question.
* Measure retrieval quality using Precision@K, Recall@K, and Mean Reciprocal Rank (MRR).
* Evaluate whether known relevant sources appear among the top retrieved results.
* Evaluate retrieval performance across different research question categories.
* Identify cases where relevant evidence is missed or irrelevant evidence is retrieved.
* Compare retrieval results against a documented baseline.

### 6.3 Answer Evaluation

The system must:

* Evaluate the factual correctness of generated findings against reference evidence.
* Evaluate whether material claims are supported by the retrieved evidence.
* Measure research coverage against the requirements of each question.
* Evaluate the accuracy and completeness of citations.
* Assess the quality of financial analysis and the correctness of financial calculations.
* Evaluate valuation methodologies, assumptions, calculations, and scenario consistency.
* Assess whether contradictory evidence and uncertainty are represented correctly.
* Evaluate whether the final report follows the required structure.
* Track research quality alongside latency and cost without allowing speed or low cost to compensate for unreliable findings.

### 6.4 Unanswerable Cases

The system must:

* Include questions for which the available evidence is insufficient to produce a reliable answer.
* Evaluate whether the system recognizes insufficient evidence.
* Verify that the system does not invent facts, sources, financial figures, or citations to fill information gaps.
* Evaluate whether the system clearly communicates missing information and relevant limitations.
* Measure the quality of fallback responses.
* Verify that the system answers supported portions of a question without presenting unsupported portions as established facts.

### 6.5 Adversarial Cases

The system must:

* Maintain a test dataset containing documents with malicious or misleading instructions.
* Evaluate whether malicious document content can manipulate research planning, tool usage, or final outputs.
* Include tests for misleading financial claims, conflicting sources, fabricated-looking citations, and unsupported conclusions.
* Verify that material claims remain grounded in evidence despite adversarial content.
* Record attack outcomes and identify security weaknesses.
* Re-run adversarial tests after changes to prompts, models, retrieval, or security controls.

### 6.6 Regression Evaluation

The system must:

* Run the established evaluation dataset when significant changes are made to the research workflow.
* Compare new results against the recorded baseline.
* Detect regressions in retrieval quality, factual correctness, evidence grounding, citation quality, valuation calculations, and fallback behavior.
* Preserve evaluation results and relevant configuration details for comparison.
* Investigate significant regressions before accepting a change.
* Maintain regression tests for previously identified failures.

### 6.7 Evaluation Acceptance Criteria

The system must:

* Define baseline measurements and minimum acceptance thresholds in `evals/benchmark.md` and `evals/rubric.md` before implementation is considered complete.
* Evaluate retrieval quality, answer correctness, evidence grounding, citation validity, research coverage, uncertainty handling, and unanswerable-question behavior.
* Define acceptance criteria for adversarial-document tests and prompt-injection defenses.
* Record measured results against the defined thresholds.
* Document unmet thresholds, known weaknesses, and limitations rather than claiming success without evaluation evidence.
* Establish thresholds based on the evaluation dataset, risk of failure, and observed baseline rather than choosing arbitrary scores.
* Treat quality acceptance as separate from latency and cost measurements.

The initial evaluation dataset should contain 40 questions:

* 15 factual questions.
* 15 multi-hop questions.
* 5 unanswerable questions.
* 5 adversarial or poisoned-document questions.

The dataset must be versioned, and its composition and limitations must be documented. The benchmark should be expanded if these 40 questions do not adequately represent the intended research tasks.

### 6.8 A/B Experiments

The system must:

* Support controlled experiments comparing alternative research and retrieval approaches.
* Define a hypothesis and evaluation metrics before each experiment.
* Compare hybrid retrieval against vector-only retrieval.
* Compare reranking against retrieval without reranking.
* Compare query rewriting against retrieval without query rewriting.
* Evaluate research quality, retrieval metrics, latency, and cost for each alternative.
* Record experiment configurations, dataset versions, results, and limitations.
* Document the engineering decision and its supporting evidence after each experiment.
* Update relevant architecture decision records when experimental results change or validate a design decision.
* Avoid adopting a more complex approach solely because it appears theoretically superior; decisions must consider measured results.

---

## 7. Constraints

### 7.1 MVP Constraints

The MVP must:

* Focus on researching one publicly listed target company per research task.
* Support company research covering business fundamentals, industry, management, financial performance, competition, risks, and valuation.
* Generate evidence-backed research reports with citations, thesis, antithesis, and scenario analysis.
* Support bounded follow-up research rather than unrestricted autonomous research.
* Prioritize factual correctness, evidence quality, research coverage, and reliability over response speed.
* Support a single-user workflow without a full authentication and account-management system.
* Remain private or use a minimal access-control mechanism when deployed, so unauthorized users cannot submit research requests or upload documents.
* Exclude autonomous trading, trade execution, portfolio management, and personalized investment recommendations.
* Deliver the core research workflow before adding advanced features or expanding the supported use cases.

Competitive research within the MVP may compare the target company with selected competitors using relevant evidence. It does not require running a complete, independent research workflow for every competitor.

### 7.2 Data Source Constraints

The MVP must:

* Use publicly available company information and financial data from accessible sources.
* Support annual reports supplied by the user and relevant publicly available company filings.
* Use financial data sources for relevant financial statements, historical metrics, and market data when available.
* Use web sources for relevant industry, competitor, management, and business research.
* Preserve the source and retrieval context of information used in research findings.
* Handle unavailable, incomplete, outdated, or conflicting source data explicitly.
* Respect applicable source access restrictions, rate limits, and usage terms.
* Avoid assuming that every required piece of company information will be available through every source.
* Identify source dates and data freshness when available and relevant to the analysis.

### 7.3 Document Constraints

The MVP must:

* Support PDF annual reports as the primary uploaded document format.
* Enforce configurable maximum upload size and page-count limits.
* Define the initial numerical size and page-count limits before implementation.
* Initially target ingestion of a 300-page annual report within 5 minutes under defined test conditions, provided the test document is within the configured limits.
* Validate document type, size, and readability before processing.
* Handle scanned, malformed, corrupted, or partially unreadable PDFs gracefully.
* Identify documents that fail processing and prevent incomplete ingestion from being treated as successful.
* Avoid creating duplicate document records when the same document is uploaded repeatedly.
* Preserve document identifiers and available page-level references for evidence traceability.
* Treat uploaded documents as untrusted content.

### 7.4 Operational Constraints

The MVP must:

* Operate within the available compute, storage, and external API budgets.
* Account for external model and data-source availability, rate limits, latency, and service failures.
* Support background processing for research tasks that exceed a normal interactive request.
* Track the progress and status of long-running research tasks.
* Support recovery or retry of interrupted processing where possible.
* Prevent recoverable failures from silently producing incomplete or misleading reports.
* Maintain sufficient logs and evaluation records to investigate research failures.
* Measure the cost of research runs and identify expensive processing stages.
* Support deployment and operation with a manageable number of services.
* Avoid requiring large-scale distributed infrastructure for the initial MVP.

---

## 8. Explicitly Out of Scope

### 8.1 Full Authentication and Account Management

The MVP will not include:

* User registration and login flows.
* Password management or account recovery.
* OAuth or third-party authentication.
* Role-based user account management.
* A full identity and account-management system.

This exclusion does not remove the deployment access-protection requirement in Section 5.5. The deployed application must remain private or have a minimal access-control mechanism.

### 8.2 Multi-User and Multi-Tenancy

The MVP will not include:

* Multiple user accounts with separate workspaces.
* Tenant-level data isolation and administration.
* Shared research workspaces between users.
* User-specific permissions and collaboration features.

### 8.3 Portfolio Management

The MVP will not include:

* Personal portfolio tracking.
* Portfolio allocation and rebalancing.
* Asset allocation recommendations.
* Portfolio performance and returns tracking.
* Personalized portfolio risk analysis.

### 8.4 Autonomous Trading

The MVP will not include:

* Automatic execution of stock trades.
* Automatic placement or modification of orders.
* Autonomous decisions to buy, sell, or hold securities.
* Direct control of trading accounts.
* Trading strategies executed without human authorization.

### 8.5 Personalized Investment Advice

The MVP will not include:

* Personalized buy, sell, or hold recommendations.
* Recommendations based on an individual's financial circumstances or risk tolerance.
* Personalized investment allocation or position-sizing advice.
* Guarantees about investment returns or future stock performance.

The system will provide company research and evidence-backed analysis to support the user's independent assessment.

### 8.6 Broker Integration

The MVP will not include:

* Connections to brokerage accounts.
* Retrieval of personal holdings or transaction history from brokers.
* Trade execution through broker APIs.
* Automated order management.
* Broker account synchronization.

### 8.7 Real-Time Market Monitoring

The MVP will not include:

* Continuous monitoring of stock prices or market movements.
* Real-time alerts for financial news or company announcements.
* Automated notifications triggered by price movements or market events.
* Continuous background research triggered by new market information.

The MVP may use available reference market data when conducting a research task, subject to source availability and data freshness.

### 8.8 Other Deferred Features

The following features are deferred beyond the initial MVP:

* Mobile applications.
* Large-scale distributed processing infrastructure.
* Kafka or Celery-based distributed task processing.
* Model fine-tuning.
* Complex long-term agent memory.
* Real-time streaming research output.
* Unrestricted continuous autonomous research.
* Automatic investment recommendations.
* Support for multiple uploaded document formats beyond the initial PDF scope.
* Comprehensive multi-company comparative research that runs separate, full research workflows for multiple companies and generates a dedicated comparative report.
* Automated generation of research reports on a recurring schedule.
* Advanced user customization of report templates.
* Production-scale multi-tenant infrastructure.

Comparing the target company with selected competitors remains in scope under Section 3.3. The deferred feature is comprehensive, independent multi-company research, not competitor analysis itself.

These features may be reconsidered after the core research workflow, evidence traceability, security controls, and evaluation process have been validated.
