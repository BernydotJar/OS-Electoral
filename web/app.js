const STATUS_CLASSES = {
  PASS: "status-pass",
  PARTIAL: "status-partial",
  BLOCKED: "status-blocked",
  RESEARCH: "status-research"
};

const EVIDENCE_CLASSES = {
  OFFICIAL: "evidence-official",
  DERIVED: "evidence-derived",
  PRELIMINARY: "evidence-preliminary"
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderMetrics(metrics) {
  const target = document.querySelector("#metricsGrid");
  target.innerHTML = metrics.map((metric) => `
    <article class="metric-card">
      <span class="metric-label">${escapeHtml(metric.label)}</span>
      <strong class="metric-value">${escapeHtml(metric.value)}</strong>
      <p class="metric-note">${escapeHtml(metric.note)}</p>
      <span class="evidence-tag ${EVIDENCE_CLASSES[metric.evidence] || ""}">
        ${escapeHtml(metric.evidence)} · ${escapeHtml(metric.source)}
      </span>
    </article>
  `).join("");
}

function renderWorkstreams(workstreams) {
  const target = document.querySelector("#workstreamList");
  target.innerHTML = workstreams.map((item) => `
    <div class="status-row">
      <div>
        <div class="row-title">${escapeHtml(item.name)}</div>
        <div class="row-detail">${escapeHtml(item.detail)}</div>
      </div>
      <span class="status-chip ${STATUS_CLASSES[item.status] || ""}">${escapeHtml(item.status)}</span>
    </div>
  `).join("");
}

function renderGates(gates) {
  const target = document.querySelector("#gateList");
  target.innerHTML = gates.map((gate) => `
    <div class="gate-row">
      <div>
        <div class="row-title">${escapeHtml(gate)}</div>
        <div class="row-detail">Requires explicit human approval and evidence.</div>
      </div>
      <span class="gate-indicator gate-closed" aria-label="Gate cerrado"></span>
    </div>
  `).join("");
}

function renderBlockers(blockers) {
  document.querySelector("#blockerList").innerHTML = blockers.map((blocker) => `
    <div class="blocker-row">
      <strong>${escapeHtml(blocker.title)}</strong>
      <p>${escapeHtml(blocker.detail)}</p>
    </div>
  `).join("");
}

function renderSources(sources) {
  document.querySelector("#sourceList").innerHTML = sources.map((source) => `
    <div class="source-row">
      <strong>${escapeHtml(source.id)} · ${escapeHtml(source.name)}</strong>
      <p>${escapeHtml(source.status)}</p>
    </div>
  `).join("");
}

function renderReconciliation(rows) {
  document.querySelector("#reconciliationTable").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Registro</th>
          <th>Valor</th>
          <th>Clase</th>
          <th>Decisión</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map((row) => `
          <tr>
            <td>${escapeHtml(row.record)}</td>
            <td><strong>${escapeHtml(row.value)}</strong></td>
            <td>${escapeHtml(row.class)}</td>
            <td>${escapeHtml(row.decision)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderPolicies(policies) {
  document.querySelector("#policyList").innerHTML = policies
    .map((policy) => `<li>${escapeHtml(policy)}</li>`)
    .join("");
}

async function loadStatus() {
  try {
    const response = await fetch("./data/status.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    document.querySelector("#snapshotDate").textContent = `Snapshot ${data.snapshotDate}`;
    document.querySelector("#dataVersion").textContent = `Data version ${data.version}`;
    document.querySelector("#overallSummary").textContent = data.overallSummary;
    document.querySelector("#progressLabel").textContent = `${data.progressPercent}%`;

    const progressBar = document.querySelector("#progressBar");
    progressBar.setAttribute("aria-valuenow", String(data.progressPercent));
    document.querySelector("#progressFill").style.width = `${data.progressPercent}%`;

    renderMetrics(data.metrics);
    renderWorkstreams(data.workstreams);
    renderGates(data.gates);
    renderBlockers(data.blockers);
    renderSources(data.sources);
    renderReconciliation(data.reconciliation);
    renderPolicies(data.policies);
  } catch (error) {
    document.querySelector("#overallSummary").textContent =
      "No fue posible cargar el snapshot local. Revise web/data/status.json.";
    document.querySelector("#progressLabel").textContent = "ERROR";
    console.error("Unable to load evidence status snapshot", error);
  }
}

loadStatus();
