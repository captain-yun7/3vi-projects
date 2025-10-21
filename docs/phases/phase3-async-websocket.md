# Phase 3: 비동기 처리 및 실시간 통신

## 개요
- **기간**: 2주
- **목표**: 장시간 스캔을 비동기로 처리하고 WebSocket으로 실시간 진행 상황 전송
- **선행 조건**: Phase 2 완료

---

## 3.1 비동기 스캔 실행 구현

### 목표
스캔 요청 즉시 응답하고 백그라운드에서 스캔 실행

### 작업 내용

#### 3.1.1 비동기 처리 방식 선택

**Week 1: FastAPI BackgroundTasks 사용**
- 빠른 프로토타입
- 인프라 최소화

**Week 2: Celery 도입 검토**
- 프로덕션 환경 대비
- 작업 영속성 보장

#### 3.1.2 BackgroundTasks 구현

```python
# backend/app/services/async_scan_service.py

import logging
from typing import Optional, Callable
from sqlalchemy.orm import Session

from app.services.langgraph_service import LangGraphService
from app.models import crud
from app.models.scan_session import ScanStatus

logger = logging.getLogger(__name__)

class AsyncScanService:
    """비동기 스캔 서비스"""

    def __init__(
        self,
        db: Session,
        session_id: str,
        target: str,
        scan_type: str,
        progress_callback: Optional[Callable] = None,
    ):
        self.db = db
        self.session_id = session_id
        self.target = target
        self.scan_type = scan_type
        self.progress_callback = progress_callback

    def run(self):
        """백그라운드에서 스캔 실행"""
        logger.info(f"Starting background scan for session {self.session_id}")

        try:
            # 상태를 RUNNING으로 변경
            crud.update_scan_status(
                self.db,
                self.session_id,
                ScanStatus.RUNNING,
                progress=0,
            )

            # LangGraph 서비스 실행 (진행 상황 콜백 전달)
            service = LangGraphService(progress_callback=self._on_progress)
            result = service.run_scan(self.target, self.scan_type)

            # 결과 저장
            crud.save_scan_result(self.db, self.session_id, result)
            crud.update_scan_status(
                self.db,
                self.session_id,
                ScanStatus.COMPLETED,
                progress=100,
            )

            logger.info(f"Scan completed for session {self.session_id}")

        except Exception as e:
            logger.error(f"Scan failed for session {self.session_id}: {e}")
            crud.update_scan_status(
                self.db,
                self.session_id,
                ScanStatus.FAILED,
                error=str(e),
            )

    def _on_progress(self, step: str, progress: int):
        """진행 상황 콜백"""
        logger.info(f"Session {self.session_id}: {step} - {progress}%")

        # DB 업데이트
        crud.update_scan_status(
            self.db,
            self.session_id,
            ScanStatus.RUNNING,
            progress=progress,
            current_step=step,
        )

        # WebSocket 콜백 (Phase 3.2에서 구현)
        if self.progress_callback:
            self.progress_callback(self.session_id, step, progress)
```

#### 3.1.3 API 엔드포인트 수정

```python
# backend/app/api/v1/langgraph.py (수정)

from fastapi import BackgroundTasks

@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """보안 스캔 시작 (비동기)"""

    # DB에 세션 생성
    session = crud.create_scan_session(db, request.target, request.scan_type)

    logger.info(f"Scan session created: {session.id}")

    # 백그라운드 태스크 추가
    async_service = AsyncScanService(
        db=db,
        session_id=session.id,
        target=request.target,
        scan_type=request.scan_type,
    )
    background_tasks.add_task(async_service.run)

    return ScanResponse(
        session_id=session.id,
        status="pending",
        message="Scan started in background"
    )
```

### 산출물
- `backend/app/services/async_scan_service.py`
- `backend/app/api/v1/langgraph.py` (수정)

### 체크포인트
- [ ] 스캔 요청 즉시 응답 (202 Accepted)
- [ ] 백그라운드에서 스캔 실행 확인
- [ ] DB에 진행 상황 업데이트 확인
- [ ] 여러 스캔 동시 실행 가능

---

## 3.2 WebSocket 실시간 진행 상황 전송

### 목표
클라이언트가 WebSocket으로 스캔 진행 상황을 실시간으로 수신

### 작업 내용

#### 3.2.1 WebSocket ConnectionManager

```python
# backend/app/core/websocket_manager.py

from typing import Dict, Set
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # session_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """클라이언트 연결"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        logger.info(f"Client connected to session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        """클라이언트 연결 해제"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # 연결이 없으면 세션 제거
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.info(f"Client disconnected from session {session_id}")

    async def send_progress(
        self,
        session_id: str,
        step: str,
        status: str,
        progress: int,
        message: str = "",
    ):
        """특정 세션의 모든 클라이언트에게 진행 상황 전송"""

        if session_id not in self.active_connections:
            logger.debug(f"No active connections for session {session_id}")
            return

        payload = {
            "session_id": session_id,
            "step": step,
            "status": status,
            "progress": progress,
            "message": message,
        }

        # 연결된 모든 클라이언트에게 전송
        disconnected = set()
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_json(payload)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.add(websocket)

        # 연결 실패한 클라이언트 제거
        for ws in disconnected:
            self.disconnect(ws, session_id)

    async def send_error(self, session_id: str, error: str):
        """에러 메시지 전송"""
        await self.send_progress(
            session_id=session_id,
            step="error",
            status="failed",
            progress=0,
            message=error,
        )

    async def send_completion(self, session_id: str):
        """완료 메시지 전송"""
        await self.send_progress(
            session_id=session_id,
            step="completed",
            status="completed",
            progress=100,
            message="Scan completed successfully",
        )

# 전역 ConnectionManager 인스턴스
manager = ConnectionManager()
```

#### 3.2.2 WebSocket 엔드포인트

```python
# backend/app/api/v1/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import logging

from app.core.websocket_manager import manager
from app.core.database import get_db
from app.models import crud

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/scan/{session_id}")
async def websocket_scan_progress(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db),
):
    """스캔 진행 상황 WebSocket"""

    # 세션 존재 확인
    scan_session = crud.get_scan_session(db, session_id)
    if not scan_session:
        await websocket.close(code=1008, reason="Session not found")
        return

    # 연결 수락
    await manager.connect(websocket, session_id)

    try:
        # 현재 상태 전송
        await manager.send_progress(
            session_id=session_id,
            step=scan_session.current_step or "pending",
            status=scan_session.status.value,
            progress=scan_session.progress,
            message=f"Connected to session {session_id}",
        )

        # 클라이언트 메시지 수신 (keep-alive)
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")

            # ping-pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        manager.disconnect(websocket, session_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)
```

```python
# backend/app/main.py (라우터 추가)

from app.api.v1 import websocket

app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])
```

#### 3.2.3 AsyncScanService에서 WebSocket 사용

```python
# backend/app/services/async_scan_service.py (수정)

from app.core.websocket_manager import manager

class AsyncScanService:
    def __init__(self, ...):
        # ...
        self.websocket_enabled = True  # WebSocket 사용 여부

    async def run(self):
        """비동기 스캔 실행 (async로 변경)"""
        logger.info(f"Starting background scan for session {self.session_id}")

        try:
            crud.update_scan_status(...)

            # WebSocket: 시작 알림
            if self.websocket_enabled:
                await manager.send_progress(
                    self.session_id,
                    step="started",
                    status="running",
                    progress=0,
                    message="Scan started",
                )

            # LangGraph 실행
            service = LangGraphService(progress_callback=self._on_progress)
            result = service.run_scan(self.target, self.scan_type)

            # 결과 저장
            crud.save_scan_result(self.db, self.session_id, result)
            crud.update_scan_status(...)

            # WebSocket: 완료 알림
            if self.websocket_enabled:
                await manager.send_completion(self.session_id)

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            crud.update_scan_status(...)

            # WebSocket: 에러 알림
            if self.websocket_enabled:
                await manager.send_error(self.session_id, str(e))

    async def _on_progress(self, step: str, progress: int):
        """진행 상황 콜백"""
        crud.update_scan_status(...)

        # WebSocket: 진행 상황 전송
        if self.websocket_enabled:
            await manager.send_progress(
                self.session_id,
                step=step,
                status="running",
                progress=progress,
                message=f"Processing: {step}",
            )
```

**문제: BackgroundTasks는 동기 함수만 지원**

해결 방법:
1. `asyncio.create_task()` 사용
2. Celery로 전환 (Week 2)

```python
# backend/app/api/v1/langgraph.py (수정)

import asyncio

@router.post("/scan", ...)
async def start_scan(...):
    # ...

    # asyncio.create_task로 비동기 태스크 실행
    asyncio.create_task(
        async_service.run()
    )

    return ScanResponse(...)
```

### 산출물
- `backend/app/core/websocket_manager.py`
- `backend/app/api/v1/websocket.py`
- `backend/app/services/async_scan_service.py` (수정)

### 체크포인트
- [ ] WebSocket 연결 성공
- [ ] 스캔 시작 시 WebSocket 메시지 수신
- [ ] 각 단계마다 진행 상황 수신
- [ ] 완료 시 100% 메시지 수신
- [ ] 에러 발생 시 에러 메시지 수신

---

## 3.3 LangGraph 노드에서 WebSocket 이벤트 발생

### 목표
LangGraph의 각 노드에서 WebSocket으로 실시간 이벤트 전송

### 작업 내용

#### 3.3.1 LangGraphService 수정

```python
# backend/app/services/langgraph_service.py (수정)

from typing import Optional, Callable, Awaitable

class LangGraphService:
    def __init__(self, progress_callback: Optional[Callable[[str, int], Awaitable]] = None):
        """
        Args:
            progress_callback: async 진행 상황 콜백 (step, progress)
        """
        self.progress_callback = progress_callback
        # ...

    async def _update_progress(self, state: SecurityScanState, step: str, progress: int):
        """진행 상황 업데이트 (async)"""
        state["current_step"] = step
        state["progress"] = progress

        if self.progress_callback:
            await self.progress_callback(step, progress)

        logger.info(f"Step: {step}, Progress: {progress}%")

    async def _analyze_input(self, state: SecurityScanState) -> SecurityScanState:
        """1단계: 입력 분석 (async로 변경)"""
        await self._update_progress(state, "analyze_input", 10)

        try:
            # 기존 로직
            # ...

            await self._update_progress(state, "analyze_input", 20)
            return state

        except Exception as e:
            # ...

    # 다른 노드들도 async로 변경
    async def _port_scan(self, state: SecurityScanState) -> SecurityScanState:
        await self._update_progress(state, "port_scan", 30)
        # ...
        await self._update_progress(state, "port_scan", 40)
        return state

    # ...

    async def run_scan_async(self, target: str, scan_type: str) -> SecurityScanState:
        """비동기 스캔 실행"""
        logger.info(f"Starting async scan for {target}")

        initial_state: SecurityScanState = {
            "target": target,
            "scan_type": scan_type,
            # ...
        }

        try:
            # LangGraph는 동기이므로 asyncio.to_thread 사용
            result = await asyncio.to_thread(self.graph.invoke, initial_state)
            logger.info("Scan completed successfully")
            return result
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            raise
```

**주의**: LangGraph 자체는 동기 실행이므로 `asyncio.to_thread()`로 래핑

### 산출물
- `backend/app/services/langgraph_service.py` (async 변환)

### 체크포인트
- [ ] 각 노드 시작 시 WebSocket 메시지 전송
- [ ] 각 노드 완료 시 WebSocket 메시지 전송
- [ ] 진행률이 정확히 계산되는가?

---

## 3.4 WebSocket 테스트

### 목표
WebSocket 통신이 정상 작동하는지 검증

### 작업 내용

#### 3.4.1 Python WebSocket 클라이언트 테스트

```python
# backend/scripts/test_websocket_client.py

import asyncio
import websockets
import json
import requests

async def test_websocket_scan():
    """WebSocket 스캔 테스트"""

    # 1. 스캔 시작
    response = requests.post(
        "http://localhost:8000/api/v1/langgraph/scan",
        json={"target": "127.0.0.1", "scan_type": "quick"}
    )
    data = response.json()
    session_id = data["session_id"]
    print(f"Scan started: {session_id}")

    # 2. WebSocket 연결
    uri = f"ws://localhost:8000/api/v1/ws/scan/{session_id}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")

        # 3. 진행 상황 수신
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                print(f"[{data['progress']}%] {data['step']}: {data['message']}")

                # 완료 확인
                if data['status'] == 'completed':
                    print("Scan completed!")
                    break

                # 에러 확인
                if data['status'] == 'failed':
                    print(f"Scan failed: {data['message']}")
                    break

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

if __name__ == "__main__":
    asyncio.run(test_websocket_scan())
```

**실행**:
```bash
python backend/scripts/test_websocket_client.py
```

#### 3.4.2 pytest로 WebSocket 테스트

```python
# backend/tests/test_websocket.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket():
    """WebSocket 통합 테스트"""
    client = TestClient(app)

    # 1. 스캔 시작
    response = client.post(
        "/api/v1/langgraph/scan",
        json={"target": "127.0.0.1", "scan_type": "quick"}
    )
    session_id = response.json()["session_id"]

    # 2. WebSocket 연결
    with client.websocket_connect(f"/api/v1/ws/scan/{session_id}") as websocket:
        # 3. 첫 메시지 수신
        data = websocket.receive_json()
        assert data["session_id"] == session_id

        # 4. ping-pong 테스트
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"
```

#### 3.4.3 브라우저 JavaScript 테스트

```html
<!-- test_websocket.html -->
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
</head>
<body>
    <h1>Security Scan WebSocket Test</h1>
    <button onclick="startScan()">Start Scan</button>
    <div id="progress"></div>
    <div id="logs"></div>

    <script>
        let ws = null;

        async function startScan() {
            // 1. 스캔 시작
            const response = await fetch('http://localhost:8000/api/v1/langgraph/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({target: '127.0.0.1', scan_type: 'quick'})
            });
            const data = await response.json();
            const sessionId = data.session_id;

            console.log('Scan started:', sessionId);

            // 2. WebSocket 연결
            ws = new WebSocket(`ws://localhost:8000/api/v1/ws/scan/${sessionId}`);

            ws.onopen = () => {
                console.log('WebSocket connected');
                addLog('Connected');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Progress:', data);

                updateProgress(data.progress);
                addLog(`[${data.progress}%] ${data.step}: ${data.message}`);

                if (data.status === 'completed' || data.status === 'failed') {
                    ws.close();
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                addLog('Error: ' + error);
            };

            ws.onclose = () => {
                console.log('WebSocket closed');
                addLog('Disconnected');
            };
        }

        function updateProgress(progress) {
            document.getElementById('progress').innerHTML =
                `<progress value="${progress}" max="100"></progress> ${progress}%`;
        }

        function addLog(message) {
            const logs = document.getElementById('logs');
            logs.innerHTML += `<p>${new Date().toLocaleTimeString()}: ${message}</p>`;
        }
    </script>
</body>
</html>
```

### 산출물
- `backend/scripts/test_websocket_client.py`
- `backend/tests/test_websocket.py`
- `test_websocket.html`

### 체크포인트
- [ ] Python 클라이언트로 WebSocket 메시지 수신 확인
- [ ] pytest 테스트 통과
- [ ] 브라우저에서 실시간 진행 상황 확인
- [ ] 여러 클라이언트 동시 연결 테스트

---

## 3.5 Celery 도입 (선택, Week 2)

### 목표
프로덕션 환경을 위한 작업 큐 구현

### 작업 내용

#### 3.5.1 Celery 설정

```python
# backend/celery_app.py

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "security_scanner",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
```

#### 3.5.2 Celery 태스크

```python
# backend/app/tasks/scan_tasks.py

from celery import Task
from celery_app import celery_app
from app.core.database import SessionLocal
from app.services.async_scan_service import AsyncScanService
import asyncio

class ScanTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """태스크 실패 시 처리"""
        print(f"Task {task_id} failed: {exc}")

@celery_app.task(base=ScanTask, bind=True)
def run_scan_task(self, session_id: str, target: str, scan_type: str):
    """Celery 스캔 태스크"""
    db = SessionLocal()

    try:
        service = AsyncScanService(
            db=db,
            session_id=session_id,
            target=target,
            scan_type=scan_type,
        )

        # async run을 동기로 실행
        asyncio.run(service.run())

    finally:
        db.close()
```

#### 3.5.3 API에서 Celery 사용

```python
# backend/app/api/v1/langgraph.py (Celery 버전)

from app.tasks.scan_tasks import run_scan_task

@router.post("/scan", ...)
async def start_scan(request: ScanRequest, db: Session = Depends(get_db)):
    session = crud.create_scan_session(...)

    # Celery 태스크 실행
    run_scan_task.delay(session.id, request.target, request.scan_type)

    return ScanResponse(
        session_id=session.id,
        status="pending",
        message="Scan queued"
    )
```

#### 3.5.4 Celery Worker 실행

```bash
# Redis 시작
redis-server

# Celery Worker 시작
celery -A celery_app worker --loglevel=info

# Celery Flower (모니터링)
celery -A celery_app flower
```

### 산출물
- `backend/celery_app.py`
- `backend/app/tasks/scan_tasks.py`
- `docker-compose.yml` (Redis, Celery worker 추가)

### 체크포인트
- [ ] Celery worker가 실행되는가?
- [ ] 태스크가 큐에 추가되는가?
- [ ] Flower에서 태스크 모니터링 가능한가?
- [ ] 서버 재시작 후에도 태스크 실행되는가?

---

## Phase 3 완료 기준

### 필수 체크리스트
- [ ] 스캔 요청 즉시 응답 (비동기)
- [ ] 백그라운드에서 스캔 실행
- [ ] WebSocket 연결 성공
- [ ] 실시간 진행 상황 WebSocket으로 수신
- [ ] 각 노드 실행 시 WebSocket 메시지 전송
- [ ] 완료 시 100% 메시지 수신
- [ ] 에러 발생 시 에러 메시지 수신
- [ ] 여러 스캔 동시 실행 가능
- [ ] Python/JavaScript 클라이언트로 테스트 완료

### 선택 체크리스트 (Celery)
- [ ] Celery worker 실행
- [ ] 태스크 큐 정상 작동
- [ ] Flower 모니터링 가능

### 산출물 목록
1. `backend/app/services/async_scan_service.py`
2. `backend/app/core/websocket_manager.py`
3. `backend/app/api/v1/websocket.py`
4. `backend/app/services/langgraph_service.py` (async 버전)
5. `backend/scripts/test_websocket_client.py`
6. `backend/tests/test_websocket.py`
7. `test_websocket.html`
8. `backend/celery_app.py` (선택)
9. `backend/app/tasks/scan_tasks.py` (선택)

### 검증 방법
1. **기능 테스트**: pytest 실행
2. **WebSocket 테스트**: Python/JavaScript 클라이언트 실행
3. **부하 테스트**: 10개 스캔 동시 실행

---

## 다음 단계

Phase 3 완료 후 [Phase 4: 채팅 플로우 연동](./phase4-chat-integration.md)로 진행

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
