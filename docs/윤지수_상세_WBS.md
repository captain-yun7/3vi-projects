# 윤지수 담당 업무 상세 WBS (Phase별)

## 프로젝트 개요
**담당자**: 윤지수
**기간**: 10월 ~ 1월 (12주)
**핵심 역할**: LangGraph 기반 AI 보안 스캔 엔진 개발 및 백엔드 연동

---

## Phase 0: PoC 및 기술 검증 ✅ (완료)

### 0.1 LangGraph PoC 생성 및 리뷰
- [x] LangGraph 기본 개념 학습
- [x] 간단한 워크플로우 구현 (simple_poc.py)
  - [x] StateGraph 구조 설계
  - [x] 5단계 노드 구현 (분석→스캔→취약점→평가→보고서)
  - [x] 노드 간 상태 전달 검증
- [x] 고급 워크플로우 구현 (advanced_poc.py)
  - [x] OpenAI API 연동
  - [x] python-nmap 연동
  - [x] 6단계 노드 구현 (AI 분석 포함)
  - [x] 에러 핸들링 및 폴백 로직
- [x] 문서화 (README.md)
- [x] 코드 리뷰 및 개선

**산출물**:
- `/01-poc/simple_poc.py`
- `/01-poc/advanced_poc.py`
- `/01-poc/README.md`

**완료 기준**: PoC 코드가 정상 실행되고 보고서가 생성됨

---

## Phase 1: 기술 스택 설계 및 환경 구축 (1주)

### 1.1 프로젝트 구조 설계
- [ ] 백엔드 디렉토리 구조 설계
  - [ ] FastAPI 프로젝트 구조 정의
  - [ ] LangGraph 서비스 레이어 위치 결정
  - [ ] 모듈 분리 전략 수립 (services, models, api)
- [ ] LangGraph 서비스 아키텍처 설계
  - [ ] PoC 코드를 서비스로 변환하는 방법 설계
  - [ ] 비동기 처리 전략 수립 (Celery vs BackgroundTasks)
  - [ ] 상태 관리 방법 결정 (Redis vs DB)

**산출물**:
- `docs/architecture/langgraph_service_design.md`
- `docs/architecture/backend_structure.md`

### 1.2 기술 스택 확정 및 환경 설정
- [ ] 기술 스택 최종 확정
  - [ ] 백엔드: FastAPI (Python 3.10+)
  - [ ] 비동기 작업: Celery + Redis 또는 BackgroundTasks
  - [ ] DB: PostgreSQL 또는 MySQL
  - [ ] WebSocket: FastAPI WebSocket
- [ ] 개발 환경 설정
  - [ ] requirements.txt 업데이트
  - [ ] Docker Compose 설정 (선택사항)
  - [ ] 환경 변수 관리 (.env.example)

**산출물**:
- `backend/requirements.txt`
- `docker-compose.yml` (선택)
- `.env.example`

### 1.3 모의해킹 기능 제약사항 분석
- [ ] 구현 불가능한 항목 식별
  - [ ] 실제 해킹 도구 사용 제약 (법적, 윤리적)
  - [ ] 네트워크 제약 (방화벽, 권한)
  - [ ] 성능 제약 (시간, 리소스)
- [ ] 대안 방안 수립
  - [ ] 시뮬레이션 모드 설계
  - [ ] 안전한 도구로 대체 (nmap → masscan)
  - [ ] 샌드박스 환경 구축 방안
- [ ] 문서화

**산출물**:
- `docs/constraints/implementation_limitations.md`
- `docs/constraints/alternative_solutions.md`

**완료 기준**:
- 프로젝트 구조가 문서화됨
- 기술 스택이 확정되고 개발 환경이 준비됨
- 제약사항 및 대안이 명확히 정리됨

---

## Phase 2: LangGraph 서비스화 및 API 기본 연동 (2주)

### 2.1 FastAPI 백엔드 기본 구조 생성
- [ ] FastAPI 프로젝트 초기화
  - [ ] `backend/` 디렉토리 생성
  - [ ] `main.py` FastAPI 앱 생성
  - [ ] CORS, 미들웨어 설정
- [ ] 디렉토리 구조 구축
  ```
  backend/
  ├── app/
  │   ├── api/              # API 라우터
  │   ├── core/             # 설정, DB
  │   ├── models/           # DB 모델
  │   ├── schemas/          # Pydantic 스키마
  │   ├── services/         # 비즈니스 로직
  │   └── main.py
  ├── tests/
  └── requirements.txt
  ```
- [ ] 기본 헬스체크 엔드포인트 생성
  - [ ] `GET /health`
  - [ ] `GET /api/v1/status`

**산출물**:
- `backend/app/main.py`
- `backend/app/api/health.py`

### 2.2 LangGraph를 서비스 클래스로 리팩토링
- [ ] LangGraph 서비스 클래스 생성
  - [ ] `backend/app/services/langgraph_service.py`
  - [ ] PoC 코드(`advanced_poc.py`)를 클래스 메서드로 변환
  - [ ] 의존성 주입 패턴 적용 (OpenAI API Key, 설정)
- [ ] 워크플로우 모듈화
  - [ ] 각 노드를 독립적인 메서드로 분리
  - [ ] 노드별 에러 핸들링 강화
  - [ ] 로깅 추가 (각 노드 실행 시작/완료 로그)
- [ ] State 관리 개선
  - [ ] SecurityScanState를 Pydantic 모델로 변환
  - [ ] 상태 직렬화/역직렬화 지원 (JSON)

**산출물**:
- `backend/app/services/langgraph_service.py`
- `backend/app/schemas/scan_state.py`

### 2.3 LangGraph 실행 API 엔드포인트 생성
- [ ] API 라우터 생성
  - [ ] `backend/app/api/v1/langgraph.py`
- [ ] 기본 엔드포인트 구현
  - [ ] `POST /api/v1/langgraph/scan` - 스캔 시작
    - 요청 바디: `{"target": "IP", "scan_type": "full"}`
    - 응답: `{"session_id": "uuid", "status": "started"}`
  - [ ] `GET /api/v1/langgraph/scan/{session_id}` - 스캔 상태 조회
  - [ ] `GET /api/v1/langgraph/scan/{session_id}/result` - 결과 조회
- [ ] 동기 실행 테스트 (일단 비동기 없이)
  - [ ] 간단한 스캔 요청 → 결과 반환 테스트

**산출물**:
- `backend/app/api/v1/langgraph.py`
- `backend/app/schemas/scan_request.py`
- `backend/app/schemas/scan_response.py`

### 2.4 DB 모델 및 데이터 저장 구현
- [ ] DB 연결 설정
  - [ ] SQLAlchemy 설정 (`backend/app/core/database.py`)
  - [ ] Alembic 마이그레이션 초기화
- [ ] 모델 정의
  - [ ] `ScanSession` 모델 (세션 ID, 대상, 상태, 생성시간)
  - [ ] `ScanResult` 모델 (세션 ID, 결과 JSON, 위험도)
- [ ] CRUD 함수 작성
  - [ ] `create_scan_session()`
  - [ ] `update_scan_status()`
  - [ ] `save_scan_result()`
  - [ ] `get_scan_result()`

**산출물**:
- `backend/app/models/scan_session.py`
- `backend/app/models/scan_result.py`
- `backend/app/core/database.py`
- `backend/alembic/versions/001_initial.py`

### 2.5 백엔드 API ↔ LangGraph 연동 테스트
- [ ] 통합 테스트 작성
  - [ ] API 호출 → LangGraph 실행 → DB 저장 플로우 테스트
  - [ ] Postman/curl로 수동 테스트
- [ ] 에러 케이스 테스트
  - [ ] 잘못된 IP 입력
  - [ ] OpenAI API 키 누락
  - [ ] nmap 미설치 시나리오

**산출물**:
- `backend/tests/test_langgraph_integration.py`
- `docs/api/langgraph_api_spec.md`

**완료 기준**:
- FastAPI 백엔드가 실행되고 `/health` 응답
- `POST /api/v1/langgraph/scan` 호출 시 LangGraph 실행되고 결과 DB에 저장
- 스캔 결과를 GET으로 조회 가능

---

## Phase 3: 비동기 처리 및 실시간 통신 (2주)

### 3.1 비동기 스캔 실행 구현
- [ ] BackgroundTasks 또는 Celery 선택 및 설정
  - [ ] Celery 사용 시: Redis 설정, Celery worker 설정
  - [ ] BackgroundTasks 사용 시: FastAPI BackgroundTasks 활용
- [ ] 비동기 스캔 로직 구현
  - [ ] `POST /api/v1/langgraph/scan` 요청 즉시 반환 (세션 ID만)
  - [ ] 백그라운드에서 LangGraph 실행
  - [ ] 실행 중 상태를 DB에 업데이트
- [ ] 상태 관리
  - [ ] 상태 값: `pending`, `running`, `completed`, `failed`
  - [ ] 각 노드 완료 시 진행률 업데이트 (예: 1/6, 2/6...)

**산출물**:
- `backend/app/services/async_scan_service.py`
- `backend/celery_app.py` (Celery 사용 시)

### 3.2 WebSocket 실시간 진행 상황 전송
- [ ] WebSocket 엔드포인트 생성
  - [ ] `WS /api/v1/ws/scan/{session_id}`
- [ ] 진행 상황 브로드캐스트 로직
  - [ ] LangGraph 각 노드 시작/완료 시 WebSocket으로 메시지 전송
  - [ ] 메시지 형식 정의
    ```json
    {
      "session_id": "uuid",
      "step": "port_scan",
      "status": "running",
      "progress": 33,
      "message": "포트 스캔 중..."
    }
    ```
- [ ] ConnectionManager 구현
  - [ ] 여러 클라이언트 연결 관리
  - [ ] 특정 세션에만 메시지 전송

**산출물**:
- `backend/app/api/v1/websocket.py`
- `backend/app/core/websocket_manager.py`

### 3.3 LangGraph 노드에서 WebSocket 이벤트 발생
- [ ] LangGraph 서비스에 WebSocket 콜백 추가
  - [ ] 각 노드 실행 전: `send_progress("node_name", "running")`
  - [ ] 각 노드 실행 후: `send_progress("node_name", "completed")`
- [ ] 진행률 계산 로직 추가
  - [ ] 전체 노드 수 대비 현재 완료된 노드 비율
- [ ] 에러 발생 시 WebSocket으로 에러 메시지 전송

**산출물**:
- `backend/app/services/langgraph_service.py` (업데이트)

### 3.4 WebSocket 테스트
- [ ] WebSocket 클라이언트 테스트 스크립트 작성
  - [ ] Python websocket-client로 테스트
  - [ ] 스캔 시작 → WebSocket 연결 → 진행 상황 수신 검증
- [ ] 부하 테스트
  - [ ] 동시 여러 스캔 실행 시 WebSocket 메시지 정상 전달 확인

**산출물**:
- `backend/tests/test_websocket.py`
- `backend/scripts/test_websocket_client.py`

**완료 기준**:
- 스캔 요청 즉시 응답 (비동기)
- WebSocket으로 실시간 진행 상황 수신 가능
- 스캔 완료 시 DB에 결과 저장 및 WebSocket으로 완료 알림

---

## Phase 4: 채팅 플로우 연동 (1주)

### 4.1 채팅 API 설계 및 구현
- [ ] 채팅 스키마 정의
  - [ ] `ChatMessage`: `{user_id, message, timestamp}`
  - [ ] `ChatResponse`: `{bot_message, action, data}`
- [ ] 채팅 엔드포인트 생성
  - [ ] `POST /api/v1/chat/message`
  - [ ] 사용자 메시지 파싱 (예: "192.168.1.1 스캔해줘")
  - [ ] 의도 분류 (스캔 요청, 결과 조회, 도움말 등)
- [ ] LangGraph 실행 트리거
  - [ ] 스캔 의도로 분류되면 LangGraph 실행
  - [ ] 세션 ID를 채팅 응답에 포함

**산출물**:
- `backend/app/api/v1/chat.py`
- `backend/app/schemas/chat.py`
- `backend/app/services/chat_service.py`

### 4.2 채팅 히스토리 저장
- [ ] ChatHistory 모델 생성
  - [ ] `user_id`, `message`, `response`, `session_id`, `timestamp`
- [ ] 채팅 CRUD
  - [ ] `save_chat_message()`
  - [ ] `get_chat_history(user_id, limit)`

**산출물**:
- `backend/app/models/chat_history.py`

### 4.3 채팅 UI ↔ 백엔드 연동 검증
- [ ] 프론트엔드 팀(이왕희)과 API 명세 공유
- [ ] Mock 채팅 클라이언트 작성 (테스트용)
  - [ ] 메시지 전송
  - [ ] 응답 수신
  - [ ] WebSocket으로 진행 상황 수신
- [ ] 통합 테스트

**산출물**:
- `docs/api/chat_api_spec.md`
- `backend/scripts/test_chat_client.py`

**완료 기준**:
- 채팅 메시지 전송 → LangGraph 실행 → 결과 반환
- 채팅 히스토리가 DB에 저장됨

---

## Phase 5: MCP 모듈화 및 확장성 구현 (2주)

### 5.1 MCP (Model Context Protocol) 개념 설계
- [ ] MCP 아키텍처 설계
  - [ ] 보안 도구를 플러그인처럼 추가/제거 가능한 구조
  - [ ] 각 도구를 독립적인 모듈로 분리
- [ ] 도구 인터페이스 정의
  - [ ] 공통 인터페이스: `execute(target, options) -> result`
  - [ ] 메타데이터: `name`, `description`, `version`, `required_params`

**산출물**:
- `docs/architecture/mcp_design.md`
- `backend/app/services/tools/base_tool.py` (추상 클래스)

### 5.2 기존 도구 모듈화
- [ ] Nmap 모듈
  - [ ] `backend/app/services/tools/nmap_tool.py`
  - [ ] BaseToolInterface 상속
- [ ] OpenAI 분석 모듈
  - [ ] `backend/app/services/tools/openai_analysis_tool.py`
- [ ] 취약점 DB 조회 모듈 (선택)
  - [ ] CVE 데이터베이스 연동

**산출물**:
- `backend/app/services/tools/nmap_tool.py`
- `backend/app/services/tools/openai_analysis_tool.py`

### 5.3 도구 레지스트리 및 동적 로딩
- [ ] ToolRegistry 클래스 생성
  - [ ] 도구 등록: `register_tool(tool_instance)`
  - [ ] 도구 조회: `get_tool(name)`
  - [ ] 모든 도구 리스트: `list_tools()`
- [ ] 동적 로딩 구현
  - [ ] `backend/app/services/tools/` 디렉토리에서 자동 스캔
  - [ ] 플러그인처럼 추가 가능

**산출물**:
- `backend/app/services/tool_registry.py`

### 5.4 LangGraph에서 MCP 도구 사용
- [ ] LangGraph 노드를 MCP 도구로 리팩토링
  - [ ] 기존 `port_scan()` 노드 → `NmapTool.execute()` 호출
  - [ ] 기존 `ai_risk_assessment()` → `OpenAIAnalysisTool.execute()`
- [ ] 도구 설정 관리
  - [ ] 사용자가 어떤 도구를 사용할지 선택 가능
  - [ ] Flow 정의에 도구 목록 포함

**산출물**:
- `backend/app/services/langgraph_service.py` (업데이트)

### 5.5 MCP 도구 추가 테스트
- [ ] 새로운 도구 추가 시뮬레이션
  - [ ] 예: `Masscan` 도구 추가
  - [ ] 플러그인 형태로 추가 → 자동 인식 확인
- [ ] 단위 테스트
  - [ ] 각 도구별 단위 테스트
  - [ ] ToolRegistry 테스트

**산출물**:
- `backend/tests/test_tool_registry.py`
- `backend/tests/test_tools.py`

**완료 기준**:
- 보안 도구들이 모듈화되어 독립적으로 관리됨
- 새 도구 추가 시 코드 수정 최소화
- LangGraph에서 동적으로 도구 사용 가능

---

## Phase 6: LangGraph 시각화 및 Flow 관리 (1주)

### 6.1 LangGraph 시각화 API 개발
- [ ] 그래프 구조 JSON 생성
  - [ ] 노드 목록: `[{id, name, type, status}]`
  - [ ] 엣지 목록: `[{from, to}]`
- [ ] 시각화 데이터 엔드포인트
  - [ ] `GET /api/v1/langgraph/graph/{session_id}` - 현재 실행 중인 그래프 상태
  - [ ] 각 노드의 실행 상태 포함 (`pending`, `running`, `completed`, `failed`)
- [ ] 실시간 업데이트
  - [ ] WebSocket으로 노드 상태 변경 시 브로드캐스트

**산출물**:
- `backend/app/api/v1/visualization.py`
- `backend/app/schemas/graph_visualization.py`

### 6.2 Flow 저장 및 불러오기
- [ ] Flow 모델 정의
  - [ ] `Flow`: `{id, name, nodes, edges, created_at}`
  - [ ] JSON 형태로 워크플로우 저장
- [ ] Flow CRUD API
  - [ ] `POST /api/v1/flow` - Flow 생성
  - [ ] `GET /api/v1/flow/{flow_id}` - Flow 조회
  - [ ] `PUT /api/v1/flow/{flow_id}` - Flow 수정
  - [ ] `DELETE /api/v1/flow/{flow_id}` - Flow 삭제
- [ ] Flow 기반 LangGraph 실행
  - [ ] 저장된 Flow를 불러와서 동적으로 LangGraph 생성
  - [ ] 커스텀 워크플로우 실행

**산출물**:
- `backend/app/models/flow.py`
- `backend/app/api/v1/flow.py`

**완료 기준**:
- LangGraph 구조를 JSON으로 조회 가능
- 프론트엔드에서 그래프 시각화에 필요한 데이터 제공
- Flow를 저장하고 불러와서 실행 가능

---

## Phase 7: 결과 수집 및 백엔드 API 연동 (1주)

### 7.1 결과 수집 API 설계
- [ ] 점검 결과 저장 API 명세 (백엔드 팀과 협의)
  - [ ] `POST /api/v1/results` - 점검 결과 저장
  - [ ] 요청 바디 스키마 정의
- [ ] LangGraph 결과를 API 형식으로 변환
  - [ ] `ScanResult` → API 요청 바디 매핑

**산출물**:
- `docs/api/result_collection_api_spec.md`

### 7.2 LangGraph에서 API 호출로 결과 저장
- [ ] DB 직접 저장 로직 제거
- [ ] API 클라이언트 추가
  - [ ] `httpx` 또는 `requests` 사용
  - [ ] `POST /api/v1/results` 호출
- [ ] 에러 핸들링
  - [ ] API 호출 실패 시 재시도 로직
  - [ ] 실패 시 로컬에 임시 저장 (선택)

**산출물**:
- `backend/app/services/result_collector.py`

### 7.3 통합 테스트
- [ ] 전체 플로우 테스트
  - [ ] 스캔 시작 → 진행 → 결과 API 호출 → DB 저장 확인
- [ ] 백엔드 팀과 통합 테스트

**산출물**:
- `backend/tests/test_result_collection.py`

**완료 기준**:
- LangGraph 스캔 완료 시 결과가 백엔드 API로 전송됨
- 백엔드 DB에 점검 결과가 정상 저장됨

---

## Phase 8: 테스트 및 최적화 (1주)

### 8.1 단위 테스트 및 통합 테스트 작성
- [ ] 단위 테스트 커버리지 80% 이상
  - [ ] LangGraph 서비스 테스트
  - [ ] 각 도구(MCP) 테스트
  - [ ] API 엔드포인트 테스트
- [ ] 통합 테스트
  - [ ] E2E 시나리오 테스트
  - [ ] 채팅 → 스캔 → 결과 조회 전체 플로우

**산출물**:
- `backend/tests/` (전체 테스트 파일)

### 8.2 성능 최적화
- [ ] LangGraph 실행 시간 측정 및 최적화
  - [ ] 병렬 처리 가능한 노드 식별
  - [ ] 불필요한 대기 시간 제거
- [ ] API 응답 속도 최적화
  - [ ] DB 쿼리 최적화
  - [ ] 캐싱 적용 (Redis)

**산출물**:
- `docs/performance/optimization_report.md`

### 8.3 에러 핸들링 및 로깅 강화
- [ ] 전역 에러 핸들러 추가
- [ ] 구조화된 로깅 (JSON 로그)
  - [ ] 각 노드 실행 로그
  - [ ] API 요청/응답 로그
- [ ] 에러 알림 (선택)
  - [ ] Slack, Email 알림

**산출물**:
- `backend/app/core/logging.py`
- `backend/app/core/error_handler.py`

**완료 기준**:
- 테스트 커버리지 80% 이상
- 주요 에러 케이스 모두 핸들링됨
- 로그로 문제 추적 가능

---

## Phase 9: 문서화 및 인수인계 준비 (1주)

### 9.1 API 문서 자동화
- [ ] Swagger/OpenAPI 문서 생성
  - [ ] FastAPI 자동 문서 활용
  - [ ] `/docs` 엔드포인트에서 확인 가능
- [ ] API 사용 예시 작성
  - [ ] curl 예시
  - [ ] Python 예시

**산출물**:
- `docs/api/api_documentation.md`

### 9.2 개발자 가이드 작성
- [ ] LangGraph 서비스 개발 가이드
  - [ ] 새 노드 추가 방법
  - [ ] 새 MCP 도구 추가 방법
- [ ] 백엔드 설치 및 실행 가이드
  - [ ] 환경 설정
  - [ ] DB 마이그레이션
  - [ ] 서버 실행

**산출물**:
- `docs/developer_guide.md`
- `backend/README.md`

### 9.3 배포 가이드 작성
- [ ] Docker 이미지 빌드 가이드
- [ ] 환경 변수 설정 가이드
- [ ] 운영 환경 배포 가이드

**산출물**:
- `docs/deployment/deployment_guide.md`

**완료 기준**:
- API 문서가 자동 생성되고 `/docs`에서 확인 가능
- 개발자 가이드를 보고 신규 개발자가 기여 가능
- 배포 가이드를 보고 운영 환경에 배포 가능

---

## Phase 10: 최종 통합 테스트 및 프로젝트 마무리 (1주)

### 10.1 전체 시스템 통합 테스트
- [ ] 백엔드(서지원) + 프론트엔드(이왕희) + LangGraph(윤지수) 통합 테스트
- [ ] 실제 사용 시나리오 테스트
  - [ ] 사용자가 채팅으로 스캔 요청
  - [ ] 실시간 진행 상황 확인
  - [ ] 결과 조회 및 보고서 다운로드
- [ ] 부하 테스트
  - [ ] 동시 100개 스캔 요청 처리

**산출물**:
- `docs/testing/integration_test_report.md`

### 10.2 실무 담당자 피드백 반영
- [ ] 모의해킹 수행으로 실용성 평가
- [ ] 피드백 수집 및 개선사항 정리
- [ ] 긴급 버그 수정

**산출물**:
- `docs/feedback/user_feedback.md`

### 10.3 최종 결과 보고서 작성
- [ ] 개인 달성도 정리
  - [ ] 완료된 기능 목록
  - [ ] 미완료 기능 및 사유
- [ ] 기술적 성과 정리
  - [ ] LangGraph 활용 사례
  - [ ] MCP 아키텍처 성과
- [ ] 향후 개선 방안 제시

**산출물**:
- `docs/final_report/yoon_jisu_final_report.md`

**완료 기준**:
- 전체 시스템 통합 테스트 통과
- 실무 담당자 승인
- 최종 보고서 제출

---

## 일정 요약

| Phase | 기간 | 주요 산출물 |
|-------|------|------------|
| Phase 0 | 완료 | PoC 코드 (simple_poc.py, advanced_poc.py) |
| Phase 1 | 1주 | 아키텍처 설계 문서, 제약사항 분석 |
| Phase 2 | 2주 | FastAPI 백엔드, LangGraph 서비스, DB 모델 |
| Phase 3 | 2주 | 비동기 처리, WebSocket 실시간 통신 |
| Phase 4 | 1주 | 채팅 API, 채팅 히스토리 |
| Phase 5 | 2주 | MCP 도구 모듈화, ToolRegistry |
| Phase 6 | 1주 | 시각화 API, Flow CRUD |
| Phase 7 | 1주 | 결과 수집 API 연동 |
| Phase 8 | 1주 | 테스트, 최적화, 로깅 |
| Phase 9 | 1주 | 문서화, 개발 가이드 |
| Phase 10 | 1주 | 통합 테스트, 최종 보고서 |
| **총 기간** | **12주** | - |

---

## 주요 체크포인트

### Week 3 (Phase 1 완료)
- ✅ 아키텍처 설계 완료
- ✅ 기술 스택 확정
- ✅ 제약사항 분석 완료

### Week 5 (Phase 2 완료)
- ✅ FastAPI 백엔드 실행
- ✅ LangGraph API 호출 가능
- ✅ DB에 스캔 결과 저장

### Week 7 (Phase 3 완료)
- ✅ 비동기 스캔 실행
- ✅ WebSocket 실시간 진행 상황 전송

### Week 8 (Phase 4 완료)
- ✅ 채팅 API 연동
- ✅ 채팅으로 스캔 실행 가능

### Week 10 (Phase 5 완료)
- ✅ MCP 도구 모듈화
- ✅ 새 도구 추가 가능

### Week 12 (Phase 10 완료)
- ✅ 전체 시스템 통합 테스트 통과
- ✅ 최종 보고서 제출

---

## 리스크 및 대응 방안

### 리스크 1: LangGraph 성능 문제
- **증상**: 스캔 시간이 너무 오래 걸림 (30초 이상)
- **대응**:
  - 병렬 처리 가능한 노드 병렬화
  - 타임아웃 설정
  - 경량 모델 사용 (gpt-4o-mini)

### 리스크 2: 백엔드/프론트엔드 API 명세 불일치
- **증상**: API 요청/응답 형식 차이로 통신 실패
- **대응**:
  - Phase 2에서 API 명세 조기 공유
  - Swagger 문서 자동 생성
  - 주 1회 통합 회의

### 리스크 3: MCP 도구 추가 시 복잡도 증가
- **증상**: 새 도구 추가 시 기존 코드 수정 필요
- **대응**:
  - 추상화 레이어 강화 (BaseToolInterface)
  - 플러그인 아키텍처 철저히 설계
  - 단위 테스트로 검증

### 리스크 4: OpenAI API 비용
- **증상**: API 호출 비용 급증
- **대응**:
  - 캐싱 적용 (같은 타겟 재스캔 시)
  - 토큰 사용량 모니터링
  - 경량 모델 우선 사용

---

## 참고 자료

- LangGraph 공식 문서: https://langchain-ai.github.io/langgraph/
- FastAPI 공식 문서: https://fastapi.tiangolo.com/
- WebSocket 가이드: https://fastapi.tiangolo.com/advanced/websockets/
- Celery 공식 문서: https://docs.celeryq.dev/

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
