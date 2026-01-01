const CATEGORY_OPTIONS = [
  { value: "IT", label: "IT 지원", team: "보안팀" },
  { value: "PURCHASE", label: "물품 구매", team: "경영지원팀" },
  { value: "FACILITY", label: "시설 수리", team: "총무팀" }
];

const STATUS_OPTIONS = [
  { value: "PENDING", label: "대기", badgeClass: "sd-badge-pending" },
  { value: "APPROVED", label: "승인", badgeClass: "sd-badge-approved" },
  { value: "REJECTED", label: "반려", badgeClass: "sd-badge-rejected" },
  { value: "COMPLETED", label: "완료", badgeClass: "sd-badge-completed" }
];

const URGENCY_OPTIONS = [
  { value: "LOW", label: "낮음", className: "sd-urgency-low" },
  { value: "NORMAL", label: "보통", className: "sd-urgency-normal" },
  { value: "URGENT", label: "긴급", className: "sd-urgency-urgent" }
];

const state = {
  category: "",
  status: "",
  q: "",
  sort: "newest",
  summaryMode: "category",
  mode: "user"
};

let searchTimer = null;
let summaryData = null;
let lastRequests = [];

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const ui = {
  summaryGrid: $("#sd-summary-grid"),
  tableBody: $("#sd-table-body"),
  totalCount: $("#sd-total-count"),
  sort: $("#sd-sort"),
  category: $("#sd-category"),
  status: $("#sd-status"),
  query: $("#sd-q"),
  newBtn: $("#sd-new-ticket"),
  overlay: $("#sd-overlay"),
  panel: $("#sd-panel"),
  panelClose: $("#sd-panel-close"),
  form: $("#sd-form"),
  cancelBtn: $("#sd-cancel"),
  filterPills: $("#sd-filter-pills"),
  resetBtn: $("#sd-reset")
};

function getCategoryInfo(value) {
  return CATEGORY_OPTIONS.find((c) => c.value === value);
}

function getStatusInfo(value) {
  return STATUS_OPTIONS.find((s) => s.value === value);
}

function getUrgencyInfo(value) {
  return URGENCY_OPTIONS.find((u) => u.value === value);
}

function syncUIFromFilters() {
  ui.sort.value = state.sort;
  ui.category.value = state.category;
  ui.status.value = state.status;
  ui.query.value = state.q;

  $$(".sd-toggle-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.mode === state.summaryMode);
  });

  $$(".sd-mode-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.mode === state.mode);
  });

  renderFilterPills();
}

function applyFiltersFromUI() {
  state.sort = ui.sort.value;
  state.category = ui.category.value;
  state.status = ui.status.value;
  state.q = ui.query.value.trim();
  syncUIFromFilters();
  fetchRequests();
}

async function fetchSummary() {
  const res = await fetch("/api/service-desk/summary");
  const data = await res.json();
  summaryData = data.summary;
  renderSummary();
}

async function fetchRequests() {
  const params = new URLSearchParams();
  if (state.category) params.set("category", state.category);
  if (state.status) params.set("status", state.status);
  if (state.q) params.set("q", state.q);
  if (state.sort) params.set("sort", state.sort);

  const res = await fetch(`/api/service-desk/requests?${params.toString()}`);
  const data = await res.json();
  lastRequests = data.requests || [];
  renderTable(lastRequests);
}

function renderSummary() {
  if (!summaryData) return;

  const cards = [];
  ui.summaryGrid.classList.toggle("is-category", state.summaryMode === "category");
  ui.summaryGrid.classList.toggle("is-status", state.summaryMode === "status");

  if (state.summaryMode === "category") {
    CATEGORY_OPTIONS.forEach((category) => {
      const total = summaryData.by_category[category.value] || 0;
      const isSelected = state.category === category.value;
      const chipHtml = STATUS_OPTIONS.map((status) => {
        const count = summaryData.by_category_status[category.value][status.value] || 0;
        const isChipSelected = isSelected && state.status === status.value;
        return `
          <button class="sd-chip ${status.badgeClass} ${isChipSelected ? "is-active" : ""}" data-category="${category.value}" data-status="${status.value}" type="button">
            ${status.label} <span>${count}</span>
          </button>
        `;
      }).join("");

      cards.push(`
        <div class="sd-card ${isSelected ? "is-selected" : ""}" data-category="${category.value}">
          <div class="sd-card-title">${category.label}</div>
          <div class="sd-card-team">담당팀: ${category.team}</div>
          <div class="sd-card-count">${total}</div>
          <div class="sd-card-chips">${chipHtml}</div>
        </div>
      `);
    });
  } else {
    STATUS_OPTIONS.forEach((status) => {
      const total = summaryData.by_status[status.value] || 0;
      const isSelected = state.status === status.value;
      const statusClass = `sd-status-${status.value.toLowerCase()}`;
      const chipHtml = CATEGORY_OPTIONS.map((category) => {
        const count = summaryData.by_status_category[status.value][category.value] || 0;
        const isChipSelected = isSelected && state.category === category.value;
        return `
          <button class="sd-chip ${isChipSelected ? "is-active" : ""}" data-status="${status.value}" data-category="${category.value}" type="button">
            ${category.label} <span>${count}</span>
          </button>
        `;
      }).join("");

      cards.push(`
        <div class="sd-card ${statusClass} ${isSelected ? "is-selected" : ""}" data-status="${status.value}">
          <div class="sd-card-title">${status.label}</div>
          <div class="sd-card-count">${total}</div>
          <div class="sd-card-chips">${chipHtml}</div>
        </div>
      `);
    });
  }

  ui.summaryGrid.innerHTML = cards.join("");
  syncUIFromFilters();
}

function renderFilterPills() {
  const pills = [];
  const activeFilters = [];
  if (state.category) {
    const category = getCategoryInfo(state.category);
    pills.push(`
      <button class="sd-filter-pill" data-type="category" type="button">
        ${category ? category.label : state.category} <span>X</span>
      </button>
    `);
    activeFilters.push("category");
  }
  if (state.status) {
    const status = getStatusInfo(state.status);
    pills.push(`
      <button class="sd-filter-pill" data-type="status" type="button">
        ${status ? status.label : state.status} <span>X</span>
      </button>
    `);
    activeFilters.push("status");
  }
  if (state.q) {
    pills.push(`
      <button class="sd-filter-pill" data-type="q" type="button">
        ${state.q} <span>X</span>
      </button>
    `);
    activeFilters.push("q");
  }
  if (state.sort && state.sort !== "newest") {
    const sortLabelMap = {
      newest: "최신순",
      pending_oldest: "대기 오래된 순",
      urgency: "긴급도순"
    };
    pills.push(`
      <button class="sd-filter-pill" data-type="sort" type="button">
        ${sortLabelMap[state.sort] || state.sort} <span>X</span>
      </button>
    `);
    activeFilters.push("sort");
  }

  ui.filterPills.innerHTML = pills.join("") || "<span class=\"sd-filter-empty\">적용된 필터가 없습니다.</span>";
  ui.resetBtn.style.display = activeFilters.length ? "inline-flex" : "none";
}

function renderTable(tickets) {
  ui.totalCount.textContent = `총 ${tickets.length}건`;

  if (!tickets.length) {
    ui.tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="sd-empty">조건에 맞는 요청이 없습니다.</td>
      </tr>
    `;
    return;
  }

  const rows = tickets.map((ticket) => {
    const status = getStatusInfo(ticket.status);
    const category = getCategoryInfo(ticket.category);
    const urgency = getUrgencyInfo(ticket.urgency);
    const dateLabel = (ticket.created_at || "").split("T")[0] || "-";

    const actions = [];
    if (state.mode === "admin") {
      if (ticket.status === "PENDING") {
        actions.push({ label: "승인", next: "APPROVED" });
        actions.push({ label: "반려", next: "REJECTED" });
      }
      if (ticket.status === "APPROVED") {
        actions.push({ label: "완료", next: "COMPLETED" });
      }
    }

    const actionsHtml = actions.length
      ? `
        <div class="sd-actions">
          ${actions
            .map(
              (action) =>
                `<button class="sd-action" data-id="${ticket.id}" data-status="${action.next}" type="button">${action.label}</button>`
            )
            .join("")}
        </div>
      `
      : "";

    return `
      <tr>
        <td>${ticket.title}</td>
        <td>
          <span class="sd-urgency-text ${urgency ? urgency.className : "sd-urgency-normal"}">${
            urgency ? urgency.label : "보통"
          }</span>
        </td>
        <td>
          <div class="sd-status-cell">
            <span class="sd-badge ${status ? status.badgeClass : ""}">${status ? status.label : ticket.status}</span>
            ${actionsHtml}
          </div>
        </td>
        <td>${category ? category.label : ticket.category}</td>
        <td>${ticket.owner_team}</td>
        <td>${ticket.requester}</td>
        <td>${dateLabel}</td>
      </tr>
    `;
  });

  ui.tableBody.innerHTML = rows.join("");
}

function handleSummaryClick(event) {
  const chip = event.target.closest(".sd-chip");
  if (chip) {
    const nextCategory = chip.dataset.category || "";
    const nextStatus = chip.dataset.status || "";

    if (state.summaryMode === "category") {
      if (state.category === nextCategory && state.status === nextStatus) {
        state.status = "";
      } else {
        state.category = nextCategory;
        state.status = nextStatus;
      }
    } else {
      if (state.status === nextStatus && state.category === nextCategory) {
        state.category = "";
      } else {
        state.status = nextStatus;
        state.category = nextCategory;
      }
    }

    syncUIFromFilters();
    fetchRequests();
    return;
  }

  const card = event.target.closest(".sd-card");
  if (!card) return;

  if (state.summaryMode === "category") {
    const nextCategory = card.dataset.category || "";
    state.category = state.category === nextCategory ? "" : nextCategory;
  } else {
    const nextStatus = card.dataset.status || "";
    state.status = state.status === nextStatus ? "" : nextStatus;
  }

  syncUIFromFilters();
  fetchRequests();
}

function openPanel() {
  ui.overlay.classList.add("is-open");
  ui.panel.classList.add("is-open");
  document.body.classList.add("sd-panel-open");
  ui.panel.setAttribute("aria-hidden", "false");
  ui.overlay.setAttribute("aria-hidden", "false");
}

function closePanel() {
  ui.overlay.classList.remove("is-open");
  ui.panel.classList.remove("is-open");
  document.body.classList.remove("sd-panel-open");
  ui.panel.setAttribute("aria-hidden", "true");
  ui.overlay.setAttribute("aria-hidden", "true");
}

async function submitForm(event) {
  event.preventDefault();
  const formData = new FormData(ui.form);
  const res = await fetch("/api/service-desk/requests", {
    method: "POST",
    body: formData
  });

  if (!res.ok) {
    alert("요청 등록에 실패했습니다.");
    return;
  }

  ui.form.reset();
  ui.form.querySelector("input[name='urgency'][value='NORMAL']").checked = true;
  closePanel();
  fetchSummary();
  fetchRequests();
}

async function handleActionClick(event) {
  const btn = event.target.closest(".sd-action");
  if (!btn) return;

  const id = btn.dataset.id;
  const status = btn.dataset.status;

  const res = await fetch(`/api/service-desk/requests/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });

  if (!res.ok) {
    alert("상태 변경에 실패했습니다.");
    return;
  }

  fetchSummary();
  fetchRequests();
}

function resetFilters() {
  state.category = "";
  state.status = "";
  state.q = "";
  state.sort = "newest";
  state.summaryMode = "category";
  state.mode = "user";
  syncUIFromFilters();
  fetchSummary();
  fetchRequests();
}

function bindEvents() {
  ui.summaryGrid.addEventListener("click", handleSummaryClick);
  ui.tableBody.addEventListener("click", handleActionClick);
  ui.filterPills.addEventListener("click", (event) => {
    const pill = event.target.closest(".sd-filter-pill");
    if (!pill) return;
    const type = pill.dataset.type;
    if (type === "category") state.category = "";
    if (type === "status") state.status = "";
    if (type === "q") state.q = "";
    if (type === "sort") state.sort = "newest";
    syncUIFromFilters();
    fetchRequests();
  });

  $$(".sd-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.summaryMode = btn.dataset.mode;
      renderSummary();
    });
  });

  $$(".sd-mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.mode = btn.dataset.mode;
      syncUIFromFilters();
      renderTable(lastRequests);
    });
  });

  ui.sort.addEventListener("change", applyFiltersFromUI);
  ui.category.addEventListener("change", applyFiltersFromUI);
  ui.status.addEventListener("change", applyFiltersFromUI);

  ui.query.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.q = ui.query.value.trim();
      fetchRequests();
      syncUIFromFilters();
    }, 300);
  });

  ui.newBtn.addEventListener("click", openPanel);
  ui.panelClose.addEventListener("click", closePanel);
  ui.cancelBtn.addEventListener("click", closePanel);
  ui.overlay.addEventListener("click", closePanel);
  ui.form.addEventListener("submit", submitForm);
  ui.resetBtn.addEventListener("click", resetFilters);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && ui.panel.classList.contains("is-open")) {
      closePanel();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  syncUIFromFilters();
  fetchSummary();
  fetchRequests();
});
