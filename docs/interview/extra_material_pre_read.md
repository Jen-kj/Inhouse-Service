# (선택) 인터뷰 전 추가자료(PDF/노션) 초안

PDF로 내보내기: 이 문서를 노션/구글독에 붙여넣어 PDF로 저장하거나, VS Code의 Markdown PDF 확장으로 바로 export 하면 됩니다.

목적: 인터뷰 20/20/20에서 “구체 데이터 기반 회고”를 빠르게 공유하기 위한 3~6p짜리 프리리드

---

## 1p. 과제 한 장 요약
### 프로젝트 한 줄
사내 구성원이 쓰는 “서비스 데스크 + 회의실 예약/회의록 + 아이디어 허브”를 하나의 인하우스 포털로 구현했습니다.

### 제가 둔 성공 기준
- 사용자가 주요 플로우를 끊김 없이 완주(목록→생성→확인)
- 예약/업보트 같은 핵심은 서버/DB에서 중복/충돌을 최종 방지
- AI 기능은 실패해도 서비스가 멈추지 않게 폴백 제공

### 구현한 기능(요약)
- Service Desk: 요청 생성/조회/상태 변경 + 요약 통계
- Onboarding: 퀘스트 체크리스트(진행률) + Q&A 검색/태그 필터 + 질문 등록 모달
- Nota Space: 회의실 예약(일간/월간) + 예약 목록, 회의록 작성/목록, 오디오 STT + AI 요약
- Idea Hub: 아이디어 등록/필터/삭제, 업보트, (해결완료) 코멘트+별점, 타임라인
- Clubs: 동아리 탐색/내 동아리/캘린더/관리자(Admin) 탭 UI + 시드 데이터 기반 상세 패널

### 스크린샷 자리(2~3장)
- Nota Space(예약 타임라인/월간)
- 회의록 작성 + 요약 결과
- Idea Hub 피드
- Clubs(Discover/Calendar/Detail 패널 중 1장)

---

## 2p. 아키텍처 / 데이터 흐름
### 컴포넌트
- Backend: Flask (`app/__init__.py`, `app/inhouse_service/routes.py`)
- DB: SQLite (`app/db.py`, `instance/service_desk.db`)
- Frontend: Jinja 템플릿 + Vanilla JS fetch (`app/templates/*`, `app/static/js/*`)

### 요청 흐름(텍스트 다이어그램)
브라우저(Jinja) → JS fetch → Flask API → SQLite 쿼리 → JSON 응답 → JS 렌더링

### AI 요약 흐름(텍스트 다이어그램)
노트/오디오 입력
→ 업로드 저장(`_save_upload`)
→ STT(Whisper, `_transcribe_audio`)
→ 텍스트 결합
→ Gemini 구조화 요약(`_summarize_with_gemini`)
→ 실패 시 로컬 요약(`_summarize_locally_structured`)
→ 사람이 읽는 텍스트로 변환(`_render_summary_text`)

### Onboarding 흐름(텍스트 다이어그램)
온보딩 페이지 진입(`/onboarding`)
→ 퀘스트 진행률 로드(LocalStorage: `nota_quest_progress`)
→ Q&A 로드(1차: `GET /api/qa`, 실패 시 더미 데이터로 대체)
→ 검색/태그 필터로 리스트 렌더링
→ Helpful/질문등록은 API 형태로 준비(현재 서버 미구현이라 실서비스에서는 `/api/qa*`를 연결)

### Clubs 흐름(텍스트 다이어그램)
동아리 페이지 진입(`/clubs`) → 카테고리 버튼은 서버에서 렌더링(`fetch_club_categories`)
→ 클라이언트 시드 로드: `GET /api/clubs/seed` → 탭(Discover/My/Calendar/Admin) UI 렌더링
→ 검색/카테고리/캘린더 필터는 프론트 상태(`store.ui`)로 즉시 반영
→ 가입/승인/지출/게시글 등 액션은 데모 목적의 클라이언트 상태 업데이트(백엔드 영속화는 확장 포인트)

---

## 3p. 핵심 결정 3개(대안 비교 포함)
### 결정 1) SQLite + 직접 SQL(ORM 미사용)
- 선택 이유: 과제 범위에서 end-to-end를 빠르게, 스키마/쿼리가 한 눈에 보이게
- 대안: SQLAlchemy(마이그레이션/모델링은 좋지만 초기 비용 증가)
- 리스크/완화: 스키마 변경은 `init_db()`에서 보정 로직 추가

### 결정 2) 예약 충돌은 서버에서 최종 보장
- 선택 이유: 동시성/중복 요청은 클라이언트만으로 막기 어려움
- 구현: `has_booking_conflict()`로 겹침 판정, 충돌 시 409
- 대안: UI에서 선검증(UX 개선) + 서버 최종 검증(현 구조에 추가 가능)

### 결정 3) AI 요약은 “성공하면 가치 추가, 실패해도 기본 기능 유지”
- 선택 이유: 외부 의존(네트워크/키/SDK/응답형식)은 불안정
- 구현: Gemini JSON 구조 강제 + 실패 시 로컬 요약 폴백
- 대안: 큐/비동기 처리(지연/비용 제어에 유리, 과제 범위에서는 단순 동기 처리)

---

## 3.5p. Onboarding(퀘스트/FAQ) 핵심 로직(짧게)
### 퀘스트 진행률(클라이언트 상태)
- `quest-item` 클릭 → 완료 토글 → 진행률(%) 갱신 → LocalStorage 저장
- 핵심 파일: `app/templates/onboarding.html`, `app/static/js/onboarding.js`

### Q&A(검색/태그/모달)
- 1차 시도: `GET /api/qa`로 서버에서 FAQ를 받는 구조
- 실패 시: `DUMMY_QA`로 폴백해 목록/검색/태그 필터는 동작
- Helpful/질문 등록은 `POST /api/qa/<id>/helpful`, `POST /api/qa` 형태로 연결 가능하도록 JS가 준비됨

---

## 3.6p. Clubs(동아리) 핵심 로직(짧게)
### 서버: 카테고리 + 시드 데이터 제공
- 카테고리(필터 버튼): SQLite의 `club_categories` (`fetch_club_categories()`)
- 시드 스토어: `GET /api/clubs/seed`가 `club_seed_store(viewer_user_id)` 반환
  - 포함 데이터: `clubs`, `memberships`, `myClubs`, `events`, `joinApprovals`, `posts`, `expenses` 등(데모용)

### 클라이언트: 단일 스토어 기반 탭/필터/상세 패널
- `loadSeed()`로 시드 수신 후 `store`에 적재 → `render()`로 탭별 화면 갱신
- Discover: 카테고리/검색 필터 → 카드 렌더 → 상세 패널 오픈
- Calendar: 월 이동 + 카테고리/형식/클럽/검색 필터 → 이벤트 캘린더 + 우측 패널
- Admin: 승인/예산/게시글 등은 UI/상태 업데이트로 데모(영속화는 추후 API로 연결)
- 핵심 파일: `app/templates/club/club.html`, `app/static/js/club.js`, `app/fixtures/seed_data.py`

---

## 4p. 문제 해결 사례 2개(재현/원인/해결)
### 사례 1) 예약 시간 겹침(경계 조건)
- 재현: 10~11 예약 후 10:30~11:30 요청(충돌) / 11~12 요청(비충돌)
- 원인: 시간 구간 판정이 모호하면 예외가 생김
- 해결: SQL에서 “겹치지 않는 조건”을 명시하고 NOT으로 겹침 정의
- 배운 점: 시간/구간은 정의(수학식)→구현 순서가 안전

### 사례 2) 요약 실패 시 UX 끊김
- 재현: 키 미설정/SDK 미설치/모델 응답 파싱 실패
- 해결: 실패 코드/메시지 반환 + 로컬 요약으로 자동 대체
- 배운 점: AI는 optional value로 만들고, “폴백 품질”이 사용자 신뢰를 좌우

---

## 5p. 품질/검증 포인트(짧게)
- 입력 검증/에러 코드: 필수 필드 400, 충돌 409, 미존재 404 등
- DB 제약: 업보트 유니크(중복 방지)
- 파일 업로드: `secure_filename` 사용, 업로드 디렉토리 분리
- AI 응답: JSON 파싱 + 실패 폴백
- Onboarding: 퀘스트 진행률은 LocalStorage로 영속(서버 연동은 확장 포인트), Q&A는 API 실패 시 더미 데이터로 폴백
- Clubs: 시드 데이터 기반으로 “한 화면에서 다양한 UI/상태”를 보여주되, 서버 영속화는 확장 포인트로 분리

---

## 6p. 다음 단계 로드맵(1주/1달)
### 1주
- 시크릿/키 관리(하드코딩 제거, `instance/.env`로 이동)
- 인코딩(UTF-8) 정리로 한글 깨짐 제거
- 클라이언트 예약 UX: 선택 슬롯 기반으로 폼 자동 채움/선검증
- Onboarding Q&A API 구현: `GET/POST /api/qa`, `POST /api/qa/<id>/helpful` 연결로 Helpful/질문등록 완성
- Clubs 영속화 API: 가입 신청/승인, RSVP, 게시글/지출 CRUD를 `/api/clubs/*`로 분리해 저장/권한/감사로그까지 확장

### 1달
- 로그인/권한(삭제/상태변경/업보트) + 감사로그
- 비동기 요약(큐) + 비용/지연 제어 + 개인정보 마스킹
- 테스트(예약 충돌, 업보트 중복, 요약 폴백) 최소 세트 구축

---

## (부록) 문서용 핵심 코드 스니펫 모음
### Clubs: 시드 제공(서버) + 초기 로드(클라이언트)
```py
# app/inhouse_service/routes.py
@bp.get("/api/clubs/seed")
def get_club_seed():
    return jsonify(club_seed_store(_current_user_id()))
```

```js
// app/static/js/club.js
async function loadSeed() {
  const res = await fetch("/api/clubs/seed");
  const data = await res.json();
  store.clubs = data.clubs || [];
  store.events = data.events || [];
  store.myClubs = data.myClubs || [];
}
```

---

## 이메일에 붙일 짧은 본문(복붙용)
안녕하세요, 과제 후 인터뷰 준비를 위해 선택 제출 자료를 전달드립니다.
본 문서는 과제에서 제가 했던 주요 결정/트레이드오프, 핵심 로직, AI 요약의 성공·실패 플로우, 그리고 다음 단계 개선안을 3~6p로 요약한 프리리드입니다.
인터뷰에서 더 구체적으로 피드백을 받고 싶은 질문들도 포함해두었습니다. 감사합니다.
