# AI Critique — Equity / Business Research Agent

**Document:** `doc/ai_critique.md`  
**Review stage:** Requirements and MVP scope  
**Status:** Design review; findings require resolution or explicit acceptance

## 1. Purpose

Challenge the current requirements and scope before implementation. The goal is to identify contradictions, hidden assumptions, unnecessary scope, and risks that could make the system unreliable or impossible to evaluate.

This review evaluates the specification, not an implemented system. No performance, quality, or security results are claimed.

## 2. Findings

### F-01 — Valuation must not be forced when evidence is insufficient

**Severity:** Critical

**Issue**

The scope says the system should always attempt a valuation range, even when data is missing. This could encourage the system to produce an apparently precise valuation from inadequate or inconsistent inputs.

**Recommended correction**

- Attempt valuation only to the extent supported by available evidence.
- Validate required inputs before calculating a valuation.
- If a decision-useful estimate cannot be supported, return `insufficient_evidence`.
- If a speculative range is still useful, label it explicitly as non-decision-grade, identify unsupported assumptions, and avoid presenting it as a reliable target.
- A missing valuation must not be silently replaced by an invented estimate.

**Acceptance test**

Provide a company case with insufficient financial inputs. The report must disclose the gap and must not present an unsupported valuation or rating as decision-grade.

### F-02 — Citation coverage is not the same as evidence support

**Severity:** Critical

**Issue**

A report can contain citations on every paragraph while still making claims those sources do not support. A cited annual report may also refer to a different financial period, unit, or entity than the claim.

**Recommended correction**

- Evaluate citation support at the material-claim level.
- Check company identity, reporting period, units, context, and whether the cited passage entails or directly supports the claim.
- Preserve source location and evidence identifiers.
- Distinguish sourced facts, calculated values, estimates, assumptions, and interpretations.
- Treat unsupported material financial claims as critical failures.

**Acceptance test**

Include examples with irrelevant citations, correct sources but wrong periods, and valid calculations based on cited inputs. The evaluator must distinguish these cases.

### F-03 — The evaluation benchmark is useful for regression, not proof of broad reliability

**Severity:** High

**Issue**

The 40-question benchmark is a reasonable initial engineering benchmark, but five questions per selected category may reveal obvious failures without establishing robust reliability. A score can also hide a severe failure behind a high aggregate score.

**Recommended correction**

- Retain the 40-question benchmark for the first release.
- Report raw counts alongside percentages.
- Keep results separated by category and track material failures individually.
- Add cases whenever a real defect is discovered.
- Maintain a separate critical-failure suite for deterministic calculations, unsupported material claims, collection isolation, recovery, and defined prompt-injection attacks.
- Avoid claims of statistical certainty or general immunity based on this dataset.

**Acceptance test**

A release report must show category-level results and critical failures. Passing the aggregate score must not override a failed mandatory gate.

### F-04 — Data-source availability and freshness need explicit handling

**Severity:** High

**Issue**

The system depends on public filings, company sources, financial data, historical prices, and competitor information. These sources may be unavailable, stale, inconsistent, incomplete, or subject to access restrictions.

**Recommended correction**

- Record source identity, retrieval time, publication/reporting period, and applicable as-of date.
- Prefer authoritative sources for material company disclosures.
- Separate a source's publication date from the date the underlying financial information covers.
- Define fallback behavior when a source is unavailable.
- Disclose stale or missing data and do not imply that the report contains real-time market information.
- Confirm API terms, access constraints, and permitted use before implementation.

**Acceptance test**

Simulate an unavailable source and a conflict between sources. The task must finish with explicit limitations or an incomplete status rather than silently fabricating missing information.

### F-05 — The MVP includes a potential source of scope creep

**Severity:** Medium

**Issue**

Technical analysis is included alongside company fundamentals, business analysis, valuation, and investment thesis development. This adds indicators, price-history validation, and another evaluation surface without being essential to validating the core evidence-backed research workflow.

**Recommended correction**

Keep basic historical price trends and a small, explicitly defined set of technical indicators only if they can be implemented and tested within the available project budget. Defer complex technical strategies, trading signals, and predictive models. Do not let technical analysis block validation of the core fundamental research workflow unless it is part of a declared release requirement.

**Acceptance test**

The report must distinguish descriptive historical indicators from predictions. No feature may imply a guaranteed future price or autonomous trading decision.

### F-06 — Background execution needs operational limits before implementation

**Severity:** High

**Issue**

The scope requires queuing, retries, checkpointing, cancellation, and recovery, but several numerical limits remain undecided. Implementing these behaviors without explicit bounds risks runaway work, excessive cost, and ambiguous task states.

**Recommended correction**

Before implementation, choose and document:
- Maximum queued jobs
- Maximum total runtime
- Maximum research steps
- Maximum retries per stage
- Maximum external calls per task
- Cancellation behavior at each stage
- How interrupted tasks resume and how duplicate work is prevented

Use conservative initial values and make configurable limits observable.

**Acceptance test**

Exhaust each limit and interrupt a running task. The system must stop safely, preserve valid completed work, and report an accurate terminal or resumable state.

## 3. Cross-document consistency checks

Before implementation, verify these points across requirements, scope, workflows, contracts, and success criteria:

1. **Rating versus insufficient evidence:** The report must support an explicit insufficient-evidence outcome; it must not force a buy/hold/sell rating.
2. **Source freshness versus as-of date:** Every report must identify its as-of date and disclose relevant source-age limitations.
3. **Collections versus authentication:** Collection isolation is a data-separation requirement, not proof that user authentication or multi-user authorization exists.
4. **Performance targets versus release gates:** Diagnostic latency and cost targets must remain distinct from mandatory safety, evidence-quality, calculation, and recovery gates.
5. **Deletion versus retained evidence:** Deletion must cover the report, uploaded documents, extracted content, evidence mappings, and derived artifacts within the documented retention boundary.
6. **Research limits versus recovery:** Retry and runtime exhaustion must produce an explicit incomplete or failed outcome, never a false completed report.

## 4. Recommended disposition

| Finding | Disposition |
|---|---|
| F-01 Valuation safety | Accept and enforce |
| F-02 Citation support | Accept and enforce |
| F-03 Benchmark limitations | Accept; retain benchmark with caveats |
| F-04 Source freshness and availability | Accept and add to contracts/workflows |
| F-05 Technical-analysis scope | Accept the scope reduction |
| F-06 Runtime and queue limits | Accept; resolve values before implementation |

## 5. Review outcome

The specification is sufficiently developed to proceed to architecture decisions, provided the critical evidence and valuation rules remain mandatory.

Before implementation, close the operational-limit decisions and verify cross-document consistency. Record any rejected recommendation with a reason rather than silently ignoring it.

This critique identifies risks from specification review. It does not establish that any risk has been eliminated in code.