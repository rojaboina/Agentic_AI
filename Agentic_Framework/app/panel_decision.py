from __future__ import annotations

from collections import Counter

from app.extractor import extract_all_cases
from app.guidelines import run_guideline_checks
from app.human_review import route_human_review
from app.llm_panel_decision import build_llm_panel_decision
from app.medication_safety import run_medication_safety_checks
from app.risk_scoring import calculate_risk_scores
from app.schemas import ClinicalExtraction, ClinicalPanelDecision
from app.specialist_agents import run_specialist_agents


def determine_decision(extraction: ClinicalExtraction, overall_risk: float, human_required: bool) -> str:
    if extraction.missing_fields:
        return "Insufficient Data"
    if overall_risk >= 0.7:
        return "Urgent Review"
    if human_required or overall_risk >= 0.35:
        return "Needs Follow-Up"
    return "Routine"


def build_recommended_actions(
    extraction: ClinicalExtraction,
    decision: str,
    reviewer_role: str | None,
) -> list[str]:
    actions: list[str] = []
    if decision == "Urgent Review":
        actions.append("Route case for same-day clinical review.")
    elif decision == "Needs Follow-Up" and reviewer_role:
        actions.append("Route case to the assigned reviewer queue.")
    elif decision == "Needs Follow-Up":
        actions.append("Track for follow-up without immediate human escalation.")
    else:
        actions.append("Continue routine workflow.")

    if reviewer_role:
        actions.append(f"Assign to {reviewer_role}.")
    if extraction.patient_case.requested_service:
        actions.append(f"Review requested service: {extraction.patient_case.requested_service}.")
    if extraction.missing_fields:
        actions.append(f"Collect missing data: {', '.join(extraction.missing_fields)}.")
    return actions


def build_panel_rationale(
    extraction: ClinicalExtraction,
    decision: str,
    overall_risk: float,
    human_required: bool,
    reviewer_role: str | None,
    triggering_agents: list[str],
) -> str:
    parts = [
        f"Panel decision is {decision} for {extraction.case_id}.",
        f"Overall risk score is {overall_risk}.",
    ]
    if human_required:
        parts.append(f"Human review is required by {reviewer_role or 'reviewer'}.")
    if triggering_agents:
        parts.append(f"Triggered by: {', '.join(triggering_agents)}.")
    if extraction.missing_fields:
        parts.append(f"Missing fields: {', '.join(extraction.missing_fields)}.")
    return " ".join(parts)


def make_panel_decision(extraction: ClinicalExtraction) -> ClinicalPanelDecision:
    guideline_result = run_guideline_checks(extraction)
    medication_safety_result = run_medication_safety_checks(extraction)
    risk_scores = calculate_risk_scores(
        extraction,
        guideline_result,
        medication_safety_result,
    )
    specialist_bundle = run_specialist_agents(extraction)
    human_route = route_human_review(extraction)
    return make_panel_decision_from_outputs(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
        human_route,
    )


def make_panel_decision_from_outputs(
    extraction,
    guideline_result,
    medication_safety_result,
    risk_scores,
    specialist_bundle,
    human_route,
) -> ClinicalPanelDecision:
    deterministic_decision = build_deterministic_panel_decision(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
        human_route,
    )
    llm_decision = try_llm_panel_decision(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
        human_route,
        deterministic_decision,
    )
    if llm_decision is None:
        return deterministic_decision
    return apply_panel_guardrails(deterministic_decision, llm_decision)


def build_deterministic_panel_decision(
    extraction,
    guideline_result,
    medication_safety_result,
    risk_scores,
    specialist_bundle,
    human_route,
) -> ClinicalPanelDecision:
    decision = determine_decision(
        extraction,
        risk_scores.overall_risk,
        human_route.human_review.required,
    )
    reviewer_role = human_route.human_review.reviewer_role
    confidence = min(
        guideline_result.confidence,
        medication_safety_result.confidence,
        specialist_bundle.clinical_risk.confidence,
    )
    if decision == "Insufficient Data":
        confidence = min(confidence, 0.65)

    return ClinicalPanelDecision(
        decision=decision,  # type: ignore[arg-type]
        confidence=confidence,
        rationale=build_panel_rationale(
            extraction,
            decision,
            risk_scores.overall_risk,
            human_route.human_review.required,
            reviewer_role,
            human_route.triggering_agents,
        ),
        recommended_actions=build_recommended_actions(
            extraction,
            decision,
            reviewer_role,
        ),
        escalate_to_human=human_route.human_review.required,
        source="deterministic",
    )


def try_llm_panel_decision(
    extraction,
    guideline_result,
    medication_safety_result,
    risk_scores,
    specialist_bundle,
    human_route,
    deterministic_decision,
) -> ClinicalPanelDecision | None:
    try:
        return build_llm_panel_decision(
            extraction,
            guideline_result,
            medication_safety_result,
            risk_scores,
            specialist_bundle,
            human_route,
            deterministic_decision,
        )
    except Exception:
        return None


def apply_panel_guardrails(
    deterministic_decision: ClinicalPanelDecision,
    llm_decision: ClinicalPanelDecision,
) -> ClinicalPanelDecision:
    if deterministic_decision.decision in {"Urgent Review", "Insufficient Data"}:
        llm_decision.decision = deterministic_decision.decision

    if deterministic_decision.escalate_to_human:
        llm_decision.escalate_to_human = True
        if llm_decision.decision == "Routine":
            llm_decision.decision = "Needs Follow-Up"

    deterministic_actions = deterministic_decision.recommended_actions
    merged_actions = list(dict.fromkeys(
        llm_decision.recommended_actions + deterministic_actions
    ))
    llm_decision.recommended_actions = merged_actions
    llm_decision.confidence = min(llm_decision.confidence, deterministic_decision.confidence)
    llm_decision.source = "llm"
    return llm_decision


def make_all_panel_decisions() -> dict[str, ClinicalPanelDecision]:
    return {
        extraction.case_id: make_panel_decision(extraction)
        for extraction in extract_all_cases()
    }


def main() -> None:
    decisions = make_all_panel_decisions()
    counts = Counter(decision.decision for decision in decisions.values())
    print(f"panel_decision_cases={len(decisions)}")
    for decision_name in ["Urgent Review", "Needs Follow-Up", "Routine", "Insufficient Data"]:
        print(f"{decision_name}={counts.get(decision_name, 0)}")


if __name__ == "__main__":
    main()
