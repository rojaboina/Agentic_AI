from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from app.schemas import (
    ClinicalExtraction,
    ClinicalPanelDecision,
    GuidelineResult,
    HumanReviewRoute,
    MedicationSafetyResult,
    MemoryContext,
    MemoryEntry,
    RiskScores,
    SpecialistReviewBundle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

MEMORY_PROVIDER = os.getenv("MEMORY_PROVIDER", "local").strip().lower()
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
MEM0_USER_ID = os.getenv("MEM0_USER_ID", "healthcare-review-demo")
LOCAL_MEMORY_PATH = Path(
    os.getenv("LOCAL_MEMORY_PATH", PROJECT_ROOT / "data" / "case_memory.json")
)


def has_real_key(value: Optional[str]) -> bool:
    if not value:
        return False
    lowered = value.strip().lower()
    return not lowered.startswith("your_") and "api_key_here" not in lowered


def case_memory_query(extraction: ClinicalExtraction) -> str:
    patient_case = extraction.patient_case
    high_signal_text = " ".join(
        [
            extraction.age_group,
            patient_case.chief_concern,
            patient_case.requested_service or "",
            " ".join(patient_case.diagnoses),
            " ".join(patient_case.medications),
            " ".join(extraction.note_signals),
        ]
    )
    return high_signal_text.lower()


def memory_entry_from_record(record: dict[str, Any]) -> MemoryEntry:
    return MemoryEntry(
        memory=str(record.get("memory") or record.get("text") or record.get("content") or ""),
        source=str(record.get("source") or "mem0"),
        score=record.get("score"),
        metadata=record.get("metadata") if isinstance(record.get("metadata"), dict) else {},
    )


def load_local_memory() -> list[dict[str, Any]]:
    if not LOCAL_MEMORY_PATH.exists():
        return []
    try:
        return json.loads(LOCAL_MEMORY_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def save_local_memory(records: list[dict[str, Any]]) -> None:
    LOCAL_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_MEMORY_PATH.write_text(json.dumps(records, indent=2))


def search_local_memory(extraction: ClinicalExtraction, limit: int) -> list[MemoryEntry]:
    query_terms = set(case_memory_query(extraction).split())
    scored: list[tuple[int, dict[str, Any]]] = []
    for record in load_local_memory():
        searchable = " ".join(
            [
                str(record.get("memory", "")),
                json.dumps(record.get("metadata", {})),
            ]
        ).lower()
        score = sum(1 for term in query_terms if len(term) > 3 and term in searchable)
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        MemoryEntry(
            memory=str(record.get("memory", "")),
            source="local",
            score=float(score),
            metadata=record.get("metadata", {}),
        )
        for score, record in scored[:limit]
    ]


def get_mem0_client():
    if MEMORY_PROVIDER != "mem0" or not has_real_key(MEM0_API_KEY):
        return None
    try:
        from mem0 import MemoryClient  # type: ignore
    except ImportError:
        return None
    return MemoryClient(api_key=MEM0_API_KEY)


def search_mem0_memory(extraction: ClinicalExtraction, limit: int) -> list[MemoryEntry]:
    client = get_mem0_client()
    if client is None:
        return []
    try:
        results = client.search(
            query=case_memory_query(extraction),
            filters={"user_id": MEM0_USER_ID},
            limit=limit,
        )
    except Exception:
        return []
    if isinstance(results, dict):
        records = results.get("results") or results.get("memories") or []
    else:
        records = results
    return [memory_entry_from_record(record) for record in records if isinstance(record, dict)]


def retrieve_case_memory(extraction: ClinicalExtraction, limit: int = 4) -> MemoryContext:
    provider = "mem0" if MEMORY_PROVIDER == "mem0" else "local"
    entries = search_mem0_memory(extraction, limit) if provider == "mem0" else []
    if not entries:
        provider = "local"
        entries = search_local_memory(extraction, limit)
    return MemoryContext(provider=provider, entries=entries)


def summarize_case_for_memory(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
    human_route: HumanReviewRoute,
    panel_decision: ClinicalPanelDecision,
) -> str:
    patient_case = extraction.patient_case
    high_flags = [flag.code for flag in guideline_result.flags if flag.severity == "high"]
    med_issues = [finding.issue for finding in medication_safety_result.findings]
    return (
        f"Case {extraction.case_id}: {patient_case.chief_concern}. "
        f"Diagnoses: {', '.join(patient_case.diagnoses)}. "
        f"Medications: {', '.join(patient_case.medications)}. "
        f"High flags: {', '.join(high_flags) or 'none'}. "
        f"Medication issues: {', '.join(med_issues) or 'none'}. "
        f"Overall risk: {risk_scores.overall_risk}. "
        f"Human review: {human_route.human_review.required} by {human_route.human_review.reviewer_role}. "
        f"Final panel decision: {panel_decision.decision}. "
        f"Specialist sources: clinical={specialist_bundle.clinical_risk.source}, "
        f"medication={specialist_bundle.medication_safety.source}, "
        f"care={specialist_bundle.care_management.source}, service={specialist_bundle.service_review.source}."
    )


def write_local_memory(memory_text: str, metadata: dict[str, Any]) -> None:
    records = load_local_memory()
    memory_id = metadata.get("case_id")
    records = [
        record
        for record in records
        if record.get("metadata", {}).get("case_id") != memory_id
    ]
    records.append({"memory": memory_text, "metadata": metadata})
    save_local_memory(records)


def write_mem0_memory(memory_text: str, metadata: dict[str, Any]) -> bool:
    client = get_mem0_client()
    if client is None:
        return False
    try:
        client.add(
            [{"role": "assistant", "content": memory_text}],
            user_id=MEM0_USER_ID,
            metadata=metadata,
        )
        return True
    except Exception:
        return False


def write_case_memory(
    extraction: ClinicalExtraction,
    guideline_result: GuidelineResult,
    medication_safety_result: MedicationSafetyResult,
    risk_scores: RiskScores,
    specialist_bundle: SpecialistReviewBundle,
    human_route: HumanReviewRoute,
    panel_decision: ClinicalPanelDecision,
) -> MemoryContext:
    memory_text = summarize_case_for_memory(
        extraction,
        guideline_result,
        medication_safety_result,
        risk_scores,
        specialist_bundle,
        human_route,
        panel_decision,
    )
    metadata = {
        "case_id": extraction.case_id,
        "decision": panel_decision.decision,
        "overall_risk": risk_scores.overall_risk,
        "reviewer_role": human_route.human_review.reviewer_role,
        "written_at": datetime.now(timezone.utc).isoformat(),
    }
    provider = "local"
    if MEMORY_PROVIDER == "mem0" and write_mem0_memory(memory_text, metadata):
        provider = "mem0"
    else:
        write_local_memory(memory_text, metadata)
    return MemoryContext(
        provider=provider,
        entries=[MemoryEntry(memory=memory_text, source=provider, metadata=metadata)],
    )
