"""
애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Application
    APP_NAME: str = "3VI Security Scanner"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Security
    SECRET_KEY: str
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """ALLOWED_ORIGINS 문자열을 리스트로 변환"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Scanning
    SCAN_TIMEOUT: int = 300
    MAX_CONCURRENT_SCANS: int = 5
    ALLOWED_TARGET_NETWORKS: str = "127.0.0.1,localhost,192.168.0.0/16,10.0.0.0/8"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_JSON_FORMAT: bool = False

    # Celery (Phase 3+)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Development
    RELOAD: bool = False
    SQL_ECHO: bool = False

    class Config:
        env_file = "../.env"  # 프로젝트 루트의 .env 파일 사용
        case_sensitive = True


settings = Settings()
