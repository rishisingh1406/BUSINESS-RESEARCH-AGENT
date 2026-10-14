"""Pydantic contracts for the Equity / Business Research Agent.

Source of truth: doc/09_contracts.md and related project requirements.
This module defines data shapes and structural validation. It does not
implement orchestration, persistence, authorization, or business policy.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class ContractModel(BaseModel):
    """Base for explicit, forward-compatible boundary contracts."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


# ---------------------------------------------------------------------------
# Shared enums and primitives
# ---------------------------------------------------------------------------

class Outcome(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class CompanyResolutionStatus(str, Enum):
    CONFIRMED = "confirmed"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"
    FAILED = "failed"


class ResearchTaskStatus(str, Enum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_LIMITATIONS = "completed_with_limitations"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ResearchStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class SourceType(str, Enum):
    OFFICIAL_COMPANY = "official_company"
    REGULATORY_FILING = "regulatory_filing"
    STOCK_EXCHANGE = "stock_exchange"
    ANNUAL_REPORT = "annual_report"
    FINANCIAL_DATA = "financial_data"
    HISTORICAL_PRICE = "historical_price"
    INDUSTRY_RESEARCH = "industry_research"
    COMPETITOR_SOURCE = "competitor_source"
    NEWS = "news"
    WEB_PAGE = "web_page"
    USER_UPLOAD = "user_upload"
    OTHER = "other"


class RetrievalStatus(str, Enum):
    SUCCESS = "success"
    EMPTY = "empty"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    BLOCKED = "blocked"


class IngestionStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


class EvidenceStrength(str, Enum):
    STRONG = "strong"
    PARTIAL = "partial"
    CONFLICTING = "conflicting"
    INSUFFICIENT = "insufficient"


class ClaimType(str, Enum):
    FACT = "fact"
    ANALYSIS = "analysis"
    INTERPRETATION = "interpretation"
    ASSUMPTION = "assumption"
    ESTIMATE = "estimate"
    PROJECTION = "projection"
    HYPOTHESIS = "hypothesis"


class FindingStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONFLICTED = "conflicted"
    UNSUPPORTED = "unsupported"
    INCOMPLETE = "incomplete"
    REJECTED = "rejected"


class ConflictType(str, Enum):
    VALUE_MISMATCH = "value_mismatch"
    PERIOD_MISMATCH = "period_mismatch"
    UNIT_MISMATCH = "unit_mismatch"
    ENTITY_MISMATCH = "entity_mismatch"
    DEFINITION_MISMATCH = "definition_mismatch"
    SOURCE_DISAGREEMENT = "source_disagreement"
    OTHER = "other"


class ConflictResolutionStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    UNRESOLVED = "unresolved"
    NOT_APPLICABLE = "not_applicable"


class InformationGapStatus(str, Enum):
    OPEN = "open"
    RESEARCHING = "researching"
    SATISFIED = "satisfied"
    UNAVAILABLE = "unavailable"
    NOT_FOUND = "not_found"
    BLOCKED = "blocked"
    CLOSED_WITH_LIMITATION = "closed_with_limitation"


class ValueOrigin(str, Enum):
    REPORTED = "reported"
    CALCULATED = "calculated"
    ESTIMATED = "estimated"
    INFERRED = "inferred"
    PROJECTED = "projected"


class CalculationStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    INVALID_INPUT = "invalid_input"
    MISSING_INPUT = "missing_input"
    INCOMPATIBLE_PERIODS = "incompatible_periods"
    INCOMPATIBLE_UNITS = "incompatible_units"
    FAILED = "failed"


class ValuationStatus(str, Enum):
    SUPPORTED = "supported"
    SPECULATIVE_NOT_DECISION_GRADE = "speculative_not_decision_grade"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"


class ValuationMethod(str, Enum):
    DCF = "dcf"
    PE_MULTIPLE = "pe_multiple"
    EV_EBITDA = "ev_ebitda"
    PRICE_TO_BOOK = "price_to_book"
    DIVIDEND_DISCOUNT = "dividend_discount"
    SUM_OF_PARTS = "sum_of_parts"
    OTHER = "other"


class ScenarioType(str, Enum):
    BULL = "bull"
    BASE = "base"
    BEAR = "bear"


class RatingValue(str, Enum):
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RatingStatus(str, Enum):
    DETERMINED = "determined"
    LOW_CONFIDENCE = "low_confidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    BLOCKED = "blocked"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    VALIDATING = "validating"
    VALID = "valid"
    VALID_WITH_LIMITATIONS = "valid_with_limitations"
    INVALID = "invalid"
    BLOCKED = "blocked"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    PASSED_WITH_LIMITATIONS = "passed_with_limitations"
    FAILED = "failed"
    BLOCKED = "blocked"


class FindingSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    VALIDATION = "validation"
    IDENTITY_RESOLUTION = "identity_resolution"
    SOURCE_UNAVAILABLE = "source_unavailable"
    EXTERNAL_SERVICE = "external_service"
    INGESTION = "ingestion"
    EXTRACTION = "extraction"
    RETRIEVAL = "retrieval"
    ANALYSIS = "analysis"
    CALCULATION = "calculation"
    VALIDATION_GATE = "validation_gate"
    RESOURCE_LIMIT = "resource_limit"
    STATE_TRANSITION = "state_transition"
    CANCELLATION = "cancellation"
    SECURITY = "security"
    PERSISTENCE = "persistence"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ResourceLimitType(str, Enum):
    RUNTIME_SECONDS = "runtime_seconds"
    RESEARCH_STEPS = "research_steps"
    STAGE_RETRIES = "stage_retries"
    EXTERNAL_API_CALLS = "external_api_calls"
    QUEUE_CAPACITY = "queue_capacity"


class CheckpointStatus(str, Enum):
    VALID = "valid"
    STALE = "stale"
    INVALID = "invalid"
    RESTORED = "restored"


class RecoveryStatus(str, Enum):
    RESUMED = "resumed"
    RESTARTED_STAGE = "restarted_stage"
    NOT_RECOVERABLE = "not_recoverable"
    RETRY_EXHAUSTED = "retry_exhausted"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EvaluationStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ExperimentStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeletionTargetType(str, Enum):
    TASK = "task"
    COLLECTION = "collection"
    DOCUMENT = "document"
    SOURCE = "source"
    EVIDENCE = "evidence"
    FINDING = "finding"
    REPORT = "report"


class DeletionStatus(str, Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"


class MissingValueReason(str, Enum):
    UNKNOWN = "unknown"
    NOT_AVAILABLE_FROM_SOURCES = "not_available_from_sources"
    NOT_APPLICABLE = "not_applicable"
    NOT_YET_COLLECTED = "not_yet_collected"
    EXTRACTION_FAILED = "extraction_failed"
    CONFLICTING_VALUES = "conflicting_values"
    INTENTIONALLY_OMITTED = "intentionally_omitted"


class TimestampedModel(ContractModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Research request and company identity
# ---------------------------------------------------------------------------

class ResearchOptions(ContractModel):
    """Only expose options the implementation explicitly supports."""
    include_historical_prices: bool = True
    include_technical_analysis: bool = True
    financial_history_years: int = Field(default=5, ge=1, le=5)
    language: str = "en"
    additional_options: dict[str, Any] = Field(default_factory=dict)


class ResearchRequest(ContractModel):
    schema_version: str = "1.0"
    company_identifier: str = Field(min_length=1, max_length=300)
    reference_date: date
    collection_id: str = Field(min_length=1)
    annual_report_document_ids: list[str] = Field(default_factory=list)
    research_options: ResearchOptions = Field(default_factory=ResearchOptions)
    request_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("company_identifier")
    @classmethod
    def strip_company_identifier(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("company_identifier must not be blank")
        return value


class ValidationIssue(ContractModel):
    field: str | None = None
    code: str
    message: str
    severity: FindingSeverity = FindingSeverity.MEDIUM


class RequestAcceptance(ContractModel):
    task_id: str
    status: ResearchTaskStatus
    accepted_at: datetime
    message: str
    validation_errors: list[ValidationIssue] = Field(default_factory=list)


class CompanyIdentity(ContractModel):
    company_id: str | None = None
    company_name: str | None = None
    ticker: str | None = None
    exchange: str | None = None
    country: str = "India"
    resolution_status: CompanyResolutionStatus
    source_references: list[str] = Field(default_factory=list)
    clarification_reason: str | None = None

    @model_validator(mode="after")
    def confirmed_identity_must_be_complete(self):
        if self.resolution_status == CompanyResolutionStatus.CONFIRMED:
            if not self.company_id or not self.company_name:
                raise ValueError("confirmed identity requires company_id and company_name")
        if self.resolution_status == CompanyResolutionStatus.AMBIGUOUS and not self.clarification_reason:
            raise ValueError("ambiguous identity requires clarification_reason")
        return self


# ---------------------------------------------------------------------------
# Research plan and source acquisition
# ---------------------------------------------------------------------------

class ResourceLimits(ContractModel):
    max_runtime_seconds: int = Field(gt=0)
    max_research_steps: int = Field(gt=0)
    max_retries_per_stage: int = Field(ge=0)
    max_external_api_calls: int = Field(gt=0)
    max_queue_size: int = Field(gt=0)


class ResearchStep(ContractModel):
    step_id: str
    task_id: str
    title: str
    objective: str
    required_information: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    required: bool = True
    status: ResearchStepStatus = ResearchStepStatus.PENDING
    evidence_requirements: list[str] = Field(default_factory=list)
    limitation: str | None = None


class ResearchPlan(ContractModel):
    task_id: str
    plan_version: int = Field(ge=1)
    created_at: datetime
    research_tasks: list[ResearchStep]
    required_sections: list[str]
    resource_limits: ResourceLimits
    completion_conditions: list[str] = Field(default_factory=list)


class SourceRecord(TimestampedModel):
    source_id: str
    collection_id: str
    source_type: SourceType
    source_name: str
    origin: str | None = None
    title: str | None = None
    url: HttpUrl | None = None
    publication_date: date | None = None
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None
    retrieved_at: datetime | None = None
    document_id: str | None = None
    version: str | None = None
    retrieval_status: RetrievalStatus
    warnings: list[str] = Field(default_factory=list)
    error_id: str | None = None


# ---------------------------------------------------------------------------
# Document ingestion
# ---------------------------------------------------------------------------

class DocumentIngestionRequest(ContractModel):
    document_id: str
    collection_id: str
    source_id: str | None = None
    company_id: str | None = None
    company_name: str | None = None
    financial_year: str | None = None
    original_filename: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    # Supported canonical MIME types: PDF, Markdown, HTML, and plain text.
    # Aliases are normalized by the validator below.
    content_type: str = "application/pdf"
    file_size_bytes: int = Field(gt=0)
    # This limit is intended for PDFs. Non-PDF parsers should leave page_count unset.
    page_count: int | None = Field(default=None, ge=1, le=300)
    upload_timestamp: datetime
    document_type: str = "annual_report"
    storage_uri: str = Field(min_length=1)
    collection_idempotency_key: str | None = None

    @field_validator("original_filename")
    @classmethod
    def filename_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("original_filename must not be blank")
        return value

    @field_validator("content_type")
    @classmethod
    def normalize_supported_content_type(cls, value: str) -> str:
        value = value.strip().lower().split(";", 1)[0].strip()
        aliases = {
            "application/pdf": "application/pdf",
            "text/markdown": "text/markdown",
            "text/x-markdown": "text/markdown",
            "text/html": "text/html",
            "text/plain": "text/plain",
        }
        if value not in aliases:
            raise ValueError(
                "unsupported content_type; expected PDF, Markdown, HTML, or plain text"
            )
        return aliases[value]

    @field_validator("storage_uri")
    @classmethod
    def storage_uri_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("storage_uri must not be blank")
        return value


class DocumentIngestionResult(ContractModel):
    document_id: str
    collection_id: str
    status: IngestionStatus
    content_sha256: str
    duplicate_of_document_id: str | None = None
    extracted_pages: int = Field(default=0, ge=0)
    chunk_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_id: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    quarantine_uri: str | None = None


    @model_validator(mode="after")
    def ingestion_result_consistency(self):
        if self.status == IngestionStatus.DUPLICATE and not self.duplicate_of_document_id:
            raise ValueError("duplicate ingestion requires duplicate_of_document_id")
        if self.status != IngestionStatus.DUPLICATE and self.duplicate_of_document_id:
            raise ValueError("duplicate_of_document_id is only valid for duplicate status")
        if self.status in {IngestionStatus.FAILED, IngestionStatus.QUARANTINED, IngestionStatus.REJECTED}:
            if not (self.error_id or (self.error_message and self.error_message.strip())):
                raise ValueError("failed, quarantined, or rejected ingestion requires an error reference or message")
        if self.started_at and self.completed_at and self.completed_at < self.started_at:
            raise ValueError("completed_at must be greater than or equal to started_at")
        return self


class ExtractedChunk(ContractModel):
    chunk_id: str
    document_id: str
    collection_id: str
    chunk_text: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    section_title: str | None = None
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    extraction_method: Literal["text", "ocr", "mixed", "unknown"] = "unknown"
    extraction_warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("chunk_text")
    @classmethod
    def chunk_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chunk_text must not be blank")
        return value

    @model_validator(mode="after")
    def chunk_offsets_are_ordered(self):
        if self.start_offset is not None and self.end_offset is not None:
            if self.end_offset < self.start_offset:
                raise ValueError(
                    "end_offset must be greater than or equal to start_offset"
                )
        return self


# ---------------------------------------------------------------------------
# Evidence and retrieval
# ---------------------------------------------------------------------------

class EvidenceRecord(TimestampedModel):
    evidence_id: str
    task_id: str
    collection_id: str
    source_id: str
    document_id: str | None = None
    chunk_id: str | None = None
    quote_or_excerpt: str = Field(min_length=1)
    source_location: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    section_title: str | None = None
    source_url: HttpUrl | None = None
    publication_date: date | None = None
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None
    relevance_score: float | None = None
    evidence_strength: EvidenceStrength = EvidenceStrength.INSUFFICIENT
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalRequest(ContractModel):
    task_id: str
    collection_id: str
    query: str = Field(min_length=1)
    research_step_id: str | None = None
    company_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=100)
    filters: dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = True


class RetrievedEvidence(ContractModel):
    evidence_id: str
    score: float | None = None
    rank: int = Field(ge=1)
    retrieval_method: str | None = None


class RetrievalResponse(ContractModel):
    task_id: str
    status: RetrievalStatus
    query: str
    results: list[RetrievedEvidence] = Field(default_factory=list)
    evidence_records: list[EvidenceRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_id: str | None = None


# ---------------------------------------------------------------------------
# Findings, conflicts, and information gaps
# ---------------------------------------------------------------------------

class AnalysisFinding(TimestampedModel):
    finding_id: str
    task_id: str
    company_id: str
    research_step_id: str | None = None
    title: str
    statement: str
    claim_type: ClaimType
    status: FindingStatus
    evidence_ids: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None


class ConflictRecord(TimestampedModel):
    conflict_id: str
    task_id: str
    conflict_type: ConflictType
    description: str
    evidence_ids: list[str] = Field(min_length=2)
    values: list[str] = Field(default_factory=list)
    resolution_status: ConflictResolutionStatus = ConflictResolutionStatus.OPEN
    selected_value: str | None = None
    resolution_rationale: str | None = None
    limitations: list[str] = Field(default_factory=list)


class InformationGap(TimestampedModel):
    gap_id: str
    task_id: str
    research_step_id: str | None = None
    requirement: str
    importance: FindingSeverity = FindingSeverity.MEDIUM
    status: InformationGapStatus = InformationGapStatus.OPEN
    searches_performed: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    impact_on_conclusion: str | None = None
    next_action: str | None = None
    resolution_note: str | None = None


class MissingValue(ContractModel):
    reason: MissingValueReason
    explanation: str | None = None
    searched_sources: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Financial data and reproducible calculations
# ---------------------------------------------------------------------------

class FinancialValue(ContractModel):
    metric_name: str
    value: float | None = None
    currency: str | None = None
    unit: str | None = None
    scale: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    fiscal_year: str | None = None
    basis: Literal["consolidated", "standalone", "unknown"] = "unknown"
    origin: ValueOrigin
    evidence_ids: list[str] = Field(default_factory=list)
    missing: MissingValue | None = None

    @model_validator(mode="after")
    def missing_value_consistency(self):
        if self.value is None and self.missing is None:
            raise ValueError("a missing financial value requires an explicit missing reason")
        if self.value is not None and self.missing is not None:
            raise ValueError("a present financial value must not also carry a missing reason")
        return self


class CalculationInput(ContractModel):
    name: str
    value: float
    unit: str | None = None
    currency: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    origin: ValueOrigin = ValueOrigin.REPORTED


class FinancialCalculation(ContractModel):
    calculation_id: str
    task_id: str
    metric_name: str
    status: CalculationStatus
    inputs: list[CalculationInput] = Field(default_factory=list)
    formula: str
    method_version: str | None = None
    output_value: float | None = None
    output_unit: str | None = None
    output_currency: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    rounding_rule: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_id: str | None = None

    @model_validator(mode="after")
    def successful_calculation_has_output(self):
        if self.status == CalculationStatus.SUCCESS and self.output_value is None:
            raise ValueError("successful calculation requires output_value")
        if self.status in {CalculationStatus.MISSING_INPUT, CalculationStatus.INVALID_INPUT} and not self.warnings:
            raise ValueError("invalid or missing-input calculation should explain the issue in warnings")
        return self


class FinancialStatement(ContractModel):
    statement_type: Literal["income_statement", "balance_sheet", "cash_flow"]
    company_id: str
    period_start: date | None = None
    period_end: date
    fiscal_year: str | None = None
    basis: Literal["consolidated", "standalone", "unknown"] = "unknown"
    values: list[FinancialValue] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Valuation, scenarios, and rating
# ---------------------------------------------------------------------------

class ValuationAssumption(ContractModel):
    name: str
    value: float | str
    unit: str | None = None
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    is_estimate: bool = False
    sensitivity_material: bool = False


class ValuationRange(ContractModel):
    low: float
    base: float | None = None
    high: float

    @model_validator(mode="after")
    def range_order(self):
        if self.low > self.high:
            raise ValueError("valuation low must be <= high")
        if self.base is not None and not self.low <= self.base <= self.high:
            raise ValueError("valuation base must be between low and high")
        return self


class ValuationRecord(TimestampedModel):
    task_id: str
    company_id: str
    valuation_id: str
    status: ValuationStatus
    method: ValuationMethod
    methodology_reference: str | None = None
    currency: str = "INR"
    value_basis: str = "per_share"
    reference_date: date
    valuation_range: ValuationRange | None = None
    current_or_reference_price: float | None = None
    assumptions: list[ValuationAssumption] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    sensitivity_notes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valuation_status_consistency(self):
        if self.status == ValuationStatus.SUPPORTED and self.valuation_range is None:
            raise ValueError("supported valuation requires a valuation range")
        if self.status == ValuationStatus.SPECULATIVE_NOT_DECISION_GRADE:
            if not self.limitations:
                raise ValueError("speculative valuation must disclose limitations")
        return self


class ScenarioRecord(ContractModel):
    scenario_id: str
    scenario_type: ScenarioType
    description: str
    assumptions: list[ValuationAssumption] = Field(default_factory=list)
    valuation_range: ValuationRange | None = None
    conditions_required: list[str] = Field(default_factory=list)
    risks_and_uncertainties: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class InvestmentRating(ContractModel):
    task_id: str
    company_id: str
    rating: RatingValue
    status: RatingStatus
    investment_horizon: str | None = None
    methodology_reference: str | None = None
    valuation_reference: str | None = None
    rationale: str
    supporting_finding_ids: list[str] = Field(default_factory=list)
    opposing_finding_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    conditions_that_change_rating: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ThesisAnalysis(ContractModel):
    thesis: list[str] = Field(default_factory=list)
    antithesis: list[str] = Field(default_factory=list)
    thesis_invalidation_conditions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    material_conflict_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Report and report validation
# ---------------------------------------------------------------------------

REQUIRED_REPORT_SECTIONS = [
    "executive_summary",
    "company_history_and_business_model",
    "management_and_corporate_governance",
    "industry_overview",
    "financial_and_fundamental_analysis",
    "competitor_comparison",
    "risks_and_uncertainties",
    "valuation_and_sensitivities",
    "bull_base_bear_scenarios",
    "historical_price_and_technical_analysis",
    "investment_thesis_and_antithesis",
    "investment_rating",
    "missing_information_conflicts_and_limitations",
    "sources_and_supporting_evidence",
]


class ReportCitation(ContractModel):
    citation_id: str
    evidence_id: str
    source_id: str
    document_id: str | None = None
    url: HttpUrl | None = None
    page_number: int | None = Field(default=None, ge=1)
    section_title: str | None = None
    source_location: str | None = None
    quote_or_excerpt: str | None = None


class ReportClaim(ContractModel):
    claim_id: str
    text: str
    claim_type: ClaimType
    finding_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    limitation: str | None = None


class ReportSection(ContractModel):
    section_id: str
    title: str
    content: str = ""
    required: bool = True
    status: Literal["complete", "partial", "missing", "not_applicable"] = "complete"
    claim_ids: list[str] = Field(default_factory=list)
    limitation: str | None = None


class ResearchReport(TimestampedModel):
    schema_version: str = "1.0"
    report_id: str
    task_id: str
    company_id: str
    collection_id: str
    reference_date: date
    status: ReportStatus
    title: str
    executive_summary: str
    sections: list[ReportSection]
    claims: list[ReportClaim] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    valuation_id: str | None = None
    scenario_ids: list[str] = Field(default_factory=list)
    rating: InvestmentRating | None = None
    missing_information: list[str] = Field(default_factory=list)
    unresolved_conflict_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime
    contract_version: str = "1.0"

    @model_validator(mode="after")
    def report_claim_citation_references(self):
        citation_ids = {citation.citation_id for citation in self.citations}
        for claim in self.claims:
            unknown = set(claim.citation_ids) - citation_ids
            if unknown:
                raise ValueError(f"claim {claim.claim_id} references unknown citations: {sorted(unknown)}")
        return self


class ReportValidationFinding(ContractModel):
    finding_id: str
    code: str
    severity: FindingSeverity
    message: str
    related_claim_id: str | None = None
    related_section_id: str | None = None
    related_evidence_id: str | None = None
    required_correction: str | None = None
    blocks_release: bool = False


class ReportValidationRequest(ContractModel):
    task_id: str
    report: ResearchReport
    evidence_records: list[EvidenceRecord] = Field(default_factory=list)
    calculation_records: list[FinancialCalculation] = Field(default_factory=list)
    required_sections: list[str] = Field(default_factory=lambda: REQUIRED_REPORT_SECTIONS.copy())
    mandatory_release_criteria: list[str] = Field(default_factory=list)


class ReportValidationResult(ContractModel):
    task_id: str
    report_id: str
    status: ValidationStatus
    findings: list[ReportValidationFinding] = Field(default_factory=list)
    required_corrections: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    release_approved: bool
    validated_at: datetime

    @model_validator(mode="after")
    def release_gate_consistency(self):
        if self.status == ValidationStatus.FAILED and self.release_approved:
            raise ValueError("failed validation cannot approve release")
        if any(f.blocks_release for f in self.findings) and self.release_approved:
            raise ValueError("release cannot be approved while blocking findings remain")
        return self


# ---------------------------------------------------------------------------
# Task lifecycle, stage execution, errors, and bounded resources
# ---------------------------------------------------------------------------

class StageExecution(TimestampedModel):
    stage_id: str
    task_id: str
    stage_name: str
    status: StageStatus
    attempt_number: int = Field(default=1, ge=1)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    input_reference_ids: list[str] = Field(default_factory=list)
    output_reference_ids: list[str] = Field(default_factory=list)
    error_id: str | None = None
    limitation: str | None = None


class ResearchTask(TimestampedModel):
    task_id: str
    collection_id: str
    request: ResearchRequest
    status: ResearchTaskStatus
    current_stage: str | None = None
    company_id: str | None = None
    plan_version: int | None = None
    stage_history: list[StageExecution] = Field(default_factory=list)
    created_at: datetime
    accepted_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    report_id: str | None = None
    error_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    progress_completed_units: int | None = Field(default=None, ge=0)
    progress_total_units: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def completed_task_requires_report(self):
        if self.status == ResearchTaskStatus.COMPLETED and not self.report_id:
            raise ValueError("completed task requires report_id")
        if self.progress_completed_units is not None and self.progress_total_units is not None:
            if self.progress_completed_units > self.progress_total_units:
                raise ValueError("completed progress units cannot exceed total units")
        return self


class ErrorRecord(TimestampedModel):
    error_id: str
    task_id: str | None = None
    stage_id: str | None = None
    category: ErrorCategory
    code: str
    message: str
    retryable: bool = False
    attempt_number: int | None = Field(default=None, ge=1)
    occurred_at: datetime
    component: str | None = None
    safe_details: dict[str, Any] = Field(default_factory=dict)
    recovery_action: str | None = None
    stack_trace_reference: str | None = None


class ResourceLimitEvent(ContractModel):
    task_id: str
    limit_type: ResourceLimitType
    configured_limit: int
    observed_value: int
    triggered_at: datetime
    action_taken: Literal["stop", "reject", "defer", "retry_blocked"]
    incomplete_work: list[str] = Field(default_factory=list)


class CheckpointRecord(TimestampedModel):
    checkpoint_id: str
    task_id: str
    stage_id: str
    stage_name: str
    status: CheckpointStatus
    schema_version: str = "1.0"
    input_fingerprint: str
    output_reference_ids: list[str] = Field(default_factory=list)
    persisted_state_reference: str
    created_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecoveryRecord(TimestampedModel):
    recovery_id: str
    task_id: str
    status: RecoveryStatus
    checkpoint_id: str | None = None
    failed_stage_id: str | None = None
    attempt_number: int = Field(ge=1)
    action_taken: str
    preserved_output_reference_ids: list[str] = Field(default_factory=list)
    error_id: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evaluation and experimentation
# ---------------------------------------------------------------------------

class EvaluationQuestionResult(ContractModel):
    question_id: str
    category: str
    expected_answer: str | None = None
    actual_answer: str | None = None
    retrieval_score: float | None = None
    factual_correctness_score: float | None = None
    evidence_faithfulness_score: float | None = None
    citation_support_score: float | None = None
    calculation_correct: bool | None = None
    passed: bool
    critical_error: bool = False
    latency_ms: float | None = Field(default=None, ge=0)
    cost_amount: float | None = Field(default=None, ge=0)
    cost_currency: str | None = None
    failure_reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationRun(ContractModel):
    evaluation_run_id: str
    dataset_version: str
    contract_version: str
    configuration_version: str
    status: EvaluationStatus
    started_at: datetime
    completed_at: datetime | None = None
    question_results: list[EvaluationQuestionResult] = Field(default_factory=list)
    aggregate_metrics: dict[str, float] = Field(default_factory=dict)
    category_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    release_gate_passed: bool | None = None
    limitations: list[str] = Field(default_factory=list)


class ExperimentRecord(ContractModel):
    experiment_id: str
    name: str
    hypothesis: str
    status: ExperimentStatus
    baseline_configuration: dict[str, Any]
    candidate_configuration: dict[str, Any]
    evaluation_run_ids: list[str] = Field(default_factory=list)
    metrics_compared: list[str] = Field(default_factory=list)
    results_summary: str | None = None
    regression_findings: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    release_gate_passed: bool | None = None


# ---------------------------------------------------------------------------
# Data deletion
# ---------------------------------------------------------------------------

class DataDeletionRequest(ContractModel):
    deletion_request_id: str
    collection_id: str
    target_type: DeletionTargetType
    target_ids: list[str] = Field(min_length=1)
    requested_at: datetime
    reason: str | None = None
    requested_by: str | None = None


class DataDeletionResult(ContractModel):
    deletion_request_id: str
    status: DeletionStatus
    completed_at: datetime | None = None
    deleted_target_ids: list[str] = Field(default_factory=list)
    retained_target_ids: list[str] = Field(default_factory=list)
    retention_reasons: dict[str, str] = Field(default_factory=dict)
    affected_reference_ids: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Small shared request/response contracts used by the interface
# ---------------------------------------------------------------------------

class TaskStatusResponse(ContractModel):
    task_id: str
    status: ResearchTaskStatus
    current_stage: str | None = None
    stage_history: list[StageExecution] = Field(default_factory=list)
    error_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    report_id: str | None = None
    updated_at: datetime | None = None


class CancellationRequest(ContractModel):
    task_id: str
    requested_at: datetime
    reason: str | None = None


class CancellationResult(ContractModel):
    task_id: str
    accepted: bool
    status: ResearchTaskStatus
    message: str
    requested_at: datetime


class CollectionReference(ContractModel):
    collection_id: str
    name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Outcome", "CompanyResolutionStatus", "ResearchTaskStatus", "StageStatus",
    "ResearchStepStatus", "SourceType", "RetrievalStatus", "IngestionStatus",
    "EvidenceStrength", "ClaimType", "FindingStatus", "ConflictType",
    "ConflictResolutionStatus", "InformationGapStatus", "ValueOrigin",
    "CalculationStatus", "ValuationStatus", "ValuationMethod", "ScenarioType",
    "RatingValue", "RatingStatus", "ReportStatus", "ValidationStatus",
    "FindingSeverity", "ErrorCategory", "ResourceLimitType", "CheckpointStatus",
    "RecoveryStatus", "EvaluationStatus", "ExperimentStatus", "DeletionTargetType",
    "DeletionStatus", "MissingValueReason", "ResearchOptions", "ValidationIssue",
    "ResearchRequest", "RequestAcceptance", "CompanyIdentity", "ResourceLimits",
    "ResearchStep", "ResearchPlan", "SourceRecord", "DocumentIngestionRequest",
    "DocumentIngestionResult", "ExtractedChunk", "EvidenceRecord", "RetrievalRequest",
    "RetrievedEvidence", "RetrievalResponse", "AnalysisFinding", "ConflictRecord",
    "InformationGap", "MissingValue", "FinancialValue", "CalculationInput",
    "FinancialCalculation", "FinancialStatement", "ValuationAssumption", "ValuationRange",
    "ValuationRecord", "ScenarioRecord", "InvestmentRating", "ThesisAnalysis",
    "REQUIRED_REPORT_SECTIONS", "ReportCitation", "ReportClaim", "ReportSection",
    "ResearchReport", "ReportValidationFinding", "ReportValidationRequest",
    "ReportValidationResult", "StageExecution", "ResearchTask", "ErrorRecord",
    "ResourceLimitEvent", "CheckpointRecord", "RecoveryRecord",
    "EvaluationQuestionResult", "EvaluationRun", "ExperimentRecord",
    "DataDeletionRequest", "DataDeletionResult", "TaskStatusResponse",
    "CancellationRequest", "CancellationResult", "CollectionReference",
]
