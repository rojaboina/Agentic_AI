from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.extractor import extract_all_cases
from app.langgraph_pipeline import review_case_with_graph


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = PROJECT_ROOT / "ui"
CASE_DETAIL_CACHE: dict[str, dict] = {}


def model_to_dict(model) -> dict:
    return model.model_dump()


def build_case_index_payload() -> list[dict]:
    return [
        {
            "case_id": extraction.case_id,
            "age": extraction.patient_case.patient_age,
            "sex": extraction.patient_case.sex,
            "chief_concern": extraction.patient_case.chief_concern,
            "requested_service": extraction.patient_case.requested_service,
            "diagnoses": extraction.patient_case.diagnoses,
        }
        for extraction in extract_all_cases()
    ]


def build_case_detail_payload(case_id: str) -> dict | None:
    cache_key = case_id.lower()
    if cache_key in CASE_DETAIL_CACHE:
        return CASE_DETAIL_CACHE[cache_key]

    matching_extraction = next(
        (
            extraction
            for extraction in extract_all_cases()
            if extraction.case_id.lower() == case_id.lower()
        ),
        None,
    )
    if matching_extraction is None:
        return None

    state = review_case_with_graph(matching_extraction)
    extraction = state["extraction"]
    guideline_result = state["guideline_result"]
    medication_safety_result = state["medication_safety_result"]
    risk_scores = state["risk_scores"]
    memory_context = state["memory_context"]
    specialist_bundle = state["specialist_bundle"]
    human_route = state["human_route"]
    panel_decision = state["panel_decision"]
    memory_write = state["memory_write"]
    patient_case = extraction.patient_case

    payload = {
        "case_id": extraction.case_id,
        "age": patient_case.patient_age,
        "sex": patient_case.sex,
        "chief_concern": patient_case.chief_concern,
        "requested_service": patient_case.requested_service,
        "diagnoses": patient_case.diagnoses,
        "medications": patient_case.medications,
        "clinical_note": patient_case.clinical_note,
        "extraction": model_to_dict(extraction),
        "guidelines": model_to_dict(guideline_result),
        "medication_safety": model_to_dict(medication_safety_result),
        "risk_scores": model_to_dict(risk_scores),
        "memory_context": model_to_dict(memory_context),
        "specialists": model_to_dict(specialist_bundle),
        "human_review": model_to_dict(human_route),
        "panel_decision": model_to_dict(panel_decision),
        "memory_write": model_to_dict(memory_write),
    }
    CASE_DETAIL_CACHE[cache_key] = payload
    return payload


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/cases":
            self.send_json(build_case_index_payload())
            return
        if parsed.path == "/api/case":
            case_id = parse_qs(parsed.query).get("id", [""])[0]
            payload = build_case_detail_payload(case_id)
            if payload is None:
                self.send_json({"error": f"Case not found: {case_id}"}, status_code=404)
                return
            self.send_json(payload)
            return
        if parsed.path == "/health":
            self.send_json({"status": "ok"})
            return
        super().do_GET()

    def send_json(self, payload, status_code: int = 200) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    host = "127.0.0.1"
    port = 8770
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"dashboard_url=http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
