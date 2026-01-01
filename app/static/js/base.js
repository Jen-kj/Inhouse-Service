(function () {
  const App = {};

  App.qs = (selector, root = document) => root.querySelector(selector);
  App.qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  App.todayISO = () => new Date().toISOString().slice(0, 10);

  App.formatHour = (hour) => `${String(hour).padStart(2, "0")}:00`;

  App.parseHour = (timeValue) => {
    if (!timeValue) return 0;
    const parts = timeValue.split(":");
    return Number(parts[0]);
  };

  App.fetchJson = async (url, options) => {
    const res = await fetch(url, options);
    let data = null;
    try {
      data = await res.json();
    } catch (error) {
      data = null;
    }
    return { res, data };
  };

  App.setActive = (elements, activeEl, className = "is-active") => {
    elements.forEach((el) => {
      el.classList.toggle(className, el === activeEl);
    });
  };

  App.bindToggleGroup = (selector, onChange) => {
    const buttons = App.qsa(selector);
    if (!buttons.length) return;
    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        App.setActive(buttons, button);
        if (onChange) onChange(button);
      });
    });
  };

  App.openModal = ({ panel, overlay, bodyClass }) => {
    if (overlay) overlay.classList.add("is-open");
    if (panel) panel.classList.add("is-open");
    if (panel) panel.setAttribute("aria-hidden", "false");
    if (overlay) overlay.setAttribute("aria-hidden", "false");
    if (bodyClass) document.body.classList.add(bodyClass);
  };

  App.closeModal = ({ panel, overlay, bodyClass }) => {
    if (overlay) overlay.classList.remove("is-open");
    if (panel) panel.classList.remove("is-open");
    if (panel) panel.setAttribute("aria-hidden", "true");
    if (overlay) overlay.setAttribute("aria-hidden", "true");
    if (bodyClass) document.body.classList.remove(bodyClass);
  };

  App.setupHeaderTime = () => {
    const el = document.getElementById("current-time");
    if (!el) return;

    const pad = (n) => String(n).padStart(2, "0");

    const tick = () => {
      const d = new Date();
      const y = d.getFullYear();
      const m = pad(d.getMonth() + 1);
      const day = pad(d.getDate());
      const hh = pad(d.getHours());
      const mm = pad(d.getMinutes());
      el.textContent = `현재: ${y}-${m}-${day} ${hh}:${mm}`;
    };

    tick();
    setInterval(tick, 1000);
  };

  App.initNav = () => {
    const groups = App.qsa(".nav-group");
    groups.forEach((group) => {
      const subnav = group.querySelector(".nav-subnav");
      if (!subnav) return;
      if (group.querySelector(".nav-sublink.is-active")) {
        subnav.classList.add("is-open");
      }
    });
  };

  window.App = App;

  document.addEventListener("DOMContentLoaded", () => {
    App.setupHeaderTime();
    App.initNav();
  });
})();
