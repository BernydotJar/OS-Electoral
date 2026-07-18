(() => {
  const escapeHtml = (value) => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const nav = document.querySelector(".module-nav");
  const main = document.querySelector("#main");
  if (!nav || !main || document.querySelector('[data-module="governance"]')) return;

  const style = document.createElement("style");
  style.textContent = `
    .governance-hero{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1.5rem;align-items:end;margin-bottom:1.5rem}
    .governance-stats{display:grid;grid-template-columns:repeat(3,minmax(92px,1fr));gap:.75rem}
    .governance-stats div,.governance-card{border:1px solid var(--border);background:var(--surface);border-radius:18px;padding:1rem}
    .governance-stats strong{display:block;font-size:1.65rem}.governance-stats span{font-size:.75rem;color:var(--muted)}
    .governance-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}
    .governance-card h3{margin:.2rem 0 .8rem}.governance-card ul{margin:.7rem 0 0;padding-left:1.1rem}.governance-card li{margin:.4rem 0}
    .governance-row{padding:.75rem 0;border-top:1px solid var(--border)}.governance-row:first-of-type{border-top:0}
    .governance-meta{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.75rem}.governance-meta span{font-size:.72rem;border:1px solid var(--border);border-radius:999px;padding:.3rem .55rem}
    .governance-warning{margin-top:1rem;padding:1rem;border:1px solid var(--warning-border,var(--border));border-radius:14px;background:var(--surface-soft,var(--surface))}
    @media(max-width:900px){.governance-hero,.governance-grid{grid-template-columns:1fr}.governance-stats{grid-template-columns:repeat(3,1fr)}}
    @media(max-width:520px){.governance-stats{grid-template-columns:1fr}}
  `;
  document.head.appendChild(style);

  const tab = document.createElement("button");
  tab.className = "module-tab";
  tab.type = "button";
  tab.dataset.module = "governance";
  tab.innerHTML = "<span>Governance Workspace</span><small>Marca, approvals y operación</small>";
  nav.appendChild(tab);

  const section = document.createElement("section");
  section.id = "governanceModule";
  section.className = "module-view";
  section.dataset.view = "governance";
  section.setAttribute("aria-labelledby", "governance-title");
  section.hidden = true;
  section.innerHTML = `
    <section class="governance-hero">
      <div><p class="section-kicker">READ-ONLY GOVERNANCE</p><h2 id="governance-title" tabindex="-1">Candidate governance workspace</h2><p id="governanceSummary" class="hero-copy">Loading governed snapshot…</p></div>
      <div class="governance-stats" aria-label="Resumen de gobernanza">
        <div><strong id="governanceBrandStatus">—</strong><span>brand status</span></div>
        <div><strong id="governanceApprovalCount">—</strong><span>pending approvals</span></div>
        <div><strong id="governanceAssignmentCount">—</strong><span>internal assignments</span></div>
      </div>
    </section>
    <section class="governance-grid" aria-label="Candidate Brand, Approval Inbox and Daily Operations">
      <article class="governance-card panel"><p class="section-kicker">CANDIDATE BRAND</p><h3>Evidence before positioning</h3><div id="governanceBrand"></div></article>
      <article class="governance-card panel"><p class="section-kicker">APPROVAL INBOX</p><h3>Human decisions pending</h3><div id="governanceApprovals"></div></article>
      <article class="governance-card panel"><p class="section-kicker">DAILY OPERATIONS</p><h3>Internal work only</h3><div id="governanceOperations"></div></article>
    </section>
    <section class="governance-warning"><strong>Safety contract</strong><p id="governanceSafety"></p></section>
  `;
  main.appendChild(section);

  function activate() {
    document.querySelectorAll("[data-view]").forEach((view) => { view.hidden = view.dataset.view !== "governance"; });
    document.querySelectorAll("[data-module]").forEach((button) => {
      const active = button.dataset.module === "governance";
      button.classList.toggle("is-active", active);
      if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
    });
    document.body.dataset.activeModule = "governance";
    document.querySelector("#activeModuleStatus").textContent = "Coordinate 04 · Human governance";
    document.querySelector("#governance-title").focus({ preventScroll: true });
  }
  tab.addEventListener("click", activate);

  function render(data) {
    document.querySelector("#governanceSummary").textContent = `Snapshot ${data.snapshotDate} · ${data.mode} · public use ${data.publicUseStatus}`;
    document.querySelector("#governanceBrandStatus").textContent = data.brand.status.replaceAll("_", " ");
    document.querySelector("#governanceApprovalCount").textContent = String(data.approvalInbox.pendingCount);
    document.querySelector("#governanceAssignmentCount").textContent = String(data.operations.kpis.total);
    document.querySelector("#governanceSafety").textContent = data.safetyStatement;

    document.querySelector("#governanceBrand").innerHTML = `
      <div class="governance-row"><strong>Identity</strong><p>${escapeHtml(data.brand.identityStatus)}</p></div>
      <div class="governance-row"><strong>Biography</strong><p>${escapeHtml(data.brand.biographyStatus)}</p></div>
      <div class="governance-row"><strong>Verified attributes</strong><p>${escapeHtml(data.brand.verifiedAttributes)}</p></div>
      <div class="governance-row"><strong>Next safe action</strong><p>${escapeHtml(data.brand.nextAction)}</p></div>
      <ul>${data.brand.warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;

    document.querySelector("#governanceApprovals").innerHTML = data.approvalInbox.requests.map((request) => `
      <div class="governance-row">
        <strong>${escapeHtml(request.title)}</strong><p>${escapeHtml(request.scope)}</p>
        <div class="governance-meta"><span>${escapeHtml(request.status)}</span><span>Role: ${escapeHtml(request.requiredRoles.join(", "))}</span></div>
        <p><b>Recommendation:</b> ${escapeHtml(request.recommendation)}</p>
        <ul>${request.options.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>`).join("") + `<p class="warning-note">${escapeHtml(data.approvalInbox.warning)}</p>`;

    document.querySelector("#governanceOperations").innerHTML = data.operations.assignments.map((assignment) => `
      <div class="governance-row">
        <strong>${escapeHtml(assignment.title)}</strong><p>${escapeHtml(assignment.owner)} · due ${escapeHtml(assignment.dueDate)}</p>
        <div class="governance-meta"><span>${escapeHtml(assignment.status)}</span><span>${assignment.overdue ? "OVERDUE" : "ON TRACK"}</span><span>${assignment.blocked ? "BLOCKED" : "UNBLOCKED"}</span></div>
        <p>Evidence: ${escapeHtml(assignment.evidenceRefs.join(", "))}</p>
      </div>`).join("") + data.operations.meetingPreparation.map((meeting) => `
      <div class="governance-row"><strong>${escapeHtml(meeting.title)}</strong><p>Evidence: ${escapeHtml(meeting.evidenceRefs.join(", "))}</p><ul>${meeting.questions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`).join("");
  }

  fetch("./data/governance.json", { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error(`Governance HTTP ${response.status}`); return response.json(); })
    .then(render)
    .catch((error) => {
      document.querySelector("#governanceSummary").textContent = "Governance snapshot unavailable; no action is authorized.";
      console.error("Unable to load governance snapshot", error);
    });
})();
