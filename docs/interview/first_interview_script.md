# 1차 인터뷰(과제 후 인터뷰) 준비 스크립트

대상 프로젝트: `Inhouse-Service` (Flask + SQLite + Vanilla JS)

핵심 기능(제가 구현/정리한 범위)
- Service Desk: 요청 생성/조회/상태 변경, 요약 통계
- Onboarding: 퀘스트 진행률(LocalStorage) + Q&A 검색/태그 필터 + 질문 등록(서버 API 연결 전제)
- Nota Space: 회의실 예약(일간 타임라인/월간 캘린더) + 예약 목록, 회의록 작성/목록, AI 요약(녹음 STT + 구조화 요약)
- Idea Hub: 아이디어 등록/필터/삭제, 업보트, 해결완료 아이디어에 코멘트(+별점), 타임라인
- Clubs: 동아리 탐색/내 동아리/캘린더/관리자(Admin) 탭 UI + 시드 데이터 기반(데모) 상태 관리

---

## 0) 20분 회고 발표(대본)

### 0-1. 오프닝(1분)
안녕하세요. 이번 과제는 “인하우스용 서비스”라는 컨셉에서 실제 사용자가 바로 쓸 수 있을 정도의 흐름을 만들고, 백엔드-프론트-데이터를 최소 단위로 끝까지 연결하는 것을 목표로 진행했습니다.

제가 세운 성공 기준은 3가지였습니다.
1) 사용자가 “목록 → 생성/수정 → 다시 목록에서 확인”까지 끊기지 않게 완주할 것
2) 예약/업보트 같은 핵심 로직은 중복/충돌을 방지할 것(서버에서 최종 보장)
3) AI 기능은 실패해도 기능이 멈추지 않게(폴백) 만들 것

---

### 0-2. 전체 구조 요약(3분)
구조는 단순하게 잡았습니다.
- 서버: Flask blueprint 하나(`app/inhouse_service/routes.py`)
- 데이터: SQLite 단일 DB(`app/db.py`)에서 스키마 생성 + 시드 데이터
- 화면: Jinja 템플릿 + 정적 JS에서 fetch로 API 호출

이 구조를 선택한 이유는 과제 범위에서 “빠르게 끝까지 연결되는 제품”을 만드는 데 유리하고, DB/라우팅/렌더링 흐름이 한눈에 보여서 리뷰가 쉽다고 판단했기 때문입니다.

증거로는 아래 파일들을 보여드리면 됩니다.
- 앱 부팅/환경변수 로딩: `app/__init__.py`
- API/페이지 라우팅: `app/inhouse_service/routes.py`
- DB 스키마/쿼리: `app/db.py`
- Nota Space UI(예약/회의록): `app/templates/nota_space/*`, `app/static/js/nota_space/*`
- Idea Hub UI: `app/templates/idea/ideahub.html`, `app/static/js/ideahub.js`

---

### 0-3. 핵심 구현 포인트 1: 회의실 예약 충돌 방지(4분)
Nota Space 예약은 “예약 충돌”이 가장 위험한 지점이라, 서버에서 겹침을 반드시 막도록 했습니다.

- API: `POST /api/nota-space/bookings` → `create_nota_space_booking()` (`app/inhouse_service/routes.py`)
- 충돌 체크: `has_booking_conflict()` (`app/db.py`)
- 쿼리에서 `NOT (end <= start OR start >= end)`로 구간 겹침을 판정하고, 충돌이면 409를 반환합니다.

트레이드오프는 “클라이언트에서도 UX상 미리 막을 수 있지만, 최종 진실은 서버에 둔다”로 정리했습니다. 프론트는 편의이고, 동시성/중복 요청은 서버에서 확실히 처리한다는 방향입니다.

---

### 0-4. 핵심 구현 포인트 2: AI 요약(성공/실패 모두 UX 유지)(6분)
회의록 요약은 두 가지 입력을 지원합니다.
1) 사용자가 직접 적은 노트
2) 녹음 파일 업로드 → STT(Whisper) → 텍스트 결합

흐름은 다음과 같습니다.
- 프론트: `meeting_log_form.html`에서 노트/오디오를 제출 (`app/templates/nota_space/meeting_log_form.html`)
- JS: `Generate AI Summary` 클릭 시 `POST /api/nota-space/meeting-summary` (`app/static/js/nota_space/meeting_log_form.js`)
- 서버:
  - 업로드 저장: `_save_upload()` (`app/inhouse_service/routes.py`)
  - STT: `_transcribe_audio()` → Whisper model 캐시(`_WHISPER_MODEL`) + ffmpeg PATH 보정
  - 요약: `_summarize_with_gemini()`로 “JSON 구조” 강제 요청
  - 실패 시: `_summarize_locally_structured()`로 로컬 구조화 요약 폴백
  - 출력: `_render_summary_text()`로 사람이 읽는 형태로 렌더링

여기서 의도한 학습 포인트는 “외부 의존(AI)이 실패하는 상황을 기본값으로 두고도 서비스가 동작하도록 설계”한 점입니다.

추가로, 로컬 요약은 섹션(목표/범위/결정/실행/리스크)을 감지하고 액션 아이템을 정규식으로 추출해서 최소한의 ‘쓸모’를 보장하도록 했습니다.

---

### 0-5. 핵심 구현 포인트 3: Idea Hub의 상호작용(4분)
Idea Hub는 “등록/필터/삭제/업보트/코멘트”의 기본 흐름을 만들고, 해결된 아이디어에는 결과물을 첨부할 수 있게 했습니다.

- API: `/api/ideas` CRUD + `/upvote`, `/comment` (`app/inhouse_service/routes.py`)
- DB:
  - `ideas`, `idea_timeline`, `idea_comments`, `idea_upvotes` (`app/db.py`)
  - 업보트는 `(idea_id, user_id)` 유니크로 중복 방지
- 프론트: Vanilla JS에서 카드 렌더링 + 모달 UI (`app/static/js/ideahub.js`)

여기서 트레이드오프는 “인증/권한은 과제 범위에서 생략하고 user를 단일 값으로 둔 것”입니다. 대신 DB 레벨 제약으로 중복 업보트는 막아두었습니다.

---

### 0-6. 어려웠던 이슈 2개(각 1~2분, 총 4분)
이 파트는 실제로 겪었던 것 위주로 말하는 게 제일 좋습니다. 아래는 제가 코드에서 보이는 ‘이슈 후보’ 형태로 대본을 만들어둔 것입니다.

이슈 후보 A) AI 요약 실패/불안정
- 증상: 외부 모델 응답이 비정형이거나 SDK/키 이슈로 실패 가능
- 가설: “성공을 전제로 하면 UX가 끊긴다”
- 해결: JSON 강제 프롬프트 + 실패 시 로컬 요약 폴백 + 프론트에 메시지 표시
- 배운 점: 외부 의존은 ‘없어도 되는 기능’으로 만들고, 성공 시만 가치를 더한다

이슈 후보 B) 예약 겹침(경계 조건)
- 증상: 10:00~11:00과 11:00~12:00은 겹치지 않아야 함 / 10:00~12:00과 11:00~13:00은 겹쳐야 함
- 해결: 겹침 판정식을 SQL 레벨로 명확히 정의
- 배운 점: 시간/구간 로직은 예외가 많아서 “정의(수학식) → 코드” 순서가 안전

---

### 0-7. 시간이 더 있으면 바꿀 것(3분)
우선순위 순으로 3가지를 제안합니다(“왜”까지 같이).
1) 시크릿/키 관리 정리: API 키 하드코딩 제거 → `instance/.env`로 이동, 운영/개발 분리
2) 인코딩/국제화 정리: 일부 템플릿/JS에서 한글이 깨져 보이는 부분이 있어 파일 인코딩(UTF-8)과 문자열 관리를 정리
3) 인증/권한/감사로그: 현재는 `user_001` 고정이라, 실제 인하우스 서비스라면 로그인/권한(삭제/상태변경)과 변경 이력(누가 언제)을 추가

---

### 0-8. 마무리(1분)
정리하면, 이번 과제에서 제가 보여드리고 싶었던 건 “끝까지 동작하는 제품을 빠르게 만들되, 핵심 로직은 서버/DB에서 안전하게 보장하고, AI 같은 불확실한 기능은 실패해도 서비스가 멈추지 않게 설계”한 경험입니다.

이제 피드백을 받고 싶은 부분은 (1) 구조를 더 확장 가능하게 만들려면 어디를 먼저 바꾸는 게 좋은지, (2) 지금의 트레이드오프가 실무 관점에서 적절했는지입니다.

---

## 1) Q&A에서 내가 먼저 던질 질문 5개(피드백 유도용)
1) 이 과제 범위에서 “가장 중요한 평가 기준”은 무엇이었나요? 제가 놓친 지점이 있다면 어디였나요?
2) 지금 구조(`Flask + SQLite + Vanilla JS`)에서 실무 확장을 전제로 한다면, 우선순위를 어디에 두고 리팩터링을 시작하시나요?
3) AI 요약 기능에서 “프로덕션 품질”을 위해 꼭 추가해야 할 안전장치(예: 비용, 지연, 개인정보)는 무엇인가요?
4) 예약 시스템에서 제가 정의한 충돌 판정/에러 코드(409 등)가 적절한지, 더 좋은 패턴이 있는지 궁금합니다.
5) 제가 이번 과제에서 가장 잘한 점/아쉬운 점을 1개씩 꼽아주신다면 무엇인가요?

---

## 2) 인터뷰 당일 들고 갈 “구체 데이터” 체크리스트
- 화면 캡처 6장(각 기능의 대표 화면)
  - Nota Space: 일간 예약 타임라인, 월간 캘린더, 예약 생성 모달, 회의록 작성 + 요약 결과
  - Idea Hub: 피드 + 필터, 코멘트 모달
- 코드 캡처 4장(핵심 로직만)
  - `app/db.py`의 `has_booking_conflict()`
  - `app/inhouse_service/routes.py`의 `nota_space_meeting_summary()`와 폴백 분기
  - `app/inhouse_service/routes.py`의 `_summarize_locally_structured()` 핵심 파트
  - `app/db.py`의 `idea_upvotes` 유니크 제약 + `upvote_idea()` 흐름(있다면)
- (있으면 좋음) `git log --oneline --decorate` 캡처 1장
