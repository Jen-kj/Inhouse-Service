import os
import random
import time

from flask import jsonify, render_template, request
from werkzeug.utils import secure_filename

from . import bp
from app.db import (
    BASE_DIR,
    CATEGORY_TO_TEAM,
    STATUS_OPTIONS,
    URGENCY_OPTIONS,
    create_ticket,
    fetch_summary,
    fetch_tickets,
    update_ticket_status,
)

REQUESTER_POOL = ["김민수", "이서연", "박준호", "최지우", "정하늘", "오유진", "nota_inhouse"]


def _pick_requester():
    return random.choice(REQUESTER_POOL)


@bp.get("/")
def home():
    return render_template("empty_page.html", active="")


@bp.get("/service-desk")
def service_desk():
    return render_template("service_desk.html", active="service-desk")


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

    attachment_path = None
    attachment_name = None
    file = request.files.get("attachment")
    if file and file.filename:
        filename = secure_filename(file.filename)
        if filename:
            attachment_name = filename
            upload_dir = os.path.join(BASE_DIR, "app", "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            stored_name = f"{int(time.time())}_{filename}"
            file.save(os.path.join(upload_dir, stored_name))
            attachment_path = f"/static/uploads/{stored_name}"

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
