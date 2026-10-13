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
  function decisionDomain(decision) {
    const text = String(decision || "").toLowerCase();
    if (/join ug|undergraduate|college|degree|university|job|workforce|career/.test(text)) return "education";
    if (/life insurance|term insurance|life cover/.test(text)) return "life";
    if (/health insurance|medical insurance|mediclaim|hospitalization/.test(text)) return "health";
    if (/insurance|policy premium|sum insured|deductible|co-pay|copay/.test(text)) return "insurance";
    if (/bike|motorcycle|scooter|car|vehicle|600 ?cc|emi|fuel|commuting/.test(text)) return "vehicle";
    if (/learn|learning|study|skill|course|project|portfolio|career|job|salary/.test(text)) return "learning";
    if (/business|startup|customer|revenue|marketing|sales|hire/.test(text)) return "business";
    return "general";
  }
  function detailItems(domain, decision, scenario) {
    const common = ["What assumptions would change this outcome?", "Which costs or constraints have not been supplied?", "What evidence should be checked before committing?"];
    const byDomain = {
      education: ["Compare total tuition, exam fees, transport, equipment and living costs for the full course.", "Estimate time until qualification and how the degree matches your target roles.", "For the job-first path, compare take-home pay, work experience, savings and whether part-time study is realistic.", "Include the opportunity cost of studying full time versus earning now, without assuming a guaranteed salary.", "Check admission eligibility, scholarships, internships, placement reports and course accreditation.", "Try a hybrid option such as working while studying, a diploma, or deferring admission for a planned period."],
      vehicle: ["Upfront price and down payment; compare loan APR, fees, EMI and total repayment.", "Fuel based on your monthly distance and realistic mileage; include servicing, tyres and repairs.", "Insurance quote, coverage, exclusions, deductibles and renewal costs.", "Registration/tax and protective gear where applicable; estimate resale value cautiously.", "Compare buying new, buying inspected used, and delaying while saving."],
      life: ["Estimate coverage needs from dependants, debts, income replacement and future obligations.", "Compare premiums for the same coverage and duration; verify whether premiums can change.", "Read exclusions, contestability terms, lapse/grace-period rules and claim requirements in the actual policy.", "Check existing employer cover and whether it continues after leaving the job.", "Compare term coverage with other product types on their actual benefits, fees and lock-ins; don't assume they are interchangeable."],
      health: ["Compare sum insured, room limits, co-pay, deductibles and sub-limits.", "Check pre-existing-condition and specific-treatment waiting periods, exclusions and network hospitals.", "Compare individual cover with family-floater limits for each covered person.", "Include renewal affordability and the possibility of out-of-pocket expenses.", "Read the policy wording and insurer disclosures; benefits vary by plan."],
      insurance: ["Compare premium with the actual coverage and benefits provided.", "Check exclusions, waiting periods, deductibles/co-pay, limits and claim conditions.", "Check renewal terms, premium changes and affordability over time.", "Use the official policy wording and written insurer quotes, not assumed policy terms."],
      learning: ["Time available each week and consistency over the selected horizon.", "Course, equipment and certification costs against the stated budget.", "Define a project milestone and a skill checklist that can be verified.", "Treat project and skill counts as planning targets, not predicted achievements."],
      business: ["Initial spend, recurring costs, cash runway and downside exposure.", "Define the metric to optimize and how it will be measured.", "Test a small reversible experiment before scaling spend.", "Separate user-supplied figures from assumptions and modelled values."],
      general: common
    };
    return byDomain[domain] || common;
  }
  function openScenarioDetails(scenario, index, data) {
    const dialog = $("scenarioDialog");
    const domain = decisionDomain(data.decision);
    const titleText = title(scenario.name || "Alternative path");
    $("detailTitle").textContent = titleText;
    $("detailSummary").textContent = scenario.assumption || "A possible path based on your decision.";
    const highlights = $("detailHighlights");
    highlights.replaceChildren();
    const timeline = scenario.timeline || [];
    const last = timeline.length ? timeline[timeline.length - 1].values || {} : {};
    const first = timeline.length ? timeline[0].values || {} : {};
    const entries = Object.entries(last).slice(0, 6);
    if (entries.length) entries.forEach(([key, value]) => {
      const box = document.createElement("div");
      box.className = "detail-highlight";
      const delta = typeof value === "number" && typeof first[key] === "number" ? value - first[key] : null;
      box.innerHTML = '<span>' + escape(metricName(key)) + '</span><strong>' + escape(format(value)) + '</strong><small>' + (delta === null ? "No baseline available" : "Change from first modeled month: " + escape((delta > 0 ? "+" : "") + format(delta))) + '</small>';
      highlights.appendChild(box);
    });
    if (!entries.length) highlights.innerHTML = '<p class="dialog-muted">No numeric starting values were supplied for this scenario. The path below is qualitative until you add the relevant real-world inputs.</p>';
    const list = $("detailConsiderations");
    list.replaceChildren();
    detailItems(domain, data.decision, scenario).forEach((item) => { const li = document.createElement("li"); li.textContent = item; list.appendChild(li); });
    const timelineBox = $("detailTimeline");
    timelineBox.replaceChildren();
    timeline.slice(0, 24).forEach((row) => {
      const line = document.createElement("div");
      line.className = "detail-timeline-row";
      const values = Object.entries(row.values || {}).map(([key, value]) => metricName(key) + ": " + format(value)).join(" · ");
      const events = (row.events || []).join(" · ");
      const month = document.createElement("strong"); month.textContent = row.month === 0 ? "START" : "MONTH " + String(row.month).padStart(2, "0");
      const body = document.createElement("span"); body.textContent = [values, events].filter(Boolean).join(" — ") || "No details returned.";
      line.append(month, body); timelineBox.appendChild(line);
    });
    if (!timeline.length) timelineBox.textContent = "No month-by-month data is available yet.";
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }
  $("closeScenarioDialog").addEventListener("click", () => $("scenarioDialog").close());
  $("scenarioDialog").addEventListener("click", (event) => { if (event.target === $("scenarioDialog")) $("scenarioDialog").close(); });

  const SAVED_KEY = "whatif-ai:saved-simulations:v1";
  function readSaved() {
    try { const data = JSON.parse(localStorage.getItem(SAVED_KEY) || "[]"); return Array.isArray(data) ? data : []; }
    catch (_) { return []; }
  }
  function refreshSavedPicker() {
    const picker = $("savedSimulations");
    if (!picker) return;
    const current = picker.value;
    picker.replaceChildren(new Option("Open saved simulation", ""));
    readSaved().forEach((item) => picker.add(new Option(item.label, item.id)));
    if ([...picker.options].some((option) => option.value === current)) picker.value = current;
  }
  function downloadFile(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url; link.download = filename; link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function exportJson() {
    if (!latestResponse) return;
    downloadFile("whatif-simulation.json", JSON.stringify({ ...latestResponse, exported_at: new Date().toISOString() }, null, 2), "application/json;charset=utf-8");
  }
  function exportCsv() {
    if (!latestResponse) return;
    const quote = (value) => '"' + String(value ?? "").replace(/"/g, '""') + '"';
    const rows = [["decision", "domain", "scenario", "month", "metric", "value", "events"]];
    (latestResponse.scenarios || []).forEach((scenario) => (scenario.timeline || []).forEach((point) => {
      Object.entries(point.values || {}).forEach(([key, value]) => rows.push([
        latestResponse.decision, latestResponse.domain || "general", scenario.name, point.month, key, value, (point.events || []).join(" | ")
      ]));
    }));
    downloadFile("whatif-simulation.csv", rows.map((row) => row.map(quote).join(",")).join("\r\n"), "text/csv;charset=utf-8");
  }
  $("saveSimulation")?.addEventListener("click", () => {
    if (!latestResponse) return;
    try {
      const saved = readSaved();
      const id = (window.crypto?.randomUUID?.() || String(Date.now()));
      saved.unshift({ id, label: (latestResponse.domain_label || "Decision") + " · " + latestResponse.decision.slice(0, 58), decision: latestResponse.decision, months: Number($("months").value), response: latestResponse, saved_at: new Date().toISOString() });
      localStorage.setItem(SAVED_KEY, JSON.stringify(saved.slice(0, 30)));
      refreshSavedPicker();
      $("savedSimulations").value = id;
      $("saveSimulation").textContent = "SAVED ✓";
    } catch (_) { formError.textContent = "Could not save locally. Check whether browser storage is available."; }
  });
  $("exportJson")?.addEventListener("click", exportJson);
  $("exportCsv")?.addEventListener("click", exportCsv);
  $("savedSimulations")?.addEventListener("change", (event) => {
    const item = readSaved().find((saved) => saved.id === event.target.value);
    if (!item) return;
    latestResponse = item.response;
    decisionInput.value = item.decision;
    decisionInput.dispatchEvent(new Event("input"));
    $("months").value = String(item.months || 3);
    renderScenarios(latestResponse);
    renderAssumptions(latestResponse);
    renderMetricOptions(latestResponse);
    resultsSection.hidden = false; emptyState.hidden = true;
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  refreshSavedPicker();

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
        '<button class="details-button" type="button">EXPLORE THIS POSSIBILITY <span>↗</span></button>' +
        '<button class="timeline-button" type="button" aria-expanded="false"><span>VIEW TIMELINE · ' + (scenario.timeline || []).length + ' MONTHS</span><span>＋</span></button>' +
        '<div class="timeline-details" hidden>' + (timelineRows || '<p class="scenario-assumption">No timeline details were returned.</p>') + '</div>';
      card.querySelector(".details-button").addEventListener("click", () => openScenarioDetails(scenario, index, data));
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
  function showChartEmpty(message) {
    chart.innerHTML = '<text x="450" y="130" fill="#c9f27a" font-size="14" text-anchor="middle">' + escape(message) + '</text><text x="450" y="157" fill="#8290a0" font-size="11" text-anchor="middle">Add relevant starting values to compare a numeric trajectory.</text>';
    $("chartLegend").replaceChildren();
  }
  function drawChart() {
    const scenarios = latestResponse?.scenarios || [];
    const key = metricSelect.value;
    $("chartNote").textContent = key ? "Metric: " + metricName(key) + " · relative scale" : "Run a simulation to compare paths";
    $("chartLegend").replaceChildren();
    if (!key || !scenarios.length) {
      showChartEmpty("Choose a metric to compare possible paths.");
      return;
    }
    const series = scenarios.map((scenario, index) => {
      const points = [{ month: 0, value: number(scenario.timeline?.[0]?.values?.[key]) }];
      (scenario.timeline || []).forEach((row) => points.push({ month: row.month, value: number(row.values?.[key]) }));
      return { name: scenario.name || "Path " + (index + 1), color: colors[index % colors.length], points: points.filter((point) => point.value !== null) };
    }).filter((item) => item.points.length);
    const values = series.flatMap((item) => item.points.map((point) => point.value));
    if (!values.length) {
      showChartEmpty("No numeric values were available for this metric.");
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
    // Remove old results immediately so a failed/new request can never look like its output.
    latestResponse = null;
    scenarioGrid.replaceChildren();
    $("chartLegend").replaceChildren();
    metricSelect.replaceChildren(new Option("Choose metric", ""));
    chart.innerHTML = '<text x="450" y="145" fill="#8290a0" font-size="13" text-anchor="middle">Generating paths for your new question…</text>';
    resultsSection.hidden = true;
    emptyState.hidden = false;
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
      $("saveSimulation").textContent = "SAVE";
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