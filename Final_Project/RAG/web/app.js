const cardsEl = document.querySelector("#cards");
const cardCountEl = document.querySelector("#cardCount");
const modeTextEl = document.querySelector("#modeText");
const refreshBtn = document.querySelector("#refreshBtn");
const moduleFilter = document.querySelector("#moduleFilter");
const messagesEl = document.querySelector("#messages");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const feedbackHistoryEl = document.querySelector("#feedbackHistory");

async function loadCards() {
  const params = new URLSearchParams();
  if (moduleFilter.value) params.set("module", moduleFilter.value);
  const response = await fetch(`/api/recommendations?${params.toString()}`);
  const data = await response.json();
  renderCards(data.cards || []);
  cardCountEl.textContent = String((data.cards || []).length);
  modeTextEl.textContent =
    data.mode === "recommendations"
      ? "Saved recommendations from your weekly pipeline."
      : "Taste signals from your current reading memory. Candidate recommendations come next.";
}

function renderCards(cards) {
  cardsEl.innerHTML = "";
  cards.forEach((card) => {
    const node = document.createElement("article");
    node.className = "book-card";
    node.innerHTML = `
      <div class="module">${label(card.module)}</div>
      <h3 class="book-title">${escapeHtml(card.title || "Untitled")}</h3>
      <p class="author">${escapeHtml(card.author || "Unknown author")}</p>
      <p class="summary">${escapeHtml(card.summary || "No summary yet.")}</p>
      <div class="meta">
        <span class="pill">${escapeHtml(card.status || "recommended")}</span>
        <span class="pill">${card.goodreads_rating ? `Goodreads ${escapeHtml(String(card.goodreads_rating))}` : "Rating pending"}</span>
        <span class="pill">${escapeHtml(card.date_added || "Not added yet")}</span>
      </div>
      <p class="why">${escapeHtml(card.why_recommended || "Recommendation reasoning pending.")}</p>
      ${card.source_url ? `<a class="source" href="${escapeHtml(card.source_url)}" target="_blank" rel="noreferrer">Open source</a>` : ""}
      <div class="actions">
        <button class="yes" data-decision="added_to_list">Yes</button>
        <button class="maybe" data-decision="maybe_later">Maybe</button>
        <button class="no" data-decision="rejected">No</button>
      </div>
    `;
    node.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => sendFeedback(card.title, button.dataset.decision, node));
    });
    cardsEl.appendChild(node);
  });
}

async function sendFeedback(title, decision, cardNode) {
  const response = await fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, decision }),
  });
  const result = await response.json();
  if (result.ok) {
    cardNode.querySelector(".actions").innerHTML = `<span class="pill">Saved: ${label(decision)}</span>`;
    loadFeedbackHistory();
  }
}

async function loadFeedbackHistory() {
  const response = await fetch("/api/feedback");
  const data = await response.json();
  const rows = data.feedback || [];
  feedbackHistoryEl.innerHTML = rows.length
    ? rows.map((row) => `<div class="feedback-row"><b>${escapeHtml(row.title)}</b><span>${label(row.decision)}</span></div>`).join("")
    : `<p class="empty">No feedback yet.</p>`;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  addMessage(message, "user");
  chatInput.value = "";
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await response.json();
  addMessage(data.reply, "assistant");
});

function addMessage(text, role) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.textContent = text;
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function label(value) {
  return String(value || "").replaceAll("_", " ");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

refreshBtn.addEventListener("click", loadCards);
moduleFilter.addEventListener("change", loadCards);
loadCards();
loadFeedbackHistory();
