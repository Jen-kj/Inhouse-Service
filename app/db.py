import os
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
IDEA_STATUS_OPTIONS = ["새로운 제안", "검토 중", "해결 완료"]
DEFAULT_CLUB_CATEGORIES = ["운동/건강", "취미/문화"]


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
                requester_user_id TEXT,
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
        if "requester_user_id" not in columns:
            conn.execute("ALTER TABLE service_desk_tickets ADD COLUMN requester_user_id TEXT")
        conn.commit()

        _backfill_service_desk_requesters(conn)
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM service_desk_tickets").fetchone()[0]
        if count == 0:
            seed_tickets(conn)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                feature TEXT NOT NULL,
                recommended_use TEXT NOT NULL,
                capacity INTEGER,
                room_type TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                agenda TEXT NOT NULL,
                presenter TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(room_id) REFERENCES rooms(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meeting_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                participant_name TEXT NOT NULL,
                FOREIGN KEY(booking_id) REFERENCES bookings(id)
            )
            """
        )
        _ensure_meeting_logs_schema(conn)
        conn.commit()

        room_count = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        if room_count == 0:
            seed_rooms(conn)

        _ensure_idea_hub_schema(conn)
        _backfill_idea_authors(conn)
        conn.commit()

        idea_count = conn.execute("SELECT COUNT(*) FROM ideas").fetchone()[0]
        if idea_count == 0:
            seed_ideas(conn)
            conn.commit()

        _ensure_club_schema(conn)
        conn.commit()


def _ensure_club_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS club_categories (
            name TEXT PRIMARY KEY,
            sort_order INTEGER NOT NULL
        )
        """
    )

    existing = {
        row["name"]
        for row in conn.execute("SELECT name FROM club_categories ORDER BY sort_order, name").fetchall()
    }
    if existing:
        return

    for index, name in enumerate(DEFAULT_CLUB_CATEGORIES):
        conn.execute(
            "INSERT OR IGNORE INTO club_categories (name, sort_order) VALUES (:name, :sort_order)",
            {"name": name, "sort_order": index},
        )


def fetch_club_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM club_categories ORDER BY sort_order, name").fetchall()
        return [row["name"] for row in rows] or list(DEFAULT_CLUB_CATEGORIES)


def seed_tickets(conn):
    from app.fixtures.seed_data import service_desk_seed_tickets, user_name

    now_iso = _now_iso()
    samples = []
    for item in service_desk_seed_tickets(now_iso):
        requester_user_id = item.get("requester_user_id")
        samples.append(
            {
                "category": item["category"],
                "owner_team": item["owner_team"],
                "title": item["title"],
                "description": item.get("description") or "",
                "requester": user_name(requester_user_id) or "nota_inhouse",
                "requester_user_id": requester_user_id,
                "status": item.get("status") or "PENDING",
                "urgency": item.get("urgency") or "NORMAL",
                "attachment_name": None,
                "attachment_path": None,
                "created_at": item.get("created_at") or now_iso,
                "updated_at": now_iso,
            }
        )

    conn.executemany(
        """
        INSERT INTO service_desk_tickets (
            category,
            owner_team,
            title,
            description,
            requester,
            requester_user_id,
            status,
            urgency,
            attachment_name,
            attachment_path,
            created_at,
            updated_at
        ) VALUES (
            :category,
            :owner_team,
            :title,
            :description,
            :requester,
            :requester_user_id,
            :status,
            :urgency,
            :attachment_name,
            :attachment_path,
            :created_at,
            :updated_at
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
    from app.fixtures.seed_data import find_user_id_by_name, user_name

    requester_user_id = (data.get("requester_user_id") or "").strip() or None
    requester = (data.get("requester") or "").strip() or None
    if requester_user_id and not requester:
        requester = user_name(requester_user_id) or requester_user_id
    if requester and not requester_user_id:
        requester_user_id = find_user_id_by_name(requester)
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO service_desk_tickets (
                category, owner_team, title, description, requester, requester_user_id, status,
                urgency, attachment_name, attachment_path, created_at, updated_at
            ) VALUES (
                :category, :owner_team, :title, :description, :requester, :requester_user_id, :status,
                :urgency, :attachment_name, :attachment_path, :created_at, :updated_at
            )
            """,
            {
                "category": data["category"],
                "owner_team": data["owner_team"],
                "title": data["title"],
                "description": data.get("description") or "",
                "requester": requester or "nota_inhouse",
                "requester_user_id": requester_user_id,
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


def seed_rooms(conn):
    rooms = [
    {
        "name": "Disagree & Commit",
        "feature": "대회의실",
        "recommended_use": "전사 미팅, 세미나, 격렬한 논의",
        "capacity": 16,
        "room_type": "meeting",
    },
    {
        "name": "Ownership",
        "feature": "원형 테이블",
        "recommended_use": "아이디어 브레인스토밍, 직급 없는 토론",
        "capacity": 8,
        "room_type": "meeting",
    },
    {
        "name": "Customer-Centric",
        "feature": "탁구대 테이블",
        "recommended_use": "고객 중심 의사결정, 액션 아이템 도출",
        "capacity": 8,
        "room_type": "meeting",
    },
    {
        "name": "Trust",
        "feature": "외부 미팅용",
        "recommended_use": "외부 미팅, 보안이 필요한 논의",
        "capacity": 6,
        "room_type": "meeting",
    },
    {
        "name": "Focus Room",
        "feature": "1인 집중실",
        "recommended_use": "딥 워크, 개인 통화",
        "capacity": 1,
        "room_type": "focus",
    },
    {
        "name": "Coworking Space",
        "feature": "We-yard 테이블",
        "recommended_use": "모각코, 협업 작업, 자유로운 아이디어 논의",
        "capacity": 12,
        "room_type": "coworking",
    },
]


    conn.executemany(
        """
        INSERT INTO rooms (name, feature, recommended_use, capacity, room_type)
        VALUES (:name, :feature, :recommended_use, :capacity, :room_type)
        """,
        rooms,
    )
    conn.commit()


def fetch_rooms():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM rooms ORDER BY name ASC").fetchall()
    return [dict(row) for row in rows]


def fetch_bookings(date_value):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT b.*, r.name as room_name, r.room_type, r.feature, r.recommended_use, r.capacity
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            WHERE b.date = :date
            ORDER BY b.start_time ASC
            """,
            {"date": date_value},
        ).fetchall()

        participants = conn.execute(
            """
            SELECT booking_id, participant_name
            FROM meeting_participants
            WHERE booking_id IN (
                SELECT id FROM bookings WHERE date = :date
            )
            """,
            {"date": date_value},
        ).fetchall()

        logs = conn.execute(
            """
            SELECT booking_id, summary, notes, audio_path, transcript
            FROM meeting_logs
            WHERE booking_id IN (
                SELECT id FROM bookings WHERE date = :date
            )
            """,
            {"date": date_value},
        ).fetchall()

    participants_map = {}
    for row in participants:
        participants_map.setdefault(row["booking_id"], []).append(row["participant_name"])

    logs_map = {row["booking_id"]: dict(row) for row in logs}

    result = []
    for row in rows:
        item = dict(row)
        item["participants"] = participants_map.get(row["id"], [])
        item["log"] = logs_map.get(row["id"])
        result.append(item)
    return result


def fetch_all_bookings():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT b.*, r.name as room_name, r.room_type, r.feature, r.recommended_use, r.capacity
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            ORDER BY b.date DESC, b.start_time DESC
            """
        ).fetchall()

    result = [dict(row) for row in rows]
    return result


def fetch_booking_days(month_value):
    month_like = f"{month_value}-%"
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT date, COUNT(*) as count
            FROM bookings
            WHERE date LIKE :month
            GROUP BY date
            """,
            {"month": month_like},
        ).fetchall()
    return {row["date"]: row["count"] for row in rows}


def create_booking(data):
    now = _now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO bookings (
                room_id, date, start_time, end_time, agenda, presenter, created_at, updated_at
            ) VALUES (
                :room_id, :date, :start_time, :end_time, :agenda, :presenter, :created_at, :updated_at
            )
            """,
            {
                "room_id": data["room_id"],
                "date": data["date"],
                "start_time": data["start_time"],
                "end_time": data["end_time"],
                "agenda": data["agenda"],
                "presenter": data["presenter"],
                "created_at": now,
                "updated_at": now,
            },
        )
        booking_id = cur.lastrowid

        participants = data.get("participants") or []
        if participants:
            conn.executemany(
                """
                INSERT INTO meeting_participants (booking_id, participant_name)
                VALUES (:booking_id, :participant_name)
                """,
                [{"booking_id": booking_id, "participant_name": name} for name in participants],
            )

        conn.commit()

    return booking_id


def has_booking_conflict(room_id, date_value, start_time, end_time):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM bookings
            WHERE room_id = :room_id
              AND date = :date
              AND NOT (end_time <= :start_time OR start_time >= :end_time)
            """,
            {
                "room_id": room_id,
                "date": date_value,
                "start_time": start_time,
                "end_time": end_time,
            },
        ).fetchone()
    return row["count"] > 0


def upsert_meeting_log(booking_id, notes, audio_path, transcript, summary):
    return upsert_meeting_log_entry(
        booking_id=booking_id,
        notes=notes,
        audio_path=audio_path,
        transcript=transcript,
        summary=summary,
    )


def _ensure_meeting_logs_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meeting_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER UNIQUE,
            notes TEXT,
            audio_path TEXT,
            transcript TEXT,
            summary TEXT,
            title TEXT,
            author TEXT,
            meeting_date TEXT,
            start_time TEXT,
            end_time TEXT,
            room_name TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(booking_id) REFERENCES bookings(id)
        )
        """
    )

    columns = [row["name"] for row in conn.execute("PRAGMA table_info(meeting_logs)").fetchall()]
    required = {
        "title",
        "author",
        "meeting_date",
        "start_time",
        "end_time",
        "room_name",
    }
    if required.issubset(set(columns)):
        return

    conn.execute(
        """
        CREATE TABLE meeting_logs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER UNIQUE,
            notes TEXT,
            audio_path TEXT,
            transcript TEXT,
            summary TEXT,
            title TEXT,
            author TEXT,
            meeting_date TEXT,
            start_time TEXT,
            end_time TEXT,
            room_name TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(booking_id) REFERENCES bookings(id)
        )
        """
    )

    conn.execute(
        """
        INSERT INTO meeting_logs_new (
            id, booking_id, notes, audio_path, transcript, summary, created_at, updated_at
        )
        SELECT id, booking_id, notes, audio_path, transcript, summary, created_at, updated_at
        FROM meeting_logs
        """
    )
    conn.execute("DROP TABLE meeting_logs")
    conn.execute("ALTER TABLE meeting_logs_new RENAME TO meeting_logs")


def fetch_booking_by_id(booking_id):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT b.*, r.name as room_name, r.room_type, r.feature, r.recommended_use, r.capacity
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            WHERE b.id = :booking_id
            """,
            {"booking_id": booking_id},
        ).fetchone()

        participants = conn.execute(
            """
            SELECT participant_name
            FROM meeting_participants
            WHERE booking_id = :booking_id
            """,
            {"booking_id": booking_id},
        ).fetchall()

        log = conn.execute(
            """
            SELECT id, summary, notes, audio_path, transcript
            FROM meeting_logs
            WHERE booking_id = :booking_id
            """,
            {"booking_id": booking_id},
        ).fetchone()

    if not row:
        return None

    result = dict(row)
    result["participants"] = [p["participant_name"] for p in participants]
    result["log"] = dict(log) if log else None
    return result


def fetch_meeting_logs():
    with get_connection() as conn:
        booking_rows = conn.execute(
            """
            SELECT
                ml.id as log_id,
                b.id as booking_id,
                b.date as meeting_date,
                b.start_time,
                b.end_time,
                r.name as room_name,
                b.agenda as agenda,
                b.presenter as presenter,
                ml.summary as summary,
                CASE WHEN ml.id IS NULL THEN 0 ELSE 1 END as has_log
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            LEFT JOIN meeting_logs ml ON ml.booking_id = b.id
            """
        ).fetchall()

        direct_rows = conn.execute(
            """
            SELECT
                ml.id as log_id,
                NULL as booking_id,
                ml.meeting_date,
                ml.start_time,
                ml.end_time,
                ml.room_name,
                ml.title as agenda,
                ml.author as presenter,
                ml.summary as summary,
                1 as has_log
            FROM meeting_logs ml
            WHERE ml.booking_id IS NULL
            """
        ).fetchall()

    combined = [dict(row) for row in booking_rows] + [dict(row) for row in direct_rows]
    combined.sort(
        key=lambda item: (
            item.get("meeting_date") or "",
            item.get("start_time") or "",
        ),
        reverse=True,
    )
    return combined


def fetch_meeting_log_by_id(log_id):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, booking_id, title, author, meeting_date, start_time, end_time, room_name,
                   notes, audio_path, transcript, summary, created_at, updated_at
            FROM meeting_logs
            WHERE id = :log_id
            """,
            {"log_id": log_id},
        ).fetchone()
    return dict(row) if row else None


def upsert_meeting_log_entry(
    booking_id,
    notes,
    audio_path,
    transcript,
    summary,
    title=None,
    author=None,
    meeting_date=None,
    start_time=None,
    end_time=None,
    room_name=None,
):
    now = _now_iso()
    with get_connection() as conn:
        if booking_id is not None:
            existing = conn.execute(
                "SELECT id FROM meeting_logs WHERE booking_id = :booking_id",
                {"booking_id": booking_id},
            ).fetchone()
        else:
            existing = None

        if existing:
            conn.execute(
                """
                UPDATE meeting_logs
                SET notes = :notes,
                    audio_path = :audio_path,
                    transcript = :transcript,
                    summary = :summary,
                    updated_at = :updated_at
                WHERE booking_id = :booking_id
                """,
                {
                    "notes": notes,
                    "audio_path": audio_path,
                    "transcript": transcript,
                    "summary": summary,
                    "updated_at": now,
                    "booking_id": booking_id,
                },
            )
        else:
            conn.execute(
                """
                INSERT INTO meeting_logs (
                    booking_id, notes, audio_path, transcript, summary,
                    title, author, meeting_date, start_time, end_time, room_name,
                    created_at, updated_at
                ) VALUES (
                    :booking_id, :notes, :audio_path, :transcript, :summary,
                    :title, :author, :meeting_date, :start_time, :end_time, :room_name,
                    :created_at, :updated_at
                )
                """,
                {
                    "booking_id": booking_id,
                    "notes": notes,
                    "audio_path": audio_path,
                    "transcript": transcript,
                    "summary": summary,
                    "title": title,
                    "author": author,
                    "meeting_date": meeting_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "room_name": room_name,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        conn.commit()

    return now


def _ensure_idea_hub_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            author TEXT NOT NULL,
            author_user_id TEXT,
            status TEXT NOT NULL DEFAULT '새로운 제안',
            created_at TEXT NOT NULL,
            completed_image TEXT,
            completed_description TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS idea_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(idea_id) REFERENCES ideas(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS idea_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            author_user_id TEXT,
            comment TEXT NOT NULL,
            rating INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(idea_id) REFERENCES ideas(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS idea_upvotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(idea_id, user_id),
            FOREIGN KEY(idea_id) REFERENCES ideas(id)
        )
        """
    )

    idea_columns = [row["name"] for row in conn.execute("PRAGMA table_info(ideas)").fetchall()]
    if "author_user_id" not in idea_columns:
        conn.execute("ALTER TABLE ideas ADD COLUMN author_user_id TEXT")

    comment_columns = [row["name"] for row in conn.execute("PRAGMA table_info(idea_comments)").fetchall()]
    if "author_user_id" not in comment_columns:
        conn.execute("ALTER TABLE idea_comments ADD COLUMN author_user_id TEXT")


def seed_ideas(conn):
    from app.fixtures.seed_data import idea_seed, user_name

    now = datetime.now()
    for sample in idea_seed(now):
        author_user_id = sample.get("author_user_id")
        row = conn.execute(
            """
            INSERT INTO ideas (
                title,
                content,
                category,
                author,
                author_user_id,
                status,
                created_at,
                completed_image,
                completed_description
            ) VALUES (
                :title,
                :content,
                :category,
                :author,
                :author_user_id,
                :status,
                :created_at,
                :completed_image,
                :completed_description
            )
            """,
            {
                "title": sample["title"],
                "content": sample["content"],
                "category": sample.get("category"),
                "author": user_name(author_user_id) or "익명",
                "author_user_id": author_user_id,
                "status": sample.get("status") or "새로운 제안",
                "created_at": sample["created_at"],
                "completed_image": sample.get("completed_image"),
                "completed_description": sample.get("completed_description"),
            },
        )
        idea_id = row.lastrowid

        for item in sample.get("timeline") or []:
            conn.execute(
                """
                INSERT INTO idea_timeline (idea_id, status, message, created_at)
                VALUES (:idea_id, :status, :message, :created_at)
                """,
                {"idea_id": idea_id, **item},
            )

        for comment in sample.get("comments") or []:
            comment_author_id = comment.get("author_user_id")
            conn.execute(
                """
                INSERT INTO idea_comments (idea_id, author, author_user_id, comment, rating, created_at)
                VALUES (:idea_id, :author, :author_user_id, :comment, :rating, :created_at)
                """,
                {
                    "idea_id": idea_id,
                    "author": user_name(comment_author_id) or "익명",
                    "author_user_id": comment_author_id,
                    "comment": comment["comment"],
                    "rating": comment.get("rating"),
                    "created_at": comment["created_at"],
                },
            )

        for user_id in sample.get("upvotes") or []:
            conn.execute(
                """
                INSERT OR IGNORE INTO idea_upvotes (idea_id, user_id, created_at)
                VALUES (:idea_id, :user_id, :created_at)
                """,
                {"idea_id": idea_id, "user_id": user_id, "created_at": _now_iso()},
            )


def create_idea(title, content, category, author):
    now = _now_iso()
    from app.fixtures.seed_data import find_user_id_by_name, user_name

    author = (author or "").strip()
    author_user_id = find_user_id_by_name(author) if author else None
    author_name = author or (user_name(author_user_id) if author_user_id else "")
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO ideas (title, content, category, author, author_user_id, status, created_at)
            VALUES (:title, :content, :category, :author, :author_user_id, :status, :created_at)
            """,
            {
                "title": title,
                "content": content,
                "category": category or None,
                "author": author_name or "익명",
                "author_user_id": author_user_id,
                "status": "새로운 제안",
                "created_at": now,
            },
        )
        idea_id = row.lastrowid
        conn.execute(
            """
            INSERT INTO idea_timeline (idea_id, status, message, created_at)
            VALUES (:idea_id, :status, :message, :created_at)
            """,
            {
                "idea_id": idea_id,
                "status": "접수 완료",
                "message": "아이디어가 접수되었습니다.",
                "created_at": now,
            },
        )
        conn.commit()
    return idea_id


def idea_exists(idea_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM ideas WHERE id = :id", {"id": idea_id}).fetchone()
    return bool(row)


def delete_idea(idea_id: int) -> bool:
    with get_connection() as conn:
        conn.execute("DELETE FROM idea_upvotes WHERE idea_id = :idea_id", {"idea_id": idea_id})
        conn.execute("DELETE FROM idea_comments WHERE idea_id = :idea_id", {"idea_id": idea_id})
        conn.execute("DELETE FROM idea_timeline WHERE idea_id = :idea_id", {"idea_id": idea_id})
        cur = conn.execute("DELETE FROM ideas WHERE id = :idea_id", {"idea_id": idea_id})
        conn.commit()
        return (cur.rowcount or 0) > 0


def _fetch_idea_timeline(conn, idea_id: int):
    rows = conn.execute(
        """
        SELECT status, message, created_at
        FROM idea_timeline
        WHERE idea_id = :idea_id
        ORDER BY created_at ASC
        """,
        {"idea_id": idea_id},
    ).fetchall()
    return [dict(row) for row in rows]


def _fetch_idea_comments(conn, idea_id: int):
    rows = conn.execute(
        """
        SELECT author, author_user_id, comment, rating, created_at
        FROM idea_comments
        WHERE idea_id = :idea_id
        ORDER BY created_at DESC
        """,
        {"idea_id": idea_id},
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_ideas(status: str | None = None):
    where_clause = ""
    params = {}
    if status:
        where_clause = "WHERE i.status = :status"
        params["status"] = status

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                i.id,
                i.title,
                i.content,
                i.category,
                i.author,
                i.author_user_id,
                i.status,
                i.created_at,
                i.completed_image,
                i.completed_description,
                COALESCE(u.upvotes, 0) AS upvotes,
                COALESCE(r.rating, 0) AS rating,
                COALESCE(r.rating_count, 0) AS rating_count
            FROM ideas i
            LEFT JOIN (
                SELECT idea_id, COUNT(*) AS upvotes
                FROM idea_upvotes
                GROUP BY idea_id
            ) u ON u.idea_id = i.id
            LEFT JOIN (
                SELECT idea_id, AVG(rating) AS rating, COUNT(rating) AS rating_count
                FROM idea_comments
                WHERE rating IS NOT NULL
                GROUP BY idea_id
            ) r ON r.idea_id = i.id
            {where_clause}
            ORDER BY i.created_at DESC
            """,
            params,
        ).fetchall()

        result = []
        for row in rows:
            idea = dict(row)
            idea["upvotes"] = int(idea.get("upvotes") or 0)
            idea["rating"] = float(idea.get("rating") or 0)
            idea["rating_count"] = int(idea.get("rating_count") or 0)
            idea["timeline"] = _fetch_idea_timeline(conn, idea["id"])
            if idea.get("status") == "해결 완료":
                idea["comments"] = _fetch_idea_comments(conn, idea["id"])
            result.append(idea)

    return result


def upvote_idea(idea_id: int, user_id: str):
    now = _now_iso()
    inserted = False
    with get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO idea_upvotes (idea_id, user_id, created_at)
                VALUES (:idea_id, :user_id, :created_at)
                """,
                {"idea_id": idea_id, "user_id": user_id, "created_at": now},
            )
            inserted = True
            conn.commit()
        except sqlite3.IntegrityError:
            inserted = False

        upvotes = conn.execute(
            "SELECT COUNT(*) FROM idea_upvotes WHERE idea_id = :idea_id",
            {"idea_id": idea_id},
        ).fetchone()[0]

    return inserted, int(upvotes)


def add_idea_comment(idea_id: int, author: str, comment: str, rating: int | None):
    now = _now_iso()
    from app.fixtures.seed_data import find_user_id_by_name, user_name

    author = (author or "").strip()
    author_user_id = find_user_id_by_name(author) if author else None
    author_name = author or (user_name(author_user_id) if author_user_id else "")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO idea_comments (idea_id, author, author_user_id, comment, rating, created_at)
            VALUES (:idea_id, :author, :author_user_id, :comment, :rating, :created_at)
            """,
            {
                "idea_id": idea_id,
                "author": author_name or "익명",
                "author_user_id": author_user_id,
                "comment": comment,
                "rating": rating,
                "created_at": now,
            },
        )
        conn.commit()

    return now


def _backfill_service_desk_requesters(conn: sqlite3.Connection) -> None:
    from app.fixtures.seed_data import find_user_id_by_name

    rows = conn.execute(
        "SELECT id, requester FROM service_desk_tickets WHERE requester_user_id IS NULL OR requester_user_id = ''"
    ).fetchall()
    for row in rows:
        requester = (row["requester"] or "").strip()
        requester_user_id = find_user_id_by_name(requester) or "user_010"
        conn.execute(
            "UPDATE service_desk_tickets SET requester_user_id = :uid WHERE id = :id",
            {"uid": requester_user_id, "id": row["id"]},
        )


def _backfill_idea_authors(conn: sqlite3.Connection) -> None:
    from app.fixtures.seed_data import find_user_id_by_name

    rows = conn.execute(
        "SELECT id, author FROM ideas WHERE author_user_id IS NULL OR author_user_id = ''"
    ).fetchall()
    for row in rows:
        author = (row["author"] or "").strip()
        author_user_id = find_user_id_by_name(author)
        if author_user_id:
            conn.execute(
                "UPDATE ideas SET author_user_id = :uid WHERE id = :id",
                {"uid": author_user_id, "id": row["id"]},
            )

    comment_rows = conn.execute(
        "SELECT id, author FROM idea_comments WHERE author_user_id IS NULL OR author_user_id = ''"
    ).fetchall()
    for row in comment_rows:
        author = (row["author"] or "").strip()
        author_user_id = find_user_id_by_name(author)
        if author_user_id:
            conn.execute(
                "UPDATE idea_comments SET author_user_id = :uid WHERE id = :id",
                {"uid": author_user_id, "id": row["id"]},
            )
