const notaSpacePage = App.qs(".page[data-page]");

if (notaSpacePage) {
  const pageType = notaSpacePage.dataset.page;

  const HOURS = Array.from({ length: 10 }, (_, idx) => idx + 9);

  const state = {
    date: App.todayISO(),
    rooms: [],
    bookings: []
  };

  const $ = (selector) => App.qs(selector);

  async function fetchRooms() {
    const res = await fetch("/api/nota-space/rooms");
    const data = await res.json();
    state.rooms = data.rooms || [];
  }

  async function fetchBookings(dateValue) {
    const res = await fetch(`/api/nota-space/bookings?date=${dateValue}`);
    const data = await res.json();
    state.bookings = data.bookings || [];
    state.date = data.date || dateValue;
  }

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

    const headerCells = [`<div class="ns-room-col">회의실</div>`].concat(
      HOURS.map((hour) => `<div class="ns-hour-col">${App.formatHour(hour)}</div>`)
    );

    const rows = [
      `<div class="ns-timeline-row ns-timeline-header">${headerCells.join("")}</div>`
    ];

    state.rooms.forEach((room) => {
      const roomBookings = bookingsByRoom.get(room.id) || [];
      const rowCells = [`<div class="ns-room-col"><div class="ns-room-name">${room.name}</div><div class="ns-room-meta">${room.feature}</div></div>`];

      HOURS.forEach((hour) => {
        const booking = roomBookings.find((item) => {
          const startHour = App.parseHour(item.start_time);
          const endHour = App.parseHour(item.end_time);
          return hour >= startHour && hour < endHour;
        });

        if (booking) {
          const startHour = App.parseHour(booking.start_time);
          const content = hour === startHour
            ? `<div class="ns-booking-title">${booking.agenda}</div><div class="ns-booking-meta">${booking.presenter}</div>`
            : "";
          rowCells.push(`<div class="ns-slot is-booked">${content}</div>`);
        } else {
          rowCells.push(
            `<button class="ns-slot" data-room="${room.id}" data-hour="${hour}" type="button"></button>`
          );
        }
      });

      rows.push(`<div class="ns-timeline-row">${rowCells.join("")}</div>`);
    });

    timeline.innerHTML = `<div class="ns-timeline-grid">${rows.join("")}</div>`;
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

  async function refreshBookingPage() {
    await fetchRooms();
    await fetchBookings(state.date);
    renderTimeline();
    renderBookingForm();
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

      const res = await fetch("/api/nota-space/bookings", {
        method: "POST",
        body: formData
      });

      const payload = await res.json();
      if (!res.ok) {
        if (message) message.textContent = payload.error || "예약에 실패했습니다.";
        return;
      }

      form.reset();
      if (message) message.textContent = "예약이 등록되었습니다.";
      await fetchBookings(state.date);
      renderTimeline();
      renderBookingForm();
    });
  }

  function bindDateChange() {
    const dateInput = $("#ns-date");
    const logDateInput = $("#ns-log-date");

    const handler = async (event) => {
      state.date = event.target.value || state.date;
      if (pageType === "room-booking") {
        await fetchBookings(state.date);
        renderTimeline();
        renderBookingForm();
      }
      if (pageType === "meeting-log") {
        await refreshLogPage();
      }
    };

    if (dateInput) dateInput.addEventListener("change", handler);
    if (logDateInput) logDateInput.addEventListener("change", handler);
  }

  function renderLogList() {
    const list = $("#ns-log-list");
    if (!list) return;

    if (!state.bookings.length) {
      list.innerHTML = "<div class=\"ns-empty\">선택한 날짜에 예약이 없습니다.</div>";
      return;
    }

    list.innerHTML = state.bookings
      .map((booking) => {
        const participants = booking.participants || [];
        const log = booking.log || null;
        return `
          <div class="ns-log-item">
            <div class="ns-log-main">
              <div class="ns-log-title">${booking.room_name} · ${booking.start_time}~${booking.end_time}</div>
              <div class="ns-log-meta">${booking.agenda} | 발표자: ${booking.presenter}</div>
              <div class="ns-log-meta">참여자: ${participants.join(", ") || "-"}</div>
              ${log && log.summary ? `<div class="ns-log-summary">${log.summary}</div>` : ""}
            </div>
            <button class="ns-btn ns-btn-light" data-booking="${booking.id}" type="button">${log ? "로그 수정" : "로그 작성"}</button>
          </div>
        `;
      })
      .join("");
  }

  function renderLogFormOptions() {
    const select = $("#ns-log-booking");
    if (!select) return;

    select.innerHTML = state.bookings
      .map((booking) => `<option value="${booking.id}">${booking.room_name} ${booking.start_time}~${booking.end_time}</option>`)
      .join("");
  }

  async function refreshLogPage() {
    await fetchRooms();
    await fetchBookings(state.date);
    const logDateInput = $("#ns-log-date");
    if (logDateInput) logDateInput.value = state.date;
    renderLogList();
    renderLogFormOptions();
  }

  function bindLogActions() {
    const list = $("#ns-log-list");
    const select = $("#ns-log-booking");
    if (!list || !select) return;

    list.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-booking]");
      if (!button) return;
      select.value = button.dataset.booking;
      select.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  function bindLogForm() {
    const form = $("#ns-log-form");
    const message = $("#ns-log-message");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const notes = String(formData.get("notes") || "").trim();
      const audio = formData.get("audio");

      if (!notes && (!audio || !audio.name)) {
        if (message) message.textContent = "오디오 또는 노트를 입력하세요.";
        return;
      }

      const res = await fetch("/api/nota-space/meeting-logs", {
        method: "POST",
        body: formData
      });

      const payload = await res.json();
      if (!res.ok) {
        if (message) message.textContent = payload.error || "로그 저장에 실패했습니다.";
        return;
      }

      form.reset();
      if (message) message.textContent = "로그가 저장되었습니다.";
      await refreshLogPage();
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    if (pageType === "room-booking") {
      await refreshBookingPage();
      bindTimelineClick();
      bindBookingForm();
      bindDateChange();
    }

    if (pageType === "meeting-log") {
      await refreshLogPage();
      bindLogActions();
      bindLogForm();
      bindDateChange();
    }
  });
}
