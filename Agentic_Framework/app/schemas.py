from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]
Decision = Literal["Routine", "Needs Follow-Up", "Urgent Review", "Insufficient Data"]


class Vitals(BaseModel):
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None


class PatientCase(BaseModel):
    case_id: str
    synthetic: bool = True
    patient_age: int = Field(ge=0, le=120)
    sex: str
    chief_concern: str
    diagnoses: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    lab_results: dict[str, float] = Field(default_factory=dict)
    vitals: Vitals = Field(default_factory=Vitals)
    recent_visits: list[str] = Field(default_factory=list)
    requested_service: Optional[str] = None
    clinical_note: str
    expected_triggers: list[str] = Field(default_factory=list)
    expected_human_review: bool = False


class ClinicalExtraction(BaseModel):
    case_id: str
    patient_case: PatientCase
    age_group: str
    normalized_diagnoses: list[str] = Field(default_factory=list)
    normalized_medications: list[str] = Field(default_factory=list)
    abnormal_labs: dict[str, float] = Field(default_factory=dict)
    vital_sign_flags: list[str] = Field(default_factory=list)
    note_signals: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class GuidelineFlag(BaseModel):
    code: str
    severity: RiskLevel
    message: str
    evidence: Optional[str] = None


class GuidelineResult(BaseModel):
    passed: bool
    flags: list[GuidelineFlag] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class ClinicalRiskAnalysis(BaseModel):
    summary: str
    severity: RiskLevel
    red_flags: list[str] = Field(default_factory=list)
    care_gaps: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "deterministic"


class MedicationSafetyFinding(BaseModel):
    medication: Optional[str] = None
    issue: str
    severity: RiskLevel
    rationale: str


class MedicationSafetyResult(BaseModel):
    has_safety_issue: bool
    findings: list[MedicationSafetyFinding] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class RiskScores(BaseModel):
    readmission_risk: float = Field(ge=0.0, le=1.0)
    medication_safety_risk: float = Field(ge=0.0, le=1.0)
    care_gap_risk: float = Field(ge=0.0, le=1.0)
    overall_risk: float = Field(ge=0.0, le=1.0)
    rationale: str


class SpecialistReview(BaseModel):
    agent_name: str
    summary: str
    severity: RiskLevel
    key_findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    needs_human_review: bool
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "deterministic"


class SpecialistReviewBundle(BaseModel):
    case_id: str
    clinical_risk: ClinicalRiskAnalysis
    medication_safety: SpecialistReview
    care_management: SpecialistReview
    service_review: SpecialistReview


class ClinicalPanelDecision(BaseModel):
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    recommended_actions: list[str] = Field(default_factory=list)
    escalate_to_human: bool
    source: str = "deterministic"


class HumanReview(BaseModel):
    required: bool
    reviewer_role: Optional[str] = None
    reviewer_decision: Optional[Decision] = None
    notes: Optional[str] = None


class HumanReviewRoute(BaseModel):
    case_id: str
    human_review: HumanReview
    routing_reasons: list[str] = Field(default_factory=list)
    triggering_agents: list[str] = Field(default_factory=list)
    urgency: RiskLevel
    source: str = "deterministic"


class HumanReviewRouteDraft(BaseModel):
    required: bool
    reviewer_role: Optional[str] = None
    notes: Optional[str] = None
    routing_reasons: list[str] = Field(default_factory=list)
    triggering_agents: list[str] = Field(default_factory=list)
    urgency: RiskLevel


class ClinicalPanelDecisionDraft(BaseModel):
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    recommended_actions: list[str] = Field(default_factory=list)
    escalate_to_human: bool


class MemoryEntry(BaseModel):
    memory: str
    source: str
    score: Optional[float] = None
    metadata: dict = Field(default_factory=dict)


class MemoryContext(BaseModel):
    provider: str = "none"
    entries: list[MemoryEntry] = Field(default_factory=list)


class FinalReport(BaseModel):
    case_id: str
    patient_case: PatientCase
    guideline_result: GuidelineResult
    clinical_risk_analysis: ClinicalRiskAnalysis
    medication_safety_result: MedicationSafetyResult
    risk_scores: RiskScores
    panel_decision: ClinicalPanelDecision
    human_review: Optional[HumanReview] = None
    markdown: str
