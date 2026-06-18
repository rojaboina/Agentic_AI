from __future__ import annotations

from app.extractor import extract_all_cases
from app.guidelines import run_guideline_checks
from app.llm_specialist_agents import (
    build_llm_clinical_risk_agent,
    build_llm_specialist_review,
)
from app.medication_safety import run_medication_safety_checks
from app.risk_scoring import calculate_risk_scores
from app.schemas import (
    ClinicalExtraction,
    ClinicalRiskAnalysis,
    GuidelineResult,
    MedicationSafetyResult,
    RiskScores,
    SpecialistReview,
    SpecialistReviewBundle,
)


PRIOR_AUTH_KEYWORDS = {
    "authorization",
    "eligibility",
    "renewal",
    "referral",
    "scheduling",
}


def severity_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def build_clinical_risk_agent(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    risk_scores: RiskScores,
) -> ClinicalRiskAnalysis:
    high_flags = [
        f"{flag.code}: {flag.message}"
        for flag in guideline_result.flags
        if flag.severity == "high"
    ]
    medium_flags = [
        f"{flag.code}: {flag.message}"
        for flag in guideline_result.flags
        if flag.severity == "medium"
    ]
    care_gaps = [
        flag.message
        for flag in guideline_result.flags
        if flag.code in {"CARE_GAP_SIGNAL", "SOCIAL_RISK_SIGNAL", "LAB_A1C", "LAB_LDL"}
    ]

    severity = severity_from_score(risk_scores.overall_risk)
    summary = (
        f"{extraction.case_id} has {severity} clinical risk with "
        f"overall score {risk_scores.overall_risk}."
    )
    return ClinicalRiskAnalysis(
        summary=summary,
        severity=severity,  # type: ignore[arg-type]
        red_flags=high_flags,
        care_gaps=care_gaps,
        missing_information=extraction.missing_fields,
        confidence=guideline_result.confidence,
    )


def build_medication_safety_agent(
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
) -> SpecialistReview:
    findings = [
        f"{finding.issue}: {finding.rationale}"
        for finding in medication_safety_result.findings
    ]
    severity = severity_from_score(risk_scores.medication_safety_risk)
    if not findings:
        findings = ["No deterministic medication safety issues were detected."]

    actions = []
    if medication_safety_result.has_safety_issue:
        actions.append("Review medication list, risk rationale, and monitoring needs.")
    if risk_scores.medication_safety_risk >= 0.7:
        actions.append("Route medication concern for clinician or pharmacist review.")

    return SpecialistReview(
        agent_name="Medication Safety Agent",
        summary=f"Medication safety risk is {risk_scores.medication_safety_risk}.",
        severity=severity,  # type: ignore[arg-type]
        key_findings=findings,
        recommended_actions=actions,
        needs_human_review=risk_scores.medication_safety_risk >= 0.7,
        confidence=medication_safety_result.confidence,
    )


def build_care_management_agent(
    extraction: ClinicalExtraction,
    risk_scores: RiskScores,
) -> SpecialistReview:
    findings: list[str] = []
    actions: list[str] = []

    if "care_gap" in extraction.note_signals:
        findings.append("Clinical note suggests a care gap or delayed follow-up.")
        actions.append("Confirm follow-up scheduling and care gap closure.")
    if "medication_access_barrier" in extraction.note_signals:
        findings.append("Medication access, transportation, or housing barriers are documented.")
        actions.append("Consider care management or social work referral.")
    if "adherence_issue" in extraction.note_signals:
        findings.append("Medication adherence concern is documented.")
        actions.append("Review adherence barriers and simplify care plan where possible.")
    if not findings:
        findings.append("No major care management signal was detected.")

    severity = severity_from_score(risk_scores.care_gap_risk)
    return SpecialistReview(
        agent_name="Care Management Agent",
        summary=f"Care gap risk is {risk_scores.care_gap_risk}.",
        severity=severity,  # type: ignore[arg-type]
        key_findings=findings,
        recommended_actions=actions,
        needs_human_review=risk_scores.care_gap_risk >= 0.7,
        confidence=0.9,
    )


def build_service_review_agent(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    risk_scores: RiskScores,
) -> SpecialistReview:
    requested_service = extraction.patient_case.requested_service or "unspecified service"
    service_text = requested_service.lower()
    high_flags = [flag.code for flag in guideline_result.flags if flag.severity == "high"]
    is_admin_review = any(keyword in service_text for keyword in PRIOR_AUTH_KEYWORDS)

    findings = [f"Requested service: {requested_service}."]
    actions: list[str] = []

    if high_flags:
        findings.append(f"High severity clinical flags are present: {', '.join(high_flags)}.")
        actions.append("Do not treat as routine administrative review; route to clinical review.")
    elif is_admin_review:
        findings.append("Service appears appropriate for administrative criteria review.")
        actions.append("Check documentation completeness and payer criteria.")
    else:
        findings.append("No special service review issue was detected.")

    severity = "high" if high_flags and risk_scores.overall_risk >= 0.7 else severity_from_score(risk_scores.overall_risk)
    return SpecialistReview(
        agent_name="Service Review Agent",
        summary=f"Service review completed for {requested_service}.",
        severity=severity,  # type: ignore[arg-type]
        key_findings=findings,
        recommended_actions=actions,
        needs_human_review=bool(high_flags) or risk_scores.overall_risk >= 0.7,
        confidence=0.9,
    )


def try_llm_clinical_risk_agent(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
) -> ClinicalRiskAnalysis | None:
    try:
        return build_llm_clinical_risk_agent(
            extraction,
            guideline_result,
            medication_safety_result,
            risk_scores,
        )
    except Exception:
        return None


def try_llm_specialist_review(
    agent_name: str,
    task: str,
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
) -> SpecialistReview | None:
    try:
        return build_llm_specialist_review(
            agent_name,
            task,
            extraction,
            guideline_result,
            medication_safety_result,
            risk_scores,
        )
    except Exception:
        return None


def run_specialist_agents(extraction: ClinicalExtraction) -> SpecialistReviewBundle:
    guideline_result = run_guideline_checks(extraction)
    medication_safety_result = run_medication_safety_checks(extraction)
    risk_scores = calculate_risk_scores(
        extraction,
        guideline_result,
        medication_safety_result,
    )

    clinical_risk = try_llm_clinical_risk_agent(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
    ) or build_clinical_risk_agent(
        extraction,
        guideline_result,
        risk_scores,
    )
    medication_safety = try_llm_specialist_review(
        "Medication Safety Agent",
        (
            "Review medication safety risks, drug-condition concerns, renal dosing issues, "
            "sedation/fall risk, allergy conflicts, anticoagulation concerns, and whether "
            "human review is needed."
        ),
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
    ) or build_medication_safety_agent(
        medication_safety_result,
        risk_scores,
    )
    care_management = try_llm_specialist_review(
        "Care Management Agent",
        (
            "Review care gaps, access barriers, adherence issues, social needs, missed visits, "
            "and follow-up needs. Decide whether care management or human review is needed."
        ),
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
    ) or build_care_management_agent(extraction, risk_scores)
    service_review = try_llm_specialist_review(
        "Service Review Agent",
        (
            "Review the requested service, administrative criteria signals, clinical escalation "
            "signals, and whether the service request should be routed to human review."
        ),
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
    ) or build_service_review_agent(
        extraction,
        guideline_result,
        risk_scores,
    )

    return SpecialistReviewBundle(
        case_id=extraction.case_id,
        clinical_risk=clinical_risk,
        medication_safety=medication_safety,
        care_management=care_management,
        service_review=service_review,
    )


def run_all_specialist_agents() -> dict[str, SpecialistReviewBundle]:
    return {
        extraction.case_id: run_specialist_agents(extraction)
        for extraction in extract_all_cases()
    }


def main() -> None:
    reviews = run_all_specialist_agents()
    human_review_cases = [
        case_id
        for case_id, bundle in reviews.items()
        if (
            bundle.clinical_risk.severity == "high"
            or bundle.medication_safety.needs_human_review
            or bundle.care_management.needs_human_review
            or bundle.service_review.needs_human_review
        )
    ]
    print(f"specialist_reviewed_cases={len(reviews)}")
    print(f"specialist_human_review_candidates={len(human_review_cases)}")
    print(f"first_human_review_candidate={human_review_cases[0] if human_review_cases else 'none'}")


if __name__ == "__main__":
    main()
