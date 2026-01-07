import json
import glob
import os
import random
import re
import shutil
import time
from collections import Counter
from datetime import datetime

from flask import jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from . import bp
from app.db import (
    BASE_DIR,
    CATEGORY_TO_TEAM,
    IDEA_STATUS_OPTIONS,
    STATUS_OPTIONS,
    URGENCY_OPTIONS,
    add_idea_comment,
    create_booking,
    create_idea,
    create_ticket,
    fetch_booking_by_id,
    fetch_all_bookings,
    fetch_meeting_log_by_id,
    fetch_bookings,
    fetch_booking_days,
    fetch_ideas,
    fetch_meeting_logs,
    fetch_rooms,
    fetch_summary,
    fetch_tickets,
    idea_exists,
    has_booking_conflict,
    upsert_meeting_log_entry,
    upvote_idea,
    update_ticket_status,
)

REQUESTER_POOL = ["김민수", "이서연", "박준호", "최지우", "정하늘", "오유진", "nota_inhouse"]

_WHISPER_MODEL = None
_OPENAI_CLIENT = None


_KOREAN_STOPWORDS = {
    "그리고",
    "하지만",
    "그래서",
    "또한",
    "그런데",
    "저희",
    "이번",
    "다음",
    "관련",
    "부분",
    "내용",
    "정도",
    "같은",
    "해서",
    "합니다",
    "있습니다",
    "없습니다",
    "가능",
    "확인",
    "진행",
    "논의",
    "회의",
}

_ENGLISH_STOPWORDS = {
    "the",
    "and",
    "or",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "as",
    "is",
    "are",
    "be",
    "we",
    "i",
    "you",
    "it",
    "this",
    "that",
}


def _split_sentences(text: str) -> list[str]:
    cleaned = (text or "").replace("\r\n", "\n").strip()
    if not cleaned:
        return []

    chunks = re.split(r"\n+", cleaned)
    sentences: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = re.split(r"(?<=[.!?])\s+", chunk)
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

    return sentences


def _extract_action_items(sentences: list[str]) -> list[dict]:
    items: list[dict] = []
    for sentence in sentences:
        owner_match = re.search(r"(담당자|담당)\s*[:：]\s*([A-Za-z가-힣]{2,10})", sentence)
        due_match = re.search(
            r"(기한|마감|due)\s*[:：]\s*([0-9]{1,4}[./-][0-9]{1,2}([./-][0-9]{1,2})?)",
            sentence,
            re.I,
        )
        task_match = re.search(r"(할\s*일|작업|todo|task)\s*[:：]\s*(.+)$", sentence, re.I)

        owner = owner_match.group(2).strip() if owner_match else ""
        due = due_match.group(2).strip() if due_match else ""
        task = ""
        if task_match:
            task = task_match.group(2).strip()
        else:
            if owner_match or due_match:
                task = sentence.strip()

        if owner and task and due:
            items.append({"owner": owner, "task": task, "due": due})

    return items


def _extract_decisions(sentences: list[str]) -> list[str]:
    decision_keywords = re.compile(r"(결정|하기로|확정|승인|합의|채택|결론)", re.I)
    decisions: list[str] = []
    seen = set()
    for sentence in sentences:
        if not decision_keywords.search(sentence):
            continue
        normalized = sentence.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            decisions.append(normalized)
    return decisions


def _pick_title(text: str, sentences: list[str]) -> str:
    for candidate in sentences[:3]:
        match = re.search(r"(회의|미팅)\s*[:：]\s*(.+)$", candidate)
        if match:
            return match.group(2).strip()[:80]
    first = (sentences[0] if sentences else "").strip()
    if 5 <= len(first) <= 80:
        return first
    return "회의 요약"


def _summarize_locally_structured(text: str) -> dict:
    input_text = _truncate_meeting_text(text)
    sentences = _split_sentences(input_text)
    if not sentences:
        return {"title": "회의 요약", "topics": [], "action_items": [], "overall_summary": ""}

    tokens = re.findall(r"[A-Za-z]{2,}|[0-9]{2,}|[가-힣]{2,}", input_text)
    filtered = []
    for t in tokens:
        lower = t.lower()
        if lower in _ENGLISH_STOPWORDS:
            continue
        if t in _KOREAN_STOPWORDS:
            continue
        if len(t) < 2:
            continue
        filtered.append(lower if re.fullmatch(r"[A-Za-z]+", t) else t)

    top_terms = [w for w, _ in Counter(filtered).most_common(12)]
    term_weights = {term: 3 if i < 4 else 2 if i < 8 else 1 for i, term in enumerate(top_terms)}

    decisions = _extract_decisions(sentences)
    action_items = _extract_action_items(sentences)

    def score(sentence: str) -> int:
        s = sentence.lower()
        return sum(weight for term, weight in term_weights.items() if term.lower() in s)

    decision_set = set(decisions)
    scored = []
    for s in sentences:
        if s in decision_set:
            continue
        if any((ai.get("task") or "") in s for ai in action_items):
            continue
        scored.append((score(s), s))

    scored.sort(key=lambda x: (-x[0], sentences.index(x[1])))
    key_points = [s for _, s in scored[:8]] if scored else sentences[:5]

    overall_summary = " ".join(key_points[:3]).strip()

    topics = []
    topics.append({"title": "주요 논의", "summary_bullets": key_points[:6], "decisions": []})

    if decisions:
        topics.append(
            {
                "title": "결정 사항",
                "summary_bullets": decisions[:6],
                "decisions": decisions[:10],
            }
        )

    for topic in topics:
        topic.setdefault("title", "")
        topic.setdefault("summary_bullets", [])
        topic.setdefault("decisions", [])

    return {
        "title": _pick_title(input_text, sentences),
        "topics": topics[:6],
        "action_items": action_items[:10],
        "overall_summary": overall_summary,
    }


def _ensure_ffmpeg_in_path():
    if shutil.which("ffmpeg"):
        return

    local_app = os.environ.get("LOCALAPPDATA")
    if not local_app:
        return

    pattern = os.path.join(
        local_app,
        "Microsoft",
        "WinGet",
        "Packages",
        "Gyan.FFmpeg_*",
        "ffmpeg-*-full_build",
        "bin",
        "ffmpeg.exe",
    )
    matches = glob.glob(pattern)
    if not matches:
        return

    ffmpeg_dir = os.path.dirname(matches[0])
    os.environ["PATH"] = f"{ffmpeg_dir};{os.environ.get('PATH', '')}"


def _pick_requester():
    return random.choice(REQUESTER_POOL)


def _save_upload(file, folder_name):
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)
    if not filename:
        return None

    upload_dir = os.path.join(BASE_DIR, "app", "static", "uploads", folder_name)
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{int(time.time())}_{filename}"
    file.save(os.path.join(upload_dir, stored_name))
    return f"/static/uploads/{folder_name}/{stored_name}"


def _transcribe_audio(audio_path, language="ko"):
    global _WHISPER_MODEL
    if not audio_path:
        return ""

    try:
        _ensure_ffmpeg_in_path()
        import whisper

        if _WHISPER_MODEL is None:
            _WHISPER_MODEL = whisper.load_model("base")
        result = _WHISPER_MODEL.transcribe(audio_path, language=language)
        return (result.get("text") or "").strip()
    except Exception as exc:
        print(f"[nota-space] whisper failed: {exc}")
        return ""


def _get_openai_client():
    api_key = _get_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing")

    # Install: .\.venv\Scripts\python.exe -m pip install openai
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _get_openai_api_key() -> str:
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if api_key:
        return api_key

    api_key_file = (os.environ.get("OPENAI_API_KEY_FILE") or "").strip()
    if api_key_file and os.path.exists(api_key_file):
        try:
            with open(api_key_file, "r", encoding="utf-8") as f:
                return (f.read() or "").strip()
        except Exception:
            return ""

    return ""


def _truncate_meeting_text(text: str, max_chars: int = 14000) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned

    head_size = min(9000, max_chars - 4000)
    tail_size = max_chars - head_size
    head = cleaned[:head_size].rstrip()
    tail = cleaned[-tail_size:].lstrip()
    return f"{head}\n\n...(중간 내용 생략됨)...\n\n{tail}"


def _summarize_with_openai_structured(text: str) -> tuple[dict | None, str | None, str | None]:
    input_text = _truncate_meeting_text(text)
    if not input_text:
        return None, "EMPTY_INPUT", "요약할 텍스트가 없습니다."

    api_key = _get_openai_api_key()
    if not api_key:
        print("[nota-space] openai failed: OPENAI_API_KEY missing")
        return (
            None,
            "OPENAI_API_KEY_MISSING",
            "서버에 OPENAI_API_KEY가 설정되지 않았습니다. (instance/.env, app/inhouse_service/instance/.env 또는 환경변수 확인)",
        )

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    summary_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "topics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "summary_bullets": {"type": "array", "items": {"type": "string"}},
                        "decisions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "summary_bullets", "decisions"],
                },
            },
            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "owner": {"type": "string"},
                        "task": {"type": "string"},
                        "due": {"type": "string"},
                    },
                    "required": ["owner", "task", "due"],
                },
            },
            "overall_summary": {"type": "string"},
        },
        "required": ["title", "topics", "action_items", "overall_summary"],
    }

    system_prompt = (
        "너는 회의록 요약 어시스턴트다. 입력 텍스트에서 주제를 3~6개 추출하고,"
        " 각 주제마다 2~4개의 요약 bullet을 작성한다. '이제/마지막으로/여기까지' 같은 말버릇을"
        " 주제 제목으로 쓰지 말고, 구체적인 주제로 제목을 만든다."
        " 결정사항은 '확정/승인/하기로/결정' 근거가 있을 때만 포함한다."
        " 실행 항목은 담당자/할 일/기한이 명확할 때만 포함하며 없으면 빈 배열로 둔다."
        " 누락 필드는 만들지 말고, 값이 없으면 빈 문자열/빈 배열로 채운다."
    )

    try:
        # Install: .\.venv\Scripts\python.exe -m pip install openai
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            temperature=0.2,
            instructions=system_prompt,
            input=input_text,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "meeting_summary",
                    "schema": summary_schema,
                    "strict": True,
                }
            },
        )

        output_text = getattr(response, "output_text", None)
        if not output_text:
            chunks = []
            for output in getattr(response, "output", []) or []:
                if getattr(output, "type", None) != "message":
                    continue
                for content in getattr(output, "content", []) or []:
                    if getattr(content, "type", None) == "output_text":
                        chunks.append(getattr(content, "text", ""))
            output_text = "".join(chunks).strip()

        parsed = json.loads(output_text or "{}")
        if not isinstance(parsed, dict):
            return None, "OPENAI_INVALID_RESPONSE", "AI 응답을 파싱하지 못했습니다."
        return parsed, None, None
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        body = getattr(exc, "body", None)
        api_message = None
        api_code = getattr(exc, "code", None)
        if isinstance(body, dict):
            if isinstance(body.get("error"), dict):
                api_message = body["error"].get("message")
                api_code = api_code or body["error"].get("code")
            else:
                api_message = body.get("message")
                api_code = api_code or body.get("code")

        if status_code == 429:
            error_code = "OPENAI_INSUFFICIENT_QUOTA" if api_code == "insufficient_quota" else "OPENAI_RATE_LIMIT"
        elif status_code == 401:
            error_code = "OPENAI_AUTH_FAILED"
        elif status_code == 400:
            error_code = "OPENAI_BAD_REQUEST"
        else:
            error_code = "OPENAI_REQUEST_FAILED"

        fallback_message = getattr(exc, "message", None) or f"OpenAI 요청 실패: {type(exc).__name__}"
        message = (api_message or "").strip() or str(fallback_message).strip()
        print(f"[nota-space] openai failed: {type(exc).__name__}: {exc}")
        return None, error_code, message


def _render_summary_text(summary: dict) -> str:
    title = (summary or {}).get("title") or ""
    topics = (summary or {}).get("topics") or []
    decisions_all = []
    action_items = (summary or {}).get("action_items") or []
    overall_summary = (summary or {}).get("overall_summary") or ""

    lines = ["📌 주요 논의 사항"]
    if title:
        lines.append(f"회의 제목: {title}")
    lines.append("")

    for topic in topics:
        topic_title = (topic or {}).get("title") or "기타"
        lines.append(f"■ {topic_title}")
        bullets = (topic or {}).get("summary_bullets") or []
        for bullet in bullets:
            if bullet:
                lines.append(f"- {bullet}")
        decisions = (topic or {}).get("decisions") or []
        for decision in decisions:
            if decision:
                decisions_all.append(decision)
        lines.append("")

    seen = set()
    deduped_decisions = []
    for item in decisions_all:
        if item not in seen:
            seen.add(item)
            deduped_decisions.append(item)

    lines.append("✅ 결정된 사항")
    if deduped_decisions:
        for decision in deduped_decisions:
            lines.append(f"- {decision}")
    else:
        lines.append("- (없음)")
    lines.append("")

    lines.append("🎯 실행 항목")
    if action_items:
        for action in action_items:
            owner = (action or {}).get("owner") or ""
            task = (action or {}).get("task") or ""
            due = (action or {}).get("due") or ""
            if not (owner or task or due):
                continue
            if due:
                lines.append(f"- {owner} - {task} (~ {due})")
            else:
                lines.append(f"- {owner} - {task}")
    else:
        lines.append("- (없음)")
    lines.append("")

    lines.append("🧾 전체 요약")
    lines.append(overall_summary)
    return "\n".join(lines).strip()

@bp.get("/")
def home():
    return render_template("empty_page.html", active="")


@bp.get("/service-desk")
def service_desk():
    return render_template("service_desk.html", active="service-desk")


@bp.get("/nota-space")
def nota_space_home():
    return redirect(url_for("inhouse_service.nota_space_room_booking"))


@bp.get("/nota-space/room-booking")
def nota_space_room_booking():
    return render_template("nota_space/booking.html", active="nota-space", subnav="room-booking")


@bp.get("/nota-space/room-booking/list")
def nota_space_room_booking_list():
    return render_template("nota_space/booking_list.html", active="nota-space", subnav="room-booking")


@bp.get("/nota-space/meeting-log")
def nota_space_meeting_log():
    return render_template("nota_space/meeting_log.html", active="nota-space", subnav="meeting-log")


@bp.get("/nota-space/meeting-log/new")
def nota_space_meeting_log_new():
    return render_template(
        "nota_space/meeting_log_form.html",
        active="nota-space",
        subnav="meeting-log",
        booking_id=None,
        log_id=None,
    )


@bp.get("/nota-space/meeting-log/<int:booking_id>")
def nota_space_meeting_log_for_booking(booking_id):
    return render_template(
        "nota_space/meeting_log_form.html",
        active="nota-space",
        subnav="meeting-log",
        booking_id=booking_id,
        log_id=None,
    )


@bp.get("/nota-space/meeting-log/entry/<int:log_id>")
def nota_space_meeting_log_entry(log_id):
    return render_template(
        "nota_space/meeting_log_form.html",
        active="nota-space",
        subnav="meeting-log",
        booking_id=None,
        log_id=log_id,
    )


@bp.get("/clubs")
def clubs_home():
    return render_template("club/club.html", active="clubs")


@bp.get("/onboarding")
def onboarding():
    return render_template("onboarding.html", active="onboarding", title="온보딩")


@bp.get("/idea")
def idea_hub():
    return render_template("idea/ideahub.html", active="idea", title="Idea Hub")


@bp.get("/api/ideas")
def get_ideas():
    status = (request.args.get("status") or "").strip() or None
    if status and status not in IDEA_STATUS_OPTIONS:
        return jsonify({"error": "Invalid status"}), 400

    ideas = fetch_ideas(status=status)
    return jsonify(ideas)


@bp.post("/api/ideas")
def create_new_idea():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    category = (payload.get("category") or "").strip()
    author = (payload.get("author") or "").strip()

    if not title or not content or not author:
        return jsonify({"success": False, "error": "MISSING_FIELDS"}), 400

    idea_id = create_idea(title, content, category, author)
    return jsonify({"success": True, "id": idea_id}), 201


@bp.post("/api/ideas/<int:idea_id>/upvote")
def upvote_idea_api(idea_id):
    if not idea_exists(idea_id):
        return jsonify({"success": False, "error": "NOT_FOUND"}), 404

    payload = request.get_json(silent=True) or {}
    user_id = (payload.get("user_id") or "").strip()
    if not user_id:
        return jsonify({"success": False, "error": "MISSING_USER_ID"}), 400

    inserted, upvotes = upvote_idea(idea_id, user_id)
    if inserted:
        return jsonify({"success": True, "upvotes": upvotes})
    return jsonify({"success": False, "already_voted": True, "upvotes": upvotes}), 200


@bp.post("/api/ideas/<int:idea_id>/comment")
def create_idea_comment_api(idea_id):
    if not idea_exists(idea_id):
        return jsonify({"success": False, "error": "NOT_FOUND"}), 404

    payload = request.get_json(silent=True) or {}
    author = (payload.get("author") or "").strip()
    comment = (payload.get("comment") or "").strip()
    rating = payload.get("rating")

    if not author or not comment:
        return jsonify({"success": False, "error": "MISSING_FIELDS"}), 400

    if rating is not None:
        try:
            rating_value = int(rating)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "INVALID_RATING"}), 400
        if rating_value < 1 or rating_value > 5:
            return jsonify({"success": False, "error": "INVALID_RATING"}), 400
    else:
        rating_value = None

    add_idea_comment(idea_id, author, comment, rating_value)
    return jsonify({"success": True}), 201


@bp.get("/api/service-desk/summary")
def get_service_desk_summary():
    summary = fetch_summary()
    return jsonify({"summary": summary})


@bp.get("/api/service-desk/requests")
def get_service_desk_requests():
    category = request.args.get("category") or None
    status = request.args.get("status") or None
    q = request.args.get("q") or None
    sort = request.args.get("sort") or "newest"

    tickets = fetch_tickets(category=category, status=status, q=q, sort=sort)
    return jsonify({"requests": tickets})


@bp.post("/api/service-desk/requests")
def create_service_desk_request():
    category = request.form.get("category")
    title = request.form.get("title")
    description = request.form.get("description")
    urgency = request.form.get("urgency") or "NORMAL"

    if not category or category not in CATEGORY_TO_TEAM:
        return jsonify({"error": "Invalid category"}), 400
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if urgency not in URGENCY_OPTIONS:
        return jsonify({"error": "Invalid urgency"}), 400

    attachment_file = request.files.get("attachment")
    attachment_path = _save_upload(attachment_file, "service_desk")
    attachment_name = attachment_file.filename if attachment_file else None

    ticket_id = create_ticket(
        {
            "category": category,
            "owner_team": CATEGORY_TO_TEAM[category],
            "title": title,
            "description": description,
            "requester": _pick_requester(),
            "urgency": urgency,
            "attachment_path": attachment_path,
            "attachment_name": attachment_name,
        }
    )

    return jsonify({"id": ticket_id}), 201


@bp.patch("/api/service-desk/requests/<int:ticket_id>/status")
def update_service_desk_request(ticket_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in STATUS_OPTIONS:
        return jsonify({"error": "Invalid status"}), 400

    updated_at = update_ticket_status(ticket_id, status)
    return jsonify({"id": ticket_id, "status": status, "updated_at": updated_at})


@bp.get("/api/nota-space/rooms")
def nota_space_rooms():
    return jsonify({"rooms": fetch_rooms()})


@bp.get("/api/nota-space/bookings")
def nota_space_bookings():
    if request.args.get("all"):
        return jsonify({"bookings": fetch_all_bookings()})

    month_value = request.args.get("month")
    if month_value:
        return jsonify({"month": month_value, "days": fetch_booking_days(month_value)})

    date_value = request.args.get("date")
    if not date_value:
        date_value = datetime.now().strftime("%Y-%m-%d")

    return jsonify({"date": date_value, "bookings": fetch_bookings(date_value)})


@bp.get("/api/nota-space/bookings/<int:booking_id>")
def nota_space_booking_detail(booking_id):
    booking = fetch_booking_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    return jsonify({"booking": booking})


@bp.get("/api/nota-space/meeting-logs")
def nota_space_meeting_logs():
    logs = fetch_meeting_logs()
    return jsonify({"logs": logs})


@bp.get("/api/nota-space/meeting-logs/<int:log_id>")
def nota_space_meeting_log_detail(log_id):
    log = fetch_meeting_log_by_id(log_id)
    if not log:
        return jsonify({"error": "Meeting log not found"}), 404
    return jsonify({"log": log})


@bp.post("/api/nota-space/meeting-summary")
def nota_space_meeting_summary():
    meeting_text = (request.form.get("meeting_text") or "").strip()
    audio_file = request.files.get("audio_file")

    if not meeting_text and not (audio_file and audio_file.filename):
        return jsonify({"error": "회의 내용 또는 녹음 파일을 추가하세요."}), 400

    audio_path = None
    transcript = ""
    if audio_file and audio_file.filename:
        audio_path = _save_upload(audio_file, "nota_space")
        if audio_path:
            absolute_audio = os.path.join(BASE_DIR, "app", audio_path.lstrip("/"))
            transcript = _transcribe_audio(absolute_audio)

    combined_parts = []
    if meeting_text:
        combined_parts.append(meeting_text)
    if transcript:
        combined_parts.append(f"녹음 텍스트:\n{transcript}")
    combined_text = "\n\n".join(combined_parts)
    if not combined_text.strip():
        return jsonify({"error": "녹음 텍스트를 추출하지 못했습니다."}), 400

    result, summary_error, summary_error_message = _summarize_with_openai_structured(combined_text)
    if not result:
        local_summary = _summarize_locally_structured(combined_text)
        summary_text = _render_summary_text(local_summary)
        return jsonify(
            {
                "summary": summary_text,
                "summary_json": local_summary,
                "summary_source": "local",
                "summary_warning": summary_error_message or summary_error or "AI 요약이 불가하여 로컬 요약으로 대체했습니다.",
            }
        )

    summary_text = _render_summary_text(result)
    return jsonify({"summary": summary_text, "summary_json": result, "summary_source": "openai"})




@bp.post("/api/nota-space/bookings")
def create_nota_space_booking():
    room_id = request.form.get("room_id")
    date_value = request.form.get("date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    agenda = request.form.get("agenda")
    presenter = request.form.get("presenter")
    participants_raw = request.form.get("participants") or ""

    if not all([room_id, date_value, start_time, end_time, agenda, presenter]):
        return jsonify({"error": "All fields are required"}), 400

    if start_time >= end_time:
        return jsonify({"error": "End time must be later than start time"}), 400

    try:
        room_id_value = int(room_id)
    except ValueError:
        return jsonify({"error": "Invalid room"}), 400

    if has_booking_conflict(room_id_value, date_value, start_time, end_time):
        return jsonify({"error": "Time slot already booked"}), 409

    participants = [name.strip() for name in participants_raw.split(",") if name.strip()]

    booking_id = create_booking(
        {
            "room_id": room_id_value,
            "date": date_value,
            "start_time": start_time,
            "end_time": end_time,
            "agenda": agenda,
            "presenter": presenter,
            "participants": participants,
        }
    )

    return jsonify({"id": booking_id}), 201


@bp.post("/api/nota-space/meeting-logs")
def create_nota_space_meeting_log():
    booking_id = request.form.get("booking_id")
    notes = (request.form.get("notes") or "").strip()
    audio_file = request.files.get("audio")
    title = (request.form.get("title") or "").strip()
    author = (request.form.get("author") or "").strip()
    meeting_date = request.form.get("meeting_date") or None
    start_time = request.form.get("start_time") or None
    end_time = request.form.get("end_time") or None
    room_name = (request.form.get("room_name") or "").strip() or None
    summary = (request.form.get("summary") or "").strip()

    if not booking_id and not title:
        return jsonify({"error": "Title is required for non-booking logs"}), 400
    if not booking_id and not author:
        return jsonify({"error": "Author is required for non-booking logs"}), 400
    if not notes and not (audio_file and audio_file.filename):
        return jsonify({"error": "회의 내용 또는 녹음 파일을 추가하세요."}), 400


    booking_id_value = None
    if booking_id:
        try:
            booking_id_value = int(booking_id)
        except ValueError:
            return jsonify({"error": "Invalid booking id"}), 400
        if not fetch_booking_by_id(booking_id_value):
            return jsonify({"error": "Booking not found"}), 404

    audio_path = None
    transcript = ""
    if audio_file and audio_file.filename:
        audio_path = _save_upload(audio_file, "nota_space")
        if audio_path:
            absolute_audio = os.path.join(BASE_DIR, "app", audio_path.lstrip("/"))
            transcript = _transcribe_audio(absolute_audio)

    combined_parts = []
    if notes:
        combined_parts.append(notes)
    if transcript:
        combined_parts.append(f"녹음 텍스트:\n{transcript}")
    combined_text = "\n\n".join(combined_parts)

    if not summary:
        result, _, _ = _summarize_with_openai_structured(combined_text)
        if not result:
            result = _summarize_locally_structured(combined_text)
        summary = _render_summary_text(result) if result else ""


    updated_at = upsert_meeting_log_entry(
        booking_id_value,
        notes or None,
        audio_path,
        transcript or None,
        summary or None,
        title=title or None,
        author=author or None,
        meeting_date=meeting_date,
        start_time=start_time,
        end_time=end_time,
        room_name=room_name,
    )

    return jsonify({"booking_id": booking_id_value, "summary": summary, "updated_at": updated_at}), 201
