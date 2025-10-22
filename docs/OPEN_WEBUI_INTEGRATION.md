# Open WebUI ↔ 3VI Backend 연동 가이드

## 개요

Open WebUI를 프론트엔드로 사용하여 3VI 보안 스캔 시스템을 채팅 인터페이스로 제어할 수 있습니다.

---

## 1. 연동 방식

### OpenAI API 호환 엔드포인트

3VI 백엔드는 OpenAI Chat Completions API와 호환되는 엔드포인트를 제공합니다:

```
POST http://localhost:8000/api/v1/chat/completions
```

**요청 형식:**
```json
{
  "model": "3vi-scanner",
  "messages": [
    {"role": "user", "content": "127.0.0.1을 quick 스캔해줘"}
  ]
}
```

**응답 형식:**
```json
{
  "id": "session-uuid",
  "object": "chat.completion",
  "model": "3vi-scanner",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "✅ 스캔 완료!\n\n포트: 2개\n취약점: 1개\n..."
    }
  }]
}
```

---

## 2. Open WebUI 설정 방법

### 2.1 Open WebUI 실행

```bash
cd /home/k8s-admin/3vi-v1/RedOpsAI-web

# Docker로 실행
docker run -d -p 3000:8080 \
  --name open-webui \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main

# 또는 로컬 실행
npm install
npm run dev
```

### 2.2 API 연결 설정

**방법 A: Settings → Connections**

1. Open WebUI 접속 (http://localhost:3000)
2. 좌측 하단 **Settings** 클릭
3. **Admin Settings** → **Connections** 탭
4. **OpenAI API** 섹션:
   ```
   API Base URL: http://host.docker.internal:8000/api
   API Key: (비워두거나 임의값 입력)
   ```
5. **Save** 클릭

**방법 B: 환경 변수**

```bash
# .env 파일
OPENAI_API_BASE_URL=http://localhost:8000/api
OPENAI_API_KEY=sk-dummy-key  # 백엔드에서 검증 안 함
```

### 2.3 모델 설정

1. **Admin Settings** → **Models** 탭
2. **Add Model** 클릭:
   ```
   Model ID: 3vi-scanner
   Model Name: 3VI Security Scanner
   Base Model: gpt-3.5-turbo (호환성을 위해)
   ```

---

## 3. 사용 방법

### 3.1 기본 스캔

**채팅창에 입력:**
```
127.0.0.1을 quick 스캔해줘
```

**AI 응답:**
```
✅ 스캔 완료!

**세션 ID**: abc-123-def-456
**대상**: 127.0.0.1
**스캔 유형**: quick

**발견된 포트**: 2개
**취약점**: 1개

**포트 상세**:
- 22/ssh (open)
- 80/http (open)

**취약점 상세**:
- [Low] SSH (포트 22)

상세 결과는 `/api/v1/langgraph/scan/abc-123.../result`에서 확인하세요.
```

### 3.2 다양한 스캔 타입

```
# Quick 스캔 (1-1000 포트)
192.168.1.1을 quick 스캔해줘

# Standard 스캔 (1-10000 포트)
10.0.0.1을 standard 스캔해줘

# Full 스캔 (전체 포트)
localhost를 full 스캔해줘
```

### 3.3 IP 주소 자동 추출

시스템이 메시지에서 IP 주소를 자동으로 추출합니다:

```
"192.168.1.100에 대해 보안 스캔 실행"
→ 192.168.1.100 추출

"127.0.0.1 취약점 검사"
→ 127.0.0.1 추출
```

---

## 4. 고급 설정

### 4.1 스트리밍 응답 (선택)

실시간 진행률을 스트리밍으로 전송하려면:

```python
# backend/app/api/v1/openai_adapter.py에 추가

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if request.stream:
        return StreamingResponse(
            stream_scan_progress(...),
            media_type="text/event-stream"
        )
```

### 4.2 Function Calling

Open WebUI Tools로 더 정교한 제어:

```python
# Open WebUI → Tools → Add New Tool

"""
title: 3VI Scanner
description: Security vulnerability scanner
"""

import requests

class Tools:
    def scan(self, target: str, scan_type: str = "quick"):
        """Execute security scan"""
        response = requests.post(
            "http://localhost:8000/api/v1/langgraph/scan",
            json={"target": target, "scan_type": scan_type}
        )
        return response.json()
```

**사용:**
```
You: 10.0.0.1 스캔
AI: [scan 함수 호출]
    결과: {...}
```

---

## 5. 테스트

### 5.1 수동 테스트

```bash
# 백엔드 서버 시작
cd /home/k8s-admin/3vi-v1/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Open WebUI 시작
cd /home/k8s-admin/3vi-v1/RedOpsAI-web
npm run dev

# 브라우저에서
# 1. http://localhost:3000 접속
# 2. Settings → Connections → OpenAI API 설정
# 3. 채팅창에 "127.0.0.1 스캔" 입력
```

### 5.2 curl 테스트

```bash
# OpenAI 호환 API 테스트
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "3vi-scanner",
    "messages": [
      {"role": "user", "content": "127.0.0.1을 quick 스캔"}
    ]
  }'

# 응답 확인
# ✅ id, choices, message 필드 확인
```

---

## 6. 아키텍처

```
┌──────────────┐     HTTP POST          ┌──────────────┐
│              │  /v1/chat/completions  │              │
│  Open WebUI  │ ───────────────────────>│  3VI Backend │
│  (Frontend)  │                         │  (FastAPI)   │
│              │ <───────────────────────│              │
└──────────────┘     JSON Response       └──────────────┘
                                                │
                                                │ Scan
                                                ▼
                                         ┌──────────────┐
                                         │  LangGraph   │
                                         │  Service     │
                                         └──────────────┘
                                                │
                                                │ Save
                                                ▼
                                         ┌──────────────┐
                                         │  PostgreSQL  │
                                         │  Database    │
                                         └──────────────┘
```

---

## 7. 제한사항 및 향후 개선

### 현재 제한사항

- ❌ 실시간 진행률 표시 어려움 (채팅 메시지는 한 번 완료되면 변경 불가)
- ❌ 테이블/그래프 같은 시각화 불가능
- ❌ 여러 스캔 세션 동시 관리 UI 부족

### 향후 개선 계획

- ✅ **Phase 3**: WebSocket 스트리밍 응답 추가
  ```
  "스캔 시작... 10%... 20%... 50%... 완료!"
  ```

- ✅ **Phase 4**: Open WebUI Plugin 개발
  - 커스텀 UI 컴포넌트 (진행률 바, 결과 테이블)
  - 실시간 업데이트

- ✅ **Phase 5**: 별도 대시보드 추가 (선택)
  - React 기반 시각화 대시보드
  - Open WebUI와 병행 사용

---

## 8. 문제 해결

### 문제 1: "Model not found"
```
해결: Settings → Models에서 3vi-scanner 모델 추가
```

### 문제 2: "Connection failed"
```bash
# 백엔드 서버 상태 확인
curl http://localhost:8000/

# Docker 네트워크 확인 (Docker 사용 시)
# host.docker.internal 대신 실제 IP 사용
```

### 문제 3: "Scan timeout"
```python
# backend/app/api/v1/openai_adapter.py
# 타임아웃 설정 조정
```

---

## 9. 참고 자료

- [Open WebUI 공식 문서](https://docs.openwebui.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat)
- [3VI Backend API 문서](http://localhost:8000/docs)

---

## 10. 다음 단계

1. ✅ Open WebUI 설정 완료
2. ⏳ Phase 3: WebSocket 실시간 진행률 구현
3. ⏳ Phase 4: Open WebUI Plugin 개발
4. ⏳ Phase 5: 시각화 대시보드 추가
