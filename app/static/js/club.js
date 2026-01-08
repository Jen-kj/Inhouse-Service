// Club UI - demo data is loaded from a single seed source on the server.

const store = {
  viewerUserId: null,
  users: [],
  clubs: [],
  memberships: [],
  myClubs: [],
  events: [],
  joinApprovals: [],
  expenses: [],
  posts: {},
  rsvps: {},
  pendingClubRequests: [],
  isAdmin: false,
  ui: {
    activeTab: "discover",
    selectedCategory: "전체",
    search: "",
    adminTab: "approvals",
    detailTab: "overview",
    calendar: {
      monthOffset: 0,
      category: "",
      format: "",
      club: "all",
      search: "",
      selectedDate: "",
    },
  },
};

const refs = {
  tabButtons: Array.from(document.querySelectorAll(".club-tab-btn")),
  tabPanels: Array.from(document.querySelectorAll("[data-tab-panel]")),
  shellMeta: document.getElementById("club-shell-meta"),
  createCta: document.getElementById("club-create-cta"),
  adminToggle: document.getElementById("club-admin-toggle"),
  searchInput: document.getElementById("club-search"),
  categoryButtons: Array.from(document.querySelectorAll(".club-chip")),
  grid: document.getElementById("club-grid"),
  myList: document.getElementById("club-my-list"),
  myEvents: document.getElementById("club-my-events"),
  calendarLabel: document.getElementById("club-calendar-label"),
  calendarPrev: document.getElementById("club-calendar-prev"),
  calendarNext: document.getElementById("club-calendar-next"),
  calendarView: document.getElementById("club-calendar-view"),
  calendarCategory: document.getElementById("club-calendar-category"),
  calendarFormat: document.getElementById("club-calendar-format"),
  calendarClub: document.getElementById("club-calendar-club"),
  calendarSearch: document.getElementById("club-calendar-search"),
  calendarPanelTitle: document.getElementById("club-calendar-panel-title"),
  calendarPanelList: document.getElementById("club-calendar-panel-list"),
  calendarGrid: document.getElementById("club-calendar-grid"),
  calendarPanel: document.getElementById("club-calendar-panel"),
  calendarCreate: document.getElementById("club-calendar-create"),
  adminLocked: document.getElementById("club-admin-locked"),
  adminPanel: document.getElementById("club-admin-panel"),
  adminTabButtons: Array.from(document.querySelectorAll(".club-admin-btn")),
  adminPanels: Array.from(document.querySelectorAll("[data-admin-panel]")),
  joinApprovals: document.getElementById("club-join-approvals"),
  createApprovals: document.getElementById("club-create-approvals"),
  budgetMonth: document.getElementById("club-budget-month"),
  budgetClub: document.getElementById("club-budget-club"),
  budgetSummary: document.getElementById("club-budget-summary"),
  expenseList: document.getElementById("club-expense-list"),
  expenseAdd: document.getElementById("club-expense-add"),
  postsClub: document.getElementById("club-posts-club"),
  postsList: document.getElementById("club-posts-list"),
  postsAdd: document.getElementById("club-posts-add"),
  overlay: document.getElementById("club-overlay"),
  panel: document.getElementById("club-panel"),
  panelClose: document.getElementById("club-panel-close"),
  panelTabs: Array.from(document.querySelectorAll(".club-panel-tab")),
  panelSections: Array.from(document.querySelectorAll("[data-panel-section]")),
  detailTitle: document.getElementById("club-detail-title"),
  detailCategory: document.getElementById("club-detail-category"),
  detailTags: document.getElementById("club-detail-tags"),
  detailJoin: document.getElementById("club-detail-join"),
  detailPosts: document.getElementById("club-detail-posts"),
  detailEvents: document.getElementById("club-detail-events"),
  detailRequests: document.getElementById("club-detail-requests"),
  detailAdmins: document.getElementById("club-detail-admins"),
  detailMembers: document.getElementById("club-detail-members"),
  detailRequestsList: document.getElementById("club-detail-requests-list"),
  modal: document.getElementById("club-modal"),
  modalTitle: document.getElementById("club-modal-title"),
  modalContent: document.getElementById("club-modal-content"),
  modalActions: document.getElementById("club-modal-actions"),
  modalClose: document.getElementById("club-modal-close"),
  toast: document.getElementById("club-toast"),
  createModal: document.getElementById("club-create-modal"),
  createClose: document.getElementById("club-create-close"),
  createCancel: document.getElementById("club-create-cancel"),
  createForm: document.getElementById("club-create-form"),
};

let selectedClub = null;

function toISO(date) {
  return date.toISOString().slice(0, 10);
}

function showToast(message) {
  refs.toast.textContent = message;
  refs.toast.classList.add("is-open");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => refs.toast.classList.remove("is-open"), 2000);
}

function openModal({ title, content, actions }) {
  refs.modalTitle.textContent = title || "알림";
  refs.modalContent.innerHTML = content || "";
  refs.modalActions.innerHTML = "";
  (actions || []).forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `btn ${action.className || "club-btn-outline"}`;
    button.textContent = action.label;
    button.addEventListener("click", () => {
      action.onClick?.();
      closeModal();
    });
    refs.modalActions.appendChild(button);
  });
  refs.modal.hidden = false;
}

function closeModal() {
  refs.modal.hidden = true;
}

function openPanel(club) {
  selectedClub = club;
  store.ui.detailTab = "overview";
  refs.overlay.hidden = false;
  refs.panel.hidden = false;
  renderDetail();
}

function closePanel() {
  refs.overlay.hidden = true;
  refs.panel.hidden = true;
}

function setActiveTab(tab) {
  store.ui.activeTab = tab;
  render();
}

function renderTabs() {
  refs.tabButtons.forEach((btn) => btn.classList.toggle("is-active", btn.dataset.tab === store.ui.activeTab));
  refs.tabPanels.forEach((panel) => (panel.hidden = panel.dataset.tabPanel !== store.ui.activeTab));
  const labelMap = { discover: "DISCOVER", my: "MY CLUBS", calendar: "CALENDAR", admin: "ADMIN" };
  if (refs.shellMeta) refs.shellMeta.textContent = labelMap[store.ui.activeTab] || "DISCOVER";
}

function filterClubs() {
  const keyword = store.ui.search.trim();
  const category = store.ui.selectedCategory;
  return store.clubs.filter((club) => {
    const matchCategory = category === "전체" || club.category === category;
    const matchKeyword = !keyword || club.name.includes(keyword);
    return matchCategory && matchKeyword;
  });
}

function renderClubCards(list, options = {}) {
  const { showJoin = true } = options;
  if (!list.length) {
    return '<div class="club-empty">조건에 맞는 동아리가 없습니다.</div>';
  }

  return list
    .map((club) => {
      const badgeClass = club.category === "운동/건강" ? "club-badge--sport" : "club-badge--hobby";
      return `
        <article class="club-card" data-club="${club.name}">
          <h3 class="club-name">${club.name}</h3>
          <div class="club-badge ${badgeClass}">${club.category}</div>
          <p class="club-mood">${club.moodLine || ""}</p>
          <div class="club-chips">
            ${(club.tags || []).slice(0, 3).map((t) => `<span class="club-chip-mini">${t}</span>`).join("")}
          </div>
          <div class="club-divider"></div>
          <div class="club-card-footer">
            <div class="club-member">👥 ${club.memberHint || "0명"}</div>
            <div class="club-card-actions">
              ${
                showJoin
                  ? '<button class="btn club-btn-primary" data-action="join" type="button">가입 신청</button>'
                  : ""
              }
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderDiscover() {
  if (refs.searchInput) refs.searchInput.value = store.ui.search;
  refs.categoryButtons.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.category === store.ui.selectedCategory);
  });
  refs.grid.innerHTML = renderClubCards(filterClubs(), { showJoin: true });
}

function renderMyClubs() {
  const myClubs = store.clubs.filter((club) => store.myClubs.includes(club.name));
  refs.myList.innerHTML = myClubs.length
    ? myClubs
        .map(
          (club) => `
            <div class="club-mini-card" data-club="${club.name}">
              <div class="club-badge ${club.category === "운동/건강" ? "club-badge--sport" : "club-badge--hobby"}">${club.category}</div>
              <div><strong>${club.name}</strong></div>
              <div class="club-mini-actions">
                <button class="btn club-btn-outline" data-action="detail" type="button">상세보기</button>
                <button class="btn club-btn-primary" data-action="schedule" type="button">달력에서 보기</button>
              </div>
            </div>
          `
        )
        .join("")
    : '<div class="club-empty">가입한 동아리가 없습니다.</div>';

  const upcoming = store.events.filter((e) => store.myClubs.includes(e.clubName)).slice(0, 3);
  refs.myEvents.innerHTML = upcoming.length
    ? upcoming.map((event) => renderEventItem(event, true)).join("")
    : '<div class="club-empty">가까운 일정이 없습니다.</div>';
}

function getCalendarDate() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth() + store.ui.calendar.monthOffset, 1);
}

function getFilteredEvents() {
  const { category, format, club, search } = store.ui.calendar;
  return store.events.filter((event) => {
    const matchCategory = !category || event.category === category;
    const matchFormat = !format || event.format === format;
    const matchClub =
      club === "all" ||
      (club === "mine" && store.myClubs.includes(event.clubName)) ||
      event.clubName === club;
    const matchSearch =
      !search ||
      event.title.includes(search) ||
      event.clubName.includes(search);
    return matchCategory && matchFormat && matchClub && matchSearch;
  });
}

function renderCalendar() {
  const calendarDate = getCalendarDate();
  const year = calendarDate.getFullYear();
  const month = calendarDate.getMonth();

  if (refs.calendarLabel) {
    refs.calendarLabel.textContent = `${year}.${String(month + 1).padStart(2, "0")}`;
  }

  if (refs.calendarCategory) refs.calendarCategory.value = store.ui.calendar.category;
  if (refs.calendarFormat) refs.calendarFormat.value = store.ui.calendar.format;

  if (refs.calendarClub) {
    const clubOptions = [
      { value: "all", label: "전체" },
      { value: "mine", label: "내 동아리" },
      ...store.clubs.map((club) => ({ value: club.name, label: club.name })),
    ];
    refs.calendarClub.innerHTML = clubOptions
      .map((opt) => `<option value="${opt.value}">${opt.label}</option>`)
      .join("");
    refs.calendarClub.value = store.ui.calendar.club;
  }

  if (refs.calendarSearch) refs.calendarSearch.value = store.ui.calendar.search;

  const firstOfMonth = new Date(year, month, 1);
  const start = new Date(firstOfMonth);
  start.setDate(start.getDate() - start.getDay());

  const events = getFilteredEvents();
  const cells = [];

  for (let i = 0; i < 42; i += 1) {
    const cellDate = new Date(start);
    cellDate.setDate(start.getDate() + i);
    const dateKey = toISO(cellDate);
    const inMonth = cellDate.getMonth() === month;
    const isSelected = store.ui.calendar.selectedDate === dateKey;

    const dayEvents = events.filter((event) => event.startDate <= dateKey && event.endDate >= dateKey);
    const visible = dayEvents.slice(0, 3);
    const overflowCount = Math.max(0, dayEvents.length - visible.length);

    const bars = visible
      .map((event) => {
        const isSports = event.category === "운동/건강";
        const segmentClass =
          event.startDate === dateKey && event.endDate === dateKey
            ? "singular"
            : event.startDate === dateKey
              ? "start"
              : event.endDate === dateKey
                ? "end"
                : "middle";
        return `<button class="club-event-bar ${isSports ? "is-sports" : "is-hobby"} ${segmentClass}" data-event-id="${event.id}" type="button">${event.title}</button>`;
      })
      .join("");

    const more = overflowCount ? `<div class="club-calendar-more">+${overflowCount} more</div>` : "";

    cells.push(`
      <div class="club-calendar-cell ${inMonth ? "" : "is-muted"} ${isSelected ? "is-selected" : ""}" data-date="${dateKey}">
        <div class="club-calendar-date">${cellDate.getDate()}</div>
        ${bars}
        ${more}
      </div>
    `);
  }

  if (refs.calendarGrid) refs.calendarGrid.innerHTML = cells.join("");
  renderCalendarPanel();
}

function renderCalendarPanel() {
  const selected = store.ui.calendar.selectedDate;
  if (!selected) {
    if (refs.calendarPanelTitle) refs.calendarPanelTitle.textContent = "날짜를 선택하세요";
    if (refs.calendarPanelList) refs.calendarPanelList.innerHTML = '<div class="club-empty">선택한 일정이 없습니다.</div>';
    return;
  }

  const events = getFilteredEvents().filter((event) => event.startDate <= selected && event.endDate >= selected);
  if (refs.calendarPanelTitle) refs.calendarPanelTitle.textContent = `${selected} 일정`;
  if (refs.calendarPanelList) {
    refs.calendarPanelList.innerHTML = events.length
      ? events.map((event) => renderEventItem(event, true)).join("")
      : '<div class="club-empty">해당 날짜에 일정이 없습니다.</div>';
  }
}

function openEventModal(event) {
  openModal({
    title: event.title,
    content: `
      <div style="display:grid;gap:6px;">
        <div>동아리: ${event.clubName}</div>
        <div>시간: ${event.time || "-"}</div>
        <div>장소: ${event.place || "-"}</div>
        <div>${event.description || ""}</div>
      </div>
    `,
    actions: [
      {
        label: "참여",
        className: "club-btn-primary",
        onClick: () => {
          store.rsvps[event.id] = "참여";
          showToast("RSVP: 참여");
          render();
        },
      },
      {
        label: "불참",
        className: "club-btn-outline",
        onClick: () => {
          store.rsvps[event.id] = "불참";
          showToast("RSVP: 불참");
          render();
        },
      },
    ],
  });
}

function renderAdmin() {
  if (!refs.adminToggle) return;
  refs.adminLocked.hidden = store.isAdmin;
  refs.adminPanel.hidden = !store.isAdmin;

  const availableTabs = new Set(refs.adminTabButtons.map((btn) => btn.dataset.adminTab).filter(Boolean));
  if (!availableTabs.has(store.ui.adminTab)) {
    store.ui.adminTab = refs.adminTabButtons[0]?.dataset.adminTab || "approvals";
  }

  refs.adminTabButtons.forEach((btn) => btn.classList.toggle("is-active", btn.dataset.adminTab === store.ui.adminTab));
  refs.adminPanels.forEach((panel) => (panel.hidden = panel.dataset.adminPanel !== store.ui.adminTab));

  if (refs.joinApprovals) {
    refs.joinApprovals.innerHTML = store.joinApprovals.length
      ? store.joinApprovals
          .map(
            (item) => `
              <div class="club-event" data-join-id="${item.id}">
                <div>클럽: ${item.clubName}</div>
                <div>요청자: ${item.applicant}</div>
                <div class="club-rsvp">
                  <button class="btn club-btn-outline" data-action="approve-join" type="button">승인</button>
                  <button class="btn club-btn-outline" data-action="reject-join" type="button">반려</button>
                </div>
              </div>
            `
          )
          .join("")
      : '<div class="club-empty">대기 중인 요청이 없습니다.</div>';
  }

  if (refs.createApprovals) {
    refs.createApprovals.innerHTML = store.pendingClubRequests.length
      ? store.pendingClubRequests
          .map(
            (item, index) => `
              <div class="club-event" data-create-index="${index}">
                <div>클럽명: ${item.name}</div>
                <div>카테고리: ${item.category}</div>
                <div>소개: ${item.moodLine}</div>
                <div class="club-rsvp">
                  <button class="btn club-btn-outline" data-action="approve-create" type="button">승인</button>
                  <button class="btn club-btn-outline" data-action="reject-create" type="button">반려</button>
                </div>
              </div>
            `
          )
          .join("")
      : '<div class="club-empty">새로운 개설 신청이 없습니다.</div>';
  }

  const clubOptions = store.clubs.map((club) => `<option value="${club.name}">${club.name}</option>`).join("");

  if (refs.postsClub) refs.postsClub.innerHTML = clubOptions;
  if (refs.budgetClub) refs.budgetClub.innerHTML = clubOptions;

  if (refs.budgetMonth) {
    const months = Array.from(new Set(store.expenses.map((exp) => exp.month).filter(Boolean))).sort().reverse();
    refs.budgetMonth.innerHTML = months.map((m) => `<option value="${m}">${m}</option>`).join("");
  }

  if (store.ui.adminTab === "budget" && refs.budgetClub && refs.budgetMonth) {
    const selectedClubName = refs.budgetClub.value || store.clubs[0]?.name;
    const selectedMonth = refs.budgetMonth.value;
    const expenses = store.expenses.filter(
      (exp) => exp.clubName === selectedClubName && (!selectedMonth || exp.month === selectedMonth)
    );
    const total = expenses.reduce((sum, exp) => sum + (Number(exp.amount) || 0), 0);

    if (refs.budgetSummary) {
      refs.budgetSummary.innerHTML = `
        <div class="club-summary-card">지출 건수: ${expenses.length}건</div>
        <div class="club-summary-card">총 지출: ${total.toLocaleString()}원</div>
      `;
    }

    if (refs.expenseList) {
      refs.expenseList.innerHTML = expenses.length
        ? expenses
            .map(
              (exp) =>
                `<div class="club-pill">${exp.title} · ${Number(exp.amount || 0).toLocaleString()}원${
                  exp.note ? ` · ${exp.note}` : ""
                }</div>`
            )
            .join("")
        : '<div class="club-empty">지출 내역이 없습니다.</div>';
    }
  }

  if (store.ui.adminTab === "posts" && refs.postsClub && refs.postsList) {
    const selectedPosts = refs.postsClub.value || store.clubs[0]?.name;
    const posts = store.posts[selectedPosts] || [];
    refs.postsList.innerHTML = posts.length
      ? posts
          .map(
            (post) => `
              <div class="club-event" data-post-id="${post.id}">
                <div>${post.type} · ${post.title}</div>
                <div class="club-rsvp">
                  <button class="btn club-btn-outline" data-action="delete-post" type="button">삭제</button>
                </div>
              </div>
            `
          )
          .join("")
      : '<div class="club-empty">작성된 글이 없습니다.</div>';
  }
}

function renderDetail() {
  if (!selectedClub) return;

  const availableTabs = new Set(refs.panelTabs.map((tab) => tab.dataset.panelTab).filter(Boolean));
  if (!availableTabs.has(store.ui.detailTab)) store.ui.detailTab = "overview";

  const userById = new Map(store.users.map((user) => [user.id, user]));
  const memberships = store.memberships.filter((m) => m.club_id === selectedClub.id);
  const adminMembers = memberships.filter((m) => m.status === "active" && m.role === "admin");
  const activeMembers = memberships.filter((m) => m.status === "active" && m.role !== "admin");
  const pendingMembers = memberships.filter((m) => m.status === "pending");

  refs.detailTitle.textContent = selectedClub.name;
  refs.detailCategory.textContent = selectedClub.category;
  refs.detailCategory.classList.remove("club-badge--sport", "club-badge--hobby");
  refs.detailCategory.classList.add(selectedClub.category === "운동/건강" ? "club-badge--sport" : "club-badge--hobby");
  refs.detailTags.textContent = `운영 방식: ${(selectedClub.tags || []).join(" / ")}`;
  refs.detailJoin.textContent = selectedClub.joinPolicy === "바로 가입" ? "가입하기" : "가입 요청";

  refs.panelTabs.forEach((tab) => tab.classList.toggle("is-active", tab.dataset.panelTab === store.ui.detailTab));
  refs.panelSections.forEach((section) => (section.hidden = section.dataset.panelSection !== store.ui.detailTab));

  refs.detailRequests.hidden = !(store.isAdmin && selectedClub.joinPolicy === "승인 필요");

  if (refs.detailAdmins) {
    refs.detailAdmins.innerHTML = adminMembers.length
      ? adminMembers
          .map((m) => `<div class="club-pill">운영진 - ${userById.get(m.user_id)?.name || m.user_id}</div>`)
          .join("")
      : '<div class="club-empty">운영진 정보가 없습니다.</div>';
  }

  if (refs.detailMembers) {
    refs.detailMembers.innerHTML = activeMembers.length
      ? activeMembers
          .map((m) => `<div class="club-pill">멤버 - ${userById.get(m.user_id)?.name || m.user_id}</div>`)
          .join("")
      : '<div class="club-empty">멤버가 없습니다.</div>';
  }

  if (refs.detailRequestsList) {
    refs.detailRequestsList.innerHTML = pendingMembers.length
      ? pendingMembers
          .map((m) => `<div class="club-pill">신청자 - ${userById.get(m.user_id)?.name || m.user_id}</div>`)
          .join("")
      : '<div class="club-empty">대기 중인 요청이 없습니다.</div>';
  }

  const posts = (store.posts[selectedClub.name] || []).slice(0, 3);
  refs.detailPosts.innerHTML = posts.length
    ? posts.map((p) => `<div class="club-pill">${p.type} · ${p.title}</div>`).join("")
    : '<div class="club-empty">등록된 글이 없습니다.</div>';

  const clubEvents = store.events.filter((event) => event.clubName === selectedClub.name);
  refs.detailEvents.innerHTML = clubEvents.length
    ? clubEvents.map((event) => renderEventItem(event, true)).join("")
    : '<div class="club-empty">예정된 일정이 없습니다.</div>';
}

function renderEventItem(event, includeRsvp) {
  const status = store.rsvps[event.id] || "";
  const meta = [event.startDate, event.time, event.clubName].filter(Boolean).join(" · ");
  return `
    <div class="club-event" data-event-id="${event.id}">
      <div class="club-event-main">
        <div><strong>${event.title}</strong></div>
        <div class="club-event-meta">${meta}</div>
      </div>
      ${
        includeRsvp
          ? `<div class="club-rsvp">
              ${["참여", "불참"]
                .map(
                  (label) =>
                    `<button class="btn club-btn-outline ${status === label ? "is-active" : ""}" data-rsvp="${label}" type="button">${label}</button>`
                )
                .join("")}
            </div>`
          : ""
      }
    </div>
  `;
}

function render() {
  renderTabs();
  if (store.ui.activeTab === "discover") renderDiscover();
  if (store.ui.activeTab === "my") renderMyClubs();
  if (store.ui.activeTab === "calendar") renderCalendar();
  if (store.ui.activeTab === "admin") renderAdmin();
  renderDetail();
}

async function loadSeed() {
  const response = await fetch("/api/clubs/seed");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();

  store.viewerUserId = data.viewer_user_id || null;
  store.users = Array.isArray(data.users) ? data.users : [];
  store.clubs = Array.isArray(data.clubs) ? data.clubs : [];
  store.memberships = Array.isArray(data.memberships) ? data.memberships : [];
  store.myClubs = Array.isArray(data.myClubs) ? data.myClubs : [];
  store.events = Array.isArray(data.events) ? data.events : [];
  store.joinApprovals = Array.isArray(data.joinApprovals) ? data.joinApprovals : [];
  store.posts = data.posts && typeof data.posts === "object" ? data.posts : {};
  store.expenses = Array.isArray(data.expenses) ? data.expenses : [];

  selectedClub = store.clubs[0] || null;
}

  async function init() {
  try {
    await loadSeed();
  } catch (error) {
    console.error("Failed to load club seed:", error);
    showToast("동아리 데이터를 불러오지 못했습니다.");
  }

  refs.tabButtons.forEach((btn) => btn.addEventListener("click", () => setActiveTab(btn.dataset.tab)));

  refs.categoryButtons.forEach((btn) =>
    btn.addEventListener("click", () => {
      store.ui.selectedCategory = btn.dataset.category;
      renderDiscover();
    })
  );

  refs.searchInput?.addEventListener("input", (event) => {
    store.ui.search = event.target.value;
    renderDiscover();
  });

  refs.grid?.addEventListener("click", (event) => {
    const card = event.target.closest(".club-card");
    if (!card) return;
    const club = store.clubs.find((c) => c.name === card.dataset.club);
    if (!club) return;

    if (event.target.dataset.action === "join") {
      const msg = club.joinPolicy === "바로 가입" ? "가입 완료" : "가입 요청 완료";
      showToast(msg);
      return;
    }

    openPanel(club);
  });

  refs.myList?.addEventListener("click", (event) => {
    const card = event.target.closest("[data-club]");
    if (!card) return;
    const club = store.clubs.find((c) => c.name === card.dataset.club);
    if (!club) return;
    if (event.target.dataset.action === "schedule") {
      store.ui.calendar.club = club.name;
      store.ui.activeTab = "calendar";
      store.ui.calendar.selectedDate = "";
      render();
      return;
    }
    openPanel(club);
  });

  refs.panelTabs.forEach((tab) =>
    tab.addEventListener("click", () => {
      store.ui.detailTab = tab.dataset.panelTab;
      renderDetail();
    })
  );

  refs.detailJoin?.addEventListener("click", () => {
    if (!selectedClub) return;
    const msg = selectedClub.joinPolicy === "바로 가입" ? "가입 완료" : "가입 요청 완료";
    showToast(msg);
  });

  refs.panelClose?.addEventListener("click", closePanel);
  refs.overlay?.addEventListener("click", closePanel);

  refs.adminToggle?.addEventListener("change", (event) => {
    store.isAdmin = Boolean(event.target.checked);
    renderAdmin();
  });

  refs.adminTabButtons.forEach((btn) =>
    btn.addEventListener("click", () => {
      store.ui.adminTab = btn.dataset.adminTab;
      renderAdmin();
    })
  );

  refs.joinApprovals?.addEventListener("click", (event) => {
    const row = event.target.closest("[data-join-id]");
    if (!row) return;
    if (event.target.dataset.action === "approve-join") {
      store.joinApprovals = store.joinApprovals.filter((j) => j.id !== row.dataset.joinId);
      showToast("가입 승인 완료");
      renderAdmin();
    }
    if (event.target.dataset.action === "reject-join") {
      showToast("가입 요청 반려됨");
      store.joinApprovals = store.joinApprovals.filter((j) => j.id !== row.dataset.joinId);
      renderAdmin();
    }
  });

  refs.postsList?.addEventListener("click", (event) => {
    const row = event.target.closest("[data-post-id]");
    if (!row) return;
    if (event.target.dataset.action === "delete-post") {
      const clubName = refs.postsClub.value;
      store.posts[clubName] = (store.posts[clubName] || []).filter((p) => p.id !== row.dataset.postId);
      renderAdmin();
    }
  });

  refs.postsAdd?.addEventListener("click", () => {
    const clubName = refs.postsClub.value;
    openModal({
      title: "글 작성",
      content:
        '<input id="club-post-title" type="text" placeholder="제목" style="width:100%;margin-bottom:8px;" />' +
        '<select id="club-post-type" style="width:100%">' +
        '<option value="공지">공지</option>' +
        '<option value="모집">모집</option>' +
        '<option value="후기">후기</option>' +
        "</select>",
      actions: [
        {
          label: "등록",
          className: "club-btn-primary",
          onClick: () => {
            const title = document.getElementById("club-post-title").value.trim();
            const type = document.getElementById("club-post-type").value;
            if (!title) return;
            store.posts[clubName] = store.posts[clubName] || [];
            store.posts[clubName].unshift({ id: `post-${Date.now()}`, type, title });
            renderAdmin();
          },
        },
      ],
    });
  });

  refs.expenseAdd?.addEventListener("click", () => {
    if (!refs.budgetClub || !refs.budgetMonth) return;
    openModal({
      title: "지출 추가",
      content:
        '<input id="club-expense-title" type="text" placeholder="항목" style="width:100%;margin-bottom:8px;" />' +
        '<input id="club-expense-amount" type="number" inputmode="numeric" placeholder="금액" style="width:100%;margin-bottom:8px;" />' +
        '<input id="club-expense-note" type="text" placeholder="메모 (옵션)" style="width:100%" />',
      actions: [
        {
          label: "저장",
          className: "club-btn-primary",
          onClick: () => {
            const title = document.getElementById("club-expense-title").value.trim();
            const amountValue = Number(document.getElementById("club-expense-amount").value);
            const note = document.getElementById("club-expense-note").value.trim();
            if (!title || !Number.isFinite(amountValue) || amountValue <= 0) return;
            store.expenses.push({
              id: `exp-${Date.now()}`,
              clubName: refs.budgetClub.value,
              month: refs.budgetMonth.value,
              title,
              amount: amountValue,
              note,
            });
            renderAdmin();
          },
        },
      ],
    });
  });

  refs.budgetClub?.addEventListener("change", renderAdmin);
  refs.budgetMonth?.addEventListener("change", renderAdmin);

  document.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-rsvp]");
    if (!btn) return;
    const card = event.target.closest("[data-event-id]");
    if (!card) return;
    store.rsvps[card.dataset.eventId] = btn.dataset.rsvp;
    showToast(`RSVP: ${btn.dataset.rsvp}`);
    render();
  });

  refs.calendarPrev?.addEventListener("click", () => {
    store.ui.calendar.monthOffset -= 1;
    renderCalendar();
  });

  refs.calendarNext?.addEventListener("click", () => {
    store.ui.calendar.monthOffset += 1;
    renderCalendar();
  });

  refs.calendarCategory?.addEventListener("change", (event) => {
    store.ui.calendar.category = event.target.value;
    renderCalendar();
  });

  refs.calendarFormat?.addEventListener("change", (event) => {
    store.ui.calendar.format = event.target.value;
    renderCalendar();
  });

  refs.calendarClub?.addEventListener("change", (event) => {
    store.ui.calendar.club = event.target.value;
    renderCalendar();
  });

  refs.calendarSearch?.addEventListener("input", (event) => {
    store.ui.calendar.search = event.target.value;
    renderCalendar();
  });

  refs.calendarGrid?.addEventListener("click", (event) => {
    const bar = event.target.closest(".club-event-bar");
    if (bar) {
      const eventData = store.events.find((item) => item.id === bar.dataset.eventId);
      if (eventData) openEventModal(eventData);
      return;
    }
    const cell = event.target.closest(".club-calendar-cell");
    if (!cell) return;
    store.ui.calendar.selectedDate = cell.dataset.date;
    renderCalendarPanel();
  });

  refs.createCta?.addEventListener("click", () => (refs.createModal.hidden = false));
  refs.createClose?.addEventListener("click", () => (refs.createModal.hidden = true));
  refs.createCancel?.addEventListener("click", () => (refs.createModal.hidden = true));
  refs.createModal?.addEventListener("click", (event) => {
    if (event.target === refs.createModal) refs.createModal.hidden = true;
  });

  refs.createForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(refs.createForm);
    const request = {
      name: String(formData.get("name") || "").trim(),
      category: String(formData.get("category") || "").trim(),
      moodLine: String(formData.get("moodLine") || "").trim(),
      format: String(formData.get("format") || "").trim(),
      joinPolicy: String(formData.get("joinPolicy") || "").trim(),
    };
    if (!request.name || !request.category || !request.moodLine) return;
    store.pendingClubRequests.push(request);
    refs.createForm.reset();
    refs.createModal.hidden = true;
    showToast("신청 완료");
    if (store.isAdmin) renderAdmin();
  });

  refs.modalClose?.addEventListener("click", closeModal);
  refs.modal?.addEventListener("click", (event) => {
    if (event.target === refs.modal) closeModal();
  });

  render();
}

init();
