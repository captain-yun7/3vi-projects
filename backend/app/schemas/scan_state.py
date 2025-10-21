"""
LangGraph State 스키마 정의
"""
from typing import TypedDict, List, Dict, Optional


class SecurityScanState(TypedDict):
    """보안 스캔 상태 (LangGraph용 TypedDict)"""
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
