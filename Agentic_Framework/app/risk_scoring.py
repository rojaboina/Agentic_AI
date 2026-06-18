from __future__ import annotations

from typing import Optional

from app.extractor import extract_all_cases
from app.guidelines import run_guideline_checks
from app.medication_safety import run_medication_safety_checks
from app.schemas import ClinicalExtraction, GuidelineResult, MedicationSafetyResult, RiskScores


READMISSION_SIGNALS = {
    "recent ed visit",
    "ed visit",
    "urgent care",
    "surgery",
    "chemotherapy",
}

MEDICATION_RISK_CODES = {
    "LAB_EGFR",
    "LAB_INR",
    "LAB_POTASSIUM",
}

CARE_GAP_CODES = {
    "CARE_GAP_SIGNAL",
    "LAB_A1C",
    "LAB_LDL",
    "SOCIAL_RISK_SIGNAL",
}


def clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def count_guideline_flags(guideline_result: GuidelineResult, severity: str) -> int:
    return sum(1 for flag in guideline_result.flags if flag.severity == severity)


def has_recent_acute_utilization(extraction: ClinicalExtraction) -> bool:
    visits = " ".join(extraction.patient_case.recent_visits).lower()
    return any(signal in visits for signal in READMISSION_SIGNALS)


def score_readmission_risk(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
) -> float:
    score = 0.1
    score += 0.18 * count_guideline_flags(guideline_result, "high")
    score += 0.06 * count_guideline_flags(guideline_result, "medium")

    if has_recent_acute_utilization(extraction):
        score += 0.18
    if extraction.age_group == "older_adult":
        score += 0.08
    if "urgent_symptom" in extraction.note_signals:
        score += 0.16
    if "infection_risk" in extraction.note_signals:
        score += 0.12
    if "heart failure" in extraction.normalized_diagnoses:
        score += 0.12
    if "chronic kidney disease" in extraction.normalized_diagnoses:
        score += 0.1

    return clamp_score(score)


def score_medication_safety_risk(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: Optional[MedicationSafetyResult] = None,
) -> float:
    score = 0.05
    guideline_codes = {flag.code for flag in guideline_result.flags}
    medications = set(extraction.normalized_medications)

    score += 0.12 * len(guideline_codes.intersection(MEDICATION_RISK_CODES))
    if extraction.age_group == "older_adult" and medications.intersection({"zolpidem", "alprazolam"}):
        score += 0.3
    if "warfarin" in medications:
        score += 0.25
    if "oxycodone" in medications:
        score += 0.25
    if "nitrofurantoin" in medications and "LAB_EGFR" in guideline_codes:
        score += 0.35
    if "ibuprofen" in medications and "LAB_HEMOGLOBIN" in guideline_codes:
        score += 0.25
    if "bleeding_risk" in extraction.note_signals:
        score += 0.15

    if medication_safety_result is not None:
        high_findings = sum(1 for finding in medication_safety_result.findings if finding.severity == "high")
        medium_findings = sum(1 for finding in medication_safety_result.findings if finding.severity == "medium")
        score += 0.25 * high_findings
        score += 0.12 * medium_findings

    return clamp_score(score)


def score_care_gap_risk(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
) -> float:
    score = 0.05
    guideline_codes = {flag.code for flag in guideline_result.flags}

    score += 0.12 * len(guideline_codes.intersection(CARE_GAP_CODES))
    if "care_gap" in extraction.note_signals:
        score += 0.2
    if "medication_access_barrier" in extraction.note_signals:
        score += 0.25
    if "adherence_issue" in extraction.note_signals:
        score += 0.18
    if "type 2 diabetes" in extraction.normalized_diagnoses and "a1c" in extraction.abnormal_labs:
        score += 0.18
    if extraction.missing_fields:
        score += 0.2

    return clamp_score(score)


def score_overall_risk(
    readmission_risk: float,
    medication_safety_risk: float,
    care_gap_risk: float,
    guideline_result: GuidelineResult,
) -> float:
    high_flag_count = count_guideline_flags(guideline_result, "high")
    weighted_score = (
        readmission_risk * 0.45
        + medication_safety_risk * 0.35
        + care_gap_risk * 0.2
    )
    weighted_score += min(0.24, 0.06 * high_flag_count)
    return clamp_score(weighted_score)


def build_rationale(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    readmission_risk: float,
    medication_safety_risk: float,
    care_gap_risk: float,
    overall_risk: float,
) -> str:
    high_flags = [flag.code for flag in guideline_result.flags if flag.severity == "high"]
    medium_flags = [flag.code for flag in guideline_result.flags if flag.severity == "medium"]
    parts = [
        f"Overall risk {overall_risk} is based on readmission={readmission_risk}, "
        f"medication_safety={medication_safety_risk}, care_gap={care_gap_risk}.",
    ]
    if high_flags:
        parts.append(f"High-severity guideline flags: {', '.join(high_flags)}.")
    if medium_flags:
        parts.append(f"Medium-severity guideline flags: {', '.join(medium_flags[:6])}.")
    if extraction.note_signals:
        parts.append(f"Extracted note signals: {', '.join(extraction.note_signals)}.")
    return " ".join(parts)


def calculate_risk_scores(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: Optional[MedicationSafetyResult] = None,
) -> RiskScores:
    readmission_risk = score_readmission_risk(extraction, guideline_result)
    medication_safety_risk = score_medication_safety_risk(
        extraction,
        guideline_result,
        medication_safety_result,
    )
    care_gap_risk = score_care_gap_risk(extraction, guideline_result)
    overall_risk = score_overall_risk(
        readmission_risk,
        medication_safety_risk,
        care_gap_risk,
        guideline_result,
    )
    return RiskScores(
        readmission_risk=readmission_risk,
        medication_safety_risk=medication_safety_risk,
        care_gap_risk=care_gap_risk,
        overall_risk=overall_risk,
        rationale=build_rationale(
            extraction,
            guideline_result,
            readmission_risk,
            medication_safety_risk,
            care_gap_risk,
            overall_risk,
        ),
    )


def calculate_all_risk_scores() -> dict[str, RiskScores]:
    scores: dict[str, RiskScores] = {}
    for extraction in extract_all_cases():
        guideline_result = run_guideline_checks(extraction)
        medication_safety_result = run_medication_safety_checks(extraction)
        scores[extraction.case_id] = calculate_risk_scores(
            extraction,
            guideline_result,
            medication_safety_result,
        )
    return scores


def main() -> None:
    scores = calculate_all_risk_scores()
    high_risk_cases = [
        case_id
        for case_id, risk_scores in scores.items()
        if risk_scores.overall_risk >= 0.7
    ]
    print(f"risk_scored_cases={len(scores)}")
    print(f"high_risk_cases={len(high_risk_cases)}")
    print(f"highest_risk_case={max(scores, key=lambda case_id: scores[case_id].overall_risk)}")


if __name__ == "__main__":
    main()
