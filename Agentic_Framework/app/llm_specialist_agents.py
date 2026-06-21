from __future__ import annotations

import json
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.schemas import (
    ClinicalExtraction,
    ClinicalRiskAnalysis,
    GuidelineResult,
    MemoryContext,
    MedicationSafetyResult,
    RiskScores,
    SpecialistReview,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def has_real_key(value: Optional[str]) -> bool:
    if not value:
        return False
    lowered = value.strip().lower()
    return not lowered.startswith("your_") and "api_key_here" not in lowered


@lru_cache(maxsize=1)
def get_llm() -> Optional[ChatOpenAI]:
    if DEFAULT_PROVIDER != "openai":
        return None
    if not has_real_key(os.getenv("OPENAI_API_KEY")):
        return None
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        temperature=0,
        timeout=20,
        max_retries=1,
    )


def get_llm_provider() -> str:
    if DEFAULT_PROVIDER == "ollama":
        return "ollama"
    if DEFAULT_PROVIDER == "groq" and has_real_key(GROQ_API_KEY):
        return "groq"
    if get_llm() is not None:
        return "openai"
    return "none"


def compact_case_context(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    memory_context: Optional[MemoryContext] = None,
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
    if memory_context is not None and memory_context.entries:
        payload["retrieved_memory"] = memory_context.model_dump()
    return json.dumps(payload, indent=2)


def invoke_structured_llm(
    output_schema,
    agent_name: str,
    task: str,
    context: str,
):
    if DEFAULT_PROVIDER == "ollama":
        return invoke_ollama_structured(output_schema, agent_name, task, context)
    if DEFAULT_PROVIDER == "groq":
        return invoke_groq_structured(output_schema, agent_name, task, context)

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


def invoke_ollama_structured(
    output_schema,
    agent_name: str,
    task: str,
    context: str,
):
    schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
    prompt = (
        "You are a healthcare case review assistant used for clinical decision support. "
        "Do not diagnose or prescribe. Use only the provided case data, rule outputs, "
        "risk scores, and safety findings. Be concise, conservative, and route uncertain "
        "or high-risk cases to human review.\n\n"
        f"Agent: {agent_name}\n"
        f"Task: {task}\n\n"
        "Return only valid JSON matching this schema. Do not wrap it in markdown.\n"
        f"JSON schema:\n{schema_json}\n\n"
        f"Case context:\n{context}"
    )
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    request = Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except URLError:
        return None

    content = response_payload.get("message", {}).get("content")
    if not content:
        return None
    return output_schema.model_validate_json(content)


def invoke_groq_structured(
    output_schema,
    agent_name: str,
    task: str,
    context: str,
):
    if not has_real_key(GROQ_API_KEY):
        return None

    schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a healthcare case review assistant used for clinical decision support. "
                "Do not diagnose or prescribe. Use only the provided case data, rule outputs, "
                "risk scores, and safety findings. Be concise, conservative, and route uncertain "
                "or high-risk cases to human review."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Agent: {agent_name}\n"
                f"Task: {task}\n\n"
                "Return only valid JSON matching this schema. Do not wrap it in markdown.\n"
                f"JSON schema:\n{schema_json}\n\n"
                f"Case context:\n{context}"
            ),
        },
    ]

    response_formats = [
        {
            "type": "json_schema",
            "json_schema": {
                "name": output_schema.__name__,
                "strict": False,
                "schema": output_schema.model_json_schema(),
            },
        },
        {"type": "json_object"},
    ]

    for response_format in response_formats:
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0,
            "response_format": response_format,
        }
        request = Request(
            f"{GROQ_BASE_URL}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "agentic-healthcare-demo/1.0",
            },
            method="POST",
        )
        response_payload = None
        for attempt in range(2):
            try:
                with urlopen(request, timeout=60) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="ignore")
                if exc.code == 429 and attempt == 0:
                    match = re.search(r"try again in ([0-9.]+)s", body, re.IGNORECASE)
                    wait_seconds = min(float(match.group(1)) + 1.0, 20.0) if match else 8.0
                    time.sleep(wait_seconds)
                    continue
                break
            except (URLError, TimeoutError, ValueError):
                break
        if response_payload is None:
            continue

        choices = response_payload.get("choices", [])
        if not choices:
            continue
        content = choices[0].get("message", {}).get("content")
        if not content:
            continue
        return output_schema.model_validate_json(content)

    return None


def build_llm_clinical_risk_agent(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    memory_context: Optional[MemoryContext] = None,
) -> Optional[ClinicalRiskAnalysis]:
    context = compact_case_context(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        memory_context,
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
    memory_context: Optional[MemoryContext] = None,
) -> Optional[SpecialistReview]:
    context = compact_case_context(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        memory_context,
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
