import os
import random
import sqlite3
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "instance", "service_desk.db")

CATEGORY_TO_TEAM = {
    "IT": "보안팀",
    "PURCHASE": "경영지원팀",
    "FACILITY": "총무팀",
}

STATUS_OPTIONS = ["PENDING", "APPROVED", "REJECTED", "COMPLETED"]
URGENCY_OPTIONS = ["LOW", "NORMAL", "URGENT"]


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS service_desk_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                owner_team TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                requester TEXT NOT NULL,
                status TEXT NOT NULL,
                urgency TEXT NOT NULL,
                attachment_name TEXT,
                attachment_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(service_desk_tickets)").fetchall()]
        if "attachment_name" not in columns:
            conn.execute("ALTER TABLE service_desk_tickets ADD COLUMN attachment_name TEXT")
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM service_desk_tickets").fetchone()[0]
        if count == 0:
            seed_tickets(conn)


def seed_tickets(conn):
    titles = [
        "노트북 보안 패치 문의",
        "VPN 접속 오류",
        "맥북 충전기 교체",
        "프로젝터 HDMI 케이블 요청",
        "회의실 조명 수리 요청",
        "에어컨 냉방 불량",
        "사무용 의자 구매",
        "모니터 암 구매",
        "랜선 교체 요청",
        "출입카드 재발급",
        "프린터 토너 교체",
        "책상 높이 조절 수리",
        "노트북 SSD 교체",
        "사무실 소독 일정 문의",
        "공용 태블릿 구매",
    ]
    descriptions = [
        "긴급 확인 부탁드립니다.",
        "증상이 반복되고 있습니다.",
        "필요 수량 2개입니다.",
        "사진 첨부했습니다.",
        "업무에 영향이 있습니다.",
    ]
    requesters = ["김민수", "이서연", "박준호", "최지우", "정하늘", "오유진"]
    categories = list(CATEGORY_TO_TEAM.keys())

    now = datetime.now()
    samples = []
    for i in range(12):
        category = random.choice(categories)
        status = random.choice(STATUS_OPTIONS)
        urgency = random.choice(URGENCY_OPTIONS)
        created_at = (now - timedelta(days=random.randint(0, 18), hours=random.randint(0, 8))).isoformat(
            timespec="seconds"
        )
        samples.append(
            {
                "category": category,
                "owner_team": CATEGORY_TO_TEAM[category],
                "title": titles[i % len(titles)],
                "description": random.choice(descriptions),
                "requester": random.choice(requesters),
                "status": status,
                "urgency": urgency,
                "attachment_name": None,
                "attachment_path": None,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

    conn.executemany(
        """
        INSERT INTO service_desk_tickets (
            category, owner_team, title, description, requester, status,
            urgency, attachment_name, attachment_path, created_at, updated_at
        ) VALUES (
            :category, :owner_team, :title, :description, :requester, :status,
            :urgency, :attachment_name, :attachment_path, :created_at, :updated_at
        )
        """,
        samples,
    )
    conn.commit()


def fetch_tickets(category=None, status=None, q=None, sort="newest"):
    sql = "SELECT * FROM service_desk_tickets WHERE 1=1"
    params = {}

    if category:
        sql += " AND category = :category"
        params["category"] = category
    if status:
        sql += " AND status = :status"
        params["status"] = status
    if q:
        sql += " AND (title LIKE :q OR requester LIKE :q)"
        params["q"] = f"%{q}%"

    if sort == "oldest":
        sql += " ORDER BY created_at ASC"
    elif sort == "pending_oldest":
        sql += """
            ORDER BY
                (julianday(updated_at) - julianday(created_at)) DESC,
                created_at DESC
        """
    elif sort == "urgency":
        sql += """
            ORDER BY
                CASE urgency
                    WHEN 'URGENT' THEN 0
                    WHEN 'NORMAL' THEN 1
                    ELSE 2
                END,
                created_at DESC
        """
    else:
        sql += " ORDER BY created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def fetch_summary():
    summary = {
        "by_category": {},
        "by_status": {},
        "by_category_status": {},
        "by_status_category": {},
    }

    for category in CATEGORY_TO_TEAM:
        summary["by_category"][category] = 0
        summary["by_category_status"][category] = {}
        for status in STATUS_OPTIONS:
            summary["by_category_status"][category][status] = 0

    for status in STATUS_OPTIONS:
        summary["by_status"][status] = 0
        summary["by_status_category"][status] = {}
        for category in CATEGORY_TO_TEAM:
            summary["by_status_category"][status][category] = 0

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT category, status, COUNT(*) as count
            FROM service_desk_tickets
            GROUP BY category, status
            """
        ).fetchall()

    for row in rows:
        category = row["category"]
        status = row["status"]
        count = row["count"]
        if category in summary["by_category"]:
            summary["by_category"][category] += count
            summary["by_category_status"][category][status] += count
        if status in summary["by_status"]:
            summary["by_status"][status] += count
            summary["by_status_category"][status][category] += count

    return summary


def create_ticket(data):
    now = _now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO service_desk_tickets (
                category, owner_team, title, description, requester, status,
                urgency, attachment_name, attachment_path, created_at, updated_at
            ) VALUES (
                :category, :owner_team, :title, :description, :requester, :status,
                :urgency, :attachment_name, :attachment_path, :created_at, :updated_at
            )
            """,
            {
                "category": data["category"],
                "owner_team": data["owner_team"],
                "title": data["title"],
                "description": data.get("description") or "",
                "requester": data["requester"],
                "status": data.get("status", "PENDING"),
                "urgency": data.get("urgency", "NORMAL"),
                "attachment_name": data.get("attachment_name"),
                "attachment_path": data.get("attachment_path"),
                "created_at": now,
                "updated_at": now,
            },
        )
        conn.commit()
        ticket_id = cur.lastrowid

    return ticket_id


def update_ticket_status(ticket_id, status):
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE service_desk_tickets
            SET status = :status, updated_at = :updated_at
            WHERE id = :id
            """,
            {"status": status, "updated_at": now, "id": ticket_id},
        )
        conn.commit()

    return now
