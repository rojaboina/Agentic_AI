from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.langgraph_pipeline import review_all_cases_with_graph


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = PROJECT_ROOT / "ui"


def model_to_dict(model) -> dict:
    return model.model_dump()


def build_case_payload() -> list[dict]:
    cases: list[dict] = []
    for state in review_all_cases_with_graph().values():
        extraction = state["extraction"]
        guideline_result = state["guideline_result"]
        medication_safety_result = state["medication_safety_result"]
        risk_scores = state["risk_scores"]
        specialist_bundle = state["specialist_bundle"]
        human_route = state["human_route"]
        panel_decision = state["panel_decision"]
        patient_case = extraction.patient_case

        cases.append(
            {
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
                "specialists": model_to_dict(specialist_bundle),
                "human_review": model_to_dict(human_route),
                "panel_decision": model_to_dict(panel_decision),
            }
        )
    return cases


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/cases":
            self.send_json(build_case_payload())
            return
        if parsed.path == "/health":
            self.send_json({"status": "ok"})
            return
        super().do_GET()

    def send_json(self, payload) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
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
