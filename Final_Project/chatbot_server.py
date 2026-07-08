from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rag_pipeline.config import Settings
from rag_pipeline.chunker import chunk_pages
from rag_pipeline.embeddings import EmbeddingModel
from rag_pipeline.pdf_loader import extract_pdf_pages, parse_patient_folder
from rag_pipeline.query_planner import QueryPlan, plan_query
from rag_pipeline.vector_store import PineconeStore


NAMESPACE = "patient-documents"
HOST = "127.0.0.1"
PORT = 8080

settings = Settings.from_env()
embedder: EmbeddingModel | None = None
store: PineconeStore | None = None


def get_embedder() -> EmbeddingModel:
    global embedder
    if embedder is None:
        embedder = EmbeddingModel(settings.embedding_model_name)
    return embedder


def get_store() -> PineconeStore:
    global store
    if store is None:
        store = PineconeStore(
            index_name=settings.pinecone_index_name,
            dimension=settings.embedding_dimension,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
        )
    return store


def list_patients() -> list[dict[str, str]]:
    patients = []
    for folder in sorted(settings.data_dir.glob("P*")):
        if folder.is_dir():
            patient_id, patient_name = parse_patient_folder(folder)
            patients.append({"id": patient_id, "name": patient_name})
    return patients


def retrieve(patient_id: str, question: str, top_k: int = 6, plan: QueryPlan | None = None) -> list[dict]:
    query_vector = get_embedder().encode([question])[0]
    response = get_store().query(
        query_vector,
        patient_id=patient_id,
        top_k=top_k,
        namespace=NAMESPACE,
        year=plan.year if plan else None,
        panel=plan.panel if plan else None,
        metric=plan.metric if plan else None,
        document_type="lab_results" if plan and plan.year else None,
    )
    return response.get("matches", [])


def build_answer(question: str, matches: list[dict], plan: QueryPlan | None = None) -> dict:
    if not matches:
        return {
            "answer": "I could not find matching evidence in this patient's uploaded documents.",
            "sources": [],
            "plan": plan.to_dict() if plan else None,
        }

    best = matches[0]["metadata"]
    metric = best.get("metric") or "this result"
    panel = best.get("panel") or "the uploaded report"
    text = best.get("chunk_text", "")
    value = extract_value(text)
    normal_range = extract_normal_range(text)

    answer_parts = [
        f"I found the strongest evidence in {panel}"
        + (f" for {metric}." if metric else ".")
    ]
    if value:
        answer_parts.append(f"The reported value is {value}.")
    if normal_range:
        answer_parts.append(f"The document lists the normal range as {normal_range}.")
    status = compare_value_to_range(value, normal_range)
    if status:
        answer_parts.append(status)

    interpretation = extract_interpretation(text)
    if interpretation:
        answer_parts.append(interpretation)

    answer_parts.append(
        "This is document-based support, not a diagnosis. For urgent symptoms or major concerns, contact a clinician or seek urgent care."
    )

    return {
        "answer": " ".join(answer_parts),
        "sources": [format_source(match) for match in matches],
        "plan": plan.to_dict() if plan else None,
    }


def extract_requested_year(question: str) -> str:
    match = re.search(r"\b(20\d{2})\b", question)
    return match.group(1) if match else ""


def build_out_of_range_answer(patient_id: str, year: int | None = None, plan: QueryPlan | None = None) -> dict:
    chunks = load_patient_chunks(patient_id)
    findings = []
    sources = []
    seen_metrics = set()

    for chunk in chunks:
        if year and chunk.year != year:
            continue
        if not chunk.metric or chunk.metric in seen_metrics:
            continue
        value = extract_value(chunk.text)
        normal_range = extract_normal_range(chunk.text)
        status = range_status(value, normal_range)
        if not status:
            continue
        seen_metrics.add(chunk.metric)
        findings.append(
            {
                "metric": chunk.metric,
                "panel": chunk.panel or "Uploaded report",
                "value": value,
                "normal_range": normal_range,
                "status": status,
            }
        )
        sources.append(
            {
                "score": 1.0,
                "patient_id": chunk.patient_id,
                "panel": chunk.panel,
                "metric": chunk.metric,
                "file_name": chunk.file_name,
                "page_number": chunk.page_number,
                "text": chunk.text[:1200],
            }
        )

    year_context = f" for {year}" if year else ""

    if not findings:
        return {
            "answer": f"I scanned this patient's uploaded lab chunks{year_context} and did not find values outside the listed reference ranges.",
            "sources": [],
            "plan": plan.to_dict() if plan else None,
        }

    lines = [f"I scanned this patient's chart{year_context} and found these values outside the listed reference ranges:"]
    for item in findings:
        direction = "low" if item["status"] == "below" else "high"
        lines.append(
            f"- {item['metric']}: {item['value']} ({direction}; normal range {item['normal_range']})"
        )
    lines.append(
        "This is document-based support, not a diagnosis. A clinician should interpret abnormal results with symptoms, history, and repeat testing when needed."
    )
    return {"answer": "\n".join(lines), "sources": sources, "plan": plan.to_dict() if plan else None}


def load_patient_chunks(patient_id: str):
    pages = []
    for folder in sorted(settings.data_dir.glob(f"{patient_id}_*")):
        for pdf_path in sorted(folder.glob("*.pdf")):
            pages.extend(extract_pdf_pages(pdf_path))
    return chunk_pages(
        pages,
        max_chars=settings.chunk_max_chars,
        overlap_chars=settings.chunk_overlap_chars,
    )


def extract_value(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        if line == "Value" and idx + 1 < len(lines):
            return lines[idx + 1]
    unit_pattern = r"^\d+(?:\.\d+)?\s*(mg/dL|mmol/L|ng/mL|ng/dL|pg/mL|%|uIU/mL|U/L|g/dL|mcg/dL)$"
    for line in lines:
        if line.lower().startswith("normal range"):
            continue
        if re.search(unit_pattern, line):
            return line
    return ""


def extract_normal_range(text: str) -> str:
    match = re.search(r"Normal range:\s*([^\n]+)", text)
    return match.group(1).strip() if match else ""


def compare_value_to_range(value: str, normal_range: str) -> str:
    if not value or not normal_range:
        return ""

    value_match = re.search(r"(\d+(?:\.\d+)?)", value)
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", normal_range)
    if not value_match or not range_match:
        return ""

    measured = float(value_match.group(1))
    low = float(range_match.group(1))
    high = float(range_match.group(2))

    if measured < low:
        return "This is below the listed reference range."
    if measured > high:
        return "This is above the listed reference range."
    return "This is within the listed reference range."


def range_status(value: str, normal_range: str) -> str:
    if not value or not normal_range:
        return ""

    value_match = re.search(r"(\d+(?:\.\d+)?)", value)
    if not value_match:
        return ""
    measured = float(value_match.group(1))

    range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", normal_range)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        if measured < low:
            return "below"
        if measured > high:
            return "above"
        return ""

    below_match = re.search(r"(?:below|<)\s*(\d+(?:\.\d+)?)", normal_range, re.IGNORECASE)
    if below_match and measured >= float(below_match.group(1)):
        return "above"

    greater_match = re.search(r"(?:>=|>|above)\s*(\d+(?:\.\d+)?)", normal_range, re.IGNORECASE)
    if greater_match and measured <= float(greater_match.group(1)):
        return "below"

    return ""


def extract_interpretation(text: str) -> str:
    interesting_lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        if any(
            token in cleaned.lower()
            for token in ["high", "low", "desirable", "prediabetes", "diabetes", "risk", "recommended"]
        ):
            interesting_lines.append(cleaned)
        if len(" ".join(interesting_lines)) > 450:
            break
    if not interesting_lines:
        return ""
    return "Relevant note from the report: " + " ".join(interesting_lines[:4])


def format_source(match: dict) -> dict:
    metadata = match["metadata"]
    text = metadata.get("chunk_text", "")
    return {
        "score": round(float(match.get("score", 0)), 4),
        "patient_id": metadata.get("patient_id", ""),
        "panel": metadata.get("panel", ""),
        "metric": metadata.get("metric", ""),
        "file_name": metadata.get("file_name", ""),
        "page_number": metadata.get("page_number", ""),
        "text": text[:1200],
    }


class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.respond_html(INDEX_HTML)
            return
        if parsed.path == "/api/patients":
            self.respond_json({"patients": list_patients()})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/chat":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or "{}")
        patient_id = str(payload.get("patient_id", "")).strip()
        question = str(payload.get("question", "")).strip()

        if not patient_id or not question:
            self.respond_json({"error": "patient_id and question are required"}, status=400)
            return

        try:
            plan = plan_query(question, patient_id)
            if plan.intent == "find_abnormal_labs":
                self.respond_json(build_out_of_range_answer(patient_id, plan.year, plan))
                return
            query_text = plan.rewritten_query or question
            matches = retrieve(patient_id, query_text, plan=plan)
            self.respond_json(build_answer(question, matches, plan))
        except Exception as exc:
            self.respond_json({"error": str(exc)}, status=500)

    def respond_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Patient Document Chat</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #172033;
      --muted: #667085;
      --line: #d7dde8;
      --panel: #f7f9fc;
      --blue: #1166cc;
      --green: #0f9f55;
      --gold: #d99a00;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #eef2f7;
      color: var(--ink);
    }
    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 290px 1fr;
    }
    aside {
      background: #ffffff;
      border-right: 1px solid var(--line);
      padding: 22px;
    }
    main {
      padding: 24px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: 18px;
      max-height: 100vh;
    }
    h1 {
      margin: 0 0 18px;
      font-size: 20px;
      letter-spacing: 0;
    }
    label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      margin-bottom: 8px;
      text-transform: uppercase;
    }
    select, textarea, button {
      width: 100%;
      font: inherit;
      border-radius: 8px;
      border: 1px solid var(--line);
    }
    select {
      padding: 10px 11px;
      background: white;
    }
    .hint {
      margin-top: 16px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .header {
      background: white;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px 20px;
    }
    .header h2 {
      margin: 0 0 6px;
      font-size: 21px;
    }
    .header p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }
    #messages {
      overflow: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding-right: 4px;
    }
    .message {
      background: white;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      line-height: 1.5;
    }
    .message.user {
      border-color: #bfd7ff;
      background: #f7fbff;
    }
    .role {
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }
    details {
      margin-top: 12px;
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }
    summary {
      cursor: pointer;
      color: var(--blue);
      font-weight: 700;
    }
    .source {
      margin-top: 10px;
      padding: 11px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
    }
    .plan {
      margin-top: 12px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 8px;
    }
    .plan-item {
      background: #eef6fc;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px;
      font-size: 12px;
    }
    .plan-label {
      color: var(--muted);
      font-weight: 800;
      text-transform: uppercase;
      margin-bottom: 3px;
    }
    .source-meta {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 7px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      line-height: 1.45;
    }
    form {
      display: grid;
      grid-template-columns: 1fr 120px;
      gap: 12px;
      background: white;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    textarea {
      min-height: 56px;
      max-height: 140px;
      resize: vertical;
      padding: 12px;
    }
    button {
      background: var(--green);
      color: white;
      border: 0;
      font-weight: 800;
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.55;
      cursor: wait;
    }
    .examples {
      display: grid;
      gap: 8px;
      margin-top: 18px;
    }
    .example {
      border: 1px solid var(--line);
      background: white;
      color: var(--blue);
      padding: 9px;
      border-radius: 8px;
      text-align: left;
      cursor: pointer;
      font-size: 13px;
    }
    @media (max-width: 800px) {
      .shell { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      main { max-height: none; }
      form { grid-template-columns: 1fr; }
      button { min-height: 44px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <h1>Patient Document Chat</h1>
      <label for="patient">Patient</label>
      <select id="patient"></select>
      <p class="hint">Answers are retrieved from the uploaded PDFs in Pinecone and include source evidence. This is not a diagnostic tool.</p>
      <div class="examples">
        <button class="example" type="button">Why is my LDL high?</button>
        <button class="example" type="button">What does my A1C mean?</button>
        <button class="example" type="button">Is my vitamin D low?</button>
        <button class="example" type="button">What thyroid results are abnormal?</button>
      </div>
    </aside>
    <main>
      <section class="header">
        <h2>Ask questions about the patient PDFs</h2>
        <p>Retrieval uses patient_id filtering, S-PubMedBert embeddings, and Pinecone cosine search.</p>
      </section>
      <section id="messages"></section>
      <form id="chat-form">
        <textarea id="question" placeholder="Ask about LDL, glucose, A1C, thyroid, vitamin D, B12, iron..."></textarea>
        <button id="send" type="submit">Ask</button>
      </form>
    </main>
  </div>
  <script>
    const patientSelect = document.getElementById("patient");
    const messages = document.getElementById("messages");
    const form = document.getElementById("chat-form");
    const question = document.getElementById("question");
    const send = document.getElementById("send");

    async function loadPatients() {
      const res = await fetch("/api/patients");
      const data = await res.json();
      patientSelect.innerHTML = data.patients
        .map(p => `<option value="${p.id}">${p.id} - ${p.name}</option>`)
        .join("");
    }

    function addMessage(role, text, sources = [], plan = null) {
      const node = document.createElement("article");
      node.className = `message ${role === "You" ? "user" : "assistant"}`;
      const planHtml = plan ? `
        <div class="plan">
          <div class="plan-item"><div class="plan-label">Intent</div>${escapeHtml(plan.intent || "")}</div>
          <div class="plan-item"><div class="plan-label">Year</div>${escapeHtml(plan.year || "Any")}</div>
          <div class="plan-item"><div class="plan-label">Metric</div>${escapeHtml(plan.metric || "Any")}</div>
          <div class="plan-item"><div class="plan-label">Planner</div>${escapeHtml(plan.planner || "")}</div>
        </div>` : "";
      const sourceHtml = sources.length ? `
        <details open>
          <summary>Source evidence (${sources.length})</summary>
          ${sources.map(s => `
            <div class="source">
              <div class="source-meta">
                score ${s.score} | ${s.patient_id} | page ${s.page_number} | ${s.panel || "Document"} | ${s.metric || "section"}
              </div>
              <pre>${escapeHtml(s.text)}</pre>
            </div>
          `).join("")}
        </details>` : "";
      node.innerHTML = `<div class="role">${role}</div><div>${escapeHtml(text)}</div>${planHtml}${sourceHtml}`;
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    async function ask(text) {
      const trimmed = text.trim();
      if (!trimmed) return;
      addMessage("You", trimmed);
      question.value = "";
      send.disabled = true;
      send.textContent = "Thinking";
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ patient_id: patientSelect.value, question: trimmed })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Request failed");
        addMessage("Assistant", data.answer, data.sources || [], data.plan || null);
      } catch (error) {
        addMessage("Assistant", `Error: ${error.message}`);
      } finally {
        send.disabled = false;
        send.textContent = "Ask";
      }
    }

    form.addEventListener("submit", event => {
      event.preventDefault();
      ask(question.value);
    });

    document.querySelectorAll(".example").forEach(button => {
      button.addEventListener("click", () => ask(button.textContent));
    });

    loadPatients();
  </script>
</body>
</html>
"""


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print(f"Chatbot running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
