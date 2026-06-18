from __future__ import annotations

from app.schemas import ClinicalExtraction, PatientCase
from app.validate_data import load_patient_cases


LAB_THRESHOLDS: dict[str, tuple[float | None, float | None]] = {
    "a1c": (None, 8.0),
    "alt": (None, 45.0),
    "absolute_neutrophil_count": (500.0, None),
    "ast": (None, 45.0),
    "bilirubin": (None, 1.2),
    "bmi": (None, 35.0),
    "bnp": (None, 400.0),
    "c_reactive_protein": (None, 10.0),
    "creatinine": (None, 1.5),
    "egfr": (45.0, None),
    "ferritin": (15.0, None),
    "gad7": (None, 10.0),
    "hemoglobin": (10.0, None),
    "inr": (None, 3.5),
    "ldl": (None, 130.0),
    "phq9": (None, 15.0),
    "platelets": (150.0, None),
    "potassium": (3.5, 5.0),
    "protein_creatinine_ratio": (None, 0.3),
    "temperature_f": (None, 100.4),
    "troponin": (None, 0.04),
    "wbc": (None, 11.0),
}

NOTE_SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "adherence_issue": ("adherence", "missed", "inconsistent"),
    "bleeding_risk": ("bruising", "dark stools", "bleeding"),
    "care_gap": ("due for", "not yet scheduled", "gap"),
    "infection_risk": ("fever", "chills", "drainage", "redness", "leukocytosis"),
    "medication_access_barrier": ("medication access", "transportation barriers", "housing instability"),
    "urgent_symptom": ("chest pressure", "shortness of breath", "confusion", "fainted"),
}


def normalize_text_list(values: list[str]) -> list[str]:
    return sorted({value.strip().lower() for value in values if value.strip()})


def get_age_group(age: int) -> str:
    if age < 13:
        return "pediatric"
    if age < 18:
        return "adolescent"
    if age < 65:
        return "adult"
    return "older_adult"


def find_abnormal_labs(lab_results: dict[str, float]) -> dict[str, float]:
    abnormal: dict[str, float] = {}
    for lab_name, value in lab_results.items():
        lower_limit, upper_limit = LAB_THRESHOLDS.get(lab_name, (None, None))
        if lower_limit is not None and value < lower_limit:
            abnormal[lab_name] = value
        if upper_limit is not None and value > upper_limit:
            abnormal[lab_name] = value
    return abnormal


def find_vital_sign_flags(case: PatientCase) -> list[str]:
    flags: list[str] = []
    vitals = case.vitals

    if vitals.systolic_bp is not None and vitals.systolic_bp >= 150:
        flags.append("elevated_systolic_bp")
    if vitals.diastolic_bp is not None and vitals.diastolic_bp >= 90:
        flags.append("elevated_diastolic_bp")
    if vitals.heart_rate is not None and vitals.heart_rate >= 100:
        flags.append("tachycardia")
    if vitals.oxygen_saturation is not None and vitals.oxygen_saturation < 92:
        flags.append("low_oxygen_saturation")

    return flags


def find_note_signals(clinical_note: str) -> list[str]:
    note = clinical_note.lower()
    signals = [
        signal
        for signal, keywords in NOTE_SIGNAL_KEYWORDS.items()
        if any(keyword in note for keyword in keywords)
    ]
    return sorted(signals)


def find_missing_fields(case: PatientCase) -> list[str]:
    missing: list[str] = []
    required_text_fields = {
        "chief_concern": case.chief_concern,
        "clinical_note": case.clinical_note,
        "sex": case.sex,
    }
    for field_name, value in required_text_fields.items():
        if not value.strip():
            missing.append(field_name)
    if case.patient_age is None:
        missing.append("patient_age")
    if not case.diagnoses:
        missing.append("diagnoses")
    return missing


def extract_patient_case(raw_case: dict) -> ClinicalExtraction:
    patient_case = PatientCase.model_validate(raw_case)
    return ClinicalExtraction(
        case_id=patient_case.case_id,
        patient_case=patient_case,
        age_group=get_age_group(patient_case.patient_age),
        normalized_diagnoses=normalize_text_list(patient_case.diagnoses),
        normalized_medications=normalize_text_list(patient_case.medications),
        abnormal_labs=find_abnormal_labs(patient_case.lab_results),
        vital_sign_flags=find_vital_sign_flags(patient_case),
        note_signals=find_note_signals(patient_case.clinical_note),
        missing_fields=find_missing_fields(patient_case),
    )


def extract_all_cases() -> list[ClinicalExtraction]:
    return [
        extract_patient_case(case.model_dump())
        for case in load_patient_cases()
    ]


def main() -> None:
    extractions = extract_all_cases()
    human_review_candidates = sum(
        1
        for extraction in extractions
        if extraction.abnormal_labs or extraction.vital_sign_flags
    )
    print(f"extracted_cases={len(extractions)}")
    print(f"first_case={extractions[0].case_id}")
    print(f"cases_with_extracted_risk_signals={human_review_candidates}")


if __name__ == "__main__":
    main()
