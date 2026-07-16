const STATUS_CLASSES = {
  PASS: "status-pass",
  PARTIAL: "status-partial",
  BLOCKED: "status-blocked",
  RESEARCH: "status-research"
};

const TEAM_STATUS_CLASSES = {
  ACTIVE: "status-active",
  RESEARCH_ONLY: "status-research-only",
  SETUP_REQUIRED: "status-setup-required",
  LOCKED: "status-locked",
  BLOCKED: "status-blocked"
};

const EVIDENCE_CLASSES = {
  OFFICIAL: "evidence-official",
  DERIVED: "evidence-derived",
  PRELIMINARY: "evidence-preliminary"
};

let teamSnapshot = null;
let drawerInvoker = null;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function listHtml(items) {
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderTeam(team) {
  teamSnapshot = team;
  document.querySelector("#candidateTitle").textContent = team.candidate.title;
  document.querySelector("#candidateSubtitle").textContent = team.candidate.subtitle;
  document.querySelector("#chiefTitle").textContent = team.chiefOfStaff.title;
  document.querySelector("#chiefSubtitle").textContent = team.chiefOfStaff.subtitle;
  document.querySelector("#teamSafetyStatement").textContent = team.safetyStatement;
  document.querySelector("#snapshotDate").textContent = `Snapshot ${team.snapshotDate}`;

  const active = team.departments.filter((department) => department.status === "ACTIVE").length;
  const gated = team.departments.filter((department) => ["SETUP_REQUIRED", "LOCKED", "BLOCKED"].includes(department.status)).length;
  document.querySelector("#departmentCount").textContent = String(team.departments.length);
  document.querySelector("#activeCount").textContent = String(active);
  document.querySelector("#lockedCount").textContent = String(gated);

  document.querySelector("#teamGrid").innerHTML = team.departments.map((department, index) => `
    <button class="department-card" type="button" role="listitem" data-department-id="${escapeHtml(department.id)}" aria-haspopup="dialog">
      <span class="department-index">DEPT ${String(index + 1).padStart(2, "0")}</span>
      <h3>${escapeHtml(department.name)}</h3>
      <p>${escapeHtml(department.mission)}</p>
      <span class="card-footer">
        <span class="status-chip ${TEAM_STATUS_CLASSES[department.status] || ""}">${escapeHtml(department.status.replaceAll("_", " "))}</span>
        <span class="open-label">Abrir detalle →</span>
      </span>
    </button>
  `).join("");

  document.querySelector("#teamGateList").innerHTML = team.closedGates.map((gate) => `
    <div class="gate-row">
      <div>
        <div class="row-title">${escapeHtml(gate)}</div>
        <div class="row-detail">Requires explicit human approval and evidence.</div>
      </div>
      <span class="gate-indicator gate-closed" aria-label="Gate cerrado"></span>
    </div>
  `).join("");

  document.querySelectorAll("[data-department-id]").forEach((button) => {
    button.addEventListener("click", () => openDepartment(button.dataset.departmentId, button));
  });
}

function renderMetrics(metrics) {
  document.querySelector("#metricsGrid").innerHTML = metrics.map((metric) => `
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
  document.querySelector("#workstreamList").innerHTML = workstreams.map((item) => `
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
  document.querySelector("#gateList").innerHTML = gates.map((gate) => `
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
      <thead><tr><th>Registro</th><th>Valor</th><th>Clase</th><th>Decisión</th></tr></thead>
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
  document.querySelector("#policyList").innerHTML = listHtml(policies);
}

function renderEvidence(data) {
  document.querySelector("#dataVersion").textContent = `Team ${teamSnapshot?.version || "—"} · Evidence ${data.version}`;
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
}

function populateDrawer(department) {
  document.querySelector("#drawerStatus").textContent = department.status.replaceAll("_", " ");
  document.querySelector("#drawerTitle").textContent = department.name;
  document.querySelector("#drawerMission").textContent = department.mission;
  document.querySelector("#drawerAutonomy").textContent = department.autonomy;
  document.querySelector("#drawerApproval").textContent = department.approvalOwner;
  document.querySelector("#drawerReviewed").textContent = department.lastReviewed;
  document.querySelector("#drawerSkills").innerHTML = listHtml(department.skills);
  document.querySelector("#drawerEvidence").innerHTML = listHtml(department.evidenceInputs);
  document.querySelector("#drawerBlockers").innerHTML = listHtml(department.blockers);
}

function openDepartment(id, invoker) {
  const department = teamSnapshot?.departments.find((item) => item.id === id);
  if (!department) return;
  drawerInvoker = invoker;
  populateDrawer(department);
  const drawer = document.querySelector("#agentDrawer");
  drawer.hidden = false;
  document.body.classList.add("drawer-open");
  document.querySelector("#drawerClose").focus();
}

function closeDrawer() {
  const drawer = document.querySelector("#agentDrawer");
  if (drawer.hidden) return;
  drawer.hidden = true;
  document.body.classList.remove("drawer-open");
  drawerInvoker?.focus();
  drawerInvoker = null;
}

function trapDrawerFocus(event) {
  const drawer = document.querySelector("#agentDrawer");
  if (drawer.hidden || event.key !== "Tab") return;
  const focusable = [...drawer.querySelectorAll('button, [href], [tabindex]:not([tabindex="-1"])')]
    .filter((element) => !element.disabled && !element.hidden);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function switchModule(moduleName, trigger) {
  document.querySelectorAll("[data-view]").forEach((view) => {
    view.hidden = view.dataset.view !== moduleName;
  });
  document.querySelectorAll("[data-module]").forEach((button) => {
    const active = button.dataset.module === moduleName;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reducedMotion && document.startViewTransition) {
    document.documentElement.style.setProperty("--transition-x", `${trigger.clientX || window.innerWidth / 2}px`);
    document.documentElement.style.setProperty("--transition-y", `${trigger.clientY || 80}px`);
  }
  document.querySelector(`[data-view="${moduleName}"] h2`)?.focus?.({ preventScroll: true });
}

function bindInteractions() {
  document.querySelectorAll("[data-module]").forEach((button) => {
    button.addEventListener("click", (event) => {
      const apply = () => switchModule(button.dataset.module, event);
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (!reducedMotion && document.startViewTransition) document.startViewTransition(apply);
      else apply();
    });
  });
  document.querySelector("#drawerClose").addEventListener("click", closeDrawer);
  document.querySelector("#drawerBackdrop").addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawer();
    trapDrawerFocus(event);
  });
}

async function loadApplication() {
  try {
    const [teamResponse, evidenceResponse] = await Promise.all([
      fetch("./data/team.json", { cache: "no-store" }),
      fetch("./data/status.json", { cache: "no-store" })
    ]);
    if (!teamResponse.ok) throw new Error(`Team HTTP ${teamResponse.status}`);
    if (!evidenceResponse.ok) throw new Error(`Evidence HTTP ${evidenceResponse.status}`);
    const [team, evidence] = await Promise.all([teamResponse.json(), evidenceResponse.json()]);
    renderTeam(team);
    renderEvidence(evidence);
    bindInteractions();
  } catch (error) {
    document.querySelector("#team-title").textContent = "No fue posible cargar el Command Center";
    document.querySelector("#overallSummary").textContent = "Revise web/data/team.json y web/data/status.json.";
    console.error("Unable to load CampaignOS snapshots", error);
  }
}

loadApplication();
