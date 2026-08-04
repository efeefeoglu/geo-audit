const form = document.querySelector("#audit-form");
const urlInput = document.querySelector("#website-url");
const submitButton = document.querySelector("#submit-button");
const resultPanel = document.querySelector("#result-panel");
const responseOutput = document.querySelector("#response-output");
const statusMessage = document.querySelector("#status-message");
const copyButton = document.querySelector("#copy-button");
const apiBaseUrl = document
  .querySelector('meta[name="geo-audit-api-url"]')
  .content.replace(/\/$/, "");

let displayedResponse = "";

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.classList.toggle("loading", isLoading);
  submitButton.setAttribute("aria-busy", String(isLoading));
}

function showResponse(data, isError = false) {
  displayedResponse = JSON.stringify(data, null, 2);
  responseOutput.textContent = displayedResponse;
  resultPanel.hidden = false;
  statusMessage.className = `status-message ${isError ? "error" : "success"}`;
  statusMessage.textContent = isError
    ? "The audit could not be completed."
    : "Audit completed successfully.";
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
