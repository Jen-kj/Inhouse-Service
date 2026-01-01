const notaSpacePage = App.qs(".page[data-page]");

if (notaSpacePage) {
  const pageType = notaSpacePage.dataset.page;
  const bookingId = notaSpacePage.dataset.bookingId || "";
  const logId = notaSpacePage.dataset.logId || "";

  const HOURS = Array.from({ length: 10 }, (_, idx) => idx + 9);

  const state = {
    date: App.todayISO(),
    rooms: [],
    bookings: [],
    logs: [],
    monthDays: {},
    view: "daily"
  };

  const $ = (selector) => App.qs(selector);
  const bookingOverlay = $("#ns-booking-overlay");
  const bookingModal = $("#ns-booking-modal");
  const bookingOpenBtn = $("#ns-open-booking");
  const bookingCloseBtn = $("#ns-booking-close");
  const dailyView = $("#ns-daily-view");
  const monthlyView = $("#ns-monthly-view");
  const viewButtons = App.qsa(".ns-view-btn");
  const calendar = $("#ns-calendar");
  const dateInput = $("#ns-date");

  const openBookingModal = () => {
    App.openModal({
      panel: bookingModal,
      overlay: bookingOverlay,
      bodyClass: "ns-modal-open"
    });
  };

  const closeBookingModal = () => {
    App.closeModal({
      panel: bookingModal,
      overlay: bookingOverlay,
      bodyClass: "ns-modal-open"
    });
  };

  const bindBookingModalControls = () => {
    if (bookingOpenBtn) {
      bookingOpenBtn.addEventListener("click", () => {
        renderBookingForm();
        openBookingModal();
      });
    }
    if (bookingCloseBtn) {
      bookingCloseBtn.addEventListener("click", closeBookingModal);
    }
    if (bookingOverlay) {
      bookingOverlay.addEventListener("click", closeBookingModal);
    }
  };

  async function fetchRooms() {
    const { data } = await App.fetchJson("/api/nota-space/rooms");
    state.rooms = (data && data.rooms) || [];
  }

  async function fetchBookings(dateValue) {
    const { data } = await App.fetchJson(`/api/nota-space/bookings?date=${dateValue}`);
    state.bookings = (data && data.bookings) || [];
    state.date = (data && data.date) || dateValue;
  }

  async function fetchAllBookings() {
    const { data } = await App.fetchJson("/api/nota-space/bookings?all=1");
    state.bookings = (data && data.bookings) || [];
  }

  async function fetchMonthlyBookings(monthValue) {
    const { data } = await App.fetchJson(`/api/nota-space/bookings?month=${monthValue}`);
    state.monthDays = (data && data.days) || {};
  }

  async function fetchMeetingLogs() {
    const { data } = await App.fetchJson("/api/nota-space/meeting-logs");
    state.logs = (data && data.logs) || [];
  }

  async function fetchBookingDetail(idValue) {
    const { data } = await App.fetchJson(`/api/nota-space/bookings/${idValue}`);
    return data && data.booking ? data.booking : null;
  }

  async function fetchMeetingLogDetail(idValue) {
    const { data } = await App.fetchJson(`/api/nota-space/meeting-logs/${idValue}`);
    return data && data.log ? data.log : null;
  }

  const titleInput = $("#ns-meeting-title");
  const metaRoom = $("#ns-meta-room");
  const metaDate = $("#ns-meta-date");
  const metaTime = $("#ns-meta-time");
  const metaPresenter = $("#ns-meta-presenter");
  const directFields = $("#ns-direct-fields");
  const summaryInput = $("#ns-summary-input");
  const summaryText = $("#ns-summary-text");
  const summarySection = $("#ns-summary-section");
  const summaryMessage = $("#ns-summary-message");

  const directAuthor = $("#ns-log-author");
  const directDate = $("#ns-log-date");
  const directRoom = $("#ns-log-room");
  const directStart = $("#ns-log-start");
  const directEnd = $("#ns-log-end");

  const setSummaryText = (value) => {
    const text = (value || "").trim();
    if (summaryText) summaryText.textContent = text || "요약 결과가 없습니다.";
    if (summaryInput) summaryInput.value = text;
  };

  const setMeta = ({ room, date, time, presenter }) => {
    if (metaRoom) metaRoom.textContent = room || "-";
    if (metaDate) metaDate.textContent = date || "-";
    if (metaTime) metaTime.textContent = time || "-";
    if (metaPresenter) metaPresenter.textContent = presenter || "-";
  };

  const updateMetaFromInputs = () => {
    const room = directRoom && directRoom.value ? directRoom.value.trim() : "";
    const date = directDate && directDate.value ? directDate.value : "";
    const start = directStart && directStart.value ? directStart.value : "";
    const end = directEnd && directEnd.value ? directEnd.value : "";
    const time = start && end ? `${start} ~ ${end}` : "";
    const presenter = directAuthor && directAuthor.value ? directAuthor.value.trim() : "";
    setMeta({ room, date, time, presenter });
  };

  function renderTimeline() {
    const timeline = $("#ns-timeline");
    if (!timeline) return;

    const bookingsByRoom = new Map();
    state.bookings.forEach((booking) => {
      if (!bookingsByRoom.has(booking.room_id)) {
        bookingsByRoom.set(booking.room_id, []);
      }
      bookingsByRoom.get(booking.room_id).push(booking);
    });

    const headerCells = [`<div class="ns-room-col ns-room-head">Room / Time</div>`].concat(
      HOURS.map((hour) => `<div class="ns-hour-col">${App.formatHour(hour)}</div>`)
    );

    const rows = [
      `<div class="ns-timeline-row ns-timeline-header">${headerCells.join("")}</div>`
    ];

    state.rooms.forEach((room) => {
      const roomBookings = bookingsByRoom.get(room.id) || [];
      const capacityText = room.capacity
        ? (room.capacity >= 16 ? `${room.capacity}명 이상` : `${room.capacity}명`)
        : "-";
      const featureText = room.feature || "-";
      const rowCells = [
        `<div class="ns-room-col"><div class="ns-room-name">${room.name}<span class="ns-room-info" aria-hidden="true">ⓘ</span><span class="ns-room-tooltip"> ${featureText}\n수용 인원: ${capacityText}</span></div></div>`
      ];

      HOURS.forEach((hour) => {
        const booking = roomBookings.find((item) => {
          const startHour = App.parseHour(item.start_time);
          const endHour = App.parseHour(item.end_time);
          return hour >= startHour && hour < endHour;
        });

        if (booking) {
          const startHour = App.parseHour(booking.start_time);
          const content = hour === startHour ? booking.agenda : "";
          rowCells.push(`<div class="ns-slot is-booked">${content}</div>`);
        } else {
          rowCells.push(
            `<button class="ns-slot is-available" data-room="${room.id}" data-hour="${hour}" type="button">-</button>`
          );
        }
      });

      rows.push(`<div class="ns-timeline-row">${rowCells.join("")}</div>`);
    });

    timeline.innerHTML = `<div class="ns-timeline-grid">${rows.join("")}</div>`;
    bindRoomTooltips();
  }

  function bindRoomTooltips() {
    const tooltips = App.qsa(".ns-room-tooltip");
    if (!tooltips.length) return;

    tooltips.forEach((tooltip) => {
      tooltip.classList.remove("is-flip");
      const rect = tooltip.getBoundingClientRect();
      if (rect.bottom > window.innerHeight - 12) {
        tooltip.classList.add("is-flip");
      }
    });
  }

  function renderMonthlyCalendar() {
    if (!calendar) return;

    const [yearStr, monthStr] = state.date.split("-");
    const year = Number(yearStr);
    const monthIndex = Number(monthStr) - 1;
    const firstDay = new Date(year, monthIndex, 1);
    const startWeekday = firstDay.getDay();
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
    const monthKey = `${yearStr}-${monthStr}`;

    const weekdays = ["일", "월", "화", "수", "목", "금", "토"];
    const header = weekdays.map((day) => `<div class="ns-calendar-header">${day}</div>`).join("");

    const cells = [];
    for (let i = 0; i < startWeekday; i += 1) {
      cells.push(`<div class="ns-cal-cell ns-cal-empty"></div>`);
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const dayValue = String(day).padStart(2, "0");
      const dateKey = `${monthKey}-${dayValue}`;
      const count = state.monthDays[dateKey] || 0;
      const bookedClass = count ? "is-booked" : "";
      const selectedClass = dateKey === state.date ? "is-selected" : "";
      const countBadge = count ? `<div class="ns-cal-count">${count}</div>` : "";
      cells.push(
        `<button class="ns-cal-cell ${bookedClass} ${selectedClass}" data-date="${dateKey}" type="button"><div class="ns-cal-day">${day}</div>${countBadge}</button>`
      );
    }

    calendar.innerHTML = header + cells.join("");
  }

  function renderBookingForm() {
    const roomSelect = $("#ns-room");
    if (!roomSelect) return;
    roomSelect.innerHTML = state.rooms
      .map((room) => `<option value="${room.id}">${room.name}</option>`)
      .join("");

    const bookingDate = $("#ns-booking-date");
    const dateInput = $("#ns-date");
    if (bookingDate) bookingDate.value = state.date;
    if (dateInput) dateInput.value = state.date;
  }

  function renderBookingList() {
    const list = $("#ns-booking-list");
    if (!list) return;

    if (!state.bookings.length) {
      list.innerHTML = "<div class=\"ns-empty\">등록된 예약이 없습니다.</div>";
      return;
    }

    const header = `
      <div class="ns-booking-row ns-booking-header">
        <div>날짜</div>
        <div>시간</div>
        <div>회의실</div>
        <div>회의 주제</div>
        <div>발제자</div>
        <div>작업</div>
      </div>
    `;

    const rows = state.bookings
      .map((booking) => {
        const date = booking.date || state.date;
        const time = `${booking.start_time} ~ ${booking.end_time}`;
        return `
          <div class="ns-booking-row">
            <div>${date}</div>
            <div>${time}</div>
            <div>${booking.room_name}</div>
            <div>${booking.agenda}</div>
            <div>${booking.presenter}</div>
            <div><a class="ns-link" href="/nota-space/meeting-log/${booking.id}">회의록 작성 →</a></div>
          </div>
        `;
      })
      .join("");

    list.innerHTML = header + rows;
  }

  async function refreshBookingPage() {
    await fetchRooms();
    await fetchBookings(state.date);
    renderTimeline();
    renderBookingForm();
  }

  async function refreshBookingListPage() {
    await fetchAllBookings();
    renderBookingList();
  }

  async function refreshMonthlyView() {
    const monthKey = state.date.slice(0, 7);
    await fetchMonthlyBookings(monthKey);
    renderMonthlyCalendar();
  }

  function setView(view) {
    state.view = view;
    viewButtons.forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.view === view);
    });
    if (dailyView) dailyView.classList.toggle("is-hidden", view !== "daily");
    if (monthlyView) monthlyView.classList.toggle("is-hidden", view !== "monthly");

    if (view === "daily") {
      refreshBookingPage();
      return;
    }
    refreshMonthlyView();
  }

  function bindTimelineClick() {
    const timeline = $("#ns-timeline");
    if (!timeline) return;

    timeline.addEventListener("click", (event) => {
      const slot = event.target.closest(".ns-slot");
      if (!slot || slot.classList.contains("is-booked")) return;

      const roomId = slot.dataset.room;
      const hour = slot.dataset.hour;
      const roomSelect = $("#ns-room");
      const bookingDate = $("#ns-booking-date");
      const startTime = $("#ns-start");
      const endTime = $("#ns-end");

      if (roomSelect) roomSelect.value = roomId;
      if (bookingDate) bookingDate.value = state.date;
      if (startTime) startTime.value = App.formatHour(Number(hour));
      if (endTime) endTime.value = App.formatHour(Number(hour) + 1);
      openBookingModal();
    });
  }

  function bindCalendarClick() {
    if (!calendar) return;
    calendar.addEventListener("click", (event) => {
      const target = event.target.closest(".ns-cal-cell[data-date]");
      if (!target) return;
      const dateValue = target.dataset.date;
      if (!dateValue) return;
      state.date = dateValue;
      if (dateInput) dateInput.value = dateValue;
      setView("daily");
    });
  }

  function bindViewTabs() {
    if (!viewButtons.length) return;
    viewButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const nextView = btn.dataset.view || "daily";
        setView(nextView);
      });
    });
  }

  function bindDateInput() {
    if (!dateInput) return;
    dateInput.addEventListener("change", () => {
      if (!dateInput.value) return;
      state.date = dateInput.value;
      if (state.view === "daily") {
        refreshBookingPage();
        return;
      }
      refreshMonthlyView();
    });
  }

  function bindBookingForm() {
    const form = $("#ns-booking-form");
    const message = $("#ns-booking-message");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      if (!formData.get("date")) formData.set("date", state.date);

      const { res, data } = await App.fetchJson("/api/nota-space/bookings", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        if (message) message.textContent = (data && data.error) || "예약에 실패했습니다.";
        return;
      }

      form.reset();
      if (message) message.textContent = "예약이 등록되었습니다.";
      await fetchBookings(state.date);
      renderTimeline();
      renderBookingForm();
      renderBookingList();
      closeBookingModal();
    });
  }

  function renderMeetingLogTable() {
    const table = $("#ns-log-table");
    if (!table) return;

    if (!state.logs.length) {
      table.innerHTML = "<div class=\"ns-empty\">회의록이 없습니다.</div>";
      return;
    }

    const header = `
      <div class="ns-log-row ns-log-header">
        <div>날짜</div>
        <div>시간</div>
        <div>회의실</div>
        <div>회의 주제</div>
        <div>발제자</div>
        <div>작업</div>
      </div>
    `;

    const rows = state.logs
      .map((item) => {
        const date = item.meeting_date || "-";
        const time = item.start_time && item.end_time ? `${item.start_time} ~ ${item.end_time}` : "-";
        const room = item.room_name || "-";
        const agenda = item.agenda || "-";
        const presenter = item.presenter || "-";
        const actionLabel = item.has_log ? "회의록 보기 →" : "회의록 작성 →";
        const actionHref = item.has_log
          ? (item.booking_id ? `/nota-space/meeting-log/${item.booking_id}` : `/nota-space/meeting-log/entry/${item.log_id}`)
          : `/nota-space/meeting-log/${item.booking_id}`;

        return `
          <div class="ns-log-row">
            <div>${date}</div>
            <div>${time}</div>
            <div>${room}</div>
            <div>${agenda}</div>
            <div>${presenter}</div>
            <div><a class="ns-link" href="${actionHref}">${actionLabel}</a></div>
          </div>
        `;
      })
      .join("");

    table.innerHTML = header + rows;
  }

  async function refreshMeetingLogList() {
    await fetchMeetingLogs();
    renderMeetingLogTable();
  }

  async function loadMeetingLogForm() {
    const bookingInput = $("#ns-log-booking");

    if (bookingId) {
      const booking = await fetchBookingDetail(bookingId);
      if (!booking) return;

      if (bookingInput) bookingInput.value = bookingId;
      if (directFields) directFields.style.display = "none";
      if (titleInput) {
        titleInput.value = booking.agenda || "";
        titleInput.readOnly = true;
        titleInput.classList.add("is-readonly");
      }
      setMeta({
        room: booking.room_name,
        date: booking.date,
        time: `${booking.start_time} ~ ${booking.end_time}`,
        presenter: booking.presenter
      });
      const notesEl = $("#ns-notes");
      if (notesEl && booking.log && booking.log.notes) {
        notesEl.value = booking.log.notes;
      }
      if (booking.log && booking.log.summary) {
        setSummaryText(booking.log.summary);
      } else {
        setSummaryText("");
      }
      return;
    }

    if (logId) {
      const log = await fetchMeetingLogDetail(logId);
      if (!log) return;

      if (bookingInput) bookingInput.value = "";
      if (directFields) directFields.style.display = "block";
      const notesEl = $("#ns-notes");

      if (titleInput) {
        titleInput.value = log.title || "";
        titleInput.readOnly = false;
        titleInput.classList.remove("is-readonly");
      }
      if (directAuthor) directAuthor.value = log.author || "";
      if (directDate) directDate.value = log.meeting_date || "";
      if (directRoom) directRoom.value = log.room_name || "";
      if (directStart) directStart.value = log.start_time || "";
      if (directEnd) directEnd.value = log.end_time || "";
      if (notesEl) notesEl.value = log.notes || "";
      setSummaryText(log.summary || "");
      updateMetaFromInputs();
      return;
    }

    if (titleInput) {
      titleInput.value = "";
      titleInput.readOnly = false;
      titleInput.classList.remove("is-readonly");
    }
    if (directFields) directFields.style.display = "block";
    if (directDate) directDate.value = App.todayISO();
    updateMetaFromInputs();
    setSummaryText("");
  }

  function bindMeetingLogForm() {
    const form = $("#ns-log-form");
    const message = $("#ns-log-message");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const notes = String(formData.get("notes") || "").trim();
      if (!notes) {
        if (message) message.textContent = "회의 내용을 입력하세요.";
        return;
      }

      const { res, data } = await App.fetchJson("/api/nota-space/meeting-logs", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        if (message) message.textContent = (data && data.error) || "로그 저장에 실패했습니다.";
        return;
      }

      if (message) message.textContent = "로그가 저장되었습니다.";
    });
  }

  function bindSummaryGenerator() {
    const button = $("#ns-generate-summary");
    if (!button) return;

    button.addEventListener("click", async () => {
      const notesEl = $("#ns-notes");
      const notes = notesEl ? String(notesEl.value || "").trim() : "";
      if (!notes) {
        if (summaryMessage) summaryMessage.textContent = "회의 내용을 입력하세요.";
        return;
      }

      if (summaryMessage) summaryMessage.textContent = "요약을 생성 중입니다...";
      const { res, data } = await App.fetchJson("/nota-space/meeting-summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meeting_text: notes })
      });

      if (!res.ok) {
        if (summaryMessage) {
          summaryMessage.textContent = (data && data.error) || "요약 생성에 실패했습니다.";
        }
        return;
      }

      setSummaryText(data && data.summary_text ? data.summary_text : "");
      if (summaryMessage) summaryMessage.textContent = "요약이 생성되었습니다.";
      if (summarySection) summarySection.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    if (pageType === "room-booking") {
      await refreshBookingPage();
      bindViewTabs();
      bindCalendarClick();
      bindDateInput();
      bindTimelineClick();
      bindBookingForm();
      bindBookingModalControls();
    }

    if (pageType === "room-booking-list") {
      await refreshBookingListPage();
    }

    if (pageType === "meeting-log-list") {
      await refreshMeetingLogList();
    }

    if (pageType === "meeting-log-form") {
      await loadMeetingLogForm();
      bindMeetingLogForm();
      bindSummaryGenerator();
      const inputs = [directAuthor, directDate, directRoom, directStart, directEnd];
      inputs.filter(Boolean).forEach((input) => {
        input.addEventListener("input", updateMetaFromInputs);
        input.addEventListener("change", updateMetaFromInputs);
      });
    }
  });
}
