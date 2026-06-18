from __future__ import annotations

from app.extractor import extract_all_cases
from app.schemas import ClinicalExtraction, GuidelineFlag, GuidelineResult


HIGH_RISK_LABS: dict[str, str] = {
    "absolute_neutrophil_count": "Possible neutropenia requires urgent oncology/infection review.",
    "egfr": "Reduced kidney function may require medication or dosing review.",
    "hemoglobin": "Low hemoglobin may indicate clinically significant anemia or bleeding risk.",
    "inr": "Supratherapeutic INR increases bleeding risk.",
    "oxygen_saturation": "Low oxygen saturation requires urgent respiratory review.",
    "protein_creatinine_ratio": "Proteinuria in pregnancy can indicate preeclampsia risk.",
    "troponin": "Elevated troponin with symptoms requires urgent cardiac review.",
}

MODERATE_RISK_LABS: dict[str, str] = {
    "a1c": "Elevated A1c suggests uncontrolled diabetes or care gap.",
    "ast": "Elevated AST may require liver risk review.",
    "alt": "Elevated ALT may require liver risk review.",
    "bilirubin": "Elevated bilirubin may require liver risk review.",
    "bnp": "Elevated BNP may indicate heart failure exacerbation risk.",
    "c_reactive_protein": "Elevated inflammatory marker may support infection or inflammation concern.",
    "creatinine": "Elevated creatinine may require kidney function review.",
    "ferritin": "Low ferritin may support iron deficiency evaluation.",
    "gad7": "Elevated anxiety score may require behavioral health follow-up.",
    "ldl": "Elevated LDL suggests cardiovascular prevention gap.",
    "phq9": "Elevated depression score may require behavioral health follow-up.",
    "platelets": "Low platelets may require bleeding or liver risk review.",
    "potassium": "Abnormal potassium may require medication or safety review.",
    "temperature_f": "Fever may require infection triage.",
    "wbc": "Elevated white blood cell count may support infection concern.",
}

HIGH_RISK_DIAGNOSES = {
    "chemotherapy-induced neutropenia",
    "coronary artery disease",
    "pregnancy",
    "syncope",
}

HIGH_RISK_SERVICES = {
    "urgent cardiology review",
    "urgent medication and infection review",
    "urgent obstetric review",
    "urgent oncology triage",
    "urgent wound care review",
}


def add_flag(
    flags: list[GuidelineFlag],
    code: str,
    severity: str,
    message: str,
    evidence: str | None = None,
) -> None:
    flags.append(
        GuidelineFlag(
            code=code,
            severity=severity,  # type: ignore[arg-type]
            message=message,
            evidence=evidence,
        )
    )


def check_missing_data(extraction: ClinicalExtraction, flags: list[GuidelineFlag]) -> None:
    if extraction.missing_fields:
        add_flag(
            flags,
            code="MISSING_REQUIRED_DATA",
            severity="medium",
            message="Case is missing fields needed for confident review.",
            evidence=", ".join(extraction.missing_fields),
        )


def check_vitals(extraction: ClinicalExtraction, flags: list[GuidelineFlag]) -> None:
    for vital_flag in extraction.vital_sign_flags:
        severity = "high" if vital_flag == "low_oxygen_saturation" else "medium"
        add_flag(
            flags,
            code=f"VITAL_{vital_flag.upper()}",
            severity=severity,
            message=f"Vital sign rule triggered: {vital_flag.replace('_', ' ')}.",
            evidence=str(extraction.patient_case.vitals.model_dump()),
        )


def check_labs(extraction: ClinicalExtraction, flags: list[GuidelineFlag]) -> None:
    for lab_name, value in extraction.abnormal_labs.items():
        if lab_name in HIGH_RISK_LABS:
            add_flag(
                flags,
                code=f"LAB_{lab_name.upper()}",
                severity="high",
                message=HIGH_RISK_LABS[lab_name],
                evidence=f"{lab_name}={value}",
            )
        elif lab_name in MODERATE_RISK_LABS:
            add_flag(
                flags,
                code=f"LAB_{lab_name.upper()}",
                severity="medium",
                message=MODERATE_RISK_LABS[lab_name],
                evidence=f"{lab_name}={value}",
            )


def check_clinical_context(extraction: ClinicalExtraction, flags: list[GuidelineFlag]) -> None:
    diagnoses = set(extraction.normalized_diagnoses)
    service = (extraction.patient_case.requested_service or "").lower()
    note_signals = set(extraction.note_signals)

    matched_diagnoses = sorted(diagnoses.intersection(HIGH_RISK_DIAGNOSES))
    if matched_diagnoses:
        add_flag(
            flags,
            code="HIGH_RISK_DIAGNOSIS",
            severity="high",
            message="Case includes a diagnosis that should receive careful clinical review.",
            evidence=", ".join(matched_diagnoses),
        )

    if service in HIGH_RISK_SERVICES:
        add_flag(
            flags,
            code="HIGH_RISK_REQUESTED_SERVICE",
            severity="high",
            message="Requested service is categorized as urgent or high-risk.",
            evidence=service,
        )

    if "urgent_symptom" in note_signals:
        add_flag(
            flags,
            code="URGENT_NOTE_SIGNAL",
            severity="high",
            message="Clinical note contains urgent symptom language.",
            evidence=extraction.patient_case.chief_concern,
        )

    if "care_gap" in note_signals:
        add_flag(
            flags,
            code="CARE_GAP_SIGNAL",
            severity="medium",
            message="Clinical note suggests a care gap or delayed follow-up.",
            evidence=extraction.patient_case.requested_service,
        )

    if "medication_access_barrier" in note_signals:
        add_flag(
            flags,
            code="SOCIAL_RISK_SIGNAL",
            severity="medium",
            message="Clinical note suggests social or medication-access barriers.",
            evidence="medication access, transportation, or housing signal",
        )


def run_guideline_checks(extraction: ClinicalExtraction) -> GuidelineResult:
    flags: list[GuidelineFlag] = []
    check_missing_data(extraction, flags)
    check_vitals(extraction, flags)
    check_labs(extraction, flags)
    check_clinical_context(extraction, flags)

    high_severity_count = sum(1 for flag in flags if flag.severity == "high")
    confidence = 1.0 if not extraction.missing_fields else 0.75
    return GuidelineResult(
        passed=high_severity_count == 0,
        flags=flags,
        confidence=confidence,
    )


def run_all_guideline_checks() -> dict[str, GuidelineResult]:
    return {
        extraction.case_id: run_guideline_checks(extraction)
        for extraction in extract_all_cases()
    }


def main() -> None:
    results = run_all_guideline_checks()
    failed_cases = [
        case_id
        for case_id, result in results.items()
        if not result.passed
    ]
    total_flags = sum(len(result.flags) for result in results.values())
    print(f"guideline_checked_cases={len(results)}")
    print(f"guideline_failed_cases={len(failed_cases)}")
    print(f"total_guideline_flags={total_flags}")
    print(f"first_failed_case={failed_cases[0] if failed_cases else 'none'}")


if __name__ == "__main__":
    main()
