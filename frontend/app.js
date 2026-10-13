const API_BASE = window.WHATIF_API_BASE || "http://127.0.0.1:8000";
const $ = (id) => document.getElementById(id);
const form = $("decisionForm");
const decisionInput = $("decision");
const charCount = $("charCount");
const runButton = $("runButton");
const runLabel = $("runLabel");
const formError = $("formError");
const resultsSection = $("resultsSection");
const emptyState = $("emptyState");
const scenarioGrid = $("scenarioGrid");
const metricSelect = $("metricSelect");
const chart = $("trajectoryChart");
const COLORS = ["#c5f36a", "#70e1d2", "#b2a0ff", "#ffb87a", "#ff8ea1", "#87b8ff"];
let latestResponse = null;

function setApiStatus(text, ok = false) {
  $("apiState").textContent = text;
  $("apiState").style.color = ok ? "var(--lime)" : "var(--muted)";
}

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2500) });
    if (!response.ok) throw new Error("API unavailable");
    setApiStatus("ENGINE ONLINE", true);
  } catch {
    setApiStatus("ENGINE OFFLINE");
  }
}
checkHealth();

decisionInput.addEventListener("input", () => {
  charCount.textContent = `${decisionInput.value.length} / 1200`;
});
document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    decisionInput.value = button.dataset.prompt;
    decisionInput.dispatchEvent(new Event("input"));
    decisionInput.focus();
  });
});

function prettyNumber(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}
function compactNumber(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(value);
}
function titleCase(value) {
  return String(value || "Scenario").replace(/[_-]+/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}
function branchTag(text) {
  const value = String(text).toLowerCase();
  if (/continue|current|maintain|baseline|keep/.test(value)) return "BASELINE";
  if (/risk|cautious|delay|reduce|avoid|conservative/.test(value)) return "DOWNSIDE";
  if (/optimistic|aggressive|intensive|increase|growth|expand|focus/.test(value)) return "UPSIDE";
  return "ALTERNATIVE";
}
function metricLabel(key) {
  return key.replace(/[_-]+/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}
function firstValues(scenario) {
  return scenario?.timeline?.[0]?.values || {};
}
function finalValues(scenario) {
  const timeline = scenario?.timeline || [];
  return timeline.length ? timeline[timeline.length - 1].values : {};
}
function statMarkup(key, value, start) {
  const delta = typeof value === "number" && typeof start === "number" ? value - start : null;
  const deltaText = delta === null ? "No numeric baseline" : `${delta > 0 ? "+" : ""}${prettyNumber(delta)} over horizon`;
  return `<div><span class="stat-label">${escapeHtml(metricLabel(key))}</span><span class="stat-value">${escapeHtml(compactNumber(value))}</span><span class="stat-delta">${escapeHtml(deltaText)}</span></div>`;
}

function renderScenarios(data) {
  const scenarios = data.scenarios || [];
  scenarioGrid.innerHTML = "";
  scenarios.forEach((scenario, index) => {
    const start = firstValues(scenario);
    const final = finalValues(scenario);
    const metrics = Object.keys(final);
    const card = document.createElement("article");
    card.className = "scenario-card";
    const stats = metrics.slice(0, 2).map((key) => statMarkup(key, final[key], start[key])).join("");
    const timelineRows = (scenario.timeline || []).map((snapshot) => {
      const values = Object.entries(snapshot.values || {}).slice(0, 3)
        .map(([key, value]) => `${escapeHtml(metricLabel(key))}: ${escapeHtml(prettyNumber(value))}`).join(" · ");
      return `<div class="timeline-row"><span>MONTH ${String(snapshot.month).padStart(2, "0")}</span><span>${values || "No numeric values"}</span></div>`;
    }).join("");
    card.innerHTML = `
      <div class="scenario-top"><span class="scenario-index">BRANCH / 0${index + 1}</span><span class="scenario-tag">${branchTag(scenario.name || scenario.assumption)}</span></div>
      <h3>${escapeHtml(titleCase(scenario.name || scenario.assumption))}</h3>
      <p class="scenario-assumption">${escapeHtml(scenario.assumption || "Alternative path based on the decision.")}</p>
      <div class="scenario-stats">${stats || '<span class="subtle">Add numeric starting values to compare metrics.</span>'}</div>
      <button class="timeline-button" type="button" aria-expanded="false"><span>OPEN TIMELINE · ${(scenario.timeline || []).length} STEPS</span><span>＋</span></button>
      <div class="timeline-details" hidden>${timelineRows || '<p class="subtle">No timeline steps returned.</p>'}</div>`;
    const toggle = card.querySelector(".timeline-button");
    const details = card.querySelector(".timeline-details");
    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!expanded));
      details.hidden = expanded;
      toggle.lastElementChild.textContent = expanded ? "＋" : "−";
      toggle.firstElementChild.textContent = `${expanded ? "OPEN" : "CLOSE"} TIMELINE · ${(scenario.timeline || []).length} STEPS`;
    });
    scenarioGrid.appendChild(card);
  });
  $("resultCount").textContent = `${scenarios.length} BRANCHES`;
  $("resultSubtitle").textContent = `${scenarios.length} alternatives · ${$("months").value}-month horizon · simulated, not predicted`;
}

function renderAssumptions(data) {
  const list = $("assumptionsList");
  list.innerHTML = "";
  const assumptions = Array.isArray(data.assumptions) ? data.assumptions : [];
  assumptions.concat(data.disclaimer ? [data.disclaimer] : []).forEach((assumption) => {
    const item = document.createElement("li");
    item.textContent = assumption;
    list.appendChild(item);
  });
  if (!list.children.length) {
    const item = document.createElement("li");
    item.textContent = "No assumptions were returned by the API.";
    list.appendChild(item);
  }
  const source = assumptions.find((value) => String(value).toLowerCase().includes("scenario branch source"));
  $("sourceLabel").textContent = source ? source.replace(/^scenario branch source:\s*/i, "").replace(/\.$/, "").toUpperCase() : "SOURCE NOT REPORTED";
}

function renderMetricOptions(data) {
  const metricSet = new Set();
  (data.scenarios || []).forEach((scenario) => {
    (scenario.timeline || []).forEach((snapshot) => Object.keys(snapshot.values || {}).forEach((key) => metricSet.add(key)));
  });
  const previous = metricSelect.value;
  metricSelect.innerHTML = '<option value="">Choose a metric</option>';
  [...metricSet].forEach((key) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = metricLabel(key);
    metricSelect.appendChild(option);
  });
  if (metricSet.has(previous)) metricSelect.value = previous;
  else if (metricSet.size) metricSelect.value = [...metricSet][0];
  drawChart();
}

function drawChart() {
  const scenarios = latestResponse?.scenarios || [];
  const key = metricSelect.value;
  $("chartNote").textContent = key ? `Metric: ${metricLabel(key)} · relative scale` : "Select a metric to compare";
  $("chartLegend").innerHTML = "";
  if (!key || !scenarios.length) {
    chart.innerHTML = '<text x="450" y="140" fill="#778291" font-size="13" text-anchor="middle">Run a simulation to reveal the possible trajectories.</text>';
    return;
  }
  const series = scenarios.map((scenario, index) => {
    const points = [{ month: 0, value: Number(scenario.timeline?.[0]?.values?.[key] ?? NaN) }];
    (scenario.timeline || []).forEach((snapshot) => points.push({ month: snapshot.month, value: Number(snapshot.values?.[key] ?? NaN) }));
    return { name: scenario.name || scenario.assumption || `Branch ${index + 1}`, color: COLORS[index % COLORS.length], points };
  }).filter((s) => s.points.some((p) => Number.isFinite(p.value)));
  const values = series.flatMap((s) => s.points.map((p) => p.value).filter(Number.isFinite));
  if (!values.length) {
    chart.innerHTML = '<text x="450" y="140" fill="#778291" font-size="13" text-anchor="middle">This metric has no numeric values.</text>';
    return;
  }
  const min = Math.min(...values), max = Math.max(...values);
  const range = max - min || Math.max(Math.abs(max) * .1, 1);
  const low = min - range * .12, high = max + range * .12;
  const left = 62, right = 875, top = 24, bottom = 230;
  const maxMonth = Math.max(1, ...series.flatMap((s) => s.points.map((p) => p.month)));
  const x = (month) => left + (month / maxMonth) * (right - left);
  const y = (value) => bottom - ((value - low) / (high - low)) * (bottom - top);
  let svg = "";
  for (let i = 0; i < 5; i++) {
    const gy = top + i * (bottom - top) / 4;
    const val = high - i * (high - low) / 4;
    svg += `<line x1="${left}" y1="${gy}" x2="${right}" y2="${gy}" stroke="#29313b" stroke-dasharray="3 6"/><text x="${left - 10}" y="${gy + 4}" text-anchor="end" fill="#758190" font-size="10" font-family="DM Mono, monospace">${escapeHtml(compactNumber(val))}</text>`;
  }
  for (let m = 0; m <= maxMonth; m += Math.max(1, Math.ceil(maxMonth / 6))) {
    svg += `<text x="${x(m)}" y="252" text-anchor="middle" fill="#758190" font-size="10" font-family="DM Mono, monospace">${m === 0 ? "START" : "M" + m}</text>`;
  }
  series.forEach((s, i) => {
    const coords = s.points.filter((p) => Number.isFinite(p.value)).map((p) => [x(p.month), y(p.value)]);
    if (!coords.length) return;
    const path = coords.map(([px, py], idx) => `${idx ? "L" : "M"} ${px.toFixed(2)} ${py.toFixed(2)}`).join(" ");
    svg += `<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity=".95"/>`;
    coords.forEach(([px, py]) => { svg += `<circle cx="${px}" cy="${py}" r="3.3" fill="#10141a" stroke="${s.color}" stroke-width="2"/>`; });
    const legend = document.createElement("span");
    legend.className = "legend-item";
    legend.innerHTML = `<span class="legend-dot" style="background:${s.color}"></span>${escapeHtml(titleCase(s.name))}`;
    $("chartLegend").appendChild(legend);
  });
  chart.innerHTML = svg;
}

metricSelect.addEventListener("change", drawChart);

function setLoading(loading) {
  runButton.disabled = loading;
  runLabel.textContent = loading ? "Exploring branches…" : "Explore possibilities";
  runButton.querySelector(".run-icon").textContent = loading ? "◌" : "✳";
  if (loading) setApiStatus("SIMULATING…");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.textContent = "";
  const decision = decisionInput.value.trim();
  if (decision.length < 3) {
    formError.textContent = "Describe a decision in at least 3 characters.";
    decisionInput.focus();
    return;
  }
  const initial_state = {};
  [["revenue", "revenue"], ["customers", "customers"], ["cost", "cost"]].forEach(([id, key]) => {
    const input = $(id);
    if (input.value.trim() !== "" && Number.isFinite(Number(input.value)) && Number(input.value) >= 0) initial_state[key] = Number(input.value);
  });
  const payload = { decision, initial_state, months: Number($("months").value), branches: [] };
  setLoading(true);
  try {
    const response = await fetch(`${API_BASE}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(90000)
    });
    let data;
    try { data = await response.json(); } catch { data = {}; }
    if (!response.ok) {
      const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data) || "Unknown API error";
      throw new Error(`API returned ${response.status}: ${detail}`);
    }
    latestResponse = data;
    renderScenarios(data);
    renderAssumptions(data);
    renderMetricOptions(data);
    resultsSection.hidden = false;
    emptyState.hidden = true;
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    setApiStatus("ENGINE ONLINE", true);
  } catch (error) {
    const message = error.name === "TimeoutError" || error.name === "AbortError"
      ? "The request took too long. Check that the backend is running and try again."
      : error instanceof TypeError
        ? `Cannot reach the backend at ${API_BASE}. Start FastAPI, then try again.`
        : error.message;
    formError.textContent = message;
    setApiStatus("ENGINE CONNECTION ISSUE");
  } finally {
    setLoading(false);
    if (latestResponse) setApiStatus("ENGINE ONLINE", true);
  }
});

const summary = document.querySelector(".assumptions-panel summary");
summary?.addEventListener("click", () => {
  const toggle = summary.querySelector(".details-toggle");
  window.setTimeout(() => { if (toggle) toggle.textContent = summary.parentElement.open ? "−" : "+"; }, 0);
});
