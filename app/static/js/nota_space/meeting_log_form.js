(() => {
  const page = App.qs(".page[data-page='meeting-log-form']");
  if (!page) return;

  const summaryButton = App.qs("#ns-generate-summary");
  const summaryMessage = App.qs("#ns-summary-message");
  const summaryText = App.qs("#ns-summary-text");
  const summarySection = App.qs("#ns-summary-section");
  const summaryInput = App.qs("#ns-summary-input");
  const audioInput = App.qs("#ns-audio");

  if (!summaryButton) return;

  const setSummary = (value) => {
    const text = (value || "").trim();
    if (summaryText) summaryText.textContent = text || "요약 결과가 없습니다.";
    if (summaryInput) summaryInput.value = text;
  };

  summaryButton.addEventListener("click", async () => {
    const notesEl = App.qs("#ns-notes");
    const notes = notesEl ? String(notesEl.value || "").trim() : "";
    const audioFile = audioInput && audioInput.files ? audioInput.files[0] : null;

    if (!notes && !audioFile) {
      if (summaryMessage) summaryMessage.textContent = "회의 내용 또는 녹음 파일을 추가하세요.";
      return;
    }

    if (summaryMessage) summaryMessage.textContent = "AI 요약을 생성하는 중...";

    const formData = new FormData();
    if (notes) formData.set("meeting_text", notes);
    if (audioFile) formData.set("audio_file", audioFile);

    const { res, data } = await App.fetchJson("/api/nota-space/meeting-summary", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const fallback = "AI 요약 생성에 실패했습니다.";
      const errorCode = data && (data.summary_error || data.error_code);
      const message =
        (data && data.error) ||
        (errorCode === "OPENAI_API_KEY_MISSING"
          ? "서버에 OPENAI_API_KEY가 설정되지 않았습니다. (instance/.env 또는 환경변수 확인)"
          : fallback);
      if (summaryMessage) {
        summaryMessage.textContent = message;
      }
      return;
    }

    const summaryValue = data && data.summary ? String(data.summary).trim() : "";
    if (!summaryValue) {
      if (summaryMessage) summaryMessage.textContent = "AI 요약 결과를 받지 못했습니다.";
      return;
    }

    setSummary(summaryValue);
    if (summaryMessage) summaryMessage.textContent = "AI 요약이 생성되었습니다.";
    if (summarySection) summarySection.scrollIntoView({ behavior: "smooth", block: "start" });
  });
})();
