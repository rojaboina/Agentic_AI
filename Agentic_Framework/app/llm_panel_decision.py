from __future__ import annotations

import json
from typing import Optional

from app.llm_human_review import compact_routing_context
from app.llm_specialist_agents import invoke_structured_llm
from app.schemas import (
    ClinicalExtraction,
    ClinicalPanelDecision,
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
    base_context = json.loads(
        compact_routing_context(
            extraction,
            guideline_result,
            medication_safety_result,
            risk_scores,
            specialist_bundle,
            human_route,
        )
    )
    base_context["human_review_route"] = human_route.model_dump()
    base_context["deterministic_panel_decision"] = deterministic_decision.model_dump()
    return json.dumps(base_context, indent=2)


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
    decision = invoke_structured_llm(
        ClinicalPanelDecision,
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
    if decision is not None:
        decision.source = "llm"
    return decision
