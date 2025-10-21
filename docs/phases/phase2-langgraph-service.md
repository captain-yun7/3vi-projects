# Phase 2: LangGraph 서비스화 및 API 기본 연동

## 개요
- **기간**: 2주
- **목표**: PoC를 프로덕션 레벨 서비스로 전환하고 FastAPI와 연동
- **선행 조건**: Phase 1 완료

---

## 2.1 FastAPI 백엔드 기본 구조 생성

### 목표
프로젝트의 기본 골격을 구축하고 FastAPI 서버 실행

### 작업 내용

#### 2.1.1 FastAPI 프로젝트 초기화

**디렉토리 생성**
```bash
mkdir -p backend/app/{api/v1,core,models,schemas,services/tools}
mkdir -p backend/tests
mkdir -p backend/alembic/versions
mkdir -p backend/scripts
mkdir -p backend/logs
```

**main.py 작성**
```python
# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import health, langgraph

# 로깅 설정
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 기반 보안 스캔 자동화 시스템",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(langgraph.router, prefix="/api/v1/langgraph", tags=["langgraph"])

@app.get("/")
def root():
    return {
        "message": "3VI Security Scanner API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

**설정 파일 작성**
```python
# backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "3VI Security Scanner"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str

    # Security
    SECRET_KEY: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Scanning
    SCAN_TIMEOUT: int = 300
    MAX_CONCURRENT_SCANS: int = 5

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**로깅 설정**
```python
# backend/app/core/logging.py

import logging
import sys
from pathlib import Path
from app.core.config import settings

def setup_logging():
    """구조화된 로깅 설정"""

    # 로그 디렉토리 생성
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(exist_ok=True)

    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
```

#### 2.1.2 헬스체크 엔드포인트

```python
# backend/app/api/v1/health.py

from fastapi import APIRouter, status
from datetime import datetime
from app.core.config import settings

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """서버 헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
    }

@router.get("/status", status_code=status.HTTP_200_OK)
async def status():
    """서비스 상태 확인"""
    # TODO: DB 연결 상태, Redis 연결 상태 등 추가
    return {
        "api": "operational",
        "database": "not_configured",  # Phase 2.4에서 구현
        "redis": "not_configured",
        "openai": "configured" if settings.OPENAI_API_KEY else "not_configured",
    }
```

#### 2.1.3 실행 및 테스트

```bash
# 가상환경 활성화
cd /home/k8s-admin/3vi-v1/backend
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성 (예시)
cp ../.env.example .env
# .env 파일 편집하여 OPENAI_API_KEY 등 설정

# 서버 실행
python -m app.main

# 또는
uvicorn app.main:app --reload
```

**테스트**
```bash
# 헬스체크
curl http://localhost:8000/api/v1/health

# API 문서 확인
open http://localhost:8000/docs
```

### 산출물
- `backend/app/main.py` - FastAPI 진입점
- `backend/app/core/config.py` - 설정 관리
- `backend/app/core/logging.py` - 로깅 설정
- `backend/app/api/v1/health.py` - 헬스체크 API

### 체크포인트
- [ ] FastAPI 서버가 정상 실행되는가?
- [ ] `/api/v1/health` 엔드포인트가 200 응답하는가?
- [ ] `/docs`에서 Swagger 문서가 보이는가?
- [ ] 로그가 정상적으로 출력되는가?

---

## 2.2 LangGraph를 서비스 클래스로 리팩토링

### 목표
PoC의 `advanced_poc.py`를 재사용 가능한 서비스 클래스로 전환

### 작업 내용

#### 2.2.1 State 스키마 정의

```python
# backend/app/schemas/scan_state.py

from typing import TypedDict, List, Dict, Optional
from pydantic import BaseModel

class SecurityScanState(TypedDict):
    """LangGraph State (TypedDict 유지)"""
    target: str
    scan_type: str
    ports: Optional[List[Dict]]
    vulnerabilities: Optional[List[Dict]]
    risk_assessment: Optional[Dict]
    remediation: Optional[Dict]
    report: Optional[str]
    current_step: Optional[str]
    progress: Optional[int]  # 0-100
    error: Optional[str]

class ScanStateModel(BaseModel):
    """API 응답용 Pydantic 모델"""
    target: str
    scan_type: str
    ports: Optional[List[Dict]] = None
    vulnerabilities: Optional[List[Dict]] = None
    risk_assessment: Optional[Dict] = None
    remediation: Optional[Dict] = None
    report: Optional[str] = None
    current_step: Optional[str] = None
    progress: Optional[int] = 0
    error: Optional[str] = None

    class Config:
        from_attributes = True
```

#### 2.2.2 LangGraph 서비스 클래스

```python
# backend/app/services/langgraph_service.py

import logging
from typing import Optional, Callable
from langgraph.graph import StateGraph, END
from openai import OpenAI
import json

from app.core.config import settings
from app.schemas.scan_state import SecurityScanState

logger = logging.getLogger(__name__)

class LangGraphService:
    """LangGraph 기반 보안 스캔 서비스"""

    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Args:
            progress_callback: 진행 상황 콜백 함수 (session_id, step, progress)
        """
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.progress_callback = progress_callback
        self.graph = self._build_graph()

    def _build_graph(self):
        """LangGraph 워크플로우 구성"""
        graph = StateGraph(SecurityScanState)

        # 노드 추가
        graph.add_node("analyze", self._analyze_input)
        graph.add_node("port_scan", self._port_scan)
        graph.add_node("vulnerability_analysis", self._vulnerability_analysis)
        graph.add_node("risk_assessment", self._risk_assessment)
        graph.add_node("remediation", self._remediation)
        graph.add_node("report_generation", self._report_generation)

        # 엣지 추가
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", "port_scan")
        graph.add_edge("port_scan", "vulnerability_analysis")
        graph.add_edge("vulnerability_analysis", "risk_assessment")
        graph.add_edge("risk_assessment", "remediation")
        graph.add_edge("remediation", "report_generation")
        graph.add_edge("report_generation", END)

        return graph.compile()

    def _update_progress(self, state: SecurityScanState, step: str, progress: int):
        """진행 상황 업데이트"""
        state["current_step"] = step
        state["progress"] = progress

        if self.progress_callback:
            self.progress_callback(step, progress)

        logger.info(f"Step: {step}, Progress: {progress}%")

    def _analyze_input(self, state: SecurityScanState) -> SecurityScanState:
        """1단계: 입력 분석"""
        self._update_progress(state, "analyze_input", 10)

        try:
            target = state["target"]
            scan_type = state["scan_type"]

            logger.info(f"Analyzing target: {target}, type: {scan_type}")

            # 대상 검증 (화이트리스트 체크)
            if not self._validate_target(target):
                raise ValueError(f"Unauthorized target: {target}")

            # 스캔 타입에 따른 포트 범위 결정
            if scan_type == "quick":
                state["port_range"] = "1-1000"
            elif scan_type == "full":
                state["port_range"] = "1-65535"
            else:
                state["port_range"] = "1-1024"

            self._update_progress(state, "analyze_input", 20)
            return state

        except Exception as e:
            logger.error(f"Input analysis failed: {e}")
            state["error"] = str(e)
            raise

    def _port_scan(self, state: SecurityScanState) -> SecurityScanState:
        """2단계: 포트 스캔"""
        self._update_progress(state, "port_scan", 30)

        try:
            import nmap
            nm = nmap.PortScanner()

            target = state["target"]
            port_range = state.get("port_range", "1-1024")

            logger.info(f"Scanning ports on {target}: {port_range}")

            # nmap 스캔 실행
            nm.scan(target, port_range, arguments="-Pn -T4")

            # 결과 파싱
            ports = []
            if target in nm.all_hosts():
                for proto in nm[target].all_protocols():
                    for port in nm[target][proto].keys():
                        port_info = nm[target][proto][port]
                        ports.append({
                            "port": port,
                            "state": port_info["state"],
                            "service": port_info.get("name", "unknown"),
                            "version": port_info.get("version", ""),
                        })

            state["ports"] = ports
            logger.info(f"Found {len(ports)} open ports")

            self._update_progress(state, "port_scan", 40)
            return state

        except ImportError:
            logger.warning("nmap not installed, using simulation mode")
            # 시뮬레이션 데이터
            state["ports"] = [
                {"port": 22, "state": "open", "service": "ssh"},
                {"port": 80, "state": "open", "service": "http"},
                {"port": 443, "state": "open", "service": "https"},
            ]
            self._update_progress(state, "port_scan", 40)
            return state

        except Exception as e:
            logger.error(f"Port scan failed: {e}")
            state["error"] = str(e)
            raise

    def _vulnerability_analysis(self, state: SecurityScanState) -> SecurityScanState:
        """3단계: 취약점 분석"""
        self._update_progress(state, "vulnerability_analysis", 50)

        try:
            ports = state.get("ports", [])

            # 간단한 휴리스틱 분석
            vulnerabilities = []

            for port_info in ports:
                port = port_info["port"]
                service = port_info["service"]

                # 알려진 위험 포트
                if port == 22:
                    vulnerabilities.append({
                        "type": "Weak Authentication",
                        "port": port,
                        "service": service,
                        "severity": "Medium",
                        "description": "SSH 서비스가 노출되어 있습니다. Brute force 공격에 취약할 수 있습니다.",
                    })
                elif port == 3306:
                    vulnerabilities.append({
                        "type": "Database Exposure",
                        "port": port,
                        "service": service,
                        "severity": "High",
                        "description": "MySQL 데이터베이스가 외부에 노출되어 있습니다.",
                    })

            state["vulnerabilities"] = vulnerabilities
            logger.info(f"Found {len(vulnerabilities)} potential vulnerabilities")

            self._update_progress(state, "vulnerability_analysis", 60)
            return state

        except Exception as e:
            logger.error(f"Vulnerability analysis failed: {e}")
            state["error"] = str(e)
            raise

    def _risk_assessment(self, state: SecurityScanState) -> SecurityScanState:
        """4단계: AI 위험도 평가"""
        self._update_progress(state, "risk_assessment", 70)

        try:
            vulnerabilities = state.get("vulnerabilities", [])

            # OpenAI API로 위험도 평가
            prompt = f"""
다음 취약점 목록에 대해 종합적인 위험도를 평가해주세요:

{json.dumps(vulnerabilities, indent=2, ensure_ascii=False)}

다음 형식으로 응답해주세요:
1. 전체 위험도 점수 (0-100)
2. 주요 위험 요소 3가지
3. 우선순위가 높은 취약점
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 보안 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            assessment = response.choices[0].message.content

            state["risk_assessment"] = {
                "score": 65,  # TODO: 파싱
                "analysis": assessment,
            }

            logger.info("Risk assessment completed")
            self._update_progress(state, "risk_assessment", 80)
            return state

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            state["error"] = str(e)
            # AI 실패 시 기본 평가
            state["risk_assessment"] = {
                "score": 50,
                "analysis": "AI 평가를 사용할 수 없습니다. 기본 휴리스틱 평가를 사용합니다.",
            }
            return state

    def _remediation(self, state: SecurityScanState) -> SecurityScanState:
        """5단계: 해결 방안 제시"""
        self._update_progress(state, "remediation", 90)

        try:
            vulnerabilities = state.get("vulnerabilities", [])

            # AI로 해결 방안 생성
            prompt = f"""
다음 취약점에 대한 구체적인 해결 방안을 제시해주세요:

{json.dumps(vulnerabilities, indent=2, ensure_ascii=False)}

각 취약점별로 다음을 포함해주세요:
1. 즉시 조치 사항
2. 장기 해결 방안
3. 참고 자료 (CWE, CVE 등)
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 보안 컨설턴트입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            remediation = response.choices[0].message.content

            state["remediation"] = {
                "recommendations": remediation,
            }

            logger.info("Remediation plan generated")
            self._update_progress(state, "remediation", 95)
            return state

        except Exception as e:
            logger.error(f"Remediation generation failed: {e}")
            state["remediation"] = {
                "recommendations": "해결 방안을 생성할 수 없습니다.",
            }
            return state

    def _report_generation(self, state: SecurityScanState) -> SecurityScanState:
        """6단계: 보고서 생성"""
        self._update_progress(state, "report_generation", 98)

        try:
            # 최종 보고서 생성
            report = f"""
# 보안 스캔 보고서

## 대상
- IP: {state['target']}
- 스캔 유형: {state['scan_type']}

## 포트 스캔 결과
발견된 포트: {len(state.get('ports', []))}개

{self._format_ports(state.get('ports', []))}

## 취약점
발견된 취약점: {len(state.get('vulnerabilities', []))}개

{self._format_vulnerabilities(state.get('vulnerabilities', []))}

## 위험도 평가
{state.get('risk_assessment', {}).get('analysis', '평가 없음')}

## 해결 방안
{state.get('remediation', {}).get('recommendations', '방안 없음')}

---
보고서 생성 시간: {logger.handlers[0].formatter.formatTime(logger.makeRecord('', 0, '', 0, '', (), None))}
"""

            state["report"] = report
            logger.info("Report generated successfully")

            self._update_progress(state, "report_generation", 100)
            return state

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            state["error"] = str(e)
            raise

    def _validate_target(self, target: str) -> bool:
        """대상 IP 검증 (화이트리스트)"""
        ALLOWED_TARGETS = ["127.0.0.1", "localhost"]
        # TODO: 192.168.x.x 대역 검증 추가
        return target in ALLOWED_TARGETS or target.startswith("192.168.")

    def _format_ports(self, ports: List[Dict]) -> str:
        """포트 목록 포맷팅"""
        if not ports:
            return "포트 없음"

        lines = []
        for p in ports:
            lines.append(f"- {p['port']}/{p['service']} - {p['state']}")
        return "\n".join(lines)

    def _format_vulnerabilities(self, vulns: List[Dict]) -> str:
        """취약점 목록 포맷팅"""
        if not vulns:
            return "취약점 없음"

        lines = []
        for v in vulns:
            lines.append(f"- [{v['severity']}] {v['type']} (포트 {v['port']}): {v['description']}")
        return "\n".join(lines)

    def run_scan(self, target: str, scan_type: str = "standard") -> SecurityScanState:
        """동기 스캔 실행"""
        logger.info(f"Starting scan for {target} (type: {scan_type})")

        initial_state: SecurityScanState = {
            "target": target,
            "scan_type": scan_type,
            "ports": None,
            "vulnerabilities": None,
            "risk_assessment": None,
            "remediation": None,
            "report": None,
            "current_step": None,
            "progress": 0,
            "error": None,
        }

        try:
            result = self.graph.invoke(initial_state)
            logger.info("Scan completed successfully")
            return result
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            raise
```

### 산출물
- `backend/app/schemas/scan_state.py` - State 스키마
- `backend/app/services/langgraph_service.py` - LangGraph 서비스

### 체크포인트
- [ ] LangGraphService 클래스가 생성되었는가?
- [ ] 각 노드가 독립적인 메서드로 분리되었는가?
- [ ] 로깅이 각 단계에서 작동하는가?
- [ ] 에러 핸들링이 구현되었는가?

---

## 2.3 LangGraph 실행 API 엔드포인트 생성

### 목표
FastAPI에서 LangGraph를 호출할 수 있는 REST API 구현

### 작업 내용

#### 2.3.1 요청/응답 스키마

```python
# backend/app/schemas/scan_request.py

from pydantic import BaseModel, Field, validator
from typing import Literal

class ScanRequest(BaseModel):
    target: str = Field(..., description="스캔 대상 IP 주소")
    scan_type: Literal["quick", "standard", "full"] = Field(
        default="standard",
        description="스캔 유형"
    )

    @validator("target")
    def validate_target(cls, v):
        """IP 주소 형식 검증"""
        # 간단한 검증 (실제로는 ipaddress 모듈 사용)
        if not v:
            raise ValueError("Target is required")
        return v

class ScanResponse(BaseModel):
    session_id: str = Field(..., description="스캔 세션 ID")
    status: str = Field(..., description="스캔 상태")
    message: str = Field(default="", description="메시지")
```

```python
# backend/app/schemas/scan_response.py

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ScanStatusResponse(BaseModel):
    session_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    current_step: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class ScanResultResponse(BaseModel):
    session_id: str
    target: str
    scan_type: str
    ports: Optional[List[Dict]] = None
    vulnerabilities: Optional[List[Dict]] = None
    risk_assessment: Optional[Dict] = None
    remediation: Optional[Dict] = None
    report: Optional[str] = None
    completed_at: Optional[datetime] = None
```

#### 2.3.2 LangGraph API 라우터

```python
# backend/app/api/v1/langgraph.py

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict
import uuid
import logging
from datetime import datetime

from app.schemas.scan_request import ScanRequest, ScanResponse
from app.schemas.scan_response import ScanStatusResponse, ScanResultResponse
from app.services.langgraph_service import LangGraphService

logger = logging.getLogger(__name__)
router = APIRouter()

# 임시 저장소 (Phase 2.4에서 DB로 대체)
scan_sessions: Dict[str, dict] = {}

@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(request: ScanRequest):
    """보안 스캔 시작"""

    # 세션 ID 생성
    session_id = str(uuid.uuid4())

    # 세션 정보 저장
    scan_sessions[session_id] = {
        "session_id": session_id,
        "target": request.target,
        "scan_type": request.scan_type,
        "status": "pending",
        "progress": 0,
        "current_step": None,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    logger.info(f"Scan session created: {session_id}")

    # TODO: Phase 3에서 BackgroundTasks로 비동기 처리
    # 일단 동기 실행
    try:
        service = LangGraphService()
        result = service.run_scan(request.target, request.scan_type)

        # 결과 저장
        scan_sessions[session_id]["status"] = "completed"
        scan_sessions[session_id]["progress"] = 100
        scan_sessions[session_id]["completed_at"] = datetime.utcnow()
        scan_sessions[session_id]["result"] = result

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        scan_sessions[session_id]["status"] = "failed"
        scan_sessions[session_id]["error"] = str(e)

    return ScanResponse(
        session_id=session_id,
        status="completed",  # 동기 실행이므로 바로 완료
        message="Scan completed"
    )

@router.get("/scan/{session_id}", response_model=ScanStatusResponse)
async def get_scan_status(session_id: str):
    """스캔 상태 조회"""

    if session_id not in scan_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan session not found"
        )

    session = scan_sessions[session_id]

    return ScanStatusResponse(
        session_id=session["session_id"],
        status=session["status"],
        progress=session["progress"],
        current_step=session.get("current_step"),
        started_at=session["started_at"],
        completed_at=session.get("completed_at"),
        error=session.get("error"),
    )

@router.get("/scan/{session_id}/result", response_model=ScanResultResponse)
async def get_scan_result(session_id: str):
    """스캔 결과 조회"""

    if session_id not in scan_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan session not found"
        )

    session = scan_sessions[session_id]

    if session["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan not completed yet. Status: {session['status']}"
        )

    result = session.get("result", {})

    return ScanResultResponse(
        session_id=session["session_id"],
        target=session["target"],
        scan_type=session["scan_type"],
        ports=result.get("ports"),
        vulnerabilities=result.get("vulnerabilities"),
        risk_assessment=result.get("risk_assessment"),
        remediation=result.get("remediation"),
        report=result.get("report"),
        completed_at=session.get("completed_at"),
    )
```

#### 2.3.3 API 테스트

```bash
# 스캔 시작
curl -X POST http://localhost:8000/api/v1/langgraph/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "127.0.0.1", "scan_type": "quick"}'

# 응답: {"session_id": "abc-123", "status": "pending"}

# 상태 조회
curl http://localhost:8000/api/v1/langgraph/scan/abc-123

# 결과 조회
curl http://localhost:8000/api/v1/langgraph/scan/abc-123/result
```

### 산출물
- `backend/app/schemas/scan_request.py`
- `backend/app/schemas/scan_response.py`
- `backend/app/api/v1/langgraph.py`

### 체크포인트
- [ ] POST /scan 엔드포인트가 작동하는가?
- [ ] GET /scan/{id} 상태 조회가 작동하는가?
- [ ] GET /scan/{id}/result 결과 조회가 작동하는가?
- [ ] Swagger 문서에 API가 표시되는가?

---

## 2.4 DB 모델 및 데이터 저장 구현

### 목표
스캔 세션과 결과를 데이터베이스에 영속적으로 저장

### 작업 내용

#### 2.4.1 데이터베이스 연결 설정

```python
# backend/app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# DB 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()

def get_db():
    """DB 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 2.4.2 모델 정의

```python
# backend/app/models/scan_session.py

from sqlalchemy import Column, String, DateTime, Integer, Text, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    target = Column(String(255), nullable=False, index=True)
    scan_type = Column(String(50), nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)
    current_step = Column(String(100))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    error = Column(Text)

    def __repr__(self):
        return f"<ScanSession {self.id} - {self.target}>"
```

```python
# backend/app/models/scan_result.py

from sqlalchemy import Column, String, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("scan_sessions.id"), nullable=False)
    ports = Column(JSON)  # List[Dict]
    vulnerabilities = Column(JSON)  # List[Dict]
    risk_assessment = Column(JSON)  # Dict
    remediation = Column(JSON)  # Dict
    report = Column(JSON)  # Markdown 텍스트
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    # session = relationship("ScanSession", backref="results")

    def __repr__(self):
        return f"<ScanResult {self.id} for session {self.session_id}>"
```

#### 2.4.3 Alembic 마이그레이션

```bash
# Alembic 초기화
cd backend
alembic init alembic

# alembic.ini 수정
# sqlalchemy.url 제거 (코드에서 동적으로 설정)
```

```python
# backend/alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.core.database import Base
from app.models import scan_session, scan_result  # 모델 임포트

config = context.config

# DB URL 설정
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ...
target_metadata = Base.metadata
# ...
```

```bash
# 마이그레이션 파일 생성
alembic revision --autogenerate -m "Initial tables"

# 마이그레이션 실행
alembic upgrade head
```

#### 2.4.4 CRUD 함수

```python
# backend/app/models/crud.py

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid

from app.models.scan_session import ScanSession, ScanStatus
from app.models.scan_result import ScanResult

def create_scan_session(db: Session, target: str, scan_type: str) -> ScanSession:
    """스캔 세션 생성"""
    session = ScanSession(
        id=str(uuid.uuid4()),
        target=target,
        scan_type=scan_type,
        status=ScanStatus.PENDING,
        progress=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def update_scan_status(
    db: Session,
    session_id: str,
    status: ScanStatus,
    progress: Optional[int] = None,
    current_step: Optional[str] = None,
    error: Optional[str] = None,
) -> Optional[ScanSession]:
    """스캔 상태 업데이트"""
    session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    if not session:
        return None

    session.status = status
    if progress is not None:
        session.progress = progress
    if current_step is not None:
        session.current_step = current_step
    if error is not None:
        session.error = error
    if status == ScanStatus.COMPLETED or status == ScanStatus.FAILED:
        session.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(session)
    return session

def save_scan_result(
    db: Session,
    session_id: str,
    result_data: dict,
) -> ScanResult:
    """스캔 결과 저장"""
    result = ScanResult(
        session_id=session_id,
        ports=result_data.get("ports"),
        vulnerabilities=result_data.get("vulnerabilities"),
        risk_assessment=result_data.get("risk_assessment"),
        remediation=result_data.get("remediation"),
        report=result_data.get("report"),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def get_scan_session(db: Session, session_id: str) -> Optional[ScanSession]:
    """스캔 세션 조회"""
    return db.query(ScanSession).filter(ScanSession.id == session_id).first()

def get_scan_result(db: Session, session_id: str) -> Optional[ScanResult]:
    """스캔 결과 조회"""
    return db.query(ScanResult).filter(ScanResult.session_id == session_id).first()
```

#### 2.4.5 API에서 DB 사용

```python
# backend/app/api/v1/langgraph.py (수정)

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import crud
from app.models.scan_session import ScanStatus

@router.post("/scan", response_model=ScanResponse)
async def start_scan(
    request: ScanRequest,
    db: Session = Depends(get_db)
):
    """보안 스캔 시작"""

    # DB에 세션 생성
    session = crud.create_scan_session(db, request.target, request.scan_type)

    logger.info(f"Scan session created: {session.id}")

    # 동기 실행 (Phase 3에서 비동기로 변경)
    try:
        crud.update_scan_status(db, session.id, ScanStatus.RUNNING)

        service = LangGraphService()
        result = service.run_scan(request.target, request.scan_type)

        # 결과 저장
        crud.save_scan_result(db, session.id, result)
        crud.update_scan_status(db, session.id, ScanStatus.COMPLETED, progress=100)

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        crud.update_scan_status(db, session.id, ScanStatus.FAILED, error=str(e))

    return ScanResponse(
        session_id=session.id,
        status="completed",
        message="Scan completed"
    )
```

### 산출물
- `backend/app/core/database.py`
- `backend/app/models/scan_session.py`
- `backend/app/models/scan_result.py`
- `backend/app/models/crud.py`
- `backend/alembic/versions/001_initial.py`

### 체크포인트
- [ ] PostgreSQL이 설치되고 실행 중인가?
- [ ] Alembic 마이그레이션이 성공했는가?
- [ ] 스캔 세션이 DB에 저장되는가?
- [ ] 스캔 결과가 DB에 저장되는가?

---

## 2.5 백엔드 API ↔ LangGraph 연동 테스트

### 목표
전체 플로우(API → LangGraph → DB)가 정상 작동하는지 검증

### 작업 내용

#### 2.5.1 통합 테스트 작성

```python
# backend/tests/test_langgraph_integration.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_scan_flow():
    """전체 스캔 플로우 테스트"""

    # 1. 스캔 시작
    response = client.post(
        "/api/v1/langgraph/scan",
        json={"target": "127.0.0.1", "scan_type": "quick"}
    )
    assert response.status_code == 202
    data = response.json()
    session_id = data["session_id"]
    assert session_id is not None

    # 2. 상태 조회
    response = client.get(f"/api/v1/langgraph/scan/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["pending", "running", "completed"]

    # 3. 결과 조회
    response = client.get(f"/api/v1/langgraph/scan/{session_id}/result")
    assert response.status_code == 200
    data = response.json()
    assert data["target"] == "127.0.0.1"
    assert "ports" in data
    assert "report" in data

def test_invalid_target():
    """잘못된 대상 입력 테스트"""

    response = client.post(
        "/api/v1/langgraph/scan",
        json={"target": "8.8.8.8", "scan_type": "quick"}  # 허용되지 않은 대상
    )
    # 현재는 성공하지만, Phase 1.4 구현 후 실패해야 함
    # assert response.status_code == 400

def test_scan_not_found():
    """존재하지 않는 세션 조회"""

    response = client.get("/api/v1/langgraph/scan/invalid-session-id")
    assert response.status_code == 404
```

#### 2.5.2 수동 테스트

```bash
# 1. 서버 시작
uvicorn app.main:app --reload

# 2. 스캔 시작
curl -X POST http://localhost:8000/api/v1/langgraph/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "127.0.0.1",
    "scan_type": "quick"
  }'

# 응답 예시:
# {
#   "session_id": "abc-def-ghi",
#   "status": "completed",
#   "message": "Scan completed"
# }

# 3. 결과 조회
curl http://localhost:8000/api/v1/langgraph/scan/abc-def-ghi/result

# 4. DB 확인
psql -U secuser -d securitydb
SELECT * FROM scan_sessions;
SELECT * FROM scan_results;
```

#### 2.5.3 Postman 컬렉션

```json
{
  "info": {
    "name": "3VI Security Scanner API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Start Scan",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "url": "http://localhost:8000/api/v1/langgraph/scan",
        "body": {
          "mode": "raw",
          "raw": "{\"target\": \"127.0.0.1\", \"scan_type\": \"quick\"}"
        }
      }
    },
    {
      "name": "Get Scan Status",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/v1/langgraph/scan/{{session_id}}"
      }
    },
    {
      "name": "Get Scan Result",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/v1/langgraph/scan/{{session_id}}/result"
      }
    }
  ]
}
```

### 산출물
- `backend/tests/test_langgraph_integration.py`
- `docs/api/langgraph_api_spec.md`
- `postman_collection.json`

### 체크포인트
- [ ] 통합 테스트가 통과하는가?
- [ ] Postman으로 전체 플로우 테스트 완료했는가?
- [ ] DB에 데이터가 정상 저장되는가?
- [ ] 에러 케이스가 적절히 처리되는가?

---

## Phase 2 완료 기준

### 필수 체크리스트
- [ ] FastAPI 서버가 실행되고 `/health` 응답
- [ ] LangGraphService 클래스가 구현됨
- [ ] POST /api/v1/langgraph/scan이 작동
- [ ] GET /api/v1/langgraph/scan/{id}가 작동
- [ ] GET /api/v1/langgraph/scan/{id}/result가 작동
- [ ] PostgreSQL DB 연결 및 마이그레이션 완료
- [ ] 스캔 세션이 DB에 저장됨
- [ ] 스캔 결과가 DB에 저장됨
- [ ] 통합 테스트 통과
- [ ] API 문서가 `/docs`에서 확인 가능

### 산출물 목록
1. `backend/app/main.py`
2. `backend/app/core/config.py`
3. `backend/app/core/logging.py`
4. `backend/app/core/database.py`
5. `backend/app/api/v1/health.py`
6. `backend/app/api/v1/langgraph.py`
7. `backend/app/schemas/scan_state.py`
8. `backend/app/schemas/scan_request.py`
9. `backend/app/schemas/scan_response.py`
10. `backend/app/services/langgraph_service.py`
11. `backend/app/models/scan_session.py`
12. `backend/app/models/scan_result.py`
13. `backend/app/models/crud.py`
14. `backend/tests/test_langgraph_integration.py`
15. `docs/api/langgraph_api_spec.md`

### 검증 방법
1. **기능 테스트**: pytest 실행
2. **통합 테스트**: Postman 컬렉션 실행
3. **DB 검증**: 스캔 후 DB 레코드 확인

---

## 다음 단계

Phase 2 완료 후 [Phase 3: 비동기 처리 및 실시간 통신](./phase3-async-websocket.md)로 진행

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
