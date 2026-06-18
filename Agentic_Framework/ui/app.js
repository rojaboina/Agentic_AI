const state = {
  cases: [],
  filtered: [],
  selectedId: null,
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

function renderList() {
  const list = document.getElementById("caseList");
  document.getElementById("caseCount").textContent = `${state.filtered.length} shown`;
  list.innerHTML = state.filtered
    .map((item) => {
      const decision = item.panel_decision.decision;
      const active = item.case_id === state.selectedId ? "active" : "";
      return `
        <button class="case-item ${active}" data-case-id="${item.case_id}">
          <div class="case-row">
            <span class="case-title">${escapeHtml(item.case_id)}</span>
            ${badge(decision, decisionClass[decision])}
          </div>
          <div class="case-subtitle">${escapeHtml(item.chief_concern)}</div>
          <div class="case-subtitle">${escapeHtml(item.requested_service || "No service request")}</div>
        </button>
      `;
    })
    .join("");
}

function renderSummary() {
  const total = state.cases.length;
  const urgent = state.cases.filter((item) => item.panel_decision.decision === "Urgent Review").length;
  const follow = state.cases.filter((item) => item.panel_decision.decision === "Needs Follow-Up").length;
  const human = state.cases.filter((item) => item.human_review.human_review.required).length;
  document.getElementById("summary").innerHTML = `
    <div class="metric"><strong>${total}</strong><span>Total Cases</span></div>
    <div class="metric"><strong>${urgent}</strong><span>Urgent Review</span></div>
    <div class="metric"><strong>${follow}</strong><span>Needs Follow-Up</span></div>
    <div class="metric"><strong>${human}</strong><span>Human Review</span></div>
  `;
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

function agentSection(title, review) {
  return `
    <div class="section">
      <h3>${escapeHtml(title)} ${badge(review.severity, review.severity)} ${badge(review.source || "deterministic", "low")}</h3>
      <p>${escapeHtml(review.summary)}</p>
      <ul>${listItems(review.key_findings, "No findings.")}</ul>
    </div>
  `;
}

function renderDetail(item) {
  const detail = document.getElementById("caseDetail");
  const decision = item.panel_decision.decision;
  const route = item.human_review;
  const risk = item.risk_scores;
  const specialists = item.specialists;
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

function applyFilters() {
  const search = document.getElementById("searchInput").value.trim().toLowerCase();
  const decision = document.getElementById("decisionFilter").value;
  const review = document.getElementById("reviewFilter").value;

  state.filtered = state.cases.filter((item) => {
    const haystack = [
      item.case_id,
      item.chief_concern,
      item.requested_service,
      item.diagnoses.join(" "),
      item.medications.join(" "),
    ].join(" ").toLowerCase();
    const matchesSearch = !search || haystack.includes(search);
    const matchesDecision = decision === "all" || item.panel_decision.decision === decision;
    const requiresReview = item.human_review.human_review.required;
    const matchesReview =
      review === "all" ||
      (review === "required" && requiresReview) ||
      (review === "not_required" && !requiresReview);
    return matchesSearch && matchesDecision && matchesReview;
  });

  if (!state.filtered.some((item) => item.case_id === state.selectedId)) {
    state.selectedId = state.filtered[0]?.case_id || null;
  }

  renderList();
  const selected = state.cases.find((item) => item.case_id === state.selectedId);
  if (selected) {
    renderDetail(selected);
  } else {
    document.getElementById("caseDetail").innerHTML = '<div class="empty-state">No matching cases.</div>';
  }
}

async function init() {
  const response = await fetch("/api/cases");
  state.cases = await response.json();
  state.filtered = state.cases;
  state.selectedId = state.cases[0]?.case_id || null;
  renderSummary();
  applyFilters();

  document.getElementById("searchInput").addEventListener("input", applyFilters);
  document.getElementById("decisionFilter").addEventListener("change", applyFilters);
  document.getElementById("reviewFilter").addEventListener("change", applyFilters);
  document.getElementById("caseList").addEventListener("click", (event) => {
    const button = event.target.closest(".case-item");
    if (!button) return;
    state.selectedId = button.dataset.caseId;
    renderList();
    renderDetail(state.cases.find((item) => item.case_id === state.selectedId));
  });
}

init().catch((error) => {
  document.getElementById("caseDetail").innerHTML = `<div class="empty-state">Failed to load dashboard: ${escapeHtml(error.message)}</div>`;
});
