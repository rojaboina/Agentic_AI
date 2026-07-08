from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict


SUPPORTED_INTENTS = {
    "focused_metric_question",
    "find_abnormal_labs",
    "metric_trend",
    "patient_summary",
}

METRIC_ALIASES = {
    "a1c": "Hemoglobin A1C",
    "hba1c": "Hemoglobin A1C",
    "average blood glucose": "Average Blood Glucose (Calculated From HgBA1c Level)",
    "glucose": "Glucose",
    "ldl": "LDL Calculated",
    "hdl": "HDL",
    "cholesterol": "Cholesterol, Total",
    "triglyceride": "Triglyceride",
    "triglycerides": "Triglyceride",
    "vitamin d": "Vitamin D Total, 25OH",
    "b12": "Vitamin B12",
    "vitamin b12": "Vitamin B12",
    "tsh": "Thyroid Stimulating Hormone (TSH)",
    "thyroid": "Thyroid Stimulating Hormone (TSH)",
    "thyroxine": "Thyroxine, Free (FT4)",
    "ft4": "Thyroxine, Free (FT4)",
    "iron": "Iron",
    "tibc": "Total Iron Binding Capacity (TIBC)",
    "transferrin": "Percent Transferrin Saturation",
    "saturation": "Percent Transferrin Saturation",
    "egfr": "Glomerular Filtration Rate (eGFR)",
    "kidney": "Glomerular Filtration Rate (eGFR)",
    "bun": "Urea Nitrogen (BUN)",
    "creatinine": "Creatinine",
}

PANEL_ALIASES = {
    "cmp": "COMPREHENSIVE METABOLIC PANEL (CMP)",
    "metabolic": "COMPREHENSIVE METABOLIC PANEL (CMP)",
    "lipid": "LIPID PANEL",
    "cholesterol": "LIPID PANEL",
    "thyroid": "Thyroid Hormone Tests",
    "iron": "IRON AND TOTAL IRON BINDING CAPACITY (TIBC)",
}


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    patient_id: str
    year: int | None = None
    metric: str | None = None
    panel: str | None = None
    scope: str = "relevant_chunks"
    rewritten_query: str = ""
    planner: str = "fallback"

    def to_dict(self) -> dict:
        return asdict(self)


def plan_query(question: str, patient_id: str) -> QueryPlan:
    api_key = os.getenv("NEBIUS_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            return plan_with_llm(question, patient_id, api_key)
        except Exception:
            return fallback_plan(question, patient_id)
    return fallback_plan(question, patient_id)


def plan_with_llm(question: str, patient_id: str, api_key: str) -> QueryPlan:
    model = os.getenv("QUERY_PLANNER_MODEL", "gpt-4.1-mini")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    prompt = {
        "role": "system",
        "content": (
            "You are a query planner for a patient lab-report RAG system. "
            "Return only valid JSON. Do not answer the medical question. "
            "Choose one intent: focused_metric_question, find_abnormal_labs, metric_trend, patient_summary. "
            "Use find_abnormal_labs when the user asks for unusual, concerning, weird, abnormal, bad, high, low, "
            "outside, out-of-bound, outlier, red-flag, or not-okay lab values. "
            "Use metric_trend when the user asks how a metric changed over time. "
            "Use focused_metric_question when the user asks about one metric/panel. "
            "The selected patient_id is authoritative; use it even if the question mentions a name. "
            "Fields: intent, patient_id, year, metric, panel, scope, rewritten_query. "
            "Use null when year, metric, or panel are unknown."
        ),
    }
    user = {
        "role": "user",
        "content": json.dumps({"patient_id": patient_id, "question": question}),
    }
    payload = {
        "model": model,
        "messages": [prompt, user],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    return validate_plan(json.loads(content), patient_id, question, planner="llm")


def validate_plan(raw_plan: dict, patient_id: str, question: str, planner: str) -> QueryPlan:
    intent = str(raw_plan.get("intent") or "focused_metric_question")
    if intent not in SUPPORTED_INTENTS:
        intent = "focused_metric_question"

    year = raw_plan.get("year")
    if isinstance(year, str) and year.isdigit():
        year = int(year)
    if not isinstance(year, int):
        year = extract_year(question)

    metric = raw_plan.get("metric")
    panel = raw_plan.get("panel")
    scope = str(raw_plan.get("scope") or "relevant_chunks")
    rewritten_query = str(raw_plan.get("rewritten_query") or question)

    return QueryPlan(
        intent=intent,
        patient_id=patient_id,
        year=year,
        metric=metric if metric else extract_metric(question),
        panel=panel if panel else extract_panel(question),
        scope=scope,
        rewritten_query=rewritten_query,
        planner=planner,
    )


def fallback_plan(question: str, patient_id: str) -> QueryPlan:
    normalized = question.lower()
    year = extract_year(question)
    metric = extract_metric(question)
    panel = extract_panel(question)

    abnormal_terms = [
        "abnormal",
        "weird",
        "odd",
        "concerning",
        "concern",
        "bad",
        "not okay",
        "not normal",
        "outside",
        "out of",
        "outlier",
        "red flag",
        "high",
        "low",
        "bound",
        "range",
        "wrong",
    ]
    trend_terms = ["trend", "changed", "change", "over time", "history", "getting worse", "improved", "worse"]
    summary_terms = ["summary", "summarize", "main risk", "health risk", "overall", "what is going on"]

    if any(term in normalized for term in trend_terms) and metric:
        intent = "metric_trend"
        scope = "metric_history"
    elif any(term in normalized for term in abnormal_terms) and (
        "all" in normalized or "values" in normalized or "labs" in normalized or "anything" in normalized or year
    ):
        intent = "find_abnormal_labs"
        scope = "all_labs"
    elif any(term in normalized for term in summary_terms):
        intent = "patient_summary"
        scope = "patient"
    else:
        intent = "focused_metric_question"
        scope = "relevant_chunks"

    return QueryPlan(
        intent=intent,
        patient_id=patient_id,
        year=year,
        metric=metric,
        panel=panel,
        scope=scope,
        rewritten_query=question,
        planner="fallback",
    )


def extract_year(question: str) -> int | None:
    match = re.search(r"\b(20\d{2})\b", question)
    return int(match.group(1)) if match else None


def extract_metric(question: str) -> str | None:
    normalized = question.lower()
    for alias, metric in sorted(METRIC_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in normalized:
            return metric
    return None


def extract_panel(question: str) -> str | None:
    normalized = question.lower()
    for alias, panel in sorted(PANEL_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in normalized:
            return panel
    return None
