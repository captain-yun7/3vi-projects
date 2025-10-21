# Phase 1: 기술 스택 설계 및 환경 구축

## 개요
- **기간**: 1주
- **목표**: 프로젝트의 기술적 기반을 확립하고 개발 환경을 구축
- **선행 조건**: Phase 0 (PoC) 완료

---

## 1.1 프로젝트 구조 설계

### 목표
PoC 단계의 단일 파일 구조를 확장 가능한 프로덕션 레벨 아키텍처로 전환

### 작업 내용

#### 1.1.1 백엔드 디렉토리 구조 설계
```
3vi-v1/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 애플리케이션 진입점
│   │   ├── api/                    # API 라우터
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # 의존성 주입
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── langgraph.py    # LangGraph 관련 엔드포인트
│   │   │       ├── chat.py         # 채팅 엔드포인트
│   │   │       ├── websocket.py    # WebSocket 엔드포인트
│   │   │       └── health.py       # 헬스체크
│   │   ├── core/                   # 핵심 설정
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # 환경 설정
│   │   │   ├── database.py         # DB 연결
│   │   │   ├── logging.py          # 로깅 설정
│   │   │   └── websocket_manager.py
│   │   ├── models/                 # SQLAlchemy 모델
│   │   │   ├── __init__.py
│   │   │   ├── scan_session.py
│   │   │   ├── scan_result.py
│   │   │   └── chat_history.py
│   │   ├── schemas/                # Pydantic 스키마
│   │   │   ├── __init__.py
│   │   │   ├── scan_state.py       # LangGraph State
│   │   │   ├── scan_request.py
│   │   │   ├── scan_response.py
│   │   │   └── chat.py
│   │   └── services/               # 비즈니스 로직
│   │       ├── __init__.py
│   │       ├── langgraph_service.py  # LangGraph 워크플로우
│   │       ├── async_scan_service.py # 비동기 스캔
│   │       ├── chat_service.py
│   │       └── tools/              # MCP 도구들
│   │           ├── __init__.py
│   │           ├── base_tool.py
│   │           ├── nmap_tool.py
│   │           └── openai_tool.py
│   ├── tests/                      # 테스트 코드
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_langgraph.py
│   │   └── test_api.py
│   ├── alembic/                    # DB 마이그레이션
│   │   ├── versions/
│   │   └── env.py
│   ├── scripts/                    # 유틸리티 스크립트
│   │   ├── test_websocket_client.py
│   │   └── test_chat_client.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── README.md
├── 01-poc/                         # PoC 코드 (참고용)
├── docs/                           # 문서
└── docker-compose.yml
```

#### 1.1.2 설계 원칙
1. **관심사 분리 (Separation of Concerns)**
   - API 계층: 요청/응답 처리
   - 서비스 계층: 비즈니스 로직 (LangGraph 실행)
   - 데이터 계층: DB 모델 및 CRUD

2. **의존성 역전 (Dependency Inversion)**
   - 인터페이스 기반 설계
   - 도구(Tools)는 BaseToolInterface 상속

3. **확장 가능성 (Scalability)**
   - 새로운 도구 추가 시 tools/ 디렉토리에 파일만 추가
   - 새로운 API 엔드포인트는 api/v1/ 에 추가

### 산출물
- `docs/architecture/backend_structure.md` - 디렉토리 구조 설명서
- `docs/architecture/design_principles.md` - 설계 원칙 문서

### 체크포인트
- [ ] 디렉토리 구조가 문서화되어 있는가?
- [ ] 각 디렉토리의 역할이 명확한가?
- [ ] 팀원들이 구조를 이해하고 동의했는가?

---

## 1.2 LangGraph 서비스 아키텍처 설계

### 목표
PoC의 단일 파일 스크립트를 재사용 가능한 서비스 클래스로 전환하는 설계 수립

### 작업 내용

#### 1.2.1 PoC → 서비스 변환 전략

**현재 PoC 구조 (advanced_poc.py)**
```python
# 전역 변수로 State 관리
class SecurityScanState(TypedDict):
    target: str
    scan_type: str
    # ...

# 개별 함수로 노드 정의
def analyze_input(state: SecurityScanState):
    # ...
    return state

def port_scan(state: SecurityScanState):
    # ...
    return state

# 메인 실행
graph = StateGraph(SecurityScanState)
graph.add_node("analyze", analyze_input)
# ...
compiled_graph = graph.compile()
result = compiled_graph.invoke({"target": "192.168.1.1"})
```

**목표 서비스 구조**
```python
class LangGraphService:
    def __init__(self, config: Config):
        self.config = config
        self.openai_client = OpenAI(api_key=config.openai_api_key)
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledGraph:
        """그래프 구조 생성"""
        graph = StateGraph(SecurityScanState)
        graph.add_node("analyze", self._analyze_input)
        graph.add_node("port_scan", self._port_scan)
        # ...
        return graph.compile()

    def _analyze_input(self, state: SecurityScanState):
        """입력 분석 노드"""
        # 로깅, 에러 핸들링 추가
        logger.info(f"Analyzing input: {state['target']}")
        try:
            # 기존 PoC 로직
            return state
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    async def run_scan_async(self, target: str, scan_type: str) -> dict:
        """비동기 스캔 실행"""
        state = {"target": target, "scan_type": scan_type}
        result = await asyncio.to_thread(self.graph.invoke, state)
        return result
```

#### 1.2.2 비동기 처리 전략 선택

**옵션 1: FastAPI BackgroundTasks**
- 장점:
  - 설정이 간단함
  - 추가 인프라 불필요
- 단점:
  - 서버 재시작 시 작업 손실
  - 분산 환경 지원 안 됨
- 적합한 경우: 프로토타입, 간단한 작업

**옵션 2: Celery + Redis**
- 장점:
  - 작업 큐 영속성 보장
  - 분산 처리 가능
  - 재시도 로직 내장
- 단점:
  - 인프라 복잡도 증가 (Redis, Celery worker)
  - 설정이 복잡함
- 적합한 경우: 프로덕션 환경, 긴 작업

**선택: Phase 2에서는 BackgroundTasks, Phase 3에서 Celery로 전환 검토**

#### 1.2.3 상태 관리 방법

**옵션 1: 메모리 (딕셔너리)**
- 장점: 빠름
- 단점: 서버 재시작 시 손실, 분산 불가
- 적합한 경우: 개발 초기

**옵션 2: Redis**
- 장점: 영속성, 분산 지원, 빠른 읽기/쓰기
- 단점: 추가 인프라 필요
- 적합한 경우: 프로덕션

**옵션 3: PostgreSQL**
- 장점: 영속성, 복잡한 쿼리 가능
- 단점: 상대적으로 느림
- 적합한 경우: 최종 결과 저장

**선택: 중간 상태는 Redis, 최종 결과는 PostgreSQL**

### 산출물
- `docs/architecture/langgraph_service_design.md` - 서비스 아키텍처 설계서
- `docs/architecture/async_strategy.md` - 비동기 처리 전략 문서

### 체크포인트
- [ ] PoC → 서비스 변환 방법이 명확한가?
- [ ] 비동기 처리 전략이 선택되었는가?
- [ ] 상태 관리 방법이 결정되었는가?

---

## 1.3 기술 스택 확정 및 환경 설정

### 목표
개발에 필요한 모든 기술 스택을 확정하고 환경을 구축

### 작업 내용

#### 1.3.1 기술 스택 확정

**백엔드 프레임워크**
- FastAPI 0.115.0+
  - 이유: 비동기 지원, 자동 API 문서 생성, 타입 힌트 활용

**Python 버전**
- Python 3.10+
  - 이유: TypedDict, 패턴 매칭 등 최신 기능 활용

**데이터베이스**
- PostgreSQL 14+
  - 이유: JSON 타입 지원, 안정성, 확장성
- Redis 7+
  - 이유: 세션 캐시, Celery 브로커

**ORM 및 마이그레이션**
- SQLAlchemy 2.0+
- Alembic 1.13+

**비동기 작업 큐**
- Celery 5.3+ (Phase 3에서 도입)
- Redis as Broker

**AI/LLM**
- LangGraph 0.2.56+
- OpenAI API (gpt-4o-mini)
- python-nmap 0.7.1+

**WebSocket**
- FastAPI 내장 WebSocket

**테스트**
- pytest 8.0+
- pytest-asyncio
- httpx (FastAPI 테스트 클라이언트)

**개발 도구**
- Black (코드 포맷터)
- Flake8 (린터)
- mypy (타입 체커)

#### 1.3.2 requirements.txt 작성

```txt
# requirements.txt

# FastAPI
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.10.3
pydantic-settings==2.6.1

# Database
sqlalchemy==2.0.36
alembic==1.13.3
psycopg2-binary==2.9.10
redis==5.2.0

# LangGraph & AI
langgraph==0.2.56
langchain==0.3.13
langchain-openai==0.2.14
openai==1.57.2

# Security Scanning
python-nmap==0.7.1

# Utils
python-dotenv==1.0.1
python-multipart==0.0.20
httpx==0.28.1

# WebSocket
websockets==14.1
```

```txt
# requirements-dev.txt

-r requirements.txt

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0

# Code Quality
black==24.10.0
flake8==7.1.1
mypy==1.13.0

# Development
ipython==8.30.0
```

#### 1.3.3 환경 변수 설정

```bash
# .env.example

# Application
APP_NAME=3VI Security Scanner
APP_VERSION=1.0.0
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/securitydb
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Celery (Phase 3)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Scanning
SCAN_TIMEOUT=300
MAX_CONCURRENT_SCANS=5
```

#### 1.3.4 Docker Compose 설정 (선택사항)

```yaml
# docker-compose.yml

version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: secuser
      POSTGRES_PASSWORD: secpass
      POSTGRES_DB: securitydb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

### 산출물
- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `.env.example`
- `docker-compose.yml` (선택)
- `docs/setup/installation_guide.md` - 설치 가이드

### 체크포인트
- [ ] requirements.txt가 작성되었는가?
- [ ] .env.example이 작성되었는가?
- [ ] Docker Compose 설정이 작성되었는가? (선택)
- [ ] 로컬 환경에서 설치 테스트 완료했는가?

---

## 1.4 모의해킹 기능 제약사항 분석

### 목표
실제 구현 시 발생 가능한 법적, 기술적 제약사항을 사전에 파악하고 대안 마련

### 작업 내용

#### 1.4.1 구현 불가능한 항목 식별

**법적/윤리적 제약**
1. **실제 공격 시뮬레이션**
   - 제약: SQL Injection, XSS 등 실제 공격 코드 실행 불가
   - 사유: 정보통신망법 위반 가능성
   - 영향: 실제 취약점 검증 제한

2. **무단 포트 스캔**
   - 제약: 허가되지 않은 대상에 대한 스캔 금지
   - 사유: 정보통신망 침해 행위
   - 영향: 스캔 대상 제한 (자체 시스템만)

3. **비밀번호 크래킹**
   - 제약: Brute force, Dictionary attack 불가
   - 사유: 정보통신망법 위반
   - 영향: 인증 취약점 검증 제한

**기술적 제약**
1. **네트워크 방화벽**
   - 제약: 외부 네트워크 스캔 차단
   - 사유: 방화벽 정책
   - 영향: 스캔 범위 제한

2. **권한 부족**
   - 제약: 일부 스캔 도구는 root 권한 필요
   - 사유: 보안 정책
   - 영향: 특정 스캔 기법 사용 불가 (SYN scan 등)

3. **성능 제약**
   - 제약: 전체 포트 스캔 시간 과다 (65535 포트)
   - 사유: 시간 제한 (API 타임아웃)
   - 영향: 스캔 범위 축소 필요

**AI 모델 제약**
1. **할루시네이션**
   - 제약: AI가 존재하지 않는 취약점 생성 가능
   - 사유: LLM 특성
   - 영향: 결과 검증 필요

2. **비용**
   - 제약: OpenAI API 호출 비용
   - 사유: 토큰당 과금
   - 영향: 분석 범위 제한

#### 1.4.2 대안 방안 수립

**1. 시뮬레이션 모드**
```python
class ScanMode(Enum):
    REAL = "real"           # 실제 스캔 (허가된 대상만)
    SIMULATION = "simulation"  # 시뮬레이션 (샘플 데이터)
    HYBRID = "hybrid"       # 실제 스캔 + AI 분석

# 시뮬레이션 데이터
SIMULATION_PORT_SCAN_RESULT = {
    "22": {"state": "open", "service": "ssh"},
    "80": {"state": "open", "service": "http"},
    "443": {"state": "open", "service": "https"},
    "3306": {"state": "open", "service": "mysql"},
}
```

**2. 안전한 도구 대체**
- nmap → masscan (빠른 스캔)
- 실제 공격 → OWASP ZAP (안전한 취약점 스캐너)
- 비밀번호 크래킹 → 강도 체크만 수행

**3. 샌드박스 환경**
```yaml
# 테스트 전용 Docker 컨테이너
test_target:
  image: vulnerable-app:latest  # 의도적으로 취약한 앱
  networks:
    - isolated_network
  # 외부 네트워크 차단
```

**4. 허용 대상 화이트리스트**
```python
ALLOWED_TARGETS = [
    "127.0.0.1",
    "localhost",
    "192.168.1.0/24",  # 내부 네트워크만
]

def validate_target(target: str) -> bool:
    """스캔 대상 검증"""
    if target in ALLOWED_TARGETS:
        return True
    raise ValueError(f"Unauthorized target: {target}")
```

**5. AI 결과 검증**
```python
def verify_ai_result(ai_analysis: dict, scan_result: dict) -> dict:
    """AI 분석 결과를 실제 스캔 결과와 교차 검증"""
    verified = {}
    for cve in ai_analysis.get("cves", []):
        # CVE 데이터베이스와 대조
        if verify_cve_exists(cve):
            verified[cve] = ai_analysis[cve]
    return verified
```

#### 1.4.3 구현 우선순위

**High Priority (반드시 구현)**
1. 대상 검증 (화이트리스트)
2. 시뮬레이션 모드
3. 안전한 포트 스캔 (nmap -Pn -T4)

**Medium Priority (권장)**
4. 샌드박스 환경
5. AI 결과 검증
6. OWASP ZAP 연동

**Low Priority (선택)**
7. 고급 취약점 스캐너 (Burp Suite API)
8. 실시간 CVE 데이터베이스 연동

### 산출물
- `docs/constraints/implementation_limitations.md` - 제약사항 상세 분석
- `docs/constraints/alternative_solutions.md` - 대안 방안
- `docs/constraints/legal_compliance.md` - 법적 준수사항
- `backend/app/core/security_policy.py` - 보안 정책 코드

### 체크포인트
- [ ] 법적 제약사항이 문서화되었는가?
- [ ] 기술적 제약사항이 파악되었는가?
- [ ] 각 제약사항에 대한 대안이 수립되었는가?
- [ ] 화이트리스트 검증 로직이 설계되었는가?

---

## Phase 1 완료 기준

### 필수 체크리스트
- [ ] 백엔드 디렉토리 구조가 설계되고 문서화됨
- [ ] LangGraph 서비스 아키텍처가 설계됨
- [ ] 비동기 처리 전략이 선택됨
- [ ] 상태 관리 방법이 결정됨
- [ ] 기술 스택이 최종 확정됨
- [ ] requirements.txt 작성 완료
- [ ] .env.example 작성 완료
- [ ] 모의해킹 제약사항이 분석됨
- [ ] 대안 방안이 수립됨
- [ ] 모든 문서가 docs/ 디렉토리에 정리됨

### 산출물 목록
1. `docs/architecture/backend_structure.md`
2. `docs/architecture/design_principles.md`
3. `docs/architecture/langgraph_service_design.md`
4. `docs/architecture/async_strategy.md`
5. `backend/requirements.txt`
6. `backend/requirements-dev.txt`
7. `.env.example`
8. `docker-compose.yml` (선택)
9. `docs/constraints/implementation_limitations.md`
10. `docs/constraints/alternative_solutions.md`
11. `docs/setup/installation_guide.md`

### 검증 방법
1. **문서 리뷰**: 팀원들과 아키텍처 문서 리뷰
2. **환경 테스트**: requirements.txt로 가상환경 생성 및 패키지 설치
3. **제약사항 확인**: 법적 검토 (필요 시 변호사 자문)

---

## 다음 단계

Phase 1 완료 후 [Phase 2: LangGraph 서비스화 및 API 기본 연동](./phase2-langgraph-service.md)로 진행

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
