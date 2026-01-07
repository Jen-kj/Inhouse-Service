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
IDEA_STATUS_OPTIONS = ["새로운 제안", "검토 중", "해결 완료"]


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
        conn.commit()

        idea_count = conn.execute("SELECT COUNT(*) FROM ideas").fetchone()[0]
        if idea_count == 0:
            seed_ideas(conn)
            conn.commit()


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


def seed_ideas(conn):
    now = datetime.now()
    samples = [
        {
            "title": "사내 스낵바에 무설탕 음료 추가",
            "content": "제로 탄산/무설탕 음료 옵션이 조금 더 있으면 좋겠습니다. 건강 챙기면서도 간식 즐기고 싶어요!",
            "category": "복지",
            "author": "김민수",
            "status": "새로운 제안",
            "created_at": (now - timedelta(hours=2)).isoformat(timespec="seconds"),
            "completed_image": None,
            "completed_description": None,
        },
        {
            "title": "회의실 예약 알림을 슬랙으로 보내주세요",
            "content": "회의 시작 10분 전에 예약자/참석자에게 슬랙 알림이 가면 노쇼가 줄어들 것 같아요.",
            "category": "시스템",
            "author": "이지은",
            "status": "검토 중",
            "created_at": (now - timedelta(days=1, hours=3)).isoformat(timespec="seconds"),
            "completed_image": None,
            "completed_description": None,
        },
        {
            "title": "온보딩 체크리스트를 좀 더 보기 쉽게",
            "content": "신규 입사자가 해야 할 것들이 한눈에 보이도록, 카드/배지 형태로 정리되면 좋겠어요.",
            "category": "문화",
            "author": "최서연",
            "status": "해결 완료",
            "created_at": (now - timedelta(days=6, hours=6)).isoformat(timespec="seconds"),
            "completed_image": "https://images.unsplash.com/photo-1557683316-973673baf926?auto=format&fit=crop&w=1200&q=60",
            "completed_description": "온보딩 페이지에 완료 상태 표시와 섹션별 구분을 추가했습니다.",
        },
    ]

    for sample in samples:
        row = conn.execute(
            """
            INSERT INTO ideas (
                title, content, category, author, status, created_at, completed_image, completed_description
            ) VALUES (
                :title, :content, :category, :author, :status, :created_at, :completed_image, :completed_description
            )
            """,
            sample,
        )
        idea_id = row.lastrowid

        created_at = sample["created_at"]
        base_time = datetime.fromisoformat(created_at)
        review_time = (base_time + timedelta(hours=8)).isoformat(timespec="seconds")
        done_time = (base_time + timedelta(days=3)).isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO idea_timeline (idea_id, status, message, created_at)
            VALUES (:idea_id, :status, :message, :created_at)
            """,
            {
                "idea_id": idea_id,
                "status": "접수 완료",
                "message": "아이디어가 접수되었습니다.",
                "created_at": created_at,
            },
        )

        if sample["status"] in ("검토 중", "해결 완료"):
            conn.execute(
                """
                INSERT INTO idea_timeline (idea_id, status, message, created_at)
                VALUES (:idea_id, :status, :message, :created_at)
                """,
                {
                    "idea_id": idea_id,
                    "status": "검토 중",
                    "message": "담당 팀에서 검토를 시작했습니다.",
                    "created_at": review_time,
                },
            )

        if sample["status"] == "해결 완료":
            conn.execute(
                """
                INSERT INTO idea_timeline (idea_id, status, message, created_at)
                VALUES (:idea_id, :status, :message, :created_at)
                """,
                {
                    "idea_id": idea_id,
                    "status": "해결 완료",
                    "message": "개선 사항이 적용되었습니다.",
                    "created_at": done_time,
                },
            )

            conn.execute(
                """
                INSERT INTO idea_comments (idea_id, author, comment, rating, created_at)
                VALUES (:idea_id, :author, :comment, :rating, :created_at)
                """,
                {
                    "idea_id": idea_id,
                    "author": "정우진",
                    "comment": "완성도 좋고, 체크도 훨씬 쉬워졌어요!",
                    "rating": 5,
                    "created_at": (datetime.fromisoformat(done_time) + timedelta(hours=4)).isoformat(timespec="seconds"),
                },
            )
            conn.execute(
                """
                INSERT INTO idea_comments (idea_id, author, comment, rating, created_at)
                VALUES (:idea_id, :author, :comment, :rating, :created_at)
                """,
                {
                    "idea_id": idea_id,
                    "author": "박준호",
                    "comment": "신규 입사자 입장에서 확실히 덜 헷갈려요.",
                    "rating": 4,
                    "created_at": (datetime.fromisoformat(done_time) + timedelta(days=1, hours=2)).isoformat(timespec="seconds"),
                },
            )

            for user_id in ["user_001", "user_002", "user_003", "user_004"]:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO idea_upvotes (idea_id, user_id, created_at)
                    VALUES (:idea_id, :user_id, :created_at)
                    """,
                    {"idea_id": idea_id, "user_id": user_id, "created_at": _now_iso()},
                )


def create_idea(title, content, category, author):
    now = _now_iso()
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO ideas (title, content, category, author, status, created_at)
            VALUES (:title, :content, :category, :author, :status, :created_at)
            """,
            {
                "title": title,
                "content": content,
                "category": category or None,
                "author": author,
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
        SELECT author, comment, rating, created_at
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
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO idea_comments (idea_id, author, comment, rating, created_at)
            VALUES (:idea_id, :author, :comment, :rating, :created_at)
            """,
            {
                "idea_id": idea_id,
                "author": author,
                "comment": comment,
                "rating": rating,
                "created_at": now,
            },
        )
        conn.commit()

    return now
