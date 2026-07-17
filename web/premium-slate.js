(() => {
  const canvas = document.querySelector("#ambientCanvas");
  const moduleStatus = document.querySelector("#activeModuleStatus");
  const context = canvas?.getContext("2d", { alpha: true });
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const coarsePointer = window.matchMedia("(pointer: coarse)");
  const glowSelector = [
    ".command-summary",
    ".hero-panel",
    ".panel",
    ".war-hero",
    ".authority-node",
    ".department-card",
    ".metric-card",
    ".war-signal-card"
  ].join(",");

  const moduleLabels = {
    team: "Coordinate 01 · Governed team",
    "war-room": "Coordinate 02 · Daily decisions",
    evidence: "Coordinate 03 · Evidence control"
  };

  let nodes = [];
  let animationFrame = 0;
  let resizeFrame = 0;
  let lastTimestamp = 0;

  function seeded(index, salt) {
    const value = Math.sin(index * 9283.31 + salt * 77.13) * 43758.5453;
    return value - Math.floor(value);
  }

  function rebuildNodes() {
    if (!canvas || !context) return;
    const width = window.innerWidth;
    const height = window.innerHeight;
    const density = Math.max(12, Math.min(30, Math.round((width * height) / 72000)));
    nodes = Array.from({ length: density }, (_, index) => ({
      x: seeded(index, 1) * width,
      y: seeded(index, 2) * height,
      radius: 1 + seeded(index, 3) * 1.35,
      driftX: (seeded(index, 4) - .5) * .065,
      driftY: (seeded(index, 5) - .5) * .05
    }));
  }

  function resizeCanvas() {
    if (!canvas || !context) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const width = window.innerWidth;
    const height = window.innerHeight;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    rebuildNodes();
    drawFrame(0, true);
  }

  function drawFrame(timestamp, staticFrame = false) {
    if (!canvas || !context) return;
    const width = window.innerWidth;
    const height = window.innerHeight;
    context.clearRect(0, 0, width, height);

    if (!staticFrame && !reducedMotion.matches) {
      const delta = Math.min(32, Math.max(0, timestamp - lastTimestamp || 16));
      nodes.forEach((node) => {
        node.x = (node.x + node.driftX * delta + width) % width;
        node.y = (node.y + node.driftY * delta + height) % height;
      });
      lastTimestamp = timestamp;
    }

    const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent-h").trim() || "139";
    context.lineWidth = .65;

    for (let first = 0; first < nodes.length; first += 1) {
      for (let second = first + 1; second < nodes.length; second += 1) {
        const a = nodes[first];
        const b = nodes[second];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        if (distance > 150) continue;
        context.strokeStyle = `hsla(${accent}, 60%, 70%, ${Math.max(0, .075 - distance / 2500)})`;
        context.beginPath();
        context.moveTo(a.x, a.y);
        context.lineTo(b.x, b.y);
        context.stroke();
      }
    }

    nodes.forEach((node, index) => {
      context.fillStyle = index % 5 === 0
        ? `hsla(${accent}, 72%, 72%, .34)`
        : "rgba(190, 199, 212, .18)";
      context.beginPath();
      context.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      context.fill();
    });

    if (!staticFrame && !reducedMotion.matches && !document.hidden) {
      animationFrame = requestAnimationFrame(drawFrame);
    }
  }

  function startCanvas() {
    cancelAnimationFrame(animationFrame);
    if (reducedMotion.matches || document.hidden) {
      drawFrame(0, true);
      return;
    }
    lastTimestamp = performance.now();
    animationFrame = requestAnimationFrame(drawFrame);
  }

  function syncActiveModule() {
    const active = document.querySelector("[data-module].is-active")?.dataset.module || "team";
    document.body.dataset.activeModule = active;
    if (moduleStatus) moduleStatus.textContent = moduleLabels[active] || moduleLabels.team;
    drawFrame(0, true);
  }

  function activateGlow(element) {
    if (element.dataset.premiumGlowReady === "true") return;
    element.dataset.premiumGlowReady = "true";
    element.classList.add("premium-glow");
    element.addEventListener("pointermove", (event) => {
      if (reducedMotion.matches || coarsePointer.matches) return;
      const rect = element.getBoundingClientRect();
      element.style.setProperty("--glow-x", `${event.clientX - rect.left}px`);
      element.style.setProperty("--glow-y", `${event.clientY - rect.top}px`);
    }, { passive: true });
  }

  function hydrateGlowSurfaces(root = document) {
    root.querySelectorAll?.(glowSelector).forEach(activateGlow);
  }

  const observer = new MutationObserver((mutations) => {
    let shouldSyncModule = false;
    mutations.forEach((mutation) => {
      if (mutation.type === "attributes" && mutation.target.matches?.("[data-module]")) {
        shouldSyncModule = true;
      }
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof Element)) return;
        if (node.matches(glowSelector)) activateGlow(node);
        hydrateGlowSurfaces(node);
      });
    });
    if (shouldSyncModule) syncActiveModule();
  });

  window.addEventListener("resize", () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(resizeCanvas);
  }, { passive: true });
  document.addEventListener("visibilitychange", startCanvas);
  reducedMotion.addEventListener?.("change", startCanvas);

  hydrateGlowSurfaces();
  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "aria-current"] });
  syncActiveModule();
  resizeCanvas();
  startCanvas();
})();
