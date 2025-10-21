# 백엔드 디렉토리 구조 설계

## 개요
이 문서는 3VI 보안 스캐너 백엔드의 디렉토리 구조 및 각 구성 요소의 역할을 정의합니다.

---

## 전체 디렉토리 구조

```
3vi-v1/
├── backend/                        # 백엔드 애플리케이션
│   ├── app/                        # 메인 애플리케이션 코드
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 애플리케이션 진입점
│   │   │
│   │   ├── api/                    # API 라우터 레이어
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # 공통 의존성 주입
│   │   │   └── v1/                 # API v1
│   │   │       ├── __init__.py
│   │   │       ├── health.py       # 헬스체크 엔드포인트
│   │   │       ├── langgraph.py    # LangGraph 스캔 엔드포인트
│   │   │       ├── chat.py         # 채팅 엔드포인트
│   │   │       ├── websocket.py    # WebSocket 엔드포인트
│   │   │       ├── visualization.py # 시각화 엔드포인트
│   │   │       └── flow.py         # Flow CRUD 엔드포인트
│   │   │
│   │   ├── core/                   # 핵심 설정 및 유틸리티
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # 환경 설정 (Pydantic Settings)
│   │   │   ├── database.py         # DB 연결 설정
│   │   │   ├── logging.py          # 로깅 설정
│   │   │   ├── security_policy.py  # 보안 정책 (화이트리스트 등)
│   │   │   ├── websocket_manager.py # WebSocket 연결 관리
│   │   │   └── error_handler.py    # 전역 에러 핸들러
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM 모델
│   │   │   ├── __init__.py
│   │   │   ├── scan_session.py     # 스캔 세션 모델
│   │   │   ├── scan_result.py      # 스캔 결과 모델
│   │   │   ├── chat_history.py     # 채팅 히스토리 모델
│   │   │   ├── flow.py             # Flow 모델
│   │   │   └── crud.py             # CRUD 함수
│   │   │
│   │   ├── schemas/                # Pydantic 스키마 (요청/응답)
│   │   │   ├── __init__.py
│   │   │   ├── scan_state.py       # LangGraph State 스키마
│   │   │   ├── scan_request.py     # 스캔 요청 스키마
│   │   │   ├── scan_response.py    # 스캔 응답 스키마
│   │   │   ├── chat.py             # 채팅 스키마
│   │   │   └── graph_visualization.py # 그래프 시각화 스키마
│   │   │
│   │   └── services/               # 비즈니스 로직 레이어
│   │       ├── __init__.py
│   │       ├── langgraph_service.py    # LangGraph 워크플로우
│   │       ├── async_scan_service.py   # 비동기 스캔 실행
│   │       ├── chat_service.py         # 채팅 처리
│   │       ├── result_collector.py     # 결과 수집 및 전송
│   │       ├── tool_registry.py        # MCP 도구 레지스트리
│   │       │
│   │       └── tools/              # MCP 도구 모듈
│   │           ├── __init__.py
│   │           ├── base_tool.py        # 추상 베이스 클래스
│   │           ├── nmap_tool.py        # Nmap 스캔 도구
│   │           └── openai_tool.py      # OpenAI 분석 도구
│   │
│   ├── tests/                      # 테스트 코드
│   │   ├── __init__.py
│   │   ├── conftest.py             # pytest 설정
│   │   ├── test_api.py             # API 테스트
│   │   ├── test_langgraph.py       # LangGraph 테스트
│   │   ├── test_websocket.py       # WebSocket 테스트
│   │   ├── test_tools.py           # 도구 테스트
│   │   └── test_tool_registry.py   # ToolRegistry 테스트
│   │
│   ├── alembic/                    # DB 마이그레이션
│   │   ├── versions/               # 마이그레이션 파일
│   │   ├── env.py                  # Alembic 환경 설정
│   │   └── README
│   │
│   ├── scripts/                    # 유틸리티 스크립트
│   │   ├── test_websocket_client.py    # WebSocket 테스트 클라이언트
│   │   └── test_chat_client.py         # 채팅 테스트 클라이언트
│   │
│   ├── logs/                       # 로그 파일 (gitignore)
│   │
│   ├── requirements.txt            # 프로덕션 의존성
│   ├── requirements-dev.txt        # 개발 의존성
│   ├── .env                        # 환경 변수 (gitignore)
│   ├── .env.example                # 환경 변수 예시
│   ├── alembic.ini                 # Alembic 설정
│   └── README.md                   # 백엔드 README
│
├── 01-poc/                         # PoC 코드 (참고용)
│   ├── simple_poc.py
│   ├── advanced_poc.py
│   └── README.md
│
├── docs/                           # 문서
│   ├── architecture/               # 아키텍처 문서
│   │   ├── backend_structure.md    # 이 문서
│   │   ├── design_principles.md    # 설계 원칙
│   │   ├── langgraph_service_design.md
│   │   ├── async_strategy.md
│   │   └── mcp_design.md
│   │
│   ├── phases/                     # Phase별 작업 문서
│   │   ├── phase1-tech-stack-design.md
│   │   ├── phase2-langgraph-service.md
│   │   └── phase3-async-websocket.md
│   │
│   ├── constraints/                # 제약사항 분석
│   │   ├── implementation_limitations.md
│   │   ├── alternative_solutions.md
│   │   └── legal_compliance.md
│   │
│   ├── api/                        # API 문서
│   │   ├── langgraph_api_spec.md
│   │   ├── chat_api_spec.md
│   │   └── api_documentation.md
│   │
│   └── setup/                      # 설치 가이드
│       └── installation_guide.md
│
├── docker-compose.yml              # Docker Compose 설정
├── .gitignore
└── README.md                       # 프로젝트 README
```

---

## 레이어별 역할

### 1. API 레이어 (`app/api/`)
**역할**: HTTP 요청/응답 처리, 입력 검증, 라우팅

**책임**:
- 요청 파라미터 검증 (Pydantic)
- 인증/인가 (향후 추가)
- 응답 포맷팅
- 에러 핸들링

**예시**:
```python
# app/api/v1/langgraph.py
@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest, db: Session = Depends(get_db)):
    # 서비스 레이어 호출
    session = crud.create_scan_session(db, request.target, request.scan_type)
    # ...
```

### 2. 서비스 레이어 (`app/services/`)
**역할**: 비즈니스 로직 구현

**책임**:
- LangGraph 워크플로우 실행
- 비동기 작업 관리
- 도구 호출 및 조율
- 결과 수집 및 가공

**예시**:
```python
# app/services/langgraph_service.py
class LangGraphService:
    def run_scan(self, target: str, scan_type: str) -> dict:
        # LangGraph 실행 로직
```

### 3. 데이터 레이어 (`app/models/`)
**역할**: 데이터베이스 모델 및 CRUD 연산

**책임**:
- ORM 모델 정의
- DB 쿼리 함수
- 데이터 변환

**예시**:
```python
# app/models/scan_session.py
class ScanSession(Base):
    __tablename__ = "scan_sessions"
    id = Column(String(36), primary_key=True)
    # ...
```

### 4. 스키마 레이어 (`app/schemas/`)
**역할**: 데이터 검증 및 직렬화

**책임**:
- 요청/응답 스키마 정의
- 타입 검증
- JSON 직렬화/역직렬화

**예시**:
```python
# app/schemas/scan_request.py
class ScanRequest(BaseModel):
    target: str
    scan_type: Literal["quick", "standard", "full"]
```

### 5. 핵심 레이어 (`app/core/`)
**역할**: 공통 설정 및 유틸리티

**책임**:
- 환경 설정 관리
- DB 연결 설정
- 로깅 설정
- 보안 정책

---

## 설계 원칙

### 1. 관심사 분리 (Separation of Concerns)
- API는 HTTP만 처리
- 서비스는 비즈니스 로직만 처리
- 모델은 데이터만 관리

### 2. 의존성 역전 (Dependency Inversion)
- 서비스는 인터페이스에 의존
- 구체적인 구현은 주입

```python
# 나쁜 예
class ScanService:
    def __init__(self):
        self.nmap = NmapTool()  # 강한 결합

# 좋은 예
class ScanService:
    def __init__(self, scan_tool: BaseTool):
        self.scan_tool = scan_tool  # 느슨한 결합
```

### 3. 단일 책임 원칙 (Single Responsibility)
- 각 클래스/함수는 하나의 책임만

### 4. DRY (Don't Repeat Yourself)
- 공통 로직은 `app/core/` 또는 유틸리티로 분리

---

## 모듈 임포트 규칙

### 절대 임포트 사용
```python
# 권장
from app.services.langgraph_service import LangGraphService
from app.models.scan_session import ScanSession

# 비권장
from ..services.langgraph_service import LangGraphService
```

### 순환 참조 방지
- API → 서비스 → 모델 (단방향)
- 서비스 간 참조는 인터페이스를 통해

---

## 확장성 고려사항

### 1. 새로운 API 버전 추가
```
app/api/
  ├── v1/
  └── v2/  # 새 버전
```

### 2. 새로운 도구 추가
```
app/services/tools/
  ├── base_tool.py
  ├── nmap_tool.py
  └── masscan_tool.py  # 새 도구
```

### 3. 새로운 서비스 추가
```
app/services/
  ├── langgraph_service.py
  └── compliance_service.py  # 새 서비스
```

---

## 파일 명명 규칙

- **모듈**: `snake_case.py`
- **클래스**: `PascalCase`
- **함수/변수**: `snake_case`
- **상수**: `UPPER_SNAKE_CASE`

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
