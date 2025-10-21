"""
LangGraph 스캔 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict
import uuid
import logging
from datetime import datetime

from app.schemas.scan_request import (
    ScanRequest,
    ScanResponse,
    ScanStatusResponse,
    ScanResultResponse,
)
from app.services.langgraph_service import LangGraphService

logger = logging.getLogger(__name__)
router = APIRouter()

# 임시 메모리 저장소 (Phase 2.4에서 DB로 대체)
scan_sessions: Dict[str, dict] = {}


@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(request: ScanRequest):
    """
    보안 스캔 시작

    - **target**: 스캔 대상 IP 주소
    - **scan_type**: quick(1-1000포트), standard(1-10000포트), full(전체포트)
    """
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

    logger.info(f"Scan session created: {session_id} for target {request.target}")

    # 동기 실행 (Phase 3에서 비동기로 변경)
    try:
        scan_sessions[session_id]["status"] = "running"

        # LangGraph 서비스 실행
        service = LangGraphService()
        result = service.run_scan(request.target, request.scan_type)

        # 결과 저장
        scan_sessions[session_id]["status"] = "completed"
        scan_sessions[session_id]["progress"] = 100
        scan_sessions[session_id]["completed_at"] = datetime.utcnow()
        scan_sessions[session_id]["result"] = result

        logger.info(f"Scan completed for session {session_id}")

        return ScanResponse(
            session_id=session_id,
            status="completed",
            message="Scan completed successfully"
        )

    except Exception as e:
        logger.error(f"Scan failed for session {session_id}: {e}")
        scan_sessions[session_id]["status"] = "failed"
        scan_sessions[session_id]["error"] = str(e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )


@router.get("/scan/{session_id}", response_model=ScanStatusResponse)
async def get_scan_status(session_id: str):
    """
    스캔 상태 조회

    - **session_id**: 스캔 세션 ID
    """
    if session_id not in scan_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan session not found: {session_id}"
        )

    session = scan_sessions[session_id]

    return ScanStatusResponse(
        session_id=session["session_id"],
        status=session["status"],
        progress=session["progress"],
        current_step=session.get("current_step"),
        error=session.get("error"),
    )


@router.get("/scan/{session_id}/result", response_model=ScanResultResponse)
async def get_scan_result(session_id: str):
    """
    스캔 결과 조회

    - **session_id**: 스캔 세션 ID
    """
    if session_id not in scan_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan session not found: {session_id}"
        )

    session = scan_sessions[session_id]

    if session["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan not completed yet. Current status: {session['status']}"
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
    )


@router.get("/sessions", response_model=list)
async def list_sessions():
    """
    모든 스캔 세션 목록 조회
    """
    sessions = []
    for session_id, session in scan_sessions.items():
        sessions.append({
            "session_id": session_id,
            "target": session["target"],
            "status": session["status"],
            "started_at": session["started_at"].isoformat(),
        })
    return sessions


@router.delete("/scan/{session_id}")
async def delete_scan(session_id: str):
    """
    스캔 세션 삭제

    - **session_id**: 스캔 세션 ID
    """
    if session_id not in scan_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan session not found: {session_id}"
        )

    del scan_sessions[session_id]
    logger.info(f"Scan session deleted: {session_id}")

    return {"message": f"Scan session {session_id} deleted successfully"}
