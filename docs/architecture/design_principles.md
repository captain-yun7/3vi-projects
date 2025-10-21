# 설계 원칙

## 개요
3VI 보안 스캐너 백엔드의 핵심 설계 원칙과 아키텍처 패턴을 정의합니다.

---

## 1. 아키텍처 패턴

### 1.1 레이어드 아키텍처 (Layered Architecture)

```
┌─────────────────────────────────────┐
│     API Layer (FastAPI Routes)     │  ← HTTP 요청/응답
├─────────────────────────────────────┤
│   Service Layer (Business Logic)   │  ← LangGraph, 비즈니스 로직
├─────────────────────────────────────┤
│    Data Layer (Models & CRUD)      │  ← DB 접근
├─────────────────────────────────────┤
│   Infrastructure (DB, Redis, etc)  │  ← 외부 의존성
└─────────────────────────────────────┘
```

**장점**:
- 각 레이어의 책임이 명확함
- 테스트 용이성
- 독립적인 변경 가능

**규칙**:
- 상위 레이어는 하위 레이어만 호출
- 하위 레이어는 상위 레이어를 모름
- 레이어 건너뛰기 금지 (API → Data 직접 접근 X)

---

### 1.2 의존성 주입 (Dependency Injection)

**나쁜 예** (강한 결합):
```python
class LangGraphService:
    def __init__(self):
        self.openai_client = OpenAI(api_key="hardcoded")  # 하드코딩
        self.db = create_engine("postgresql://...")       # 강한 결합
```

**좋은 예** (느슨한 결합):
```python
class LangGraphService:
    def __init__(self, config: Config, db: Session):
        self.openai_client = OpenAI(api_key=config.openai_api_key)
        self.db = db

# FastAPI에서 의존성 주입
@router.post("/scan")
async def start_scan(
    request: ScanRequest,
    db: Session = Depends(get_db),  # 의존성 주입
):
    service = LangGraphService(config=settings, db=db)
    # ...
```

**장점**:
- 테스트 시 Mock 객체 주입 가능
- 설정 변경 용이
- 코드 재사용성 향상

---

### 1.3 Repository 패턴

**목적**: 데이터 접근 로직을 캡슐화

```python
# app/models/crud.py

def create_scan_session(db: Session, target: str, scan_type: str) -> ScanSession:
    """스캔 세션 생성"""
    session = ScanSession(id=str(uuid.uuid4()), target=target, scan_type=scan_type)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_scan_session(db: Session, session_id: str) -> Optional[ScanSession]:
    """스캔 세션 조회"""
    return db.query(ScanSession).filter(ScanSession.id == session_id).first()
```

**장점**:
- DB 쿼리 로직 중앙화
- 서비스 레이어는 DB 세부사항 몰라도 됨
- DB 변경 시 CRUD만 수정

---

## 2. SOLID 원칙

### 2.1 단일 책임 원칙 (Single Responsibility Principle)

**나쁜 예**:
```python
class LangGraphService:
    def run_scan(self, target: str):
        # 1. 포트 스캔
        # 2. 취약점 분석
        # 3. 보고서 생성
        # 4. 이메일 전송  ← 책임 과다
        # 5. DB 저장
```

**좋은 예**:
```python
class LangGraphService:
    def run_scan(self, target: str):
        # 스캔 워크플로우 실행만

class ReportGenerator:
    def generate(self, scan_result: dict):
        # 보고서 생성만

class NotificationService:
    def send_email(self, report: str):
        # 이메일 전송만
```

---

### 2.2 개방-폐쇄 원칙 (Open-Closed Principle)

**목적**: 확장에는 열려있고, 수정에는 닫혀있어야 함

```python
# app/services/tools/base_tool.py

from abc import ABC, abstractmethod

class BaseTool(ABC):
    """모든 도구의 기반 클래스"""

    @abstractmethod
    def execute(self, target: str, options: dict) -> dict:
        """도구 실행"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """도구 이름"""
        pass

# app/services/tools/nmap_tool.py

class NmapTool(BaseTool):
    def execute(self, target: str, options: dict) -> dict:
        # Nmap 실행
        pass

    @property
    def name(self) -> str:
        return "nmap"

# 새 도구 추가 (기존 코드 수정 없음)
class MasscanTool(BaseTool):
    def execute(self, target: str, options: dict) -> dict:
        # Masscan 실행
        pass

    @property
    def name(self) -> str:
        return "masscan"
```

---

### 2.3 리스코프 치환 원칙 (Liskov Substitution Principle)

**목적**: 하위 타입은 상위 타입을 대체 가능해야 함

```python
def run_security_tool(tool: BaseTool, target: str):
    """어떤 도구든 BaseTool을 상속하면 실행 가능"""
    result = tool.execute(target, {})
    return result

# NmapTool, MasscanTool 모두 사용 가능
result1 = run_security_tool(NmapTool(), "192.168.1.1")
result2 = run_security_tool(MasscanTool(), "192.168.1.1")
```

---

### 2.4 인터페이스 분리 원칙 (Interface Segregation Principle)

**나쁜 예**:
```python
class Tool(ABC):
    @abstractmethod
    def scan_ports(self): pass

    @abstractmethod
    def analyze_vulnerabilities(self): pass

    @abstractmethod
    def generate_report(self): pass  # 모든 도구가 보고서를 생성하지 않음
```

**좋은 예**:
```python
class ScanTool(ABC):
    @abstractmethod
    def scan(self): pass

class AnalysisTool(ABC):
    @abstractmethod
    def analyze(self): pass

class NmapTool(ScanTool):
    def scan(self): pass  # 스캔만 구현

class ReportGenerator(AnalysisTool):
    def analyze(self): pass  # 분석만 구현
```

---

### 2.5 의존성 역전 원칙 (Dependency Inversion Principle)

**목적**: 고수준 모듈은 저수준 모듈에 의존하지 않고, 둘 다 추상화에 의존

```python
# 나쁜 예
class ScanService:
    def __init__(self):
        self.nmap = NmapTool()  # 구체적인 클래스에 의존

# 좋은 예
class ScanService:
    def __init__(self, scan_tool: BaseTool):  # 추상화에 의존
        self.scan_tool = scan_tool

# 사용
service = ScanService(scan_tool=NmapTool())  # NmapTool 주입
service = ScanService(scan_tool=MasscanTool())  # MasscanTool로 교체 가능
```

---

## 3. 에러 처리 전략

### 3.1 계층별 에러 처리

**원칙**:
- API 레이어: HTTP 상태 코드로 변환
- 서비스 레이어: 비즈니스 예외 발생
- 데이터 레이어: DB 예외 발생

```python
# app/services/langgraph_service.py
class ScanError(Exception):
    """스캔 관련 예외"""
    pass

class LangGraphService:
    def run_scan(self, target: str):
        if not self._validate_target(target):
            raise ScanError(f"Invalid target: {target}")

# app/api/v1/langgraph.py
from fastapi import HTTPException

@router.post("/scan")
async def start_scan(request: ScanRequest):
    try:
        service = LangGraphService()
        result = service.run_scan(request.target)
    except ScanError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

### 3.2 전역 예외 핸들러

```python
# app/core/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )

# app/main.py
from app.core.error_handler import global_exception_handler

app.add_exception_handler(Exception, global_exception_handler)
```

---

## 4. 비동기 처리 원칙

### 4.1 async/await 사용

```python
# FastAPI 엔드포인트는 async
@router.post("/scan")
async def start_scan(request: ScanRequest):
    # DB 접근은 동기이므로 asyncio.to_thread 사용
    result = await asyncio.to_thread(sync_function)
    return result

# LangGraph는 동기이므로 래핑
async def run_scan_async(target: str):
    result = await asyncio.to_thread(langgraph_service.run_scan, target)
    return result
```

---

### 4.2 BackgroundTasks vs Celery

**BackgroundTasks** (Phase 2-3):
- 간단한 비동기 작업
- 서버 재시작 시 작업 손실 가능
- 인프라 최소화

**Celery** (Phase 3 이후):
- 장시간 작업
- 작업 영속성 보장
- 분산 처리 가능

```python
# BackgroundTasks
@router.post("/scan")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scan, request.target)
    return {"message": "Scan started"}

# Celery
from app.tasks.scan_tasks import run_scan_task

@router.post("/scan")
async def start_scan(request: ScanRequest):
    run_scan_task.delay(request.target)
    return {"message": "Scan queued"}
```

---

## 5. 테스트 전략

### 5.1 테스트 피라미드

```
        /\
       /  \      E2E Tests (10%)
      /────\
     /      \    Integration Tests (30%)
    /────────\
   /          \  Unit Tests (60%)
  /────────────\
```

### 5.2 단위 테스트

```python
# backend/tests/test_langgraph.py

def test_analyze_input():
    """입력 분석 단위 테스트"""
    service = LangGraphService()
    state = {"target": "127.0.0.1", "scan_type": "quick"}

    result = service._analyze_input(state)

    assert result["port_range"] == "1-1000"
```

### 5.3 통합 테스트

```python
# backend/tests/test_api.py

def test_full_scan_flow(client):
    """전체 스캔 플로우 통합 테스트"""
    response = client.post("/api/v1/langgraph/scan", json={"target": "127.0.0.1"})
    assert response.status_code == 202

    session_id = response.json()["session_id"]

    response = client.get(f"/api/v1/langgraph/scan/{session_id}/result")
    assert response.status_code == 200
```

---

## 6. 로깅 전략

### 6.1 구조화된 로깅

```python
# app/core/logging.py

import logging
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id

        return json.dumps(log_data)
```

### 6.2 로그 레벨

- **DEBUG**: 상세한 디버깅 정보
- **INFO**: 정상 동작 정보 (스캔 시작/완료)
- **WARNING**: 예상치 못한 상황 (nmap 미설치)
- **ERROR**: 에러 발생 (스캔 실패)
- **CRITICAL**: 치명적 에러 (DB 연결 실패)

```python
logger.info(f"Scan started: {session_id}")
logger.warning("nmap not found, using simulation mode")
logger.error(f"Scan failed: {error}", exc_info=True)
```

---

## 7. 보안 원칙

### 7.1 입력 검증

```python
from pydantic import validator
import ipaddress

class ScanRequest(BaseModel):
    target: str

    @validator("target")
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("Invalid IP address")
        return v
```

### 7.2 화이트리스트

```python
# app/core/security_policy.py

ALLOWED_TARGETS = ["127.0.0.1", "localhost"]

def is_allowed_target(target: str) -> bool:
    """대상 IP가 허용되는지 확인"""
    if target in ALLOWED_TARGETS:
        return True

    # 사설 IP 대역 허용
    if target.startswith("192.168.") or target.startswith("10."):
        return True

    return False
```

---

## 8. 성능 최적화 원칙

### 8.1 DB 쿼리 최적화

```python
# N+1 문제 방지
# 나쁜 예
sessions = db.query(ScanSession).all()
for session in sessions:
    result = db.query(ScanResult).filter(ScanResult.session_id == session.id).first()

# 좋은 예 (Eager Loading)
sessions = db.query(ScanSession).options(joinedload(ScanSession.results)).all()
```

### 8.2 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cve_info(cve_id: str):
    """CVE 정보 캐싱"""
    # API 호출
    pass
```

---

## 요약

1. **레이어드 아키텍처**: 책임 분리
2. **SOLID 원칙**: 유지보수성 향상
3. **의존성 주입**: 테스트 용이성
4. **에러 처리**: 계층별 적절한 처리
5. **비동기 처리**: 성능 향상
6. **테스트**: 품질 보장
7. **로깅**: 문제 추적
8. **보안**: 입력 검증, 화이트리스트

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
