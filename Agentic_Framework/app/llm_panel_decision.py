from __future__ import annotations

import json
from typing import Optional

from app.llm_human_review import compact_routing_context
from app.llm_specialist_agents import invoke_structured_llm
from app.schemas import (
    ClinicalExtraction,
    ClinicalPanelDecision,
    ClinicalPanelDecisionDraft,
    GuidelineResult,
    HumanReviewRoute,
    MedicationSafetyResult,
    RiskScores,
    SpecialistReviewBundle,
)


def compact_panel_context(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
    human_route: HumanReviewRoute,
    deterministic_decision: ClinicalPanelDecision,
) -> str:
    patient_case = extraction.patient_case
    payload = {
        "case_id": extraction.case_id,
        "case_summary": {
            "chief_concern": patient_case.chief_concern,
            "requested_service": patient_case.requested_service,
        },
        "scores": {
            "overall": risk_scores.overall_risk,
            "medication": risk_scores.medication_safety_risk,
            "care_gap": risk_scores.care_gap_risk,
        },
        "high_flags": [flag.code for flag in guideline_result.flags if flag.severity == "high"],
        "medication_issues": [finding.issue for finding in medication_safety_result.findings],
        "specialist_summaries": {
            "clinical_risk": {"severity": specialist_bundle.clinical_risk.severity, "summary": specialist_bundle.clinical_risk.summary},
            "medication_safety": {"severity": specialist_bundle.medication_safety.severity, "summary": specialist_bundle.medication_safety.summary},
            "care_management": {"severity": specialist_bundle.care_management.severity, "summary": specialist_bundle.care_management.summary},
            "service_review": {"severity": specialist_bundle.service_review.severity, "summary": specialist_bundle.service_review.summary},
        },
        "human_review_route": {
            "required": human_route.human_review.required,
            "reviewer_role": human_route.human_review.reviewer_role,
            "urgency": human_route.urgency,
            "source": human_route.source,
        },
        "deterministic_panel_decision": deterministic_decision.model_dump(),
    }
    return json.dumps(payload, separators=(",", ":"))


def build_llm_panel_decision(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
    human_route: HumanReviewRoute,
    deterministic_decision: ClinicalPanelDecision,
) -> Optional[ClinicalPanelDecision]:
    context = compact_panel_context(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
        human_route,
        deterministic_decision,
    )
    draft = invoke_structured_llm(
        ClinicalPanelDecisionDraft,
        "Panel Decision Agent",
        (
            "Create the final panel decision using all upstream outputs: guideline flags, "
            "medication safety findings, risk scores, specialist reviews, and human review route. "
            "Allowed decisions are Routine, Needs Follow-Up, Urgent Review, and Insufficient Data. "
            "You may improve the rationale and recommended actions, but do not downgrade urgent, "
            "missing-data, or required-human-review cases below the deterministic panel decision."
        ),
        context,
    )
    if draft is None:
        return None
    return ClinicalPanelDecision(
        decision=draft.decision,
        confidence=draft.confidence,
        rationale=draft.rationale,
        recommended_actions=draft.recommended_actions,
        escalate_to_human=draft.escalate_to_human,
        source="llm",
    )
