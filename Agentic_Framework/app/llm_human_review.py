from __future__ import annotations

import json
from typing import Optional

from app.llm_specialist_agents import compact_case_context, invoke_structured_llm
from app.schemas import (
    ClinicalExtraction,
    GuidelineResult,
    HumanReviewRoute,
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
    base_context = json.loads(
        compact_case_context(
            extraction,
            guideline_result,
            medication_safety_result,
            risk_scores,
        )
    )
    base_context["specialist_reviews"] = specialist_bundle.model_dump()
    base_context["deterministic_route"] = deterministic_route.model_dump()
    return json.dumps(base_context, indent=2)


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
    route = invoke_structured_llm(
        HumanReviewRoute,
        "Human Review Router",
        (
            "Decide whether this case needs human review, the best reviewer role, urgency, "
            "routing reasons, and triggering agents. You may refine the deterministic route, "
            "but do not downgrade high-risk or mandatory review cases. If deterministic_route "
            "requires review, your output must also require review."
        ),
        context,
    )
    if route is not None:
        route.case_id = extraction.case_id
        route.source = "llm"
    return route
