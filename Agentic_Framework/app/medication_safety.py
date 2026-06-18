from __future__ import annotations

from app.extractor import extract_all_cases
from app.schemas import ClinicalExtraction, MedicationSafetyFinding, MedicationSafetyResult


OLDER_ADULT_HIGH_RISK_MEDICATIONS = {
    "alprazolam": "Benzodiazepines can increase sedation, confusion, and fall risk in older adults.",
    "zolpidem": "Sedative-hypnotics can increase confusion and fall risk in older adults.",
}

CONTROLLED_SUBSTANCE_MEDICATIONS = {
    "oxycodone": "Controlled substance refill requests require safety and agreement review.",
}

ANTICOAGULANTS = {
    "warfarin",
    "apixaban",
}


def add_finding(
    findings: list[MedicationSafetyFinding],
    medication: str | None,
    issue: str,
    severity: str,
    rationale: str,
) -> None:
    findings.append(
        MedicationSafetyFinding(
            medication=medication,
            issue=issue,
            severity=severity,  # type: ignore[arg-type]
            rationale=rationale,
        )
    )


def check_older_adult_medications(
    extraction: ClinicalExtraction,
    findings: list[MedicationSafetyFinding],
) -> None:
    if extraction.age_group != "older_adult":
        return

    medications = set(extraction.normalized_medications)
    for medication, rationale in OLDER_ADULT_HIGH_RISK_MEDICATIONS.items():
        if medication in medications:
            add_finding(
                findings,
                medication=medication,
                issue="high-risk medication in older adult",
                severity="high",
                rationale=rationale,
            )

    if {"alprazolam", "zolpidem"}.issubset(medications):
        add_finding(
            findings,
            medication="alprazolam + zolpidem",
            issue="sedative combination",
            severity="high",
            rationale="Combined sedating medications can further increase fall, confusion, and respiratory safety risk.",
        )


def check_renal_medication_risk(
    extraction: ClinicalExtraction,
    findings: list[MedicationSafetyFinding],
) -> None:
    medications = set(extraction.normalized_medications)
    egfr = extraction.patient_case.lab_results.get("egfr")

    if "nitrofurantoin" in medications and egfr is not None and egfr < 45:
        add_finding(
            findings,
            medication="nitrofurantoin",
            issue="renal function medication concern",
            severity="high",
            rationale=f"eGFR is {egfr}; nitrofurantoin may be inappropriate or less effective with reduced renal function.",
        )

    creatinine = extraction.patient_case.lab_results.get("creatinine")
    if creatinine is not None and creatinine > 1.5 and medications.intersection({"metformin", "lisinopril", "losartan"}):
        add_finding(
            findings,
            medication=", ".join(sorted(medications.intersection({"metformin", "lisinopril", "losartan"}))),
            issue="kidney function monitoring needed",
            severity="medium",
            rationale=f"Creatinine is {creatinine}; kidney-sensitive medications may need monitoring.",
        )


def check_anticoagulation_risk(
    extraction: ClinicalExtraction,
    findings: list[MedicationSafetyFinding],
) -> None:
    medications = set(extraction.normalized_medications)

    if "warfarin" in medications:
        inr = extraction.patient_case.lab_results.get("inr")
        if inr is not None and inr > 3.5:
            add_finding(
                findings,
                medication="warfarin",
                issue="supratherapeutic INR",
                severity="high",
                rationale=f"INR is {inr}; elevated INR increases bleeding risk.",
            )
        else:
            add_finding(
                findings,
                medication="warfarin",
                issue="anticoagulation monitoring",
                severity="medium",
                rationale="Warfarin requires ongoing INR and bleeding risk monitoring.",
            )

    if medications.intersection(ANTICOAGULANTS) and "bleeding_risk" in extraction.note_signals:
        add_finding(
            findings,
            medication=", ".join(sorted(medications.intersection(ANTICOAGULANTS))),
            issue="bleeding symptom signal",
            severity="high",
            rationale="Clinical note contains bleeding-risk language while anticoagulation is present.",
        )


def check_pain_and_bleeding_risk(
    extraction: ClinicalExtraction,
    findings: list[MedicationSafetyFinding],
) -> None:
    medications = set(extraction.normalized_medications)

    if "ibuprofen" in medications and "hemoglobin" in extraction.abnormal_labs:
        add_finding(
            findings,
            medication="ibuprofen",
            issue="NSAID with anemia/possible bleeding concern",
            severity="high",
            rationale="NSAID use plus low hemoglobin or dark stools can suggest gastrointestinal bleeding risk.",
        )

    for medication, rationale in CONTROLLED_SUBSTANCE_MEDICATIONS.items():
        if medication in medications:
            severity = "high" if "missed" in " ".join(extraction.patient_case.recent_visits).lower() else "medium"
            add_finding(
                findings,
                medication=medication,
                issue="controlled substance safety review",
                severity=severity,
                rationale=rationale,
            )

    if {"oxycodone", "cyclobenzaprine"}.issubset(medications):
        add_finding(
            findings,
            medication="oxycodone + cyclobenzaprine",
            issue="sedating medication combination",
            severity="medium",
            rationale="Opioid plus muscle relaxant can increase sedation and safety risk.",
        )


def check_allergy_conflicts(
    extraction: ClinicalExtraction,
    findings: list[MedicationSafetyFinding],
) -> None:
    medications = set(extraction.normalized_medications)
    allergies = set(extraction.patient_case.allergies)

    if "amoxicillin" in medications and "amoxicillin" in allergies:
        add_finding(
            findings,
            medication="amoxicillin",
            issue="documented allergy conflict",
            severity="high",
            rationale="Medication appears to conflict with a documented allergy.",
        )

    if "ciprofloxacin" in medications and "ciprofloxacin" in allergies:
        add_finding(
            findings,
            medication="ciprofloxacin",
            issue="documented allergy conflict",
            severity="high",
            rationale="Medication appears to conflict with a documented allergy.",
        )


def run_medication_safety_checks(extraction: ClinicalExtraction) -> MedicationSafetyResult:
    findings: list[MedicationSafetyFinding] = []
    check_older_adult_medications(extraction, findings)
    check_renal_medication_risk(extraction, findings)
    check_anticoagulation_risk(extraction, findings)
    check_pain_and_bleeding_risk(extraction, findings)
    check_allergy_conflicts(extraction, findings)

    return MedicationSafetyResult(
        has_safety_issue=bool(findings),
        findings=findings,
        confidence=1.0,
    )


def run_all_medication_safety_checks() -> dict[str, MedicationSafetyResult]:
    return {
        extraction.case_id: run_medication_safety_checks(extraction)
        for extraction in extract_all_cases()
    }


def main() -> None:
    results = run_all_medication_safety_checks()
    flagged_cases = [
        case_id
        for case_id, result in results.items()
        if result.has_safety_issue
    ]
    total_findings = sum(len(result.findings) for result in results.values())
    print(f"medication_checked_cases={len(results)}")
    print(f"medication_flagged_cases={len(flagged_cases)}")
    print(f"total_medication_findings={total_findings}")
    print(f"first_flagged_case={flagged_cases[0] if flagged_cases else 'none'}")


if __name__ == "__main__":
    main()
