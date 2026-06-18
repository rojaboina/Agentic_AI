from __future__ import annotations

from app.extractor import extract_all_cases
from app.guidelines import run_guideline_checks
from app.llm_human_review import build_llm_human_review_route
from app.medication_safety import run_medication_safety_checks
from app.risk_scoring import calculate_risk_scores
from app.schemas import (
    ClinicalExtraction,
    GuidelineResult,
    HumanReview,
    HumanReviewRoute,
    MedicationSafetyResult,
    RiskScores,
    SpecialistReviewBundle,
)
from app.specialist_agents import run_specialist_agents


def choose_reviewer_role(bundle: SpecialistReviewBundle, risk_scores: RiskScores) -> str | None:
    if bundle.medication_safety.needs_human_review:
        return "clinical pharmacist"
    if bundle.care_management.needs_human_review:
        return "care manager"
    if bundle.service_review.needs_human_review and risk_scores.overall_risk < 0.7:
        return "clinical reviewer"
    if bundle.clinical_risk.severity == "high" or risk_scores.overall_risk >= 0.7:
        return "clinician"
    return None


def choose_urgency(risk_scores: RiskScores, bundle: SpecialistReviewBundle) -> str:
    if risk_scores.overall_risk >= 0.7 or bundle.clinical_risk.severity == "high":
        return "high"
    if (
        risk_scores.overall_risk >= 0.35
        or bundle.medication_safety.needs_human_review
        or bundle.care_management.needs_human_review
        or bundle.service_review.needs_human_review
    ):
        return "medium"
    return "low"


def collect_routing_reasons(bundle: SpecialistReviewBundle, risk_scores: RiskScores) -> list[str]:
    reasons: list[str] = []

    if bundle.clinical_risk.severity == "high":
        reasons.append(bundle.clinical_risk.summary)
    if bundle.clinical_risk.red_flags:
        reasons.extend(bundle.clinical_risk.red_flags[:5])
    if bundle.medication_safety.needs_human_review:
        reasons.append(bundle.medication_safety.summary)
    if bundle.care_management.needs_human_review:
        reasons.append(bundle.care_management.summary)
    if bundle.service_review.needs_human_review:
        reasons.append(bundle.service_review.summary)
    if risk_scores.overall_risk >= 0.7:
        reasons.append(f"Overall risk score is {risk_scores.overall_risk}.")

    return reasons


def collect_triggering_agents(bundle: SpecialistReviewBundle) -> list[str]:
    agents: list[str] = []
    if bundle.clinical_risk.severity == "high":
        agents.append("Clinical Risk Agent")
    if bundle.medication_safety.needs_human_review:
        agents.append(bundle.medication_safety.agent_name)
    if bundle.care_management.needs_human_review:
        agents.append(bundle.care_management.agent_name)
    if bundle.service_review.needs_human_review:
        agents.append(bundle.service_review.agent_name)
    return agents


def route_human_review(extraction: ClinicalExtraction) -> HumanReviewRoute:
    guideline_result = run_guideline_checks(extraction)
    medication_safety_result = run_medication_safety_checks(extraction)
    risk_scores = calculate_risk_scores(
        extraction,
        guideline_result,
        medication_safety_result,
    )
    specialist_bundle = run_specialist_agents(extraction)
    return route_human_review_from_outputs(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
    )


def route_human_review_from_outputs(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
) -> HumanReviewRoute:
    _ = guideline_result
    _ = medication_safety_result

    deterministic_route = build_deterministic_human_review_route(
        extraction,
        risk_scores,
        specialist_bundle,
    )
    llm_route = try_llm_human_review_route(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
        deterministic_route,
    )
    if llm_route is None:
        return deterministic_route
    return apply_human_review_guardrails(deterministic_route, llm_route)


def build_deterministic_human_review_route(
    extraction: ClinicalExtraction,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
) -> HumanReviewRoute:

    routing_reasons = collect_routing_reasons(specialist_bundle, risk_scores)
    triggering_agents = collect_triggering_agents(specialist_bundle)
    reviewer_role = choose_reviewer_role(specialist_bundle, risk_scores)
    required = reviewer_role is not None or bool(routing_reasons)
    urgency = choose_urgency(risk_scores, specialist_bundle)

    return HumanReviewRoute(
        case_id=extraction.case_id,
        human_review=HumanReview(
            required=required,
            reviewer_role=reviewer_role,
            reviewer_decision=None,
            notes="; ".join(routing_reasons) if routing_reasons else None,
        ),
        routing_reasons=routing_reasons,
        triggering_agents=triggering_agents,
        urgency=urgency,  # type: ignore[arg-type]
        source="deterministic",
    )


def try_llm_human_review_route(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
    deterministic_route: HumanReviewRoute,
) -> HumanReviewRoute | None:
    try:
        return build_llm_human_review_route(
            extraction,
            guideline_result,
            medication_safety_result,
            risk_scores,
            specialist_bundle,
            deterministic_route,
        )
    except Exception:
        return None


def apply_human_review_guardrails(
    deterministic_route: HumanReviewRoute,
    llm_route: HumanReviewRoute,
) -> HumanReviewRoute:
    if deterministic_route.human_review.required:
        llm_route.human_review.required = True
        if not llm_route.human_review.reviewer_role:
            llm_route.human_review.reviewer_role = deterministic_route.human_review.reviewer_role

    if deterministic_route.urgency == "high":
        llm_route.urgency = "high"

    merged_reasons = list(dict.fromkeys(
        deterministic_route.routing_reasons + llm_route.routing_reasons
    ))
    merged_agents = list(dict.fromkeys(
        deterministic_route.triggering_agents + llm_route.triggering_agents
    ))
    llm_route.routing_reasons = merged_reasons
    llm_route.triggering_agents = merged_agents
    if merged_reasons:
        llm_route.human_review.notes = "; ".join(merged_reasons)
    llm_route.source = "llm"
    return llm_route


def route_all_human_reviews() -> dict[str, HumanReviewRoute]:
    return {
        extraction.case_id: route_human_review(extraction)
        for extraction in extract_all_cases()
    }


def main() -> None:
    routes = route_all_human_reviews()
    required_routes = [
        route
        for route in routes.values()
        if route.human_review.required
    ]
    high_urgency_routes = [
        route
        for route in required_routes
        if route.urgency == "high"
    ]
    print(f"routed_cases={len(routes)}")
    print(f"human_review_required={len(required_routes)}")
    print(f"high_urgency_reviews={len(high_urgency_routes)}")
    print(f"first_required_case={required_routes[0].case_id if required_routes else 'none'}")


if __name__ == "__main__":
    main()
