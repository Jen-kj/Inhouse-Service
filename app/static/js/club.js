const store = {
  clubs: [
    {
      id: "club-tt",
      name: "탁구",
      category: "운동/건강",
      tags: ["혼합 운영", "입문", "편안/유쾌"],
      moodLine: "짧게 참여해도 좋은 실내 스포츠, 가볍게 땀 내며 친해져요",
      memberHint: "12명",
      snapshot: ["실내 활동", "단식·복식 모두", "점심/퇴근 후 참여"],
      joinPolicy: "바로 가입",
      format: "혼합 운영",
      icon: "TT",
      gradient: "linear-gradient(135deg, #ffb36b, #e56f4a)"
    },
    {
      id: "club-bk",
      name: "농구",
      category: "운동/건강",
      tags: ["정기 모임", "초중급", "경기 위주"],
      moodLine: "팀 스포츠 특유의 호흡, 함께 뛰며 자연스럽게 가까워져요",
      memberHint: "9명",
      snapshot: ["경기 중심", "실내/실외 선택", "팀플 교류"],
      joinPolicy: "바로 가입",
      format: "정기 모임",
      icon: "BK",
      gradient: "linear-gradient(135deg, #5f8dff, #3843a9)"
    },
    {
      id: "club-fs",
      name: "풋살",
      category: "운동/건강",
      tags: ["정기 모임", "초중급", "친목 위주"],
      moodLine: "실수해도 괜찮은 분위기, 즐겁게 뛰는 모임",
      memberHint: "10명",
      snapshot: ["야외 활동", "분위기 편안", "끝나고 교류"],
      joinPolicy: "바로 가입",
      format: "정기 모임",
      icon: "FS",
      gradient: "linear-gradient(135deg, #56c1a7, #1a8a72)"
    },
    {
      id: "club-cl",
      name: "클라이밍",
      category: "운동/건강",
      tags: ["혼합 운영", "초중급", "도전/성장"],
      moodLine: "코스 하나씩 정복하며 서로 응원하는 도전형 스포츠",
      memberHint: "8명",
      snapshot: ["난이도 선택", "기록/목표 공유", "주말 활동"],
      joinPolicy: "승인 필요",
      format: "혼합 운영",
      icon: "CL",
      gradient: "linear-gradient(135deg, #7c6cff, #4b3bb4)"
    },
    {
      id: "club-bg",
      name: "보드게임",
      category: "취미/문화",
      tags: ["정기 모임", "상관없음", "친목 위주"],
      moodLine: "룰은 천천히, 웃음은 크게—편하게 모여 즐겨요",
      memberHint: "7명",
      snapshot: ["입문자 안내", "게임 다양", "소규모 테이블"],
      joinPolicy: "바로 가입",
      format: "정기 모임",
      icon: "BG",
      gradient: "linear-gradient(135deg, #f8c86b, #b7772f)"
    },
    {
      id: "club-mv",
      name: "영화감상",
      category: "취미/문화",
      tags: ["정기 모임", "상관없음", "토론 중심"],
      moodLine: "같이 보고 이야기하며 취향을 넓히는 감상 모임",
      memberHint: "6명",
      snapshot: ["작품 투표", "감상 후 토크", "OTT/극장 혼합"],
      joinPolicy: "승인 필요",
      format: "정기 모임",
      icon: "MV",
      gradient: "linear-gradient(135deg, #ff9aa8, #b23b5a)"
    },
    {
      id: "club-bw",
      name: "볼링",
      category: "취미/문화",
      tags: ["정기 모임", "입문", "편안/유쾌"],
      moodLine: "응원과 하이파이브가 기본, 같이 치면 더 재밌어요",
      memberHint: "11명",
      snapshot: ["연습 + 이벤트 게임", "처음도 OK", "친목 분위기"],
      joinPolicy: "바로 가입",
      format: "정기 모임",
      icon: "BW",
      gradient: "linear-gradient(135deg, #ffbf6b, #f08a39)"
    },
    {
      id: "club-ar",
      name: "예술",
      category: "취미/문화",
      tags: ["정기 모임", "상관없음", "창작/표현"],
      moodLine: "잘 그리는 것보다, 다르게 보는 법을 함께 연습해요",
      memberHint: "5명",
      snapshot: ["기초부터 천천히", "주제/재료 실습", "공유/피드백"],
      joinPolicy: "승인 필요",
      format: "정기 모임",
      icon: "AR",
      gradient: "linear-gradient(135deg, #69c3ff, #356fb7)"
    }
  ],
  myClubs: ["탁구", "보드게임", "영화감상"],
  events: [],
  joinApprovals: [
    { id: "join-1", clubName: "클라이밍", applicant: "SH" },
    { id: "join-2", clubName: "영화감상", applicant: "KR" }
  ],
  rsvps: {},
  pendingClubRequests: [],
  expenses: [
    { id: "exp-1", clubName: "탁구", title: "공간 대여", note: "정산 예정" },
    { id: "exp-2", clubName: "보드게임", title: "소모품", note: "집계 중" }
  ],
  posts: {
    "탁구": [
      { id: "post-tt-1", type: "공지", title: "이번 주 실내 공간 공유" },
      { id: "post-tt-2", type: "모집", title: "입문자 환영 세션" },
      { id: "post-tt-3", type: "후기", title: "점심 랠리 후기" }
    ],
    "보드게임": [
      { id: "post-bg-1", type: "공지", title: "룰 설명 자료 업데이트" }
    ]
  },
  isAdmin: false,
  ui: {
    activeTab: "discover",
    selectedCategory: "전체",
    filters: { format: "", join: "" },
    search: "",
    calendar: {
      monthOffset: 0,
      category: "",
      format: "",
      club: "all",
      search: "",
      selectedDate: ""
    },
    adminTab: "approvals",
    detailTab: "overview"
  }
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
  calendarPrev: document.getElementById("club-calendar-prev"),
  calendarNext: document.getElementById("club-calendar-next"),
  calendarLabel: document.getElementById("club-calendar-label"),
  calendarCategory: document.getElementById("club-calendar-category"),
  calendarFormat: document.getElementById("club-calendar-format"),
  calendarClub: document.getElementById("club-calendar-club"),
  calendarSearch: document.getElementById("club-calendar-search"),
  calendarGrid: document.getElementById("club-calendar-grid"),
  calendarPanelTitle: document.getElementById("club-calendar-panel-title"),
  calendarPanelList: document.getElementById("club-calendar-panel-list"),
  calendarCreate: document.getElementById("club-calendar-create"),
  createModal: document.getElementById("club-create-modal"),
  createClose: document.getElementById("club-create-close"),
  createCancel: document.getElementById("club-create-cancel"),
  createForm: document.getElementById("club-create-form"),
  adminLocked: document.getElementById("club-admin-locked"),
  adminPanel: document.getElementById("club-admin-panel"),
  adminTabButtons: Array.from(document.querySelectorAll(".club-admin-btn")),
  adminPanels: Array.from(document.querySelectorAll("[data-admin-panel]")),
  joinApprovals: document.getElementById("club-join-approvals"),
  createApprovals: document.getElementById("club-create-approvals"),
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
  healthWidget: document.getElementById("club-health"),
  healthCta: document.getElementById("club-health-cta"),
  modal: document.getElementById("club-modal"),
  modalTitle: document.getElementById("club-modal-title"),
  modalContent: document.getElementById("club-modal-content"),
  modalActions: document.getElementById("club-modal-actions"),
  modalClose: document.getElementById("club-modal-close"),
  toast: document.getElementById("club-toast")
};

let selectedClub = store.clubs[0];

function toISO(date) {
  return date.toISOString().slice(0, 10);
}

function buildEvents() {
  const base = new Date();
  const addDays = (days) => {
    const d = new Date(base);
    d.setDate(d.getDate() + days);
    return d;
  };

  store.events = [
    {
      id: "evt-tt-1",
      title: "점심 가볍게 랠리",
      clubName: "탁구",
      category: "운동/건강",
      format: "혼합 운영",
      startDate: toISO(addDays(2)),
      endDate: toISO(addDays(2)),
      time: "12:30",
      place: "실내 코트",
      description: "가볍게 랠리하고 팀 구성은 현장에서 정해요."
    },
    {
      id: "evt-bk-1",
      title: "팀플 연습 경기",
      clubName: "농구",
      category: "운동/건강",
      format: "정기 모임",
      startDate: toISO(addDays(5)),
      endDate: toISO(addDays(5)),
      time: "18:30",
      place: "실외 코트",
      description: "워밍업 후 팀을 나눠 진행합니다."
    },
    {
      id: "evt-fs-1",
      title: "퇴근 후 풋살",
      clubName: "풋살",
      category: "운동/건강",
      format: "정기 모임",
      startDate: toISO(addDays(8)),
      endDate: toISO(addDays(8)),
      time: "19:00",
      place: "야외 구장",
      description: "초중급 템포로 진행합니다."
    },
    {
      id: "evt-bg-1",
      title: "라이트 보드게임",
      clubName: "보드게임",
      category: "취미/문화",
      format: "정기 모임",
      startDate: toISO(addDays(1)),
      endDate: toISO(addDays(1)),
      time: "12:00",
      place: "라운지",
      description: "룰 설명부터 함께 시작합니다."
    },
    {
      id: "evt-mv-1",
      title: "이번 주 작품 감상",
      clubName: "영화감상",
      category: "취미/문화",
      format: "정기 모임",
      startDate: toISO(addDays(10)),
      endDate: toISO(addDays(10)),
      time: "16:00",
      place: "미디어룸",
      description: "투표로 선정한 작품을 함께 봅니다."
    },
    {
      id: "evt-cl-1",
      title: "기초 루트 챌린지",
      clubName: "클라이밍",
      category: "운동/건강",
      format: "혼합 운영",
      startDate: toISO(addDays(12)),
      endDate: toISO(addDays(12)),
      time: "10:00",
      place: "클라이밍 센터",
      description: "서로 기록을 공유하며 진행해요."
    },
    {
      id: "evt-ar-1",
      title: "드로잉 연습",
      clubName: "예술",
      category: "취미/문화",
      format: "정기 모임",
      startDate: toISO(addDays(4)),
      endDate: toISO(addDays(6)),
      time: "15:00",
      place: "스튜디오",
      description: "주제에 맞춰 같이 그립니다."
    }
  ];
}
function setActiveTab(tab) {
  store.ui.activeTab = tab;
  render();
}

function showToast(message) {
  refs.toast.textContent = message;
  refs.toast.classList.add("is-open");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => refs.toast.classList.remove("is-open"), 2000);
}

function openModal({ title, content, actions = [] }) {
  refs.modalTitle.textContent = title;
  refs.modalContent.innerHTML = content;
  refs.modalActions.innerHTML = "";
  actions.forEach((action) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = action.label;
    btn.className = `btn ${action.className || "club-btn-outline"}`;
    btn.addEventListener("click", () => {
      action.onClick?.();
      closeModal();
    });
    refs.modalActions.appendChild(btn);
  });
  refs.modal.hidden = false;
}

function closeModal() {
  refs.modal.hidden = true;
}

function openCreateModal() {
  refs.createModal.hidden = false;
}

function closeCreateModal() {
  refs.createModal.hidden = true;
}

function openPanel(club) {
  selectedClub = club;
  store.ui.detailTab = "overview";
  renderDetail();
  refs.overlay.hidden = false;
  refs.panel.hidden = false;
}

function closePanel() {
  refs.overlay.hidden = true;
  refs.panel.hidden = true;
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
          <p class="club-mood">${club.moodLine}</p>
          <div class="club-chips">
            <span class="club-chip-mini">${club.tags[0]}</span>
            <span class="club-chip-mini">${club.tags[1]}</span>
            <span class="club-chip-mini">${club.tags[2]}</span>
          </div>
          <div class="club-divider"></div>
          <div class="club-card-footer">
            <div class="club-member">👥 ${club.memberHint || "활동 중"}</div>
            <div class="club-card-actions">
              <button class="btn club-btn-outline" data-action="detail" type="button">상세보기</button>
              ${showJoin
                ? '<button class="btn club-btn-primary" data-action="join" type="button">가입 신청</button>'
                : '<button class="btn club-btn-primary" data-action="join" type="button">가입 신청</button>'
              }
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderDiscover() {
  refs.searchInput.value = store.ui.search;
  refs.categoryButtons.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.category === store.ui.selectedCategory);
  });

  const filtered = filterClubs();
  refs.grid.innerHTML = renderClubCards(filtered);
}
function renderMyClubs() {
  const myClubs = store.clubs.filter((club) => store.myClubs.includes(club.name));
  const upcoming = store.events
    .filter((event) => store.myClubs.includes(event.clubName))
    .slice(0, 3);

  refs.myList.innerHTML = myClubs
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
    .join("");

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
  const viewDate = getCalendarDate();
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  refs.calendarLabel.textContent = `${year}.${String(month + 1).padStart(2, "0")}`;

  refs.calendarCategory.value = store.ui.calendar.category;
  refs.calendarFormat.value = store.ui.calendar.format;
  refs.calendarClub.value = store.ui.calendar.club;
  refs.calendarSearch.value = store.ui.calendar.search;
  refs.calendarCreate.hidden = !store.isAdmin;

  const events = getFilteredEvents().sort((a, b) => a.startDate.localeCompare(b.startDate));
  const firstDay = new Date(year, month, 1);
  const start = new Date(firstDay);
  start.setDate(firstDay.getDate() - firstDay.getDay());

  const cells = [];
  for (let i = 0; i < 42; i += 1) {
    const cellDate = new Date(start);
    cellDate.setDate(start.getDate() + i);
    const dateKey = toISO(cellDate);
    const dayEvents = events
      .filter((event) => event.startDate <= dateKey && event.endDate >= dateKey)
      .map((event) => {
        let position = "middle";
        if (event.startDate === dateKey && event.endDate === dateKey) {
          position = "singular";
        } else if (event.startDate === dateKey) {
          position = "start";
        } else if (event.endDate === dateKey) {
          position = "end";
        }
        return { ...event, position };
      });
    const inMonth = cellDate.getMonth() === month;
    const isSelected = store.ui.calendar.selectedDate === dateKey;
    const maxBars = 2;
    const visibleEvents = dayEvents.slice(0, maxBars);
    const overflowCount = Math.max(0, dayEvents.length - maxBars);

    const bars = visibleEvents
      .map((event) => {
        const categoryClass = event.category === "운동/건강" ? "is-sports" : "is-hobby";
        return `<div class="club-event-bar ${categoryClass} ${event.position}" data-event-id="${event.id}">${event.title}</div>`;
      })
      .join("");
    const more = overflowCount > 0
      ? `<div class="club-event-bar overflow">+${overflowCount} more</div>`
      : "";

    cells.push(`
      <div class="club-calendar-cell ${inMonth ? "" : "is-muted"} ${isSelected ? "is-selected" : ""}" data-date="${dateKey}">
        <div class="club-calendar-date">${cellDate.getDate()}</div>
        ${bars}
        ${more}
      </div>
    `);
  }

  refs.calendarGrid.innerHTML = cells.join("");
  renderCalendarPanel();
}

function renderCalendarPanel() {
  const selected = store.ui.calendar.selectedDate;
  if (!selected) {
    refs.calendarPanelTitle.textContent = "날짜를 선택하세요";
    refs.calendarPanelList.innerHTML = '<div class="club-empty">선택한 일정이 없습니다.</div>';
    return;
  }

  const events = getFilteredEvents().filter((event) => event.startDate <= selected && event.endDate >= selected);
  refs.calendarPanelTitle.textContent = `${selected} 일정`;
  refs.calendarPanelList.innerHTML = events.length
    ? events.map((event) => renderEventItem(event, true)).join("")
    : '<div class="club-empty">해당 날짜에 일정이 없습니다.</div>';
}

function renderAdmin() {
  refs.adminLocked.hidden = store.isAdmin;
  refs.adminPanel.hidden = !store.isAdmin;

  refs.adminTabButtons.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.adminTab === store.ui.adminTab);
  });

  refs.adminPanels.forEach((panel) => {
    panel.hidden = panel.dataset.adminPanel !== store.ui.adminTab;
  });

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

  const clubOptions = store.clubs.map((club) => `<option value="${club.name}">${club.name}</option>`).join("");
  refs.budgetClub.innerHTML = clubOptions;
  refs.postsClub.innerHTML = clubOptions;

  const selectedBudget = refs.budgetClub.value || store.clubs[0]?.name;
  refs.budgetSummary.innerHTML = `
    <div class="club-summary-card">사용액: 집계 예정</div>
    <div class="club-summary-card">잔액: 정산 예정</div>
  `;

  refs.expenseList.innerHTML = store.expenses
    .filter((exp) => exp.clubName === selectedBudget)
    .map((exp) => `<div class="club-pill">${exp.title} - ${exp.note}</div>`)
    .join("") || '<div class="club-empty">지출 내역이 없습니다.</div>';

  const selectedPosts = refs.postsClub.value || store.clubs[0]?.name;
  const posts = store.posts[selectedPosts] || [];
  refs.postsList.innerHTML = posts.length
    ? posts
        .map(
          (post) => `
            <div class="club-event" data-post-id="${post.id}">
              <div>${post.type} · ${post.title}</div>
              <div class="club-rsvp">
                <button class="btn club-btn-outline" data-action="edit-post" type="button">편집</button>
                <button class="btn club-btn-outline" data-action="delete-post" type="button">삭제</button>
              </div>
            </div>
          `
        )
        .join("")
    : '<div class="club-empty">작성된 글이 없습니다.</div>';
}

function renderDetail() {
  const club = selectedClub;
  refs.detailTitle.textContent = club.name;
  refs.detailCategory.textContent = club.category;
  refs.detailCategory.classList.remove("club-badge--sport", "club-badge--hobby");
  refs.detailCategory.classList.add(
    club.category === "운동/건강" ? "club-badge--sport" : "club-badge--hobby"
  );
  refs.detailTags.textContent = `운영 방식: ${club.tags.join(" / ")}`;
  refs.detailJoin.textContent = club.joinPolicy === "바로 가입" ? "가입하기" : "가입 요청";

  refs.panelTabs.forEach((tab) => {
    const isActive = tab.dataset.panelTab === store.ui.detailTab;
    tab.classList.toggle("is-active", isActive);
    if (tab.dataset.panelTab === "budget") {
      tab.hidden = !store.isAdmin;
    }
  });

  refs.panelSections.forEach((section) => {
    section.hidden = section.dataset.panelSection !== store.ui.detailTab;
  });

  const isSports = club.category === "운동/건강";
  refs.healthWidget.hidden = !isSports;
  refs.detailRequests.hidden = !(store.isAdmin && club.joinPolicy === "승인 필요");

  const posts = (store.posts[club.name] || []).slice(0, 3);
  refs.detailPosts.innerHTML = posts.length
    ? posts.map((post) => `<div class="club-pill">${post.type} · ${post.title}</div>`).join("")
    : '<div class="club-empty">등록된 글이 없습니다.</div>';

  const clubEvents = store.events.filter((event) => event.clubName === club.name);
  refs.detailEvents.innerHTML = clubEvents.length
    ? clubEvents.map((event) => renderEventItem(event, true)).join("")
    : '<div class="club-empty">예정된 일정이 없습니다.</div>';
}

function renderEventItem(event, includeRsvp) {
  const status = store.rsvps[event.id] || "";
  return `
    <div class="club-event" data-event-id="${event.id}">
      <div><strong>${event.title}</strong></div>
      <div>${event.startDate} · ${event.time || ""} · ${event.clubName}</div>
      ${includeRsvp ? `
        <div class="club-rsvp">
          ${["참여", "대기", "불참"].map((label) => `
            <button class="btn club-btn-outline ${status === label ? "is-active" : ""}" data-rsvp="${label}" type="button">${label}</button>
          `).join("")}
        </div>
      ` : ""}
    </div>
  `;
}

function renderTabs() {
  refs.tabButtons.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.tab === store.ui.activeTab);
  });

  refs.tabPanels.forEach((panel) => {
    panel.hidden = panel.dataset.tabPanel !== store.ui.activeTab;
  });

  const labelMap = {
    discover: "DISCOVER",
    my: "MY CLUBS",
    calendar: "CALENDAR",
    admin: "ADMIN"
  };
  refs.shellMeta.textContent = labelMap[store.ui.activeTab] || "DISCOVER";
}

function render() {
  renderTabs();
  if (store.ui.activeTab === "discover") {
    renderDiscover();
  }
  if (store.ui.activeTab === "my") {
    renderMyClubs();
  }
  if (store.ui.activeTab === "calendar") {
    renderCalendar();
  }
  if (store.ui.activeTab === "admin") {
    renderAdmin();
  }
  renderDetail();
}

function approveJoin(id) {
  store.joinApprovals = store.joinApprovals.filter((item) => item.id !== id);
  showToast("가입 승인 완료");
  renderAdmin();
}

function rejectJoin(id) {
  openModal({
    title: "반려 사유",
    content: '<textarea id="club-reject-reason" rows="3" style="width:100%" placeholder="사유 입력"></textarea>',
    actions: [
      {
        label: "반려",
        className: "club-btn-primary",
        onClick: () => {
          store.joinApprovals = store.joinApprovals.filter((item) => item.id !== id);
          showToast("가입 요청 반려됨");
          renderAdmin();
        }
      }
    ]
  });
}

function approveCreate(index) {
  const request = store.pendingClubRequests.splice(index, 1)[0];
  if (!request) return;

  const vibeByCategory = {
    "운동/건강": "도전/성장",
    "취미/문화": "창작/표현"
  };

  store.clubs.push({
    name: request.name,
    category: request.category,
    tags: [request.format, "입문", vibeByCategory[request.category] || "편안/유쾌"],
    moodLine: request.moodLine,
    snapshot: ["신규 제안", "입문자 환영", "자율 참여"],
    joinPolicy: request.joinPolicy,
    format: request.format,
    icon: request.name.slice(0, 2).toUpperCase(),
    gradient: "linear-gradient(135deg, #6db2ff, #375a9e)"
  });

  showToast("개설 신청 승인됨");
  render();
}

function rejectCreate(index) {
  openModal({
    title: "반려 사유",
    content: '<textarea rows="3" style="width:100%" placeholder="사유 입력"></textarea>',
    actions: [
      {
        label: "반려",
        className: "club-btn-primary",
        onClick: () => {
          store.pendingClubRequests.splice(index, 1);
          showToast("개설 신청 반려됨");
          renderAdmin();
        }
      }
    ]
  });
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
        }
      },
      {
        label: "대기",
        className: "club-btn-outline",
        onClick: () => {
          store.rsvps[event.id] = "대기";
          showToast("RSVP: 대기");
          render();
        }
      },
      {
        label: "불참",
        className: "club-btn-outline",
        onClick: () => {
          store.rsvps[event.id] = "불참";
          showToast("RSVP: 불참");
          render();
        }
      }
    ]
  });
}

function openCreateEventModal(dateValue) {
  const clubOptions = store.clubs.map((club) => `<option value="${club.name}">${club.name}</option>`).join("");
  openModal({
    title: "이벤트 생성",
    content: `
      <div style="display:grid;gap:10px;">
        <label>날짜<input id="club-event-date" type="date" value="${dateValue}" style="width:100%" /></label>
        <label>시간<input id="club-event-time" type="time" style="width:100%" /></label>
        <label>동아리<select id="club-event-club" style="width:100%">${clubOptions}</select></label>
        <label>형태<select id="club-event-format" style="width:100%">
          <option value="정기 모임">정기 모임</option>
          <option value="번개 중심">번개 중심</option>
          <option value="혼합 운영">혼합 운영</option>
        </select></label>
        <label>장소<input id="club-event-place" type="text" style="width:100%" /></label>
        <label>설명<textarea id="club-event-desc" rows="3" style="width:100%"></textarea></label>
      </div>
    `,
    actions: [
      {
        label: "저장",
        className: "club-btn-primary",
        onClick: () => {
          const date = document.getElementById("club-event-date").value;
          const time = document.getElementById("club-event-time").value;
          const clubName = document.getElementById("club-event-club").value;
        const format = document.getElementById("club-event-format").value;
        const place = document.getElementById("club-event-place").value;
        const description = document.getElementById("club-event-desc").value;
        const club = store.clubs.find((item) => item.name === clubName);
        if (!date || !club) return;

        store.events.push({
          id: `evt-${Date.now()}`,
          title: "신규 이벤트",
          clubName,
          category: club.category,
          format,
          startDate: date,
          endDate: date,
          time,
          place,
          description
        });

          store.ui.calendar.selectedDate = date;
          renderCalendar();
          showToast("이벤트 생성 완료");
        }
      }
    ]
  });
}
function init() {
  refs.modal.hidden = true;
  refs.panel.hidden = true;
  refs.overlay.hidden = true;
  refs.createModal.hidden = true;

  buildEvents();

  store.ui.calendar.selectedDate = toISO(new Date());

  refs.tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
  });

  refs.createCta.addEventListener("click", openCreateModal);
  refs.createClose.addEventListener("click", closeCreateModal);
  refs.createCancel.addEventListener("click", closeCreateModal);

  refs.adminToggle.addEventListener("change", (event) => {
    store.isAdmin = event.target.checked;
    render();
  });

  refs.searchInput.addEventListener("input", (event) => {
    store.ui.search = event.target.value;
    renderDiscover();
  });

  refs.categoryButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      store.ui.selectedCategory = btn.dataset.category;
      renderDiscover();
    });
  });

  refs.grid.addEventListener("click", (event) => {
    const card = event.target.closest(".club-card");
    if (!card) return;
    const club = store.clubs.find((item) => item.name === card.dataset.club);
    if (!club) return;

    if (event.target.dataset.action === "detail") {
      openPanel(club);
    }
    if (event.target.dataset.action === "join") {
      const msg = club.joinPolicy === "바로 가입" ? "가입 완료" : "가입 요청 완료";
      showToast(msg);
    }
  });

  refs.myList.addEventListener("click", (event) => {
    const card = event.target.closest("[data-club]");
    if (!card) return;
    const club = store.clubs.find((item) => item.name === card.dataset.club);
    if (!club) return;

    if (event.target.dataset.action === "detail") {
      openPanel(club);
    }
    if (event.target.dataset.action === "schedule") {
      store.ui.calendar.club = club.name;
      store.ui.activeTab = "calendar";
      render();
    }
  });

  refs.calendarPrev.addEventListener("click", () => {
    store.ui.calendar.monthOffset -= 1;
    renderCalendar();
  });

  refs.calendarNext.addEventListener("click", () => {
    store.ui.calendar.monthOffset += 1;
    renderCalendar();
  });

  refs.calendarCategory.addEventListener("change", (event) => {
    store.ui.calendar.category = event.target.value;
    renderCalendar();
  });

  refs.calendarFormat.addEventListener("change", (event) => {
    store.ui.calendar.format = event.target.value;
    renderCalendar();
  });

  refs.calendarClub.addEventListener("change", (event) => {
    store.ui.calendar.club = event.target.value;
    renderCalendar();
  });

  refs.calendarSearch.addEventListener("input", (event) => {
    store.ui.calendar.search = event.target.value;
    renderCalendar();
  });

  refs.calendarGrid.addEventListener("click", (event) => {
    const bar = event.target.closest(".club-event-bar");
    if (bar && !bar.classList.contains("overflow")) {
      const eventData = store.events.find((item) => item.id === bar.dataset.eventId);
      if (eventData) {
        openEventModal(eventData);
      }
      return;
    }

    const cell = event.target.closest(".club-calendar-cell");
    if (!cell) return;
    store.ui.calendar.selectedDate = cell.dataset.date;
    renderCalendar();
  });

  refs.calendarPanelList.addEventListener("click", handleRsvpClick);
  refs.myEvents.addEventListener("click", handleRsvpClick);
  refs.detailEvents.addEventListener("click", handleRsvpClick);

  refs.calendarCreate.addEventListener("click", () => {
    const dateValue = store.ui.calendar.selectedDate || toISO(new Date());
    openCreateEventModal(dateValue);
  });

  refs.createForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(refs.createForm);
    const request = {
      name: formData.get("name").trim(),
      category: formData.get("category"),
      moodLine: formData.get("moodLine").trim(),
      format: formData.get("format"),
      joinPolicy: formData.get("joinPolicy"),
      schedule: formData.get("schedule").trim(),
      place: formData.get("place"),
      slack: formData.get("slack").trim(),
      flashOnly: formData.get("flashOnly") === "on"
    };

    store.pendingClubRequests.push(request);
    refs.createForm.reset();
    closeCreateModal();
    showToast("신청 완료");
    if (store.isAdmin) {
      renderAdmin();
    }
  });

  refs.adminTabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      store.ui.adminTab = btn.dataset.adminTab;
      renderAdmin();
    });
  });

  refs.joinApprovals.addEventListener("click", (event) => {
    const card = event.target.closest("[data-join-id]");
    if (!card) return;
    if (event.target.dataset.action === "approve-join") {
      approveJoin(card.dataset.joinId);
    }
    if (event.target.dataset.action === "reject-join") {
      rejectJoin(card.dataset.joinId);
    }
  });

  refs.createApprovals.addEventListener("click", (event) => {
    const card = event.target.closest("[data-create-index]");
    if (!card) return;
    const index = Number(card.dataset.createIndex);
    if (event.target.dataset.action === "approve-create") {
      approveCreate(index);
    }
    if (event.target.dataset.action === "reject-create") {
      rejectCreate(index);
    }
  });

  refs.expenseAdd.addEventListener("click", () => {
    openModal({
      title: "지출 추가",
      content: '<input id="club-expense-title" type="text" placeholder="항목" style="width:100%;margin-bottom:8px;" />' +
        '<input id="club-expense-note" type="text" placeholder="메모" style="width:100%" />',
      actions: [
        {
          label: "저장",
          className: "club-btn-primary",
          onClick: () => {
            const title = document.getElementById("club-expense-title").value.trim();
            const note = document.getElementById("club-expense-note").value.trim();
            if (!title) return;
            store.expenses.push({
              id: `exp-${Date.now()}`,
              clubName: refs.budgetClub.value,
              title,
              note: note || "정산 예정"
            });
            renderAdmin();
          }
        }
      ]
    });
  });

  refs.budgetClub.addEventListener("change", renderAdmin);
  refs.postsClub.addEventListener("change", renderAdmin);

  refs.postsAdd.addEventListener("click", () => {
    const clubName = refs.postsClub.value;
    openModal({
      title: "글 작성",
      content: '<input id="club-post-title" type="text" placeholder="제목" style="width:100%;margin-bottom:8px;" />' +
        '<select id="club-post-type" style="width:100%">' +
        '<option value="공지">공지</option>' +
        '<option value="모집">모집</option>' +
        '<option value="후기">후기</option>' +
        '</select>',
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
          }
        }
      ]
    });
  });

  refs.postsList.addEventListener("click", (event) => {
    const card = event.target.closest("[data-post-id]");
    if (!card) return;
    const clubName = refs.postsClub.value;
    const posts = store.posts[clubName] || [];
    const post = posts.find((item) => item.id === card.dataset.postId);
    if (!post) return;

    if (event.target.dataset.action === "delete-post") {
      store.posts[clubName] = posts.filter((item) => item.id !== post.id);
      renderAdmin();
    }

    if (event.target.dataset.action === "edit-post") {
      openModal({
        title: "글 편집",
        content: `<input id="club-post-title" type="text" value="${post.title}" style="width:100%;margin-bottom:8px;" />` +
          `<select id="club-post-type" style="width:100%">` +
          `<option value="공지" ${post.type === "공지" ? "selected" : ""}>공지</option>` +
          `<option value="모집" ${post.type === "모집" ? "selected" : ""}>모집</option>` +
          `<option value="후기" ${post.type === "후기" ? "selected" : ""}>후기</option>` +
          `</select>`,
        actions: [
          {
            label: "저장",
            className: "club-btn-primary",
            onClick: () => {
              post.title = document.getElementById("club-post-title").value.trim();
              post.type = document.getElementById("club-post-type").value;
              renderAdmin();
            }
          }
        ]
      });
    }
  });

  refs.panelTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      store.ui.detailTab = tab.dataset.panelTab;
      renderDetail();
    });
  });

  refs.detailJoin.addEventListener("click", () => {
    const msg = selectedClub.joinPolicy === "바로 가입" ? "가입 완료" : "가입 요청 완료";
    showToast(msg);
  });

  refs.panelClose.addEventListener("click", closePanel);
  refs.overlay.addEventListener("click", closePanel);

  refs.healthCta.addEventListener("click", () => {
    openModal({
      title: "번개 이벤트 생성",
      content: "오늘 같이 운동 모집을 위한 템플릿입니다.",
      actions: [{ label: "확인", className: "club-btn-primary" }]
    });
  });

  refs.modalClose.addEventListener("click", closeModal);
  refs.modal.addEventListener("click", (event) => {
    if (event.target === refs.modal) {
      closeModal();
    }
  });

  refs.createModal.addEventListener("click", (event) => {
    if (event.target === refs.createModal) {
      closeCreateModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeModal();
      closePanel();
      closeCreateModal();
    }
  });

  const params = new URLSearchParams(window.location.search);
  const category = params.get("category");
  if (["전체", "운동/건강", "취미/문화"].includes(category)) {
    store.ui.selectedCategory = category;
  }

  refs.calendarClub.innerHTML = [
    '<option value="all">전체</option>',
    '<option value="mine">내 동아리만</option>',
    ...store.clubs.map((club) => `<option value="${club.name}">${club.name}</option>`)
  ].join("");

  render();
}

function handleRsvpClick(event) {
  const btn = event.target.closest("button[data-rsvp]");
  if (!btn) return;
  const card = event.target.closest("[data-event-id]");
  if (!card) return;
  store.rsvps[card.dataset.eventId] = btn.dataset.rsvp;
  showToast(`RSVP: ${btn.dataset.rsvp}`);
  render();
}

init();
