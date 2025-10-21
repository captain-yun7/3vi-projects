"""
헬스체크 API 엔드포인트
"""
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
    return {
        "api": "operational",
        "database": "not_configured",  # Phase 2.4에서 구현
        "redis": "not_configured",
        "openai": "configured" if settings.OPENAI_API_KEY else "not_configured",
    }
