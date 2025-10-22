"""
LangGraph 스캔 API 엔드포인트 (DB 연동)
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from app.schemas.scan_request import (
    ScanRequest,
    ScanResponse,
    ScanStatusResponse,
    ScanResultResponse,
)
from app.services.langgraph_service import LangGraphService
from app.core.database import get_db
from app.models.scan_session import ScanSession, ScanStatus, ScanType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """
    보안 스캔 시작

    - **target**: 스캔 대상 IP 주소
    - **scan_type**: quick(1-1000포트), standard(1-10000포트), full(전체포트)
    """
    # DB에 세션 생성
    db_session = ScanSession(
        target=request.target,
        scan_type=ScanType(request.scan_type),  # 이미 소문자 값 (quick/standard/full)
        status=ScanStatus.PENDING,
        progress=0,
        started_at=datetime.utcnow(),
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    session_id = str(db_session.id)
    logger.info(f"Scan session created: {session_id} for target {request.target}")

    # 동기 실행 (Phase 3에서 비동기로 변경)
    try:
        # 상태 업데이트: running
        db_session.status = ScanStatus.RUNNING
        db.commit()

        # LangGraph 서비스 실행
        service = LangGraphService()
        result = service.run_scan(request.target, request.scan_type)

        # 결과를 DB에 저장
        db_session.status = ScanStatus.COMPLETED
        db_session.progress = 100
        db_session.completed_at = datetime.utcnow()
        db_session.ports = result.get("ports")
        db_session.vulnerabilities = result.get("vulnerabilities")
        db_session.risk_assessment = result.get("risk_assessment")
        db_session.remediation = result.get("remediation")
        db_session.report = result.get("report")
        db.commit()

        logger.info(f"Scan completed for session {session_id}")

        return ScanResponse(
            session_id=session_id,
            status="completed",
            message="Scan completed successfully"
        )

    except Exception as e:
        logger.error(f"Scan failed for session {session_id}: {e}")

        # 실패 상태로 업데이트
        db_session.status = ScanStatus.FAILED
        db_session.error = str(e)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )


@router.get("/scan/{session_id}", response_model=ScanStatusResponse)
async def get_scan_status(session_id: str, db: Session = Depends(get_db)):
    """
    스캔 상태 조회

    - **session_id**: 스캔 세션 ID
    """
    db_session = db.query(ScanSession).filter(
        ScanSession.id == session_id
    ).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan session not found: {session_id}"
        )

    return ScanStatusResponse(
        session_id=str(db_session.id),
        status=db_session.status.value,
        progress=db_session.progress,
        current_step=db_session.current_step,
        error=db_session.error,
    )


@router.get("/scan/{session_id}/result", response_model=ScanResultResponse)
async def get_scan_result(session_id: str, db: Session = Depends(get_db)):
    """
    스캔 결과 조회

    - **session_id**: 스캔 세션 ID
    """
    db_session = db.query(ScanSession).filter(
        ScanSession.id == session_id
    ).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan session not found: {session_id}"
        )

    if db_session.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan not completed yet. Current status: {db_session.status.value}"
        )

    return ScanResultResponse(
        session_id=str(db_session.id),
        target=db_session.target,
        scan_type=db_session.scan_type.value.lower(),
        ports=db_session.ports,
        vulnerabilities=db_session.vulnerabilities,
        risk_assessment=db_session.risk_assessment,
        remediation=db_session.remediation,
        report=db_session.report,
    )


@router.get("/sessions", response_model=List[dict])
async def list_sessions(db: Session = Depends(get_db)):
    """
    모든 스캔 세션 목록 조회
    """
    sessions = db.query(ScanSession).order_by(
        ScanSession.created_at.desc()
    ).all()

    return [
        {
            "session_id": str(session.id),
            "target": session.target,
            "status": session.status.value,
            "started_at": session.started_at.isoformat() if session.started_at else None,
        }
        for session in sessions
    ]


@router.delete("/scan/{session_id}")
async def delete_scan(session_id: str, db: Session = Depends(get_db)):
    """
    스캔 세션 삭제

    - **session_id**: 스캔 세션 ID
    """
    db_session = db.query(ScanSession).filter(
        ScanSession.id == session_id
    ).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan session not found: {session_id}"
        )

    db.delete(db_session)
    db.commit()

    logger.info(f"Scan session deleted: {session_id}")

    return {"message": f"Scan session {session_id} deleted successfully"}
