from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.schemas import (
    ClinicalExtraction,
    ClinicalRiskAnalysis,
    GuidelineResult,
    MedicationSafetyResult,
    RiskScores,
    SpecialistReview,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@lru_cache(maxsize=1)
def get_llm() -> Optional[ChatOpenAI]:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        temperature=0,
        timeout=20,
        max_retries=1,
    )


def compact_case_context(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
) -> str:
    patient_case = extraction.patient_case
    payload = {
        "case_id": extraction.case_id,
        "age": patient_case.patient_age,
        "sex": patient_case.sex,
        "chief_concern": patient_case.chief_concern,
        "diagnoses": patient_case.diagnoses,
        "medications": patient_case.medications,
        "allergies": patient_case.allergies,
        "labs": patient_case.lab_results,
        "vitals": patient_case.vitals.model_dump(),
        "recent_visits": patient_case.recent_visits,
        "requested_service": patient_case.requested_service,
        "clinical_note": patient_case.clinical_note,
        "extracted_signals": {
            "age_group": extraction.age_group,
            "abnormal_labs": extraction.abnormal_labs,
            "vital_sign_flags": extraction.vital_sign_flags,
            "note_signals": extraction.note_signals,
            "missing_fields": extraction.missing_fields,
        },
        "guideline_flags": [
            flag.model_dump()
            for flag in guideline_result.flags
        ],
        "medication_findings": [
            finding.model_dump()
            for finding in medication_safety_result.findings
        ],
        "risk_scores": risk_scores.model_dump(),
    }
    return json.dumps(payload, indent=2)


def invoke_structured_llm(
    output_schema,
    agent_name: str,
    task: str,
    context: str,
):
    llm = get_llm()
    if llm is None:
        return None

    structured_llm = llm.with_structured_output(output_schema)
    return structured_llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a healthcare case review assistant used for clinical decision support. "
                    "Do not diagnose or prescribe. Use only the provided case data, rule outputs, "
                    "risk scores, and safety findings. Be concise, conservative, and route uncertain "
                    "or high-risk cases to human review."
                )
            ),
            HumanMessage(
                content=(
                    f"Agent: {agent_name}\n"
                    f"Task: {task}\n\n"
                    f"Case context:\n{context}"
                )
            ),
        ]
    )


def build_llm_clinical_risk_agent(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
) -> Optional[ClinicalRiskAnalysis]:
    context = compact_case_context(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
    )
    review = invoke_structured_llm(
        ClinicalRiskAnalysis,
        "Clinical Risk Agent",
        (
            "Summarize clinical risk, red flags, care gaps, and missing information. "
            "Severity must be low, medium, or high."
        ),
        context,
    )
    if review is not None:
        review.source = "llm"
    return review


def build_llm_specialist_review(
    agent_name: str,
    task: str,
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
) -> Optional[SpecialistReview]:
    context = compact_case_context(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
    )
    review = invoke_structured_llm(
        SpecialistReview,
        agent_name,
        task,
        context,
    )
    if review is not None:
        review.source = "llm"
    return review
