# ADR-003: Bounded Research Execution with Durable Checkpoints

- **Status:** Accepted for MVP
- **Date:** 2026-10-10
- **Decision owner:** Project engineer

## 1. Context

A company research task spans multiple activities: identity resolution, source collection, evidence retrieval, financial calculations, conflict handling, valuation, rating, and report validation.

External services may fail, evidence may be insufficient, and some stages may take substantial time. An unrestricted agent loop would make execution cost, task completion, and recovery difficult to reason about.

## 2. Decision drivers

- Every task must have a unique identifier and observable state.
- Execution must have explicit runtime, research-step, retry, and external-call limits.
- Completed work should survive interruption where practical.
- Retries must be bounded and safe.
- The report must distinguish completed, failed, cancelled, and incomplete tasks.
- Material claims must remain traceable to evidence and calculations.
- A task must never be marked completed merely because report generation returned text.

## 3. Options considered

### Option A — Unrestricted autonomous agent loop

Allow the agent to choose and repeat actions until it decides the research is complete.

**Advantages**
- Flexible exploration
- Can adapt its actions dynamically

**Disadvantages**
- Difficult to bound runtime and cost
- Greater risk of unnecessary calls or repeated work
- Harder to reproduce and debug
- Completion criteria may be inconsistent

### Option B — Explicit staged workflow with bounded decisions

Use named research stages, defined transitions, configurable limits, and validation gates. Allow limited adaptive research within those boundaries.

**Advantages**
- Easier to inspect and evaluate
- Explicit failure and recovery paths
- More predictable resource consumption
- Clear points for validation and evidence recording

**Disadvantages**
- Requires explicit state and transition design
- Less flexible for research outside the defined workflow
- The stage sequence may need revision as evaluation reveals gaps

## 4. Decision

Use an explicit staged workflow with bounded adaptive research.

The initial logical stages are:

1. Validate request and resolve company identity.
2. Establish the report as-of date and research requirements.
3. Collect available source records and uploaded-document evidence.
4. Retrieve and assess evidence.
5. Detect information gaps and material conflicts.
6. Perform validated financial calculations.
7. Produce supported valuation scenarios and rating, or an insufficient-evidence outcome.
8. Generate and validate the report.
9. Persist the final status, report, provenance, and limitations.

A stage may request bounded additional research when a material information gap is identified. Every additional action consumes a configured resource limit.

## 5. State and recovery rules

- Persist task state and valid completed-stage outputs at documented checkpoints.
- Record stage attempts, failures, timestamps, and recovery decisions.
- Retry only eligible transient failures, with bounded attempts.
- Do not retry deterministic validation failures indefinitely.
- Make repeated stage execution safe through idempotency or duplicate-work detection.
- On cancellation, stop safely at a supported boundary and preserve valid completed work.
- If a required stage cannot finish within limits, return an explicit incomplete or failed outcome.
- A report can be marked completed only after required validation succeeds.

The exact storage technology and task-queue implementation are separate decisions and are not specified by this ADR.

## 6. Consequences

**Positive**
- Research execution is easier to audit and reproduce.
- Resource usage is bounded.
- Failure and recovery behavior can be tested systematically.
- Report completion has explicit criteria.

**Negative**
- The workflow requires more explicit state management.
- Stage definitions can become rigid if they are not revised based on evaluation.
- Checkpointing and idempotency introduce additional test requirements.

## 7. Decisions required before implementation

Set and document initial values for:
- Maximum queued jobs
- Maximum total task runtime
- Maximum research steps per task
- Maximum retries per stage
- Maximum external calls per task
- Cancellation boundaries and behavior

Choose conservative initial limits and expose them through configuration. Record the workload and rationale used to choose them.

## 8. Validation plan

Test:
- A successful end-to-end research task
- An external dependency failure
- Exhausted retry and research-step limits
- Worker interruption after a completed checkpoint
- Safe restart without duplicated completed work
- Cancellation of queued and running tasks
- A task with insufficient evidence
- A task that fails report validation
- Accurate final states and preserved provenance

Record recovery success, duplicate processing, state consistency, task duration, resource consumption, and incomplete-task reporting.

## 9. Revisit conditions

Reconsider this decision if benchmark results show that the staged workflow prevents necessary research, or if operational evidence shows that the state model is too complex or insufficient for reliable recovery.

Any alternative must retain bounded execution, explicit completion criteria, auditable state, and safe failure handling.