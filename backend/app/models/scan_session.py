"""
스캔 세션 데이터베이스 모델
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ScanStatus(str, enum.Enum):
    """스캔 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanType(str, enum.Enum):
    """스캔 유형"""
    QUICK = "quick"
    STANDARD = "standard"
    FULL = "full"


class ScanSession(Base):
    """
    스캔 세션 모델

    스캔 요청부터 완료까지의 전체 정보를 저장
    """
    __tablename__ = "scan_sessions"

    # 기본 정보
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="세션 ID (UUID)"
    )

    # 스캔 대상 정보
    target = Column(
        String(255),
        nullable=False,
        index=True,
        comment="스캔 대상 IP 주소"
    )

    scan_type = Column(
        SQLEnum(ScanType),
        nullable=False,
        default=ScanType.STANDARD,
        comment="스캔 유형 (quick/standard/full)"
    )

    # 상태 정보
    status = Column(
        SQLEnum(ScanStatus),
        nullable=False,
        default=ScanStatus.PENDING,
        index=True,
        comment="스캔 상태"
    )

    progress = Column(
        Integer,
        default=0,
        comment="진행률 (0-100)"
    )

    current_step = Column(
        String(100),
        nullable=True,
        comment="현재 진행 중인 단계"
    )

    error = Column(
        Text,
        nullable=True,
        comment="에러 메시지 (실패 시)"
    )

    # 스캔 결과 (JSON 형태로 저장)
    ports = Column(
        JSONB,
        nullable=True,
        comment="발견된 포트 목록"
    )

    vulnerabilities = Column(
        JSONB,
        nullable=True,
        comment="발견된 취약점 목록"
    )

    risk_assessment = Column(
        JSONB,
        nullable=True,
        comment="위험도 평가 결과"
    )

    remediation = Column(
        JSONB,
        nullable=True,
        comment="해결 방안"
    )

    report = Column(
        Text,
        nullable=True,
        comment="최종 보고서 (Markdown)"
    )

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="생성 시간"
    )

    started_at = Column(
        DateTime,
        nullable=True,
        comment="스캔 시작 시간"
    )

    completed_at = Column(
        DateTime,
        nullable=True,
        comment="스캔 완료 시간"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="마지막 업데이트 시간"
    )

    def __repr__(self):
        return f"<ScanSession(id={self.id}, target={self.target}, status={self.status})>"

    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "session_id": str(self.id),
            "target": self.target,
            "scan_type": self.scan_type.value if self.scan_type else None,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "current_step": self.current_step,
            "error": self.error,
            "ports": self.ports,
            "vulnerabilities": self.vulnerabilities,
            "risk_assessment": self.risk_assessment,
            "remediation": self.remediation,
            "report": self.report,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
