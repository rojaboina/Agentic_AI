from __future__ import annotations

import json
from typing import Optional

from app.llm_specialist_agents import compact_case_context, invoke_structured_llm
from app.schemas import (
    ClinicalExtraction,
    GuidelineResult,
    HumanReview,
    HumanReviewRoute,
    HumanReviewRouteDraft,
    MedicationSafetyResult,
    RiskScores,
    SpecialistReviewBundle,
)


def compact_routing_context(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
    deterministic_route: HumanReviewRoute,
) -> str:
    patient_case = extraction.patient_case
    payload = {
        "case_id": extraction.case_id,
        "case_summary": {
            "age": patient_case.patient_age,
            "chief_concern": patient_case.chief_concern,
            "diagnoses": patient_case.diagnoses,
            "medications": patient_case.medications,
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
            "clinical_risk": {"severity": specialist_bundle.clinical_risk.severity, "summary": specialist_bundle.clinical_risk.summary, "source": specialist_bundle.clinical_risk.source},
            "medication_safety": {"severity": specialist_bundle.medication_safety.severity, "summary": specialist_bundle.medication_safety.summary, "needs_human_review": specialist_bundle.medication_safety.needs_human_review, "source": specialist_bundle.medication_safety.source},
            "care_management": {"severity": specialist_bundle.care_management.severity, "summary": specialist_bundle.care_management.summary, "needs_human_review": specialist_bundle.care_management.needs_human_review, "source": specialist_bundle.care_management.source},
            "service_review": {"severity": specialist_bundle.service_review.severity, "summary": specialist_bundle.service_review.summary, "needs_human_review": specialist_bundle.service_review.needs_human_review, "source": specialist_bundle.service_review.source},
        },
        "deterministic_route": {
            "required": deterministic_route.human_review.required,
            "reviewer_role": deterministic_route.human_review.reviewer_role,
            "urgency": deterministic_route.urgency,
            "routing_reasons": deterministic_route.routing_reasons,
            "triggering_agents": deterministic_route.triggering_agents,
        },
        "reviewer_role_guidance": {
            "clinician": "Use when overall clinical risk, acute symptoms, abnormal labs, or clinical deterioration is the dominant concern.",
            "clinical pharmacist": "Use when medication safety, renal dosing, allergy conflict, anticoagulation, or drug interaction risk is the dominant concern.",
            "care manager": "Use when adherence, access barriers, missed follow-up, social needs, or care gaps are the dominant concern.",
            "clinical reviewer": "Use when requested service, authorization, documentation, or utilization review is the dominant concern.",
        },
    }
    return json.dumps(payload, separators=(",", ":"))


def build_llm_human_review_route(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
    deterministic_route: HumanReviewRoute,
) -> Optional[HumanReviewRoute]:
    context = compact_routing_context(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
        deterministic_route,
    )
    draft = invoke_structured_llm(
        HumanReviewRouteDraft,
        "Human Review Router",
        (
            "Decide whether this case needs human review, the best reviewer role, urgency, "
            "routing reasons, and triggering agents. You may refine the deterministic route, "
            "but do not downgrade high-risk or mandatory review cases. If deterministic_route "
            "requires review, your output must also require review. Choose the reviewer role "
            "from the dominant specialist signal; do not default to clinical pharmacist unless "
            "medication safety is the main reason for review."
        ),
        context,
    )
    if draft is None:
        return None
    return HumanReviewRoute(
        case_id=extraction.case_id,
        human_review=HumanReview(
            required=draft.required,
            reviewer_role=draft.reviewer_role,
            reviewer_decision=None,
            notes=draft.notes,
        ),
        routing_reasons=draft.routing_reasons,
        triggering_agents=draft.triggering_agents,
        urgency=draft.urgency,
        source="llm",
    )
