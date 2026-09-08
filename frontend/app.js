const form = document.querySelector("#audit-form");
const urlInput = document.querySelector("#website-url");
const submitButton = document.querySelector("#submit-button");
const resultPanel = document.querySelector("#result-panel");
const responseOutput = document.querySelector("#response-output");
const statusMessage = document.querySelector("#status-message");
const copyButton = document.querySelector("#copy-button");
const reportContent = document.querySelector("#report-content");
const resultUrl = document.querySelector("#result-url");
const checkGrid = document.querySelector("#check-grid");
const apiBaseUrl = document
  .querySelector('meta[name="geo-audit-api-url"]')
  .content.replace(/\/$/, "");

let displayedResponse = "";

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.classList.toggle("loading", isLoading);
  submitButton.setAttribute("aria-busy", String(isLoading));
}

function escapeHtml(value) {
  const element = document.createElement("span");
  element.textContent = String(value);
  return element.innerHTML;
}

function renderCard({ icon, title, state, label, summary, detail, items = [] }) {
  const itemList = items.length
    ? `<ul class="agent-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
    : "";
  return `<article class="check-card">
    <div class="check-card-top">
      <div class="check-card-title"><span class="check-icon" aria-hidden="true">${icon}</span><h3>${escapeHtml(title)}</h3></div>
      <span class="badge ${state}">${escapeHtml(label)}</span>
    </div>
    <p class="check-summary">${escapeHtml(summary)}</p>
    <p class="check-detail">${escapeHtml(detail)}</p>${itemList}
  </article>`;
}

function renderReport(data) {
  const robotsPass = data.robots.passed;
  const llmsPass = data.llms.passed;
  const jsKnown = data.javascript.rendering_available !== false && data.javascript.js_reliant !== null;
  const jsPass = jsKnown && !data.javascript.js_reliant;
  const schemaPass = data.schema.script_count > 0 && data.schema.invalid_script_count === 0;
  const results = [robotsPass, llmsPass, jsKnown ? jsPass : null, schemaPass];
  const evaluated = results.filter((value) => value !== null);
  const passed = evaluated.filter(Boolean).length;
  const attention = evaluated.length - passed;
  const score = evaluated.length ? Math.round((passed / evaluated.length) * 100) : 0;

  document.querySelector("#score-value").textContent = score;
  const scoreRing = document.querySelector("#score-ring");
  scoreRing.style.setProperty("--score", `${score}%`);
  scoreRing.setAttribute("aria-label", `${score} out of 100`);
  document.querySelector("#passed-count").textContent = passed;
  document.querySelector("#attention-count").textContent = attention;

  const scoreTitle = score >= 75 ? "AI-ready foundation" : score >= 50 ? "A solid start" : "There’s room to improve";
  const scoreDescription = score >= 75
    ? "Your site gives AI systems strong signals. Review the details below to fine-tune visibility."
    : "Address the highlighted checks to make your content easier for AI systems to find and understand.";
  document.querySelector("#score-title").textContent = scoreTitle;
  document.querySelector("#score-description").textContent = scoreDescription;

  const allowedAgents = data.robots.agents.filter((agent) => agent.status === "allowed").map((agent) => agent.agent);
  const detectedTypes = data.schema.types.length ? data.schema.types : ["No schema types found"];
  const cards = [
    {
      icon: "◎", title: "AI crawler access", state: robotsPass ? "pass" : "fail", label: robotsPass ? "Passed" : "Blocked",
      summary: robotsPass ? "AI crawlers can access your site" : "One or more AI crawlers are restricted",
      detail: data.robots.found ? "Based on the rules published in your robots.txt file." : "No robots.txt was found, so crawlers are allowed by default.",
      items: allowedAgents,
    },
    {
      icon: "≡", title: "LLM guidance", state: llmsPass ? "pass" : "warn", label: llmsPass ? "Passed" : "Improve",
      summary: llmsPass ? "Valid LLM guidance is available" : "Add an llms.txt file",
      detail: llmsPass ? "At least one guidance file contains a clear Markdown heading." : "A valid llms.txt helps AI systems understand your most important content.",
    },
    {
      icon: "⌁", title: "JavaScript reliance", state: !jsKnown ? "warn" : jsPass ? "pass" : "fail", label: !jsKnown ? "Not tested" : jsPass ? "Passed" : "High reliance",
      summary: !jsKnown ? "Rendering was unavailable" : jsPass ? "Key content is available without JavaScript" : "Important content may require JavaScript",
      detail: !jsKnown ? "This check could not run in the current environment." : `${data.javascript.raw_word_count} words in source HTML · ${data.javascript.rendered_word_count} after rendering.`,
    },
    {
      icon: "◇", title: "Structured data", state: schemaPass ? "pass" : "warn", label: schemaPass ? "Passed" : "Improve",
      summary: schemaPass ? `${data.schema.script_count} valid schema block${data.schema.script_count === 1 ? "" : "s"} found` : "Add or fix Schema.org markup",
      detail: schemaPass ? "Structured data helps machines identify the entities on your page." : data.schema.invalid_script_count ? `${data.schema.invalid_script_count} invalid JSON-LD block(s) need attention.` : "No JSON-LD structured data was detected.",
      items: detectedTypes,
    },
  ];
  checkGrid.innerHTML = cards.map(renderCard).join("");
}

function showResponse(data, isError = false) {
  displayedResponse = JSON.stringify(data, null, 2);
  responseOutput.textContent = displayedResponse;
  resultPanel.hidden = false;
  copyButton.hidden = isError;
  reportContent.hidden = isError;
  resultUrl.textContent = isError ? "" : (data.final_url || data.requested_url);
  statusMessage.className = `status-message ${isError ? "error" : "success"}`;
  statusMessage.textContent = isError
    ? (data.detail || "The audit could not be completed. Please check the URL and try again.")
    : "Audit complete — here’s how your site performed.";
  if (!isError) renderReport(data);
  resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;

  setLoading(true);
  statusMessage.className = "status-message";

  try {
    const response = await fetch(`${apiBaseUrl}/api/audit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: urlInput.value.trim() }),
    });

    let data;
    try {
      data = await response.json();
    } catch {
      data = { detail: `The server returned an unreadable response (${response.status}).` };
    }

    showResponse(data, !response.ok);
  } catch {
    showResponse(
      { detail: `Could not connect to the API at ${apiBaseUrl}. Make sure the backend is running.` },
      true,
    );
  } finally {
    setLoading(false);
  }
});

copyButton.addEventListener("click", async () => {
  if (!displayedResponse) return;

  try {
    await navigator.clipboard.writeText(displayedResponse);
    copyButton.textContent = "Copied";
    window.setTimeout(() => { copyButton.textContent = "Copy JSON"; }, 1600);
  } catch {
    copyButton.textContent = "Copy failed";
  }
});
