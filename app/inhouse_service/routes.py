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

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None

from . import bp
from app.fixtures.seed_data import club_seed_store
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
    delete_idea,
    fetch_club_categories,
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


_SECTION_ORDER = ["목표", "범위", "결정", "실행", "리스크", "기타"]


def _detect_section_marker(sentence: str) -> str | None:
    s = (sentence or "").strip()
    if not s:
        return None
    # 섹션 제목 같은 짧은 문장 + "입니다." 종결을 우선 마커로 본다
    if len(s) <= 60 and (
        s.endswith("입니다.")
        or s.endswith("입니다")
        or s.endswith("정리합니다.")
        or s.endswith("정리합니다")
        or s.endswith("합니다.")
        or s.endswith("합니다")
    ):
        if "목표" in s:
            return "목표"
        if "범위" in s or "스코프" in s or "scope" in s or "핵심 범위" in s:
            return "범위"
        if "결정" in s:
            return "결정"
        if "실행" in s or "액션" in s or "action" in s or "할 일" in s:
            return "실행"
        if "리스크" in s or "위험" in s or "risk" in s:
            return "리스크"
    return None


def _group_sentences_by_sections(sentences: list[str]) -> dict[str, list[str]]:
    grouped = {k: [] for k in _SECTION_ORDER}
    current = "기타"
    for sent in sentences:
        marker = _detect_section_marker(sent)
        if marker:
            current = marker
            continue  # 마커 문장은 버린다
        grouped[current].append(sent)
    # 빈 섹션 정리(하지만 key는 유지)
    return grouped


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
    seen = set()

    action_kw = re.compile(r"(하기로|하자|진행|준비|작성|정리|공유|확인|세팅|설정|테스트|배포|점검|추가)", re.I)
    due_pat = re.compile(
        r"("
        r"(다음\s*주|이번\s*주)?\s*(월|화|수|목|금|토|일)\s*요일(까지)?"
        r"|[0-9]{4}[./-][0-9]{1,2}[./-][0-9]{1,2}"
        r"|[0-9]{1,2}\s*월\s*[0-9]{1,2}\s*일(까지)?"
        r"|[0-9]{1,2}[./-][0-9]{1,2}([./-][0-9]{1,2})?"
        r"|내일|모레|오늘"
        r")"
    )

    def normalize_due(value: str) -> str:
        due_value = (value or "").strip()
        if not due_value:
            return ""

        due_value = re.sub(r"\s+", " ", due_value)
        due_value = re.sub(r"(까지|까지입니다|까지 입니다)$", "", due_value).strip()

        match = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", due_value)
        if match:
            m = int(match.group(1))
            d = int(match.group(2))
            return f"{m}/{d}"

        match = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})(?:[./-](\d{1,2}))?", due_value)
        if match and match.group(3) is None:
            m = int(match.group(1))
            d = int(match.group(2))
            return f"{m}/{d}"

        match = re.fullmatch(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", due_value)
        if match:
            y = match.group(1)
            m = int(match.group(2))
            d = int(match.group(3))
            return f"{y}-{m:02d}-{d:02d}"

        return due_value

    def clean_task(sentence_text: str, owner: str, due_value: str) -> str:
        task_value = (sentence_text or "").strip()

        if owner:
            task_value = re.sub(rf"^{re.escape(owner)}(은|는|이|가)\s+", "", task_value)

        if due_value and due_value != "미정":
            task_value = re.sub(rf"\b{re.escape(due_value)}\b", "", task_value)
        task_value = re.sub(
            r"(\d{1,2}\s*월\s*\d{1,2}\s*일\s*까지|\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}[./-]\d{1,2}([./-]\d{1,2})?\s*까지?)",
            "",
            task_value,
        )

        task_value = re.sub(r"(하도록\s*합니다|하기로\s*합니다|하겠습니다|합니다|한다|한다\.)$", "", task_value).strip()
        task_value = task_value.strip(" .·•-–—")
        task_value = re.sub(r"\s+", " ", task_value).strip()
        return task_value

    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue

        owner_match = re.search(r"(담당자|담당)\s*[:：]\s*([A-Za-z가-힣]{2,10})", s)
        due_match = re.search(r"(기한|마감|due)\s*[:：]\s*(.+)$", s, re.I)
        task_match = re.search(r"(할\s*일|작업|todo|task)\s*[:：]\s*(.+)$", s, re.I)
        natural_owner = re.match(r"^([A-Za-z가-힣]{2,10})(?:은|는|이|가)\s+", s)

        owner = owner_match.group(2).strip() if owner_match else ""
        due = ""
        task = ""

        if task_match:
            task = task_match.group(2).strip()

        if due_match:
            due = due_match.group(2).strip()
        else:
            m = due_pat.search(s)
            if m:
                due = m.group(1).strip()

        if not owner and natural_owner:
            owner = natural_owner.group(1).strip()

        due = normalize_due(due)

        if (owner_match or due_match or task_match) and (task or s):
            task = task or s
        else:
            if not (action_kw.search(s) or natural_owner):
                continue
            task = s

        task = clean_task(task, owner, due)
        if not task:
            continue

        key = (owner, task, due)
        if key in seen:
            continue
        seen.add(key)

        items.append({"owner": owner or "미정", "task": task[:120], "due": due or "미정"})

        if len(items) >= 10:
            break

    return items


def _extract_decisions(sentences: list[str]) -> list[str]:
    decision_keywords = re.compile(r"(결정|하기로|확정|승인|합의|채택|결론)", re.I)
    decisions: list[str] = []
    seen = set()
    for sentence in sentences:
        if _detect_section_marker(sentence):
            continue
        if re.search(r"(결정된\s*사항|결정\s*사항)\s*입니다\.?$", (sentence or "").strip()):
            continue
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

    grouped_sections = _group_sentences_by_sections(sentences)
    section_non_empty = sum(
        1
        for key in ("목표", "범위", "결정", "실행", "리스크")
        if grouped_sections.get(key)
    )
    section_mode = section_non_empty >= 2

    def clean_bullet(sentence_text: str) -> str:
        t = (sentence_text or "").strip()
        if _detect_section_marker(t):
            return ""
        t = re.sub(r"^\s*[-*•]\s*", "", t).strip()
        t = t.strip(" .·•-–—")
        return t

    def pick_one(sent_list: list[str]) -> str:
        for s in sent_list or []:
            t = clean_bullet(s)
            if t:
                return t[:120]
        return ""

    if section_mode:
        goals = [clean_bullet(s) for s in (grouped_sections.get("목표") or [])]
        goals = [s for s in goals if s]
        scope = [clean_bullet(s) for s in (grouped_sections.get("범위") or [])]
        scope = [s for s in scope if s]
        risks = [clean_bullet(s) for s in (grouped_sections.get("리스크") or [])]
        risks = [s for s in risks if s]
        misc = [clean_bullet(s) for s in (grouped_sections.get("기타") or [])]
        misc = [s for s in misc if s]

        decisions = []
        seen_decisions = set()
        for s in grouped_sections.get("결정") or []:
            t = clean_bullet(s)
            if not t:
                continue
            if t in seen_decisions:
                continue
            seen_decisions.add(t)
            decisions.append(t)
            if len(decisions) >= 6:
                break

        action_items = _extract_action_items(grouped_sections.get("실행") or [])
        if not action_items:
            action_items = _extract_action_items(sentences)

        topics = []
        if goals:
            topics.append({"title": "목표", "summary_bullets": goals[:4], "decisions": []})
        if scope:
            topics.append({"title": "범위", "summary_bullets": scope[:4], "decisions": []})
        if risks:
            topics.append({"title": "리스크", "summary_bullets": risks[:4], "decisions": []})
        if misc:
            topics.append({"title": "기타", "summary_bullets": misc[:4], "decisions": []})

        overall_sentences = []
        for part in (pick_one(goals), pick_one(scope), pick_one(decisions)):
            if part:
                overall_sentences.append(part)
        overall_summary = " ".join(overall_sentences[:3]).strip()

        return {
            "title": _pick_title(input_text, sentences),
            "topics": topics[:6],
            "action_items": action_items[:10],
            "overall_summary": overall_summary,
            "decisions": decisions[:6],
        }

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

    top_terms = [w for w, _ in Counter(filtered).most_common(12) if not re.fullmatch(r"[0-9]+", str(w))]
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
    key_points = [s for _, s in scored[:12]] if scored else sentences[:8]

    overall_pieces = []
    for s in key_points:
        if s not in overall_pieces:
            overall_pieces.append(s)
        if len(overall_pieces) >= 5:
            break
    if decisions:
        for decision in decisions:
            if decision and decision not in overall_pieces:
                overall_pieces.append(decision)
                break
    overall_summary = " ".join(overall_pieces).strip()

    def contains_term(sentence: str, term: str) -> bool:
        if not term:
            return False
        if re.fullmatch(r"[A-Za-z]+", term or ""):
            return term.lower() in sentence.lower()
        return term in sentence

    grouped: dict[str, list[str]] = {}
    for sentence in key_points:
        assigned = None
        for term in top_terms[:10]:
            if contains_term(sentence, term):
                assigned = term
                break
        grouped.setdefault(assigned or "기타", []).append(sentence)

    candidates = []
    for term, group_sentences in grouped.items():
        if term == "기타":
            continue
        group_score = sum(score(s) for s in group_sentences)
        candidates.append((len(group_sentences), group_score, term))
    candidates.sort(key=lambda x: (-x[0], -x[1]))

    topics = [{"title": "주요 논의", "summary_bullets": key_points[:10], "decisions": []}]

    for _, __, term in candidates[:3]:
        group_sentences = grouped.get(term, [])
        ranked = sorted(group_sentences, key=lambda s: (-score(s), key_points.index(s)))
        bullets = []
        for s in ranked:
            if s and s not in bullets:
                bullets.append(s)
            if len(bullets) >= 5:
                break
        if bullets:
            topics.append({"title": str(term), "summary_bullets": bullets, "decisions": []})
        if len(topics) >= 4:
            break

    if decisions:
        topics.append({"title": "결정", "summary_bullets": decisions[:10], "decisions": decisions[:12]})

    action_bullets = []
    for item in action_items[:10]:
        owner = (item or {}).get("owner") or "미정"
        task = (item or {}).get("task") or ""
        due = (item or {}).get("due") or "미정"
        if task:
            action_bullets.append(f"{owner} - {task} (~ {due})")
    if action_bullets:
        topics.append({"title": "실행", "summary_bullets": action_bullets[:10], "decisions": []})

    if len(topics) < 3 and grouped.get("기타"):
        topics.append({"title": "기타", "summary_bullets": grouped.get("기타", [])[:8], "decisions": []})

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


def _current_user_id() -> str:
    return "user_001"


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


def _summarize_with_gemini(text: str) -> tuple[dict | None, str | None, str | None]:
    input_text = _truncate_meeting_text(text)
    if not input_text:
        return None, "EMPTY_INPUT", "요약할 텍스트가 없습니다."

    api_key = "AIzaSyDiYCgUeH_ODhSlHQb40rgMHLYKKdXmi1I"
    if not api_key:
        return (
            None,
            "GEMINI_API_KEY_MISSING",
            "서버에 GOOGLE_API_KEY(또는 GEMINI_API_KEY)가 설정되지 않았습니다. (instance/.env 또는 환경변수 확인)",
        )

    if genai is None:
        return None, "GEMINI_SDK_MISSING", "google-generativeai 패키지가 설치되지 않았습니다. (requirements.txt 확인)"

    try:
        genai.configure(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "models/gemini-flash-latest")
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"},
        )

        system_prompt = (
            "너는 회의록 요약 전문가다. 입력된 텍스트는 STT 결과물이라 오타가 많으니 문맥을 파악해 정제해라.\n"
            "다음 JSON 구조를 엄격히 지켜서 출력해라:\n"
            "{\n"
            '  "title": "회의 제목",\n'
            '  "topics": [\n'
            '    {"title": "주제", "summary_bullets": ["요약1", "요약2"], "decisions": ["결정사항"]}\n'
            "  ],\n"
            '  "action_items": [\n'
            '    {"owner": "담당자", "task": "할일", "due": "기한"}\n'
            "  ],\n"
            '  "overall_summary": "전체 요약"\n'
            "}\n"
        )

        response = model.generate_content(f"{system_prompt}\n\n[회의 내용]\n{input_text}")
        output_text = (getattr(response, "text", None) or "").strip()

        if output_text.startswith("```"):
            output_text = re.sub(r"^```[a-zA-Z]*\n?", "", output_text).strip()
            output_text = re.sub(r"\n?```$", "", output_text).strip()

        parsed = json.loads(output_text or "{}")
        if not isinstance(parsed, dict):
            return None, "GEMINI_INVALID_RESPONSE", "Gemini 응답을 파싱하지 못했습니다."
        return parsed, None, None
    except Exception as exc:
        print(f"❌ Gemini 요약 실패: {exc}")
        return None, "GEMINI_ERROR", str(exc)


def _render_summary_text(summary: dict) -> str:
    title = (summary or {}).get("title") or ""
    topics = (summary or {}).get("topics") or []
    decisions_all = list((summary or {}).get("decisions") or [])
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
            owner = (action or {}).get("owner") or "미정"
            task = (action or {}).get("task") or ""
            due = (action or {}).get("due") or "미정"
            task = (task or "").strip()
            if not task:
                continue
            lines.append(f"- {owner} | {task} (기한: {due})")
    else:
        lines.append("- (없음)")
    lines.append("")

    lines.append("🧾 전체 요약")
    lines.append(overall_summary)
    return "\n".join(lines).strip()

@bp.get("/")
def home():
    return redirect(url_for("inhouse_service.service_desk"))


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
    return render_template("club/club.html", active="clubs", club_categories=fetch_club_categories())


@bp.get("/api/clubs/categories")
def get_club_categories():
    return jsonify({"categories": fetch_club_categories()})


@bp.get("/api/clubs/seed")
def get_club_seed():
    return jsonify(club_seed_store(_current_user_id()))


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


@bp.delete("/api/ideas/<int:idea_id>")
def delete_idea_api(idea_id):
    if not idea_exists(idea_id):
        return jsonify({"success": False, "error": "NOT_FOUND"}), 404

    deleted = delete_idea(idea_id)
    if not deleted:
        return jsonify({"success": False, "error": "DELETE_FAILED"}), 500

    return jsonify({"success": True})


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
            "requester_user_id": _current_user_id(),
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

    print(f"🚀 Gemini 요약 요청 시작! (텍스트 길이: {len(combined_text)})")

    result, summary_error, summary_error_message = _summarize_with_gemini(combined_text)
    if not result:
        print("\n" + "!" * 50)
        print("❌ Gemini 요약 실패! 원인을 확인하세요.")
        print(f"👉 에러 코드: {summary_error}")
        print(f"👉 에러 메시지: {summary_error_message}")
        print("!" * 50 + "\n")

        local_summary = _summarize_locally_structured(combined_text)
        summary_text = _render_summary_text(local_summary)
        return jsonify(
            {
                "summary": summary_text,
                "summary_json": local_summary,
                "summary_source": "local",
                "summary_warning": (
                    f"AI 요약 실패({summary_error}): {summary_error_message}. 로컬 알고리즘으로 대체됨."
                    if (summary_error or summary_error_message)
                    else "AI 요약이 불가하여 로컬 요약으로 대체했습니다."
                ),
            }
        )

    print("✅ Gemini 요약 성공!")
    summary_text = _render_summary_text(result)
    return jsonify({"summary": summary_text, "summary_json": result, "summary_source": "gemini"})




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
        result, _, _ = _summarize_with_gemini(combined_text)
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
