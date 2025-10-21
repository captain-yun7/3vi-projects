"""
FastAPI 애플리케이션 진입점
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import health, langgraph

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
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
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(langgraph.router, prefix="/api/v1/langgraph", tags=["langgraph"])


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("Shutting down application")


@app.get("/")
def root():
    """루트 엔드포인트"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.RELOAD,
    )
