(() => {
  const EVIDENCE_CLASSES = {
    OFFICIAL: "war-evidence-official",
    CAMPAIGN_RESEARCH: "war-evidence-research",
    PERCEPTION: "war-evidence-perception",
    HYPOTHESIS: "war-evidence-hypothesis",
    UNKNOWN: "war-evidence-unknown"
  };

  let snapshot = null;
  let detailInvoker = null;

  const ENTITIES = {
    amp: String.fromCharCode(38, 97, 109, 112, 59),
    lt: String.fromCharCode(38, 108, 116, 59),
    gt: String.fromCharCode(38, 103, 116, 59),
    quot: String.fromCharCode(38, 113, 117, 111, 116, 59),
    apos: String.fromCharCode(38, 35, 48, 51, 57, 59)
  };

  const escapeHtml = (value) => String(value)
    .replaceAll(String.fromCharCode(38), ENTITIES.amp)
    .replaceAll("<", ENTITIES.lt)
    .replaceAll(">", ENTITIES.gt)
    .replaceAll('"', ENTITIES.quot)
    .replaceAll("'", ENTITIES.apos);

  const listHtml = (items) => items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");

  function focusAfterPaint(element) {
    if (!element) return;
    queueMicrotask(() => {
      requestAnimationFrame(() => {
        if (!element.isConnected || element.closest("[hidden]")) return;
        element.focus({ preventScroll: true });
      });
    });
  }

  function renderPipeline(items) {
    document.querySelector("#warPipeline").innerHTML = items.map((item, index) => `
      <li><span>${String(index + 1).padStart(2, "0")}</span><strong>${escapeHtml(item)}</strong></li>
    `).join("");
  }

  function renderSignals(signals) {
    document.querySelector("#warSignalList").innerHTML = signals.map((signal) => `
      <div class="war-signal-item" role="listitem">
        <button class="war-signal-card" type="button" data-war-signal="${escapeHtml(signal.id)}" aria-haspopup="dialog">
          <span class="war-card-topline">
            <span>${escapeHtml(signal.id)}</span>
            <span class="war-status">${escapeHtml(signal.status.replaceAll("_", " "))}</span>
          </span>
          <h3>${escapeHtml(signal.title)}</h3>
          <p>${escapeHtml(signal.summary)}</p>
          <span class="war-card-footer">
            <span class="war-evidence ${EVIDENCE_CLASSES[signal.evidenceClass] || ""}">${escapeHtml(signal.evidenceClass.replaceAll("_", " "))}</span>
            <span>${escapeHtml(signal.owner)} →</span>
          </span>
        </button>
      </div>
    `).join("");

    document.querySelectorAll("[data-war-signal]").forEach((button) => {
      button.addEventListener("click", () => openSignal(button.dataset.warSignal, button));
    });
  }

  function renderDecisions(decisions) {
    document.querySelector("#warDecisionList").innerHTML = decisions.map((decision) => `
      <article class="war-row">
        <div><span>${escapeHtml(decision.id)}</span><strong>${escapeHtml(decision.title)}</strong><small>Owner: ${escapeHtml(decision.owner)}</small></div>
        <span class="war-approval">${escapeHtml(decision.status.replaceAll("_", " "))}</span>
      </article>
    `).join("");
  }

  function renderAssignments(assignments) {
    document.querySelector("#warAssignmentList").innerHTML = assignments.map((assignment) => `
      <article class="war-row">
        <div><span>${escapeHtml(assignment.id)}</span><strong>${escapeHtml(assignment.title)}</strong><small>${escapeHtml(assignment.owner)} · ${escapeHtml(assignment.executionBoundary.replaceAll("_", " "))}</small></div>
        <span class="war-assignment-status">${escapeHtml(assignment.status.replaceAll("_", " "))}</span>
      </article>
    `).join("");
  }

  function renderRisks(risks) {
    document.querySelector("#warRiskList").innerHTML = risks.map((risk) => `
      <article class="war-risk">
        <span>${escapeHtml(risk.level)}</span><strong>${escapeHtml(risk.title)}</strong><p>${escapeHtml(risk.mitigation)}</p>
      </article>
    `).join("");
  }

  function renderLearning(items) {
    document.querySelector("#warLearningList").innerHTML = items.map((item) => `
      <article class="war-learning"><strong>${escapeHtml(item.statement)}</strong><span>${escapeHtml(item.source)}</span></article>
    `).join("");
  }

  function renderGates(gates) {
    document.querySelector("#warGateList").innerHTML = gates.map((gate) => `
      <div class="gate-row"><div><div class="row-title">${escapeHtml(gate)}</div><div class="row-detail">Requires explicit human approval and sufficient evidence.</div></div><span class="gate-indicator gate-closed" aria-label="Gate cerrado"></span></div>
    `).join("");
  }

  function populateSignal(signal) {
    document.querySelector("#warDetailClass").textContent = `${signal.evidenceClass.replaceAll("_", " ")} · ${signal.confidence.replaceAll("_", " ")}`;
    document.querySelector("#warDetailTitle").textContent = signal.title;
    document.querySelector("#warDetailSummary").textContent = signal.summary;
    document.querySelector("#warDetailAssessment").textContent = signal.assessment;
    document.querySelector("#warDetailDecision").textContent = signal.decisionRequired;
    document.querySelector("#warDetailOwner").textContent = signal.owner;
    document.querySelector("#warDetailDue").textContent = signal.dueDate;
    document.querySelector("#warDetailGate").textContent = signal.gate;
    document.querySelector("#warDetailApproval").textContent = signal.approvalStatus.replaceAll("_", " ");
    document.querySelector("#warDetailSource").textContent = signal.source;
    document.querySelector("#warDetailOptions").innerHTML = listHtml(signal.options);
    document.querySelector("#warDetailBlockers").innerHTML = listHtml(signal.blockers);
  }

  function openSignal(id, invoker) {
    const signal = snapshot?.signals.find((item) => item.id === id);
    if (!signal) return;
    detailInvoker = invoker;
    populateSignal(signal);
    const dialog = document.querySelector("#warDetailDialog");
    dialog.hidden = false;
    document.body.classList.add("drawer-open");
    focusAfterPaint(document.querySelector("#warDetailClose"));
  }

  function closeSignal() {
    const dialog = document.querySelector("#warDetailDialog");
    if (dialog.hidden) return;
    dialog.hidden = true;
    document.body.classList.remove("drawer-open");
    const invoker = detailInvoker;
    detailInvoker = null;
    focusAfterPaint(invoker);
  }

  function trapFocus(event) {
    const dialog = document.querySelector("#warDetailDialog");
    if (dialog.hidden || event.key !== "Tab") return;
    const focusable = [...dialog.querySelectorAll('button, [href], [tabindex]')]
      .filter((element) => !element.disabled && !element.hidden && element.tabIndex >= 0);
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

  function render(snapshotData) {
    snapshot = snapshotData;
    document.querySelector("#warSummary").textContent = snapshot.summary;
    document.querySelector("#warSafetyStatement").textContent = snapshot.safetyStatement;
    document.querySelector("#warSignalCount").textContent = String(snapshot.signals.length);
    document.querySelector("#warDecisionCount").textContent = String(snapshot.decisions.length);
    document.querySelector("#warBlockedCount").textContent = String(snapshot.signals.filter((item) => item.status === "BLOCKED").length);
    renderPipeline(snapshot.pipeline);
    renderSignals(snapshot.signals);
    renderDecisions(snapshot.decisions);
    renderAssignments(snapshot.assignments);
    renderRisks(snapshot.risks);
    renderLearning(snapshot.learning);
    renderGates(snapshot.closedGates);
  }

  async function loadWarRoom() {
    try {
      const response = await fetch("./data/war-room.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`War Room HTTP ${response.status}`);
      render(await response.json());
    } catch (error) {
      document.querySelector("#war-room-title").textContent = "No fue posible cargar el Daily War Room";
      document.querySelector("#warSummary").textContent = "Revise web/data/war-room.json.";
      console.error("Unable to load Daily War Room snapshot", error);
    }
  }

  document.querySelector("#warDetailClose").addEventListener("click", closeSignal);
  document.querySelector("#warDetailBackdrop").addEventListener("click", closeSignal);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeSignal();
    trapFocus(event);
  });

  loadWarRoom();
})();
