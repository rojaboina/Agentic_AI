const state = {
  caseIndex: [],
  selectedId: null,
  selectedCase: null,
};

const decisionClass = {
  "Urgent Review": "urgent",
  "Needs Follow-Up": "follow",
  Routine: "routine",
  "Insufficient Data": "follow",
};

function badge(label, className) {
  return `<span class="badge ${className || ""}">${label}</span>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderSummary() {
  document.getElementById("summary").innerHTML = `
    <div class="metric"><strong>${state.caseIndex.length}</strong><span>Total Cases</span></div>
    <div class="metric"><strong>1</strong><span>Case At A Time</span></div>
    <div class="metric"><strong>LLM</strong><span>On Demand</span></div>
    <div class="metric"><strong>8770</strong><span>Local Port</span></div>
  `;
}

function renderList() {
  const list = document.getElementById("caseList");
  document.getElementById("caseCount").textContent = `${state.caseIndex.length} available`;
  list.innerHTML = state.caseIndex
    .map((item) => {
      const active = item.case_id === state.selectedId ? "active" : "";
      return `
        <button class="case-item ${active}" data-case-id="${item.case_id}">
          <div class="case-row">
            <span class="case-title">${escapeHtml(item.case_id)}</span>
            ${badge("Load", "low")}
          </div>
          <div class="case-subtitle">${escapeHtml(item.chief_concern)}</div>
          <div class="case-subtitle">${escapeHtml(item.requested_service || "No service request")}</div>
        </button>
      `;
    })
    .join("");
}

function listItems(items, fallback) {
  if (!items || items.length === 0) {
    return `<li>${escapeHtml(fallback)}</li>`;
  }
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderFlags(flags) {
  if (!flags || flags.length === 0) {
    return "<li>No guideline flags.</li>";
  }
  return flags
    .map((flag) => `<li><strong>${escapeHtml(flag.code)}</strong> ${badge(flag.severity, flag.severity)}<br>${escapeHtml(flag.message)}<br><span class="muted">${escapeHtml(flag.evidence || "")}</span></li>`)
    .join("");
}

function renderMedicationFindings(findings) {
  if (!findings || findings.length === 0) {
    return "<li>No medication safety findings.</li>";
  }
  return findings
    .map((finding) => `<li><strong>${escapeHtml(finding.issue)}</strong> ${badge(finding.severity, finding.severity)}<br>${escapeHtml(finding.rationale)}<br><span class="muted">${escapeHtml(finding.medication || "")}</span></li>`)
    .join("");
}

function renderMemoryEntries(entries, fallback) {
  if (!entries || entries.length === 0) {
    return `<li>${escapeHtml(fallback)}</li>`;
  }
  return entries
    .map((entry) => {
      const score = entry.score === null || entry.score === undefined ? "" : ` · score ${entry.score}`;
      return `<li>${badge(entry.source || "memory", "low")}<span class="muted">${escapeHtml(score)}</span><br>${escapeHtml(entry.memory)}</li>`;
    })
    .join("");
}

function agentSection(title, review) {
  return `
    <div class="section">
      <h3>${escapeHtml(title)} ${badge(review.severity, review.severity)} ${badge(review.source || "deterministic", "low")}</h3>
      <p>${escapeHtml(review.summary)}</p>
      <ul>${listItems(review.key_findings, "No findings.")}</ul>
    </div>
  `;
}

function setLoading(caseId) {
  document.getElementById("caseDetail").innerHTML = `
    <div class="empty-state">
      Running LangGraph review for ${escapeHtml(caseId)}...
    </div>
  `;
}

function renderError(message) {
  document.getElementById("caseDetail").innerHTML = `
    <div class="empty-state">${escapeHtml(message)}</div>
  `;
}

function renderDetail(item) {
  const detail = document.getElementById("caseDetail");
  const decision = item.panel_decision.decision;
  const route = item.human_review;
  const risk = item.risk_scores;
  const specialists = item.specialists;
  const memoryContext = item.memory_context || { provider: "none", entries: [] };
  const memoryWrite = item.memory_write || { provider: "none", entries: [] };
  detail.innerHTML = `
    <div class="detail-header">
      <div>
        <h2 class="detail-title">${escapeHtml(item.case_id)} · ${escapeHtml(item.chief_concern)}</h2>
        <p class="muted">${escapeHtml(item.age)} years · ${escapeHtml(item.sex)} · ${escapeHtml(item.requested_service || "No service request")}</p>
        <p>${escapeHtml(item.clinical_note)}</p>
      </div>
      <div class="decision-stack">
        ${badge(decision, decisionClass[decision])}
        ${badge(`Urgency: ${route.urgency}`, route.urgency)}
        ${route.human_review.required ? badge(`Reviewer: ${route.human_review.reviewer_role}`, "follow") : badge("No human review", "routine")}
      </div>
    </div>

    <div class="score-grid">
      <div class="score"><strong>${risk.overall_risk}</strong><span>Overall Risk</span></div>
      <div class="score"><strong>${risk.readmission_risk}</strong><span>Readmission</span></div>
      <div class="score"><strong>${risk.medication_safety_risk}</strong><span>Medication Safety</span></div>
      <div class="score"><strong>${risk.care_gap_risk}</strong><span>Care Gap</span></div>
    </div>

    <div class="section">
      <h3>Panel Decision ${badge(item.panel_decision.source || "deterministic", "low")}</h3>
      <p>${escapeHtml(item.panel_decision.rationale)}</p>
      <ul>${listItems(item.panel_decision.recommended_actions, "No recommended actions.")}</ul>
    </div>

    <div class="section">
      <h3>Human Review Route ${badge(route.source || "deterministic", "low")}</h3>
      <p>${escapeHtml(route.human_review.notes || "No human review route required.")}</p>
      <ul>${listItems(route.triggering_agents, "No triggering agents.")}</ul>
    </div>

    <div class="memory-grid">
      <div class="section">
        <h3>Retrieved Memory ${badge(memoryContext.provider || "none", "low")}</h3>
        <ul>${renderMemoryEntries(memoryContext.entries, "No prior memory matched this case.")}</ul>
      </div>
      <div class="section">
        <h3>Written Memory ${badge(memoryWrite.provider || "none", "low")}</h3>
        <ul>${renderMemoryEntries(memoryWrite.entries, "No memory was written.")}</ul>
      </div>
    </div>

    <div class="agent-grid">
      <div class="section">
        <h3>Clinical Risk ${badge(specialists.clinical_risk.severity, specialists.clinical_risk.severity)} ${badge(specialists.clinical_risk.source || "deterministic", "low")}</h3>
        <p>${escapeHtml(specialists.clinical_risk.summary)}</p>
        <ul>${listItems(specialists.clinical_risk.red_flags, "No clinical red flags.")}</ul>
      </div>
      ${agentSection("Medication Safety", specialists.medication_safety)}
      ${agentSection("Care Management", specialists.care_management)}
      ${agentSection("Service Review", specialists.service_review)}
    </div>

    <div class="section">
      <h3>Guideline Flags</h3>
      <ul>${renderFlags(item.guidelines.flags)}</ul>
    </div>

    <div class="section">
      <h3>Medication Findings</h3>
      <ul>${renderMedicationFindings(item.medication_safety.findings)}</ul>
    </div>

    <div class="section">
      <h3>Extracted Signals</h3>
      <ul>
        <li><strong>Diagnoses:</strong> ${escapeHtml(item.diagnoses.join(", ") || "None")}</li>
        <li><strong>Medications:</strong> ${escapeHtml(item.medications.join(", ") || "None")}</li>
        <li><strong>Abnormal labs:</strong> ${escapeHtml(JSON.stringify(item.extraction.abnormal_labs))}</li>
        <li><strong>Vital flags:</strong> ${escapeHtml(item.extraction.vital_sign_flags.join(", ") || "None")}</li>
        <li><strong>Note signals:</strong> ${escapeHtml(item.extraction.note_signals.join(", ") || "None")}</li>
      </ul>
    </div>
  `;
}

async function loadCase(caseId) {
  const normalizedCaseId = caseId.trim().toUpperCase();
  if (!normalizedCaseId) {
    renderError("Enter a case ID such as HC-007.");
    return;
  }

  state.selectedId = normalizedCaseId;
  renderList();
  setLoading(normalizedCaseId);

  const response = await fetch(`/api/case?id=${encodeURIComponent(normalizedCaseId)}`);
  const payload = await response.json();
  if (!response.ok) {
    renderError(payload.error || `Could not load ${normalizedCaseId}.`);
    return;
  }

  state.selectedCase = payload;
  document.getElementById("caseIdInput").value = payload.case_id;
  renderDetail(payload);
}

async function init() {
  const response = await fetch("/api/cases");
  state.caseIndex = await response.json();
  renderSummary();
  renderList();
  document.getElementById("caseDetail").innerHTML = `
    <div class="empty-state">Enter a case ID or select a case to run the review.</div>
  `;

  document.getElementById("loadCaseButton").addEventListener("click", () => {
    loadCase(document.getElementById("caseIdInput").value).catch((error) => renderError(error.message));
  });
  document.getElementById("caseIdInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      loadCase(event.target.value).catch((error) => renderError(error.message));
    }
  });
  document.getElementById("caseList").addEventListener("click", (event) => {
    const button = event.target.closest(".case-item");
    if (!button) return;
    loadCase(button.dataset.caseId).catch((error) => renderError(error.message));
  });
}

init().catch((error) => {
  renderError(`Failed to load dashboard: ${error.message}`);
});
