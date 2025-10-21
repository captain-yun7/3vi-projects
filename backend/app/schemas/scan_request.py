"""
스캔 요청/응답 스키마
"""
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List, Dict
import ipaddress


class ScanRequest(BaseModel):
    """스캔 요청"""
    target: str = Field(..., description="스캔 대상 IP 주소")
    scan_type: Literal["quick", "standard", "full"] = Field(
        default="standard",
        description="스캔 유형: quick(1-1000포트), standard(1-10000포트), full(전체포트)"
    )

    @validator("target")
    def validate_target(cls, v):
        """IP 주소 형식 검증"""
        if not v:
            raise ValueError("Target IP is required")

        # IP 주소 형식 확인
        try:
            ipaddress.ip_address(v)
        except ValueError:
            # hostname일 수도 있으니 localhost는 허용
            if v not in ["localhost", "127.0.0.1"]:
                raise ValueError(f"Invalid IP address format: {v}")

        return v


class ScanResponse(BaseModel):
    """스캔 응답"""
    session_id: str = Field(..., description="스캔 세션 ID")
    status: str = Field(..., description="스캔 상태")
    message: str = Field(default="", description="메시지")


class ScanStatusResponse(BaseModel):
    """스캔 상태 응답"""
    session_id: str
    status: str  # pending, running, completed, failed
    progress: int = 0  # 0-100
    current_step: Optional[str] = None
    error: Optional[str] = None


class ScanResultResponse(BaseModel):
    """스캔 결과 응답"""
    session_id: str
    target: str
    scan_type: str
    ports: Optional[List[Dict]] = None
    vulnerabilities: Optional[List[Dict]] = None
    risk_assessment: Optional[Dict] = None
    remediation: Optional[Dict] = None
    report: Optional[str] = None
