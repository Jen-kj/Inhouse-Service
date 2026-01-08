from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str | None = None
    team: str | None = None


USERS: list[User] = [
    User(id="user_001", name="김민수", email="minsu.kim@nota.ai", team="보안팀"),
    User(id="user_002", name="이서연", email="seoyeon.lee@nota.ai", team="경영지원팀"),
    User(id="user_003", name="박준호", email="junho.park@nota.ai", team="총무팀"),
    User(id="user_004", name="최지우", email="jiwoo.choi@nota.ai", team="보안팀"),
    User(id="user_005", name="정하늘", email="haneul.jung@nota.ai", team="경영지원팀"),
    User(id="user_006", name="오유진", email="yujin.oh@nota.ai", team="총무팀"),
    User(id="user_007", name="이지은", email="jieun.lee@nota.ai", team="보안팀"),
    User(id="user_008", name="최서연", email="seoyeon.choi@nota.ai", team="경영지원팀"),
    User(id="user_009", name="정우진", email="woojin.jung@nota.ai", team="보안팀"),
    User(id="user_010", name="nota_inhouse", email="nota_inhouse@nota.ai", team="경영지원팀"),
]


def users() -> list[dict[str, Any]]:
    return [u.__dict__ for u in USERS]


def user_map() -> dict[str, dict[str, Any]]:
    return {u.id: u.__dict__ for u in USERS}


def user_name(user_id: str | None) -> str:
    if not user_id:
        return ""
    return user_map().get(user_id, {}).get("name", "")


def find_user_id_by_name(name: str | None) -> str | None:
    if not name:
        return None
    for user in USERS:
        if user.name == name:
            return user.id
    return None


CLUBS: list[dict[str, Any]] = [
    {
        "id": "club-tt",
        "name": "탁구",
        "category": "운동/건강",
        "tags": ["혼합 운영", "입문", "편안/유쾌"],
        "moodLine": "짧게 참여해도 좋은 실내 스포츠, 가볍게 땀 내며 친해져요",
        "snapshot": ["실내 활동", "단식·복식 모두", "점심/퇴근 후 참여"],
        "joinPolicy": "바로 가입",
        "format": "혼합 운영",
        "icon": "TT",
        "gradient": "linear-gradient(135deg, #ffb36b, #e56f4a)",
        "owner_user_id": "user_001",
    },
    {
        "id": "club-bk",
        "name": "농구",
        "category": "운동/건강",
        "tags": ["정기 모임", "초중급", "경기 위주"],
        "moodLine": "팀 스포츠 특유의 호흡, 함께 뛰며 자연스럽게 가까워져요",
        "snapshot": ["경기 중심", "실내/실외 선택", "팀플 교류"],
        "joinPolicy": "바로 가입",
        "format": "정기 모임",
        "icon": "BK",
        "gradient": "linear-gradient(135deg, #5f8dff, #3843a9)",
        "owner_user_id": "user_003",
    },
    {
        "id": "club-fs",
        "name": "풋살",
        "category": "운동/건강",
        "tags": ["정기 모임", "초중급", "친목 위주"],
        "moodLine": "실수해도 괜찮은 분위기, 즐겁게 뛰는 모임",
        "snapshot": ["야외 활동", "분위기 편안", "끝나고 교류"],
        "joinPolicy": "바로 가입",
        "format": "정기 모임",
        "icon": "FS",
        "gradient": "linear-gradient(135deg, #56c1a7, #1a8a72)",
        "owner_user_id": "user_005",
    },
    {
        "id": "club-cl",
        "name": "클라이밍",
        "category": "운동/건강",
        "tags": ["혼합 운영", "초중급", "도전/성장"],
        "moodLine": "코스 하나씩 정복하며 서로 응원하는 도전형 스포츠",
        "snapshot": ["난이도 선택", "기록/목표 공유", "주말 활동"],
        "joinPolicy": "승인 필요",
        "format": "혼합 운영",
        "icon": "CL",
        "gradient": "linear-gradient(135deg, #7c6cff, #4b3bb4)",
        "owner_user_id": "user_004",
    },
    {
        "id": "club-bg",
        "name": "보드게임",
        "category": "취미/문화",
        "tags": ["정기 모임", "상관없음", "친목 위주"],
        "moodLine": "룰은 천천히, 웃음은 크게? 편하게 모여 즐겨요",
        "snapshot": ["입문자 안내", "게임 다양", "소규모 테이블"],
        "joinPolicy": "바로 가입",
        "format": "정기 모임",
        "icon": "BG",
        "gradient": "linear-gradient(135deg, #f8c86b, #b7772f)",
        "owner_user_id": "user_002",
    },
    {
        "id": "club-mv",
        "name": "영화감상",
        "category": "취미/문화",
        "tags": ["정기 모임", "상관없음", "토론 중심"],
        "moodLine": "같이 보고 이야기하며 취향을 넓히는 감상 모임",
        "snapshot": ["작품 투표", "감상 후 토크", "OTT/극장 혼합"],
        "joinPolicy": "승인 필요",
        "format": "정기 모임",
        "icon": "MV",
        "gradient": "linear-gradient(135deg, #ff9aa8, #b23b5a)",
        "owner_user_id": "user_007",
    },
    {
        "id": "club-bw",
        "name": "볼링",
        "category": "취미/문화",
        "tags": ["정기 모임", "입문", "편안/유쾌"],
        "moodLine": "응원과 하이파이브가 기본, 같이 치면 더 재밌어요",
        "snapshot": ["연습 + 이벤트 게임", "처음도 OK", "친목 분위기"],
        "joinPolicy": "바로 가입",
        "format": "정기 모임",
        "icon": "BW",
        "gradient": "linear-gradient(135deg, #ffbf6b, #f08a39)",
        "owner_user_id": "user_006",
    },
    {
        "id": "club-ar",
        "name": "예술",
        "category": "취미/문화",
        "tags": ["정기 모임", "상관없음", "창작/표현"],
        "moodLine": "잘 그리는 것보다, 다르게 보는 법을 함께 연습해요",
        "snapshot": ["기초부터 천천히", "주제/재료 실습", "공유/피드백"],
        "joinPolicy": "승인 필요",
        "format": "정기 모임",
        "icon": "AR",
        "gradient": "linear-gradient(135deg, #69c3ff, #356fb7)",
        "owner_user_id": "user_008",
    },
]


CLUB_MEMBERSHIPS: list[dict[str, Any]] = [
    {"club_id": "club-tt", "user_id": "user_001", "role": "admin", "status": "active"},
    {"club_id": "club-tt", "user_id": "user_002", "role": "member", "status": "active"},
    {"club_id": "club-tt", "user_id": "user_003", "role": "member", "status": "active"},
    {"club_id": "club-tt", "user_id": "user_004", "role": "member", "status": "active"},
    {"club_id": "club-bg", "user_id": "user_001", "role": "member", "status": "active"},
    {"club_id": "club-bg", "user_id": "user_006", "role": "admin", "status": "active"},
    {"club_id": "club-mv", "user_id": "user_001", "role": "member", "status": "active"},
    {"club_id": "club-mv", "user_id": "user_007", "role": "admin", "status": "active"},
    {"club_id": "club-cl", "user_id": "user_004", "role": "admin", "status": "active"},
    {"club_id": "club-cl", "user_id": "user_002", "role": "member", "status": "pending"},
    {"club_id": "club-mv", "user_id": "user_003", "role": "member", "status": "pending"},
]


def _member_hint_by_club() -> dict[str, str]:
    counts: dict[str, int] = {}
    for m in CLUB_MEMBERSHIPS:
        if m["status"] != "active":
            continue
        counts[m["club_id"]] = counts.get(m["club_id"], 0) + 1
    return {club_id: f"{counts.get(club_id, 0)}명" for club_id in {c["id"] for c in CLUBS}}


def club_seed_store(viewer_user_id: str = "user_001") -> dict[str, Any]:
    member_hint = _member_hint_by_club()
    clubs = []
    for club in CLUBS:
        item = dict(club)
        item["memberHint"] = member_hint.get(club["id"], "0명")
        clubs.append(item)

    my_clubs = [
        c["name"]
        for c in CLUBS
        if any(
            m["club_id"] == c["id"] and m["user_id"] == viewer_user_id and m["status"] == "active"
            for m in CLUB_MEMBERSHIPS
        )
    ]

    join_approvals = [
        {
            "id": f"join-{m['club_id']}-{m['user_id']}",
            "clubName": next(c["name"] for c in CLUBS if c["id"] == m["club_id"]),
            "applicant": user_name(m["user_id"]),
            "club_id": m["club_id"],
            "user_id": m["user_id"],
        }
        for m in CLUB_MEMBERSHIPS
        if m["status"] == "pending"
    ]

    base = datetime(2026, 1, 7)
    events = [
        {
            "id": "evt-tt-1",
            "title": "점심 가볍게 랠리",
            "clubName": "탁구",
            "category": "운동/건강",
            "format": "혼합 운영",
            "startDate": (base + timedelta(days=2)).strftime("%Y-%m-%d"),
            "endDate": (base + timedelta(days=2)).strftime("%Y-%m-%d"),
            "time": "12:30",
            "place": "실내 코트",
            "description": "가볍게 랠리하고 팀 구성은 현장에서 정해요.",
        },
        {
            "id": "evt-bk-1",
            "title": "팀플 연습 경기",
            "clubName": "농구",
            "category": "운동/건강",
            "format": "정기 모임",
            "startDate": (base + timedelta(days=5)).strftime("%Y-%m-%d"),
            "endDate": (base + timedelta(days=5)).strftime("%Y-%m-%d"),
            "time": "18:30",
            "place": "실외 코트",
            "description": "워밍업 후 팀을 나눠 진행합니다.",
        },
        {
            "id": "evt-fs-1",
            "title": "퇴근 후 풋살",
            "clubName": "풋살",
            "category": "운동/건강",
            "format": "정기 모임",
            "startDate": (base + timedelta(days=8)).strftime("%Y-%m-%d"),
            "endDate": (base + timedelta(days=8)).strftime("%Y-%m-%d"),
            "time": "19:00",
            "place": "야외 구장",
            "description": "초중급 템포로 진행합니다.",
        },
        {
            "id": "evt-bg-1",
            "title": "라이트 보드게임",
            "clubName": "보드게임",
            "category": "취미/문화",
            "format": "정기 모임",
            "startDate": (base + timedelta(days=1)).strftime("%Y-%m-%d"),
            "endDate": (base + timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "12:00",
            "place": "라운지",
            "description": "룰 설명부터 함께 시작합니다.",
        },
        {
            "id": "evt-mv-1",
            "title": "이번 주 작품 감상",
            "clubName": "영화감상",
            "category": "취미/문화",
            "format": "정기 모임",
            "startDate": (base + timedelta(days=10)).strftime("%Y-%m-%d"),
            "endDate": (base + timedelta(days=10)).strftime("%Y-%m-%d"),
            "time": "16:00",
            "place": "미디어룸",
            "description": "투표로 선정한 작품을 함께 봅니다.",
        },
        {
            "id": "evt-cl-1",
            "title": "기초 루트 챌린지",
            "clubName": "클라이밍",
            "category": "운동/건강",
            "format": "혼합 운영",
            "startDate": (base + timedelta(days=12)).strftime("%Y-%m-%d"),
            "endDate": (base + timedelta(days=12)).strftime("%Y-%m-%d"),
            "time": "10:00",
            "place": "클라이밍 센터",
            "description": "서로 기록을 공유하며 진행해요.",
        },
        {
            "id": "evt-ar-1",
            "title": "드로잉 연습",
            "clubName": "예술",
            "category": "취미/문화",
            "format": "정기 모임",
            "startDate": (base + timedelta(days=4)).strftime("%Y-%m-%d"),
            "endDate": (base + timedelta(days=6)).strftime("%Y-%m-%d"),
            "time": "15:00",
            "place": "스튜디오",
            "description": "주제에 맞춰 같이 그립니다.",
        },
    ]

    posts = {
        "탁구": [
            {"id": "post-tt-1", "type": "공지", "title": "이번 주 실내 공간 공유"},
            {"id": "post-tt-2", "type": "모집", "title": "입문자 환영 세션"},
            {"id": "post-tt-3", "type": "후기", "title": "점심 랠리 후기"},
        ],
        "보드게임": [{"id": "post-bg-1", "type": "공지", "title": "룰 설명 자료 업데이트"}],
    }

    expenses = [
        {"id": "exp-1", "clubName": "탁구", "month": "2026-01", "title": "공간 대여", "amount": 80000, "note": "정산 예정"},
        {"id": "exp-2", "clubName": "보드게임", "month": "2026-01", "title": "소모품", "amount": 25000, "note": "집계 중"},
        {"id": "exp-3", "clubName": "탁구", "month": "2025-12", "title": "셔틀콕/볼", "amount": 15000, "note": ""},
    ]

    return {
        "viewer_user_id": viewer_user_id,
        "users": users(),
        "clubs": clubs,
        "memberships": list(CLUB_MEMBERSHIPS),
        "myClubs": my_clubs,
        "events": events,
        "joinApprovals": join_approvals,
        "posts": posts,
        "expenses": expenses,
    }


def service_desk_seed_tickets(now_iso: str) -> list[dict[str, Any]]:
    return [
        {
            "category": "IT",
            "owner_team": "보안팀",
            "title": "VPN 접속 오류",
            "description": "사내 VPN 접속이 간헐적으로 끊깁니다.",
            "requester_user_id": "user_002",
            "urgency": "NORMAL",
            "status": "PENDING",
            "created_at": now_iso,
        },
        {
            "category": "PURCHASE",
            "owner_team": "경영지원팀",
            "title": "맥북 충전기 교체",
            "description": "충전기가 간헐적으로 연결이 끊겨요.",
            "requester_user_id": "user_001",
            "urgency": "LOW",
            "status": "APPROVED",
            "created_at": now_iso,
        },
        {
            "category": "FACILITY",
            "owner_team": "총무팀",
            "title": "회의실 조명 수리 요청",
            "description": "회의실 조명이 깜빡입니다.",
            "requester_user_id": "user_003",
            "urgency": "URGENT",
            "status": "PENDING",
            "created_at": now_iso,
        },
    ]


def idea_seed(now: datetime) -> list[dict[str, Any]]:
    return [
        {
            "title": "사내 스낵바에 무설탕 음료 추가",
            "content": "제로 탄산/무설탕 음료 옵션이 조금 더 있으면 좋겠습니다. 건강 챙기면서도 간식 즐기고 싶어요!",
            "category": "복지",
            "author_user_id": "user_001",
            "status": "새로운 제안",
            "created_at": (now - timedelta(hours=2)).isoformat(timespec="seconds"),
            "completed_image": None,
            "completed_description": None,
            "comments": [],
            "upvotes": ["user_001"],
            "timeline": [
                {"status": "접수 완료", "message": "아이디어가 접수되었습니다.", "created_at": (now - timedelta(hours=2)).isoformat(timespec="seconds")},
            ],
        },
        {
            "title": "회의실 예약 알림을 슬랙으로 보내주세요",
            "content": "회의 시작 10분 전에 예약자/참석자에게 슬랙 알림이 가면 노쇼가 줄어들 것 같아요.",
            "category": "시스템",
            "author_user_id": "user_007",
            "status": "검토 중",
            "created_at": (now - timedelta(days=1, hours=3)).isoformat(timespec="seconds"),
            "completed_image": None,
            "completed_description": None,
            "comments": [],
            "upvotes": ["user_001", "user_002"],
            "timeline": [
                {"status": "접수 완료", "message": "아이디어가 접수되었습니다.", "created_at": (now - timedelta(days=1, hours=3)).isoformat(timespec="seconds")},
                {"status": "검토 중", "message": "담당 팀에서 검토를 시작했습니다.", "created_at": (now - timedelta(days=1, hours=1)).isoformat(timespec="seconds")},
            ],
        },
        {
            "title": "온보딩 체크리스트를 좀 더 보기 쉽게",
            "content": "신규 입사자가 해야 할 것들이 한눈에 보이도록, 카드/배지 형태로 정리되면 좋겠어요.",
            "category": "문화",
            "author_user_id": "user_008",
            "status": "해결 완료",
            "created_at": (now - timedelta(days=6, hours=6)).isoformat(timespec="seconds"),
            "completed_image": "https://images.unsplash.com/photo-1557683316-973673baf926?auto=format&fit=crop&w=1200&q=60",
            "completed_description": "온보딩 페이지에 완료 상태 표시와 섹션별 구분을 추가했습니다.",
            "comments": [
                {
                    "author_user_id": "user_009",
                    "comment": "완성도 좋고, 체크도 훨씬 쉬워졌어요!",
                    "rating": 5,
                    "created_at": (now - timedelta(days=3, hours=2)).isoformat(timespec="seconds"),
                },
                {
                    "author_user_id": "user_003",
                    "comment": "신규 입사자 입장에서 확실히 덜 헷갈려요.",
                    "rating": 4,
                    "created_at": (now - timedelta(days=2, hours=5)).isoformat(timespec="seconds"),
                },
            ],
            "upvotes": ["user_001", "user_002", "user_003", "user_004"],
            "timeline": [
                {"status": "접수 완료", "message": "아이디어가 접수되었습니다.", "created_at": (now - timedelta(days=6, hours=6)).isoformat(timespec="seconds")},
                {"status": "검토 중", "message": "담당 팀에서 검토를 시작했습니다.", "created_at": (now - timedelta(days=6, hours=1)).isoformat(timespec="seconds")},
                {"status": "해결 완료", "message": "개선 사항이 적용되었습니다.", "created_at": (now - timedelta(days=3)).isoformat(timespec="seconds")},
            ],
        },
    ]
