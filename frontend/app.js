(() => {
  "use strict";
  const API_BASE = String(window.WHATIF_API_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");
  const $ = (id) => document.getElementById(id);
  const form = $("decisionForm");
  const decisionInput = $("decision");
  const runButton = $("runButton");
  const runLabel = $("runLabel");
  const formError = $("formError");
  const resultsSection = $("resultsSection");
  const emptyState = $("emptyState");
  const scenarioGrid = $("scenarioGrid");
  const metricSelect = $("metricSelect");
  const chart = $("trajectoryChart");
  const colors = ["#c9f27a", "#82e4d5", "#b9a8ff", "#ffc28d", "#ff91a5", "#91baff"];
  let latestResponse = null;
  let healthController = null;

  function setApiStatus(message, state = "checking") {
    $("apiState").textContent = message;
    $("apiDot").className = "connection-dot " + state;
  }
  async function checkHealth() {
    if (healthController) healthController.abort();
    healthController = new AbortController();
    const timeout = window.setTimeout(() => healthController.abort(), 3500);
    try {
      const response = await fetch(API_BASE + "/health", { signal: healthController.signal, cache: "no-store" });
      if (!response.ok) throw new Error("Health endpoint returned " + response.status);
      const data = await response.json();
      if (data.status !== "ok") throw new Error("Unexpected health response");
      setApiStatus("ENGINE CONNECTED", "online");
      return true;
    } catch (error) {
      setApiStatus("ENGINE OFFLINE", "offline");
      return false;
    } finally {
      clearTimeout(timeout);
    }
  }
  $("retryHealth").addEventListener("click", checkHealth);
  checkHealth();

  decisionInput.addEventListener("input", () => {
    $("charCount").textContent = decisionInput.value.length + " / 1200";
  });
  document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => {
    decisionInput.value = button.dataset.prompt;
    decisionInput.dispatchEvent(new Event("input"));
    decisionInput.focus();
  }));

  const number = (value) => typeof value === "number" && Number.isFinite(value) ? value : null;
  const format = (value) => number(value) === null ? "—" : new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
  const compact = (value) => number(value) === null ? "—" : new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(value);
  const title = (value) => String(value || "Scenario").replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  const metricName = (value) => title(value);
  function branchTag(value) {
    const text = String(value || "").toLowerCase();
    if (/continue|current|maintain|baseline|keep/.test(text)) return "BASELINE";
    if (/risk|cautious|delay|reduce|avoid|conservative|pessimistic/.test(text)) return "CAUTIOUS";
    if (/optimistic|aggressive|increase|growth|expand|focus|intensive/.test(text)) return "GROWTH";
    return "ALTERNATIVE";
  }
  function finalValues(scenario) {
    const rows = scenario.timeline || [];
    return rows.length ? rows[rows.length - 1].values || {} : {};
  }
  function startValues(scenario) {
    const rows = scenario.timeline || [];
    return rows.length ? rows[0].values || {} : {};
  }
  function renderScenarios(data) {
    const scenarios = Array.isArray(data.scenarios) ? data.scenarios : [];
    scenarioGrid.replaceChildren();
    scenarios.forEach((scenario, index) => {
      const final = finalValues(scenario);
      const start = startValues(scenario);
      const keys = Object.keys(final).slice(0, 2);
      const stats = keys.map((key) => {
        const baseline = start[key];
        const delta = number(final[key]) !== null && number(baseline) !== null ? final[key] - baseline : null;
        return '<div><span class="stat-label">' + escape(metricName(key)) + '</span><span class="stat-value">' + escape(compact(final[key])) + '</span><span class="stat-delta">' + (delta === null ? "No numeric baseline" : escape((delta > 0 ? "+" : "") + format(delta) + " over horizon")) + '</span></div>';
      }).join("");
      const timelineRows = (scenario.timeline || []).map((snapshot) => {
        const values = Object.entries(snapshot.values || {}).slice(0, 3).map(([key, value]) => escape(metricName(key)) + ": " + escape(format(value))).join(" · ");
        const events = (snapshot.events || []).slice(0, 2).map(escape).join(" · ");
        return '<div class="timeline-row"><span>MONTH ' + String(snapshot.month).padStart(2, "0") + '</span><span>' + (values || "No numeric values") + (events ? '<br><small>' + events + '</small>' : "") + '</span></div>';
      }).join("");
      const card = document.createElement("article");
      card.className = "scenario-card";
      card.innerHTML = '<div class="scenario-top"><span class="scenario-index">PATH / ' + String(index + 1).padStart(2, "0") + '</span><span class="scenario-tag">' + branchTag(scenario.name || scenario.assumption) + '</span></div>' +
        '<h3>' + escape(title(scenario.name || "Alternative path")) + '</h3><p class="scenario-assumption">' + escape(scenario.assumption || "A possible path based on the decision.") + '</p>' +
        '<div class="scenario-stats">' + (stats || '<p class="scenario-assumption">Add numeric starting values to compare metrics.</p>') + '</div>' +
        '<button class="timeline-button" type="button" aria-expanded="false"><span>VIEW TIMELINE · ' + (scenario.timeline || []).length + ' MONTHS</span><span>＋</span></button>' +
        '<div class="timeline-details" hidden>' + (timelineRows || '<p class="scenario-assumption">No timeline details were returned.</p>') + '</div>';
      const toggle = card.querySelector(".timeline-button");
      const details = card.querySelector(".timeline-details");
      toggle.addEventListener("click", () => {
        const open = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!open));
        details.hidden = open;
        toggle.querySelector("span:last-child").textContent = open ? "＋" : "−";
        toggle.querySelector("span:first-child").textContent = (open ? "VIEW" : "HIDE") + " TIMELINE · " + (scenario.timeline || []).length + " MONTHS";
      });
      scenarioGrid.appendChild(card);
    });
    $("resultCount").textContent = scenarios.length + " PATHS";
    $("resultSubtitle").textContent = scenarios.length + " possible paths · " + $("months").value + "-month horizon · illustrative only";
  }
  function renderAssumptions(data) {
    const list = $("assumptionsList");
    list.replaceChildren();
    const items = Array.isArray(data.assumptions) ? [...data.assumptions] : [];
    if (data.disclaimer) items.push(data.disclaimer);
    if (!items.length) items.push("The API did not return assumptions for this simulation.");
    items.forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      list.appendChild(li);
    });
    const source = items.find((item) => /scenario branch source/i.test(item));
    $("sourceLabel").textContent = source ? source.replace(/^scenario branch source:\s*/i, "").replace(/\.$/, "").toUpperCase() : "SOURCE NOT REPORTED";
  }
  function renderMetricOptions(data) {
    const keys = new Set();
    (data.scenarios || []).forEach((scenario) => (scenario.timeline || []).forEach((row) => Object.keys(row.values || {}).forEach((key) => keys.add(key))));
    const previous = metricSelect.value;
    metricSelect.replaceChildren(new Option("Choose metric", ""));
    // Put decision-relevant progress metrics first; financial metrics should not
    // dominate a learning scenario just because a budget was mentioned.
    const preferred = ["projects_completed", "skills_practiced", "study_hours_per_week", "learning_budget_remaining_inr"];
    const orderedKeys = [...keys].sort((a, b) => {
      const ai = preferred.indexOf(a), bi = preferred.indexOf(b);
      return (ai < 0 ? preferred.length : ai) - (bi < 0 ? preferred.length : bi);
    });
    orderedKeys.forEach((key) => metricSelect.add(new Option(metricName(key), key)));
    metricSelect.value = keys.has(previous) ? previous : (orderedKeys[0] || "");
    drawChart();
  }
  function drawChart() {
    const scenarios = latestResponse?.scenarios || [];
    const key = metricSelect.value;
    $("chartNote").textContent = key ? "Metric: " + metricName(key) + " · relative scale" : "Run a simulation to compare paths";
    $("chartLegend").replaceChildren();
    if (!key || !scenarios.length) {
      chart.innerHTML = '<text x="450" y="145" fill="#8290a0" font-size="13" text-anchor="middle">Your scenario trajectories will appear here.</text>';
      return;
    }
    const series = scenarios.map((scenario, index) => {
      const points = [{ month: 0, value: number(scenario.timeline?.[0]?.values?.[key]) }];
      (scenario.timeline || []).forEach((row) => points.push({ month: row.month, value: number(row.values?.[key]) }));
      return { name: scenario.name || "Path " + (index + 1), color: colors[index % colors.length], points: points.filter((point) => point.value !== null) };
    }).filter((item) => item.points.length);
    const values = series.flatMap((item) => item.points.map((point) => point.value));
    if (!values.length) {
      chart.innerHTML = '<text x="450" y="145" fill="#8290a0" font-size="13" text-anchor="middle">This metric has no numeric values.</text>';
      return;
    }
    const min = Math.min(...values), max = Math.max(...values), span = max - min || Math.max(Math.abs(max) * .1, 1);
    const low = min - span * .12, high = max + span * .12, left = 65, right = 880, top = 24, bottom = 235;
    const maxMonth = Math.max(1, ...series.flatMap((item) => item.points.map((point) => point.month)));
    const x = (month) => left + month / maxMonth * (right - left);
    const y = (value) => bottom - (value - low) / (high - low) * (bottom - top);
    let svg = "";
    for (let index = 0; index < 5; index++) {
      const yy = top + index * (bottom - top) / 4, value = high - index * (high - low) / 4;
      svg += '<line x1="' + left + '" y1="' + yy + '" x2="' + right + '" y2="' + yy + '" stroke="#2b3541" stroke-dasharray="3 6"/><text x="' + (left - 10) + '" y="' + (yy + 4) + '" text-anchor="end" fill="#7c8999" font-size="10">' + escape(compact(value)) + '</text>';
    }
    const interval = Math.max(1, Math.ceil(maxMonth / 6));
    for (let month = 0; month <= maxMonth; month += interval) svg += '<text x="' + x(month) + '" y="260" text-anchor="middle" fill="#7c8999" font-size="10">' + (month === 0 ? "START" : "M" + month) + '</text>';
    series.forEach((item) => {
      const coords = item.points.map((point) => [x(point.month), y(point.value)]);
      const path = coords.map(([px, py], index) => (index ? "L" : "M") + " " + px.toFixed(2) + " " + py.toFixed(2)).join(" ");
      svg += '<path d="' + path + '" fill="none" stroke="' + item.color + '" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>';
      coords.forEach(([px, py]) => { svg += '<circle cx="' + px + '" cy="' + py + '" r="3.2" fill="#111720" stroke="' + item.color + '" stroke-width="2"/>'; });
      const legend = document.createElement("span");
      legend.className = "legend-item";
      legend.innerHTML = '<span class="legend-dot" style="background:' + item.color + '"></span>' + escape(title(item.name));
      $("chartLegend").appendChild(legend);
    });
    chart.innerHTML = svg;
  }
  metricSelect.addEventListener("change", drawChart);
  document.querySelector(".assumptions summary")?.addEventListener("click", () => {
    const icon = document.querySelector(".summary-icon");
    window.setTimeout(() => { icon.textContent = document.querySelector(".assumptions").open ? "−" : "+"; }, 0);
  });
  function loading(active) {
    runButton.disabled = active;
    runLabel.textContent = active ? "Exploring possible paths…" : "Explore possible futures";
    runButton.querySelector(".button-star").textContent = active ? "◌" : "✳";
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    formError.textContent = "";
    const decision = decisionInput.value.trim();
    if (decision.length < 3) {
      formError.textContent = "Please describe your decision in at least three characters.";
      decisionInput.focus();
      return;
    }
    const initial_state = {};
    [["revenue", "revenue"], ["customers", "customers"], ["cost", "cost"]].forEach(([id, key]) => {
      const raw = $(id).value.trim();
      if (raw !== "" && Number.isFinite(Number(raw)) && Number(raw) >= 0) initial_state[key] = Number(raw);
    });
    loading(true);
    setApiStatus("RUNNING SIMULATION", "checking");
    try {
      const response = await fetch(API_BASE + "/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, initial_state, months: Number($("months").value), branches: [] }),
        signal: AbortSignal.timeout(90000)
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data);
        throw new Error("API " + response.status + ": " + (detail || "Request failed"));
      }
      if (data.safety_notice) {
        latestResponse = null;
        resultsSection.hidden = true;
        emptyState.hidden = false;
        formError.textContent = data.safety_notice;
        setApiStatus("SAFETY NOTICE", "offline");
        return;
      }
      if (!Array.isArray(data.scenarios)) throw new Error("The API response did not contain scenario results.");
      latestResponse = data;
      renderScenarios(data);
      renderAssumptions(data);
      renderMetricOptions(data);
      resultsSection.hidden = false;
      emptyState.hidden = true;
      setApiStatus("ENGINE CONNECTED", "online");
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      const networkError = error instanceof TypeError;
      formError.textContent = networkError
        ? "Cannot reach " + API_BASE + ". Start the backend with run-whatif.ps1, then use Check connection."
        : error.name === "TimeoutError" || error.name === "AbortError"
          ? "The simulation timed out. Check the backend terminal and try again."
          : error.message;
      setApiStatus("CONNECTION ISSUE", "offline");
    } finally {
      loading(false);
    }
  });
  window.whatIfCheckHealth = checkHealth;
})();