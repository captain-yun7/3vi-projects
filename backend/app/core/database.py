"""
데이터베이스 연결 및 세션 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# DB 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    echo=settings.DEBUG,  # SQL 로그 출력
    pool_size=5,  # 연결 풀 크기
    max_overflow=10,  # 최대 추가 연결 수
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 클래스 (모든 모델의 부모)
Base = declarative_base()


def get_db():
    """
    DB 세션 의존성 주입용 함수
    FastAPI에서 Depends(get_db)로 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    데이터베이스 초기화
    테이블 생성 (개발용, 프로덕션에서는 Alembic 사용)
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def check_db_connection():
    """
    데이터베이스 연결 상태 확인
    헬스체크에서 사용
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
