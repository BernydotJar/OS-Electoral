(() => {
  const teamGrid = document.querySelector("#teamGrid");
  const backdrop = document.querySelector("#drawerBackdrop");

  backdrop?.setAttribute("tabindex", "-1");
  document.querySelector("#team-title")?.setAttribute("tabindex", "-1");
  document.querySelector("#overview-title")?.setAttribute("tabindex", "-1");

  function normalizeDepartmentCards() {
    if (!teamGrid) return;
    [...teamGrid.querySelectorAll(":scope > .department-card")].forEach((button) => {
      button.removeAttribute("role");
      button.style.width = "100%";
      button.style.height = "100%";
      const wrapper = document.createElement("div");
      wrapper.className = "department-item";
      wrapper.setAttribute("role", "listitem");
      wrapper.style.minWidth = "0";
      wrapper.style.height = "100%";
      button.before(wrapper);
      wrapper.append(button);
    });
  }

  normalizeDepartmentCards();
  if (teamGrid) {
    const observer = new MutationObserver(() => normalizeDepartmentCards());
    observer.observe(teamGrid, { childList: true });
  }
})();
