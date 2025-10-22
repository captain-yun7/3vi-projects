"""
OpenAI API 호환 어댑터
Open WebUI 연동을 위한 엔드포인트
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from app.core.database import get_db
from app.services.langgraph_service import LangGraphService
from app.models.scan_session import ScanSession, ScanStatus, ScanType

router = APIRouter()


# OpenAI 호환 스키마
class Model(BaseModel):
    id: str
    object: str = "model"
    created: int = 1704067200  # 2024-01-01
    owned_by: str = "3vi"


class ModelList(BaseModel):
    object: str = "list"
    data: List[Model]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "3vi-scanner"
    messages: List[ChatMessage]
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str = "3vi-scanner"
    choices: List[dict]


@router.get("/v1/models", response_model=ModelList)
async def list_models():
    """
    OpenAI 호환 Models API

    사용 가능한 모델 목록 반환
    """
    return ModelList(
        data=[
            Model(
                id="3vi-scanner",
                owned_by="3vi",
            )
        ]
    )


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest, db: Session = Depends(get_db)):
    """
    OpenAI 호환 Chat Completions API

    사용자 메시지에서 스캔 요청을 파싱하고 실행
    """
    # 마지막 사용자 메시지 가져오기
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        return ChatCompletionResponse(
            id="error",
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "스캔 대상을 지정해주세요. 예: '127.0.0.1을 quick 스캔해줘'"
                }
            }]
        )

    last_message = user_messages[-1].content

    # 간단한 파싱 (실제로는 LLM으로 파싱하거나 정규식 사용)
    target = "127.0.0.1"  # 기본값
    scan_type = "quick"

    # "127.0.0.1", "192.168.1.1" 같은 IP 주소 추출
    import re
    ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', last_message)
    if ip_match:
        target = ip_match.group(0)

    # "quick", "standard", "full" 추출
    if "full" in last_message.lower():
        scan_type = "full"
    elif "standard" in last_message.lower():
        scan_type = "standard"

    # DB에 세션 생성
    db_session = ScanSession(
        target=target,
        scan_type=ScanType(scan_type),
        status=ScanStatus.PENDING,
        progress=0,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    session_id = str(db_session.id)

    # 스캔 실행 (동기)
    try:
        db_session.status = ScanStatus.RUNNING
        db.commit()

        service = LangGraphService()
        result = service.run_scan(target, scan_type)

        # 결과 저장
        db_session.status = ScanStatus.COMPLETED
        db_session.progress = 100
        db_session.ports = result.get("ports")
        db_session.vulnerabilities = result.get("vulnerabilities")
        db_session.risk_assessment = result.get("risk_assessment")
        db_session.report = result.get("report")
        db.commit()

        # OpenAI 형식으로 응답
        response_text = f"""✅ 스캔 완료!

**세션 ID**: {session_id}
**대상**: {target}
**스캔 유형**: {scan_type}

**발견된 포트**: {len(result.get('ports', []))}개
**취약점**: {len(result.get('vulnerabilities', []))}개

**포트 상세**:
{_format_ports(result.get('ports', []))}

**취약점 상세**:
{_format_vulnerabilities(result.get('vulnerabilities', []))}

상세 결과는 `/api/v1/langgraph/scan/{session_id}/result`에서 확인하세요.
"""

        return ChatCompletionResponse(
            id=session_id,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }]
        )

    except Exception as e:
        db_session.status = ScanStatus.FAILED
        db_session.error = str(e)
        db.commit()

        return ChatCompletionResponse(
            id=session_id,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"❌ 스캔 실패: {str(e)}"
                }
            }]
        )


def _format_ports(ports):
    """포트 리스트를 문자열로 포맷"""
    if not ports:
        return "없음"
    lines = []
    for p in ports[:5]:  # 최대 5개만
        lines.append(f"- {p['port']}/{p['service']} ({p['state']})")
    if len(ports) > 5:
        lines.append(f"... 외 {len(ports) - 5}개")
    return "\n".join(lines)


def _format_vulnerabilities(vulns):
    """취약점 리스트를 문자열로 포맷"""
    if not vulns:
        return "없음"
    lines = []
    for v in vulns[:5]:
        lines.append(f"- [{v['severity']}] {v['type']} (포트 {v['port']})")
    if len(vulns) > 5:
        lines.append(f"... 외 {len(vulns) - 5}개")
    return "\n".join(lines)
