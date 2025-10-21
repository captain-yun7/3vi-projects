# 3VI Security Scanner - Backend

AI 기반 보안 스캔 자동화 시스템의 백엔드 API 서버

---

## 기술 스택

- **Framework**: FastAPI 0.115.0
- **Python**: 3.10+
- **Database**: PostgreSQL 14+
- **Cache/Queue**: Redis 7+
- **AI/LLM**: LangGraph, OpenAI API
- **Security Tools**: python-nmap

---

## 빠른 시작

### 1. 사전 요구사항

```bash
# Python 3.10 이상
python3 --version

# PostgreSQL 설치
sudo apt install postgresql postgresql-contrib

# Redis 설치
sudo apt install redis-server

# nmap 설치
sudo apt install nmap
```

### 2. 가상환경 생성 및 활성화

```bash
cd /home/k8s-admin/3vi-v1/backend
python3 -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치

```bash
# 프로덕션 의존성
pip install -r requirements.txt

# 개발 의존성 (선택)
pip install -r requirements-dev.txt
```

### 4. 환경 변수 설정

```bash
# .env 파일 생성
cp ../.env.example .env

# .env 파일 편집
nano .env
```

**필수 설정**:
- `OPENAI_API_KEY`: OpenAI API 키
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `SECRET_KEY`: JWT 시크릿 키

### 5. 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성
sudo -u postgres psql
CREATE DATABASE securitydb;
CREATE USER secuser WITH PASSWORD 'secpass';
GRANT ALL PRIVILEGES ON DATABASE securitydb TO secuser;
\q

# 마이그레이션 실행 (Phase 2에서 구현)
# alembic upgrade head
```

### 6. 서버 실행

```bash
# 개발 모드 (자동 재로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

서버 실행 후 다음 URL에서 확인:
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 헬스체크: http://localhost:8000/api/v1/health

---

## 프로젝트 구조

```
backend/
├── app/
│   ├── api/                # API 라우터
│   │   └── v1/
│   │       ├── health.py
│   │       ├── langgraph.py
│   │       └── websocket.py
│   ├── core/               # 핵심 설정
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logging.py
│   ├── models/             # DB 모델
│   │   ├── scan_session.py
│   │   └── scan_result.py
│   ├── schemas/            # Pydantic 스키마
│   │   ├── scan_request.py
│   │   └── scan_response.py
│   ├── services/           # 비즈니스 로직
│   │   ├── langgraph_service.py
│   │   └── tools/
│   └── main.py             # 진입점
├── tests/                  # 테스트
├── requirements.txt
└── README.md
```

---

## API 사용 예시

### 스캔 시작

```bash
curl -X POST http://localhost:8000/api/v1/langgraph/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "127.0.0.1",
    "scan_type": "quick"
  }'
```

**응답**:
```json
{
  "session_id": "abc-123-def-456",
  "status": "pending",
  "message": "Scan started"
}
```

### 스캔 상태 조회

```bash
curl http://localhost:8000/api/v1/langgraph/scan/abc-123-def-456
```

### 스캔 결과 조회

```bash
curl http://localhost:8000/api/v1/langgraph/scan/abc-123-def-456/result
```

---

## 개발 가이드

### 코드 포맷팅

```bash
# Black (코드 포맷터)
black app/

# isort (import 정렬)
isort app/

# Flake8 (린터)
flake8 app/
```

### 타입 체크

```bash
mypy app/
```

### 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트 파일만
pytest tests/test_langgraph.py
```

---

## 트러블슈팅

### nmap 권한 에러

```bash
# nmap에 권한 부여
sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which nmap)
```

### PostgreSQL 연결 실패

```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# PostgreSQL 재시작
sudo systemctl restart postgresql
```

### Redis 연결 실패

```bash
# Redis 상태 확인
sudo systemctl status redis

# Redis 시작
sudo systemctl start redis
```

---

## Phase별 진행 상황

- [x] **Phase 0**: PoC 완료
- [ ] **Phase 1**: 기술 스택 설계 및 환경 구축 (진행 중)
- [ ] **Phase 2**: LangGraph 서비스화 및 API 기본 연동
- [ ] **Phase 3**: 비동기 처리 및 실시간 통신
- [ ] **Phase 4**: 채팅 플로우 연동
- [ ] **Phase 5**: MCP 모듈화

상세 일정은 [`/docs/phases/`](../docs/phases/) 참조

---

## 문서

- [백엔드 구조](../docs/architecture/backend_structure.md)
- [설계 원칙](../docs/architecture/design_principles.md)
- [Phase 1 가이드](../docs/phases/phase1-tech-stack-design.md)

---

## 라이선스

MIT License

---

**작성일**: 2025-10-21
**작성자**: 윤지수
