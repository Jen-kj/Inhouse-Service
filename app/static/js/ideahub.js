// ==========================================
// Idea Hub - Vanilla JavaScript
// ==========================================

(() => {
  const USER_ID = "user_001";
  const UPVOTED_KEY = `ideaHub.upvoted.${USER_ID}`;

  const ideaFeed = document.getElementById("ideaFeed");
  if (!ideaFeed) return;

  const filterButtons = Array.from(document.querySelectorAll(".idea-chip"));
  const submitIdeaBtn = document.getElementById("submitIdeaBtn");
  const submitModal = document.getElementById("submitModal");
  const cancelSubmitBtn = document.getElementById("cancelSubmitBtn");
  const confirmSubmitBtn = document.getElementById("confirmSubmitBtn");

  const commentModal = document.getElementById("commentModal");
  const cancelCommentBtn = document.getElementById("cancelCommentBtn");
  const confirmCommentBtn = document.getElementById("confirmCommentBtn");
  const ratingStars = Array.from(document.querySelectorAll(".idea-star"));

  let allIdeas = [];
  let upvotedIdeas = new Set(loadUpvotedFromStorage());
  let selectedRating = 0;
  let currentCommentIdeaId = null;

  // ✅ 현재 필터 유지용 (삭제 후 다시 로드)
  let currentStatusFilter = "";

  document.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    loadIdeas("");
  });

  function setupEventListeners() {
    filterButtons.forEach((btn) => {
      btn.addEventListener("click", () => handleFilter(btn));
    });

    submitIdeaBtn?.addEventListener("click", () => openModal(submitModal));
    cancelSubmitBtn?.addEventListener("click", () => closeModal(submitModal));
    confirmSubmitBtn?.addEventListener("click", handleSubmitIdea);

    cancelCommentBtn?.addEventListener("click", () => {
      closeModal(commentModal);
      resetCommentModal();
    });
    confirmCommentBtn?.addEventListener("click", handleSubmitComment);

    ratingStars.forEach((star) => {
      star.addEventListener("click", () => handleRatingClick(star));
    });

    document.addEventListener("click", (e) => {
      const closeBtn = e.target.closest("[data-close-modal]");
      if (closeBtn) {
        const id = closeBtn.getAttribute("data-close-modal");
        const modal = document.getElementById(id);
        if (modal) closeModal(modal);
        if (id === "commentModal") resetCommentModal();
        return;
      }

      const modal = e.target.classList.contains("idea-modal") ? e.target : null;
      if (modal && modal.classList.contains("is-open")) {
        closeModal(modal);
        if (modal.id === "commentModal") resetCommentModal();
      }

      // ✅ 아이디어 카드 ⋯ 메뉴: 바깥 클릭 시 닫기
      if (!e.target.closest(".idea-more-wrap")) {
        ideaFeed.querySelectorAll(".idea-more-menu").forEach((m) => (m.hidden = true));
      }
    });

    ideaFeed.addEventListener("click", (e) => {
      // ✅ ⋯ 메뉴 토글
      const toggleBtn = e.target.closest('[data-action="toggle-idea-menu"]');
      if (toggleBtn) {
        const card = toggleBtn.closest(".idea-card");
        if (!card) return;

        // 다른 카드의 열린 메뉴 닫기
        ideaFeed.querySelectorAll(".idea-more-menu").forEach((m) => {
          if (!card.contains(m)) m.hidden = true;
        });

        const menu = card.querySelector(".idea-more-menu");
        if (menu) menu.hidden = !menu.hidden;
        return;
      }

      // ✅ 삭제
      const deleteBtn = e.target.closest('[data-action="delete-idea"]');
      if (deleteBtn) {
        const ideaId = Number(deleteBtn.dataset.ideaId);
        if (!Number.isFinite(ideaId)) return;

        // 메뉴 닫기
        ideaFeed.querySelectorAll(".idea-more-menu").forEach((m) => (m.hidden = true));

        if (!confirm("이 글을 삭제할까요?")) return;

        handleDeleteIdea(ideaId);
        return;
      }

      const upvoteBtn = e.target.closest(".idea-upvote");
      if (upvoteBtn) {
        const ideaId = Number(upvoteBtn.dataset.ideaId);
        if (Number.isFinite(ideaId)) handleUpvote(ideaId, upvoteBtn);
        return;
      }

      const commentBtn = e.target.closest(".idea-add-comment");
      if (commentBtn) {
        const ideaId = Number(commentBtn.dataset.ideaId);
        if (Number.isFinite(ideaId)) openCommentModal(ideaId);
      }
    });
  }

  async function loadIdeas(statusFilter = "") {
    // ✅ 현재 필터 저장
    currentStatusFilter = statusFilter;

    try {
      const url = statusFilter
        ? `/api/ideas?status=${encodeURIComponent(statusFilter)}`
        : "/api/ideas";
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      allIdeas = await response.json();
      renderIdeas(allIdeas);
    } catch (error) {
      console.error("Failed to load ideas:", error);
      ideaFeed.innerHTML = emptyState("😢", "아이디어를 불러올 수 없습니다.");
    }
  }

  function renderIdeas(ideas) {
    if (!Array.isArray(ideas) || ideas.length === 0) {
      ideaFeed.innerHTML = emptyState(
        "💡",
        "아직 아이디어가 없습니다.<br>첫 아이디어를 제안해보세요!"
      );
      return;
    }
    ideaFeed.innerHTML = ideas.map((idea) => createIdeaCard(idea)).join("");
  }

  function createIdeaCard(idea) {
    const hasVoted = upvotedIdeas.has(idea.id);
    const statusClass = String(idea.status || "").replace(/ /g, "-");
    const isCompleted = idea.status === "해결 완료";

    const createdAt = idea.created_at ? new Date(idea.created_at) : null;
    const timeAgo = createdAt ? getTimeAgo(createdAt) : "";

    const author = String(idea.author || "익명");
    const initial = author.charAt(0) || "?";
    const category = idea.category ? String(idea.category) : "";

    const timelineHTML =
      Array.isArray(idea.timeline) && idea.timeline.length > 0
        ? `
      <div class="idea-timeline">
        <div class="idea-timeline-title">📍 진행 상황</div>
        ${idea.timeline
          .map(
            (item) => `
          <div class="idea-timeline-item">
            <div class="idea-timeline-dot"></div>
            <div class="idea-timeline-content">
              <div class="idea-timeline-status">${escapeHtml(item.status || "")}</div>
              <div class="idea-timeline-message">${escapeHtml(item.message || "")}</div>
              <div class="idea-timeline-date">${formatDate(item.created_at)}</div>
            </div>
          </div>
        `
          )
          .join("")}
      </div>`
        : "";

    const completedHTML =
      isCompleted && (idea.completed_image || idea.completed_description)
        ? `
      <div class="idea-completed">
        <div class="idea-completed-title">✅ 완성 결과</div>
        ${
          idea.completed_image
            ? `<img src="${escapeAttr(idea.completed_image)}" alt="완성 사진" class="idea-completed-image">`
            : ""
        }
        ${
          idea.completed_description
            ? `<p class="idea-completed-desc">${escapeHtml(idea.completed_description)}</p>`
            : ""
        }
      </div>`
        : "";

    const comments = Array.isArray(idea.comments) ? idea.comments : [];
    const commentsHTML = isCompleted
      ? `
        <div class="idea-comments">
          <div class="idea-comments-title">💬 피드백 (${comments.length})</div>
          ${
            comments.length > 0
              ? comments
                  .map(
                    (c) => `
                    <div class="idea-comment">
                      <div class="idea-comment-meta">
                        <span class="idea-comment-author">${escapeHtml(c.author || "")}</span>
                        ${
                          c.rating
                            ? `<span class="idea-comment-stars">${"⭐".repeat(Number(c.rating) || 0)}</span>`
                            : ""
                        }
                      </div>
                      <div class="idea-comment-text">${escapeHtml(c.comment || "")}</div>
                    </div>
                  `
                  )
                  .join("")
              : ""
          }
          <div class="idea-comment-actions">
            <button class="idea-add-comment" data-idea-id="${Number(idea.id)}" type="button">+ 피드백 남기기</button>
          </div>
        </div>
      `
      : "";

    const rating =
      typeof idea.rating === "number" && idea.rating > 0 ? idea.rating : 0;
    const ratingCount =
      typeof idea.rating_count === "number" ? idea.rating_count : 0;
    const ratingHTML =
      rating > 0
        ? `<span class="idea-rating-summary"><span class="idea-rating-stars">⭐ ${rating.toFixed(
            1
          )}</span><span>(${ratingCount}명)</span></span>`
        : `<span class="idea-rating-summary"><span>별점 없음</span></span>`;

    return `
      <article class="idea-card" data-idea-id="${Number(idea.id)}">
        <div class="idea-card-header">
          <div class="idea-avatar">${escapeHtml(initial)}</div>
          <div class="idea-meta">
            <div class="idea-author">${escapeHtml(author)}</div>
            <div class="idea-time">${escapeHtml(timeAgo)}</div>
          </div>

          <span class="idea-status ${escapeAttr(statusClass)}">${escapeHtml(idea.status || "")}</span>

          <!-- ✅ 추가: ⋯ 메뉴(삭제) -->
          <div class="idea-more-wrap">
            <button
              class="idea-more-btn"
              type="button"
              aria-label="메뉴"
              data-action="toggle-idea-menu"
              data-idea-id="${Number(idea.id)}"
            >⋯</button>

            <div class="idea-more-menu" hidden>
              <button
                class="idea-more-item"
                type="button"
                data-action="delete-idea"
                data-idea-id="${Number(idea.id)}"
              >삭제</button>
            </div>
          </div>
        </div>

        <div class="idea-card-body">
          <h3 class="idea-title">${escapeHtml(idea.title || "")}</h3>
          <p class="idea-content">${escapeHtml(idea.content || "")}</p>
          ${category ? `<span class="idea-category">#${escapeHtml(category)}</span>` : ""}
          ${completedHTML}
          ${timelineHTML}
        </div>

        <div class="idea-card-footer">
          <button class="idea-upvote ${hasVoted ? "is-voted" : ""}" data-idea-id="${Number(
            idea.id
          )}" type="button">
            👍 <span class="idea-upvote-count">${Number(idea.upvotes || 0)}</span>
          </button>
          ${ratingHTML}
        </div>
        ${commentsHTML}
      </article>
    `;
  }

  function handleFilter(button) {
    const status = button.dataset.status || "";
    currentStatusFilter = status; // ✅ 유지
    filterButtons.forEach((btn) => btn.classList.remove("is-active"));
    button.classList.add("is-active");
    loadIdeas(status);
  }

  async function handleSubmitIdea() {
    const title = document.getElementById("ideaTitle").value.trim();
    const content = document.getElementById("ideaContent").value.trim();
    const category = document.getElementById("ideaCategory").value;
    const author = document.getElementById("ideaAuthor").value.trim();

    if (!title || !content || !author) {
      alert("제목, 내용, 이름을 모두 입력해주세요.");
      return;
    }

    try {
      const response = await fetch("/api/ideas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content, category, author }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error("CREATE_FAILED");

      closeModal(submitModal);
      document.getElementById("ideaTitle").value = "";
      document.getElementById("ideaContent").value = "";
      document.getElementById("ideaCategory").value = "";
      document.getElementById("ideaAuthor").value = "";

      await loadIdeas("");
      alert("✅ 아이디어가 제안되었습니다! 검토 후 답변드리겠습니다.");
    } catch (error) {
      console.error("Failed to submit idea:", error);
      alert("❌ 제안에 실패했습니다.");
    }
  }

  async function handleUpvote(ideaId, button) {
    if (upvotedIdeas.has(ideaId)) return;

    try {
      const response = await fetch(`/api/ideas/${ideaId}/upvote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error("UPVOTE_FAILED");

      if (data.success) {
        upvotedIdeas.add(ideaId);
        persistUpvotedToStorage(upvotedIdeas);
        button.classList.add("is-voted");
      }

      const countNode = button.querySelector(".idea-upvote-count");
      if (countNode) countNode.textContent = String(data.upvotes ?? 0);

      button.style.transform = "scale(1.05)";
      setTimeout(() => {
        button.style.transform = "";
      }, 180);
    } catch (error) {
      console.error("Failed to upvote:", error);
    }
  }

  // ✅ 추가: 삭제 처리
  async function handleDeleteIdea(ideaId) {
    try {
      const response = await fetch(`/api/ideas/${ideaId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.success === false) throw new Error("DELETE_FAILED");

      // 로컬 upvote 기록도 제거(선택)
      if (upvotedIdeas.has(ideaId)) {
        upvotedIdeas.delete(ideaId);
        persistUpvotedToStorage(upvotedIdeas);
      }

      await loadIdeas(currentStatusFilter);
      alert("✅ 삭제되었습니다.");
    } catch (error) {
      console.error("Failed to delete idea:", error);
      alert("❌ 삭제에 실패했습니다.");
    }
  }

  function openCommentModal(ideaId) {
    currentCommentIdeaId = ideaId;
    openModal(commentModal);
  }

  function resetCommentModal() {
    selectedRating = 0;
    ratingStars.forEach((star) => star.classList.remove("is-active"));
    document.getElementById("commentText").value = "";
    document.getElementById("commentAuthor").value = "";
    currentCommentIdeaId = null;
  }

  function handleRatingClick(star) {
    selectedRating = Number(star.dataset.rating) || 0;
    ratingStars.forEach((s) => {
      const rating = Number(s.dataset.rating) || 0;
      s.classList.toggle("is-active", rating <= selectedRating);
    });
  }

  async function handleSubmitComment() {
    const comment = document.getElementById("commentText").value.trim();
    const author = document.getElementById("commentAuthor").value.trim();

    if (!comment || !author || !currentCommentIdeaId) {
      alert("댓글과 이름을 입력해주세요.");
      return;
    }

    try {
      const response = await fetch(`/api/ideas/${currentCommentIdeaId}/comment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          comment,
          author,
          rating: selectedRating > 0 ? selectedRating : null,
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error("COMMENT_FAILED");

      closeModal(commentModal);
      resetCommentModal();
      await loadIdeas("");
      alert("✅ 피드백이 등록되었습니다!");
    } catch (error) {
      console.error("Failed to submit comment:", error);
      alert("❌ 피드백 등록에 실패했습니다.");
    }
  }

  function openModal(modal) {
    if (!modal) return;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
  }

  function emptyState(icon, htmlText) {
    return `
      <div class="idea-empty">
        <div class="idea-empty-icon">${icon}</div>
        <div class="idea-empty-text">${htmlText}</div>
      </div>
    `;
  }

  function getTimeAgo(date) {
    const now = new Date();
    const diffSeconds = Math.floor((now - date) / 1000);
    if (diffSeconds < 60) return "방금 전";
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}분 전`;
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}시간 전`;
    if (diffSeconds < 2592000) return `${Math.floor(diffSeconds / 86400)}일 전`;
    return date.toLocaleDateString("ko-KR");
  }

  function formatDate(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function loadUpvotedFromStorage() {
    try {
      const raw = localStorage.getItem(UPVOTED_KEY);
      const ids = JSON.parse(raw || "[]");
      if (!Array.isArray(ids)) return [];
      return ids.map((n) => Number(n)).filter((n) => Number.isFinite(n));
    } catch {
      return [];
    }
  }

  function persistUpvotedToStorage(set) {
    try {
      localStorage.setItem(UPVOTED_KEY, JSON.stringify(Array.from(set)));
    } catch {
      // ignore
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll("`", "&#96;");
  }
})();
