import os
import random
import time
from datetime import datetime

from flask import jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from . import bp
from app.db import (
    BASE_DIR,
    CATEGORY_TO_TEAM,
    STATUS_OPTIONS,
    URGENCY_OPTIONS,
    create_booking,
    create_ticket,
    fetch_bookings,
    fetch_rooms,
    fetch_summary,
    fetch_tickets,
    has_booking_conflict,
    upsert_meeting_log,
    update_ticket_status,
)

REQUESTER_POOL = ["김민수", "이서연", "박준호", "최지우", "정하늘", "오유진", "nota_inhouse"]

_WHISPER_MODEL = None
_SUMMARY_PIPELINE = None


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


def _transcribe_audio(audio_path):
    global _WHISPER_MODEL
    if not audio_path:
        return ""

    try:
        import whisper

        if _WHISPER_MODEL is None:
            _WHISPER_MODEL = whisper.load_model("base")
        result = _WHISPER_MODEL.transcribe(audio_path)
        return (result.get("text") or "").strip()
    except Exception:
        return ""


def _summarize_text(text):
    global _SUMMARY_PIPELINE
    if not text:
        return ""

    try:
        from transformers import pipeline

        if _SUMMARY_PIPELINE is None:
            _SUMMARY_PIPELINE = pipeline("text2text-generation", model="google/flan-t5-small")
        prompt = (
            "Summarize the following meeting notes into:\n"
            "1. Key discussion points\n"
            "2. Decisions made\n"
            "3. Action items\n\n"
            f"Notes:\n{text}"
        )
        output = _SUMMARY_PIPELINE(prompt, max_length=256, min_length=80, do_sample=False)
        return (output[0].get("generated_text") or "").strip()
    except Exception:
        return "AI summary unavailable."


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
    return render_template("nota_space_room_booking.html", active="nota-space", subnav="room-booking")


@bp.get("/nota-space/meeting-log")
def nota_space_meeting_log():
    return render_template("nota_space_meeting_log.html", active="nota-space", subnav="meeting-log")


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
    date_value = request.args.get("date")
    if not date_value:
        date_value = datetime.now().strftime("%Y-%m-%d")

    return jsonify({"date": date_value, "bookings": fetch_bookings(date_value)})


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

    if not booking_id:
        return jsonify({"error": "booking_id is required"}), 400

    if not notes and not (audio_file and audio_file.filename):
        return jsonify({"error": "Audio or notes required"}), 400

    try:
        booking_id_value = int(booking_id)
    except ValueError:
        return jsonify({"error": "Invalid booking id"}), 400

    audio_path = None
    transcript = ""
    if audio_file and audio_file.filename:
        audio_path = _save_upload(audio_file, "nota_space")
        if audio_path:
            absolute_audio = os.path.join(BASE_DIR, "app", audio_path.lstrip("/"))
            transcript = _transcribe_audio(absolute_audio)

    combined_text = "\n".join([text for text in [notes, transcript] if text])
    summary = _summarize_text(combined_text) if combined_text else "AI summary unavailable."

    updated_at = upsert_meeting_log(
        booking_id_value,
        notes or None,
        audio_path,
        transcript or None,
        summary or None,
    )

    return jsonify({"booking_id": booking_id_value, "summary": summary, "updated_at": updated_at}), 201
