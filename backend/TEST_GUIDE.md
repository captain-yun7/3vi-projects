# 3VI Security Scanner - 테스트 가이드

## 서버 실행

```bash
cd /home/k8s-admin/3vi-v1/backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 테스트 방법 1: Python 테스트 스크립트 (추천)

가장 편리한 방법입니다. 전체 API 흐름을 자동으로 테스트합니다.

```bash
# 새 터미널에서
cd /home/k8s-admin/3vi-v1/backend
source venv/bin/activate
python test_api.py
```

**결과:**
- 스캔 시작 → 상태 조회 → 결과 조회 → 세션 목록 → 삭제 → 확인
- 모든 엔드포인트를 순차적으로 테스트

---

## 테스트 방법 2: curl 명령어

### 2.1 기본 헬스체크
```bash
# 서버 상태 확인
curl http://localhost:8000/
curl http://localhost:8000/api/v1/health
```

### 2.2 스캔 시작
```bash
curl -X POST http://localhost:8000/api/v1/langgraph/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "127.0.0.1",
    "scan_type": "quick"
  }'
```

**응답 예시:**
```json
{
  "session_id": "abc-123-def-456",
  "status": "completed",
  "message": "Scan completed successfully"
}
```

### 2.3 스캔 상태 조회
```bash
# session_id는 위에서 받은 값으로 변경
curl http://localhost:8000/api/v1/langgraph/scan/{session_id}
```

### 2.4 스캔 결과 조회
```bash
curl http://localhost:8000/api/v1/langgraph/scan/{session_id}/result
```

### 2.5 세션 목록 조회
```bash
curl http://localhost:8000/api/v1/langgraph/sessions
```

### 2.6 세션 삭제
```bash
curl -X DELETE http://localhost:8000/api/v1/langgraph/scan/{session_id}
```

---

## 테스트 방법 3: Swagger UI (가장 직관적)

브라우저에서 아래 URL 접속:

```
http://localhost:8000/docs
```

### Swagger UI 사용법:

1. **스캔 시작 테스트**
   - `POST /api/v1/langgraph/scan` 클릭
   - "Try it out" 버튼 클릭
   - Request body 입력:
     ```json
     {
       "target": "127.0.0.1",
       "scan_type": "quick"
     }
     ```
   - "Execute" 클릭
   - 응답에서 `session_id` 복사

2. **상태 조회**
   - `GET /api/v1/langgraph/scan/{session_id}` 클릭
   - "Try it out" 클릭
   - session_id 입력
   - "Execute" 클릭

3. **결과 조회**
   - `GET /api/v1/langgraph/scan/{session_id}/result` 클릭
   - 위와 동일한 방법으로 테스트

4. **세션 목록**
   - `GET /api/v1/langgraph/sessions` 클릭
   - "Try it out" → "Execute"

5. **세션 삭제**
   - `DELETE /api/v1/langgraph/scan/{session_id}` 클릭
   - session_id 입력 후 실행

---

## 테스트 방법 4: HTTPie (curl보다 깔끔)

HTTPie 설치:
```bash
pip install httpie
```

### 사용 예시:
```bash
# 스캔 시작
http POST localhost:8000/api/v1/langgraph/scan \
  target=127.0.0.1 \
  scan_type=quick

# 상태 조회
http GET localhost:8000/api/v1/langgraph/scan/{session_id}

# 결과 조회
http GET localhost:8000/api/v1/langgraph/scan/{session_id}/result

# 세션 목록
http GET localhost:8000/api/v1/langgraph/sessions

# 세션 삭제
http DELETE localhost:8000/api/v1/langgraph/scan/{session_id}
```

---

## 예상 테스트 결과

### 정상 동작 시:

1. **포트 스캔 결과**
   ```json
   "ports": [
     {"port": 22, "state": "open", "service": "ssh"},
     {"port": 80, "state": "open", "service": "http"}
   ]
   ```

2. **취약점 발견**
   ```json
   "vulnerabilities": [
     {
       "port": 22,
       "service": "ssh",
       "type": "Outdated Service",
       "severity": "Low",
       "description": "SSH 서비스가 실행 중입니다..."
     }
   ]
   ```

3. **리스크 평가**
   ```json
   "risk_assessment": {
     "overall_risk": "Low",
     "critical_count": 0,
     "high_count": 0,
     "medium_count": 0,
     "low_count": 1
   }
   ```

4. **보고서 생성**
   - Markdown 형식의 상세 보고서

---

## 문제 해결

### 서버가 시작되지 않을 때:
```bash
# 포트 충돌 확인
lsof -i :8000

# 기존 프로세스 종료
pkill -f "uvicorn app.main:app"
```

### Docker 컨테이너가 실행되지 않을 때:
```bash
# Docker 상태 확인
docker ps

# Docker Compose 재시작
cd /home/k8s-admin/3vi-v1
docker-compose up -d
```

### Import 에러 발생 시:
```bash
# 가상환경 재활성화
deactivate
source venv/bin/activate

# 패키지 재설치
pip install -r requirements.txt
```

---

## 권장 테스트 순서

1. **개발 중**: Swagger UI (`/docs`) 사용
   - 가장 직관적이고 빠름
   - 스키마 확인 가능

2. **자동화 테스트**: `test_api.py` 실행
   - CI/CD 통합 가능
   - 회귀 테스트에 유용

3. **디버깅**: curl 또는 HTTPie
   - 터미널에서 빠르게 확인
   - 스크립트 작성 가능

---

## 다음 단계

Phase 2.4에서는 pytest를 사용한 단위 테스트와 통합 테스트를 추가할 예정입니다.
