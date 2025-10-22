# 3VI Security Scanner - Docker 배포 가이드

## 🚀 빠른 시작 (Docker Compose)

### 1. 전체 스택 실행

```bash
# 이미지 빌드 및 컨테이너 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 보기
docker-compose logs -f backend
```

### 2. 접속

- **프론트엔드 (Open WebUI)**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 3. 초기 설정

1. http://localhost:3000 접속
2. 첫 사용자 계정 생성 (첫 사용자가 자동으로 관리자가 됩니다)
3. 로그인 후 채팅창에서 모델 선택: `3vi-scanner`
4. 스캔 실행: "127.0.0.1 스캔해줘"

## 🛠️ 관리 명령어

### 서비스 제어

```bash
# 전체 중지
docker-compose down

# 전체 중지 + 볼륨 삭제 (데이터 초기화)
docker-compose down -v

# 특정 서비스만 재시작
docker-compose restart backend

# 서비스 상태 확인
docker-compose ps
```

### 로그 및 디버깅

```bash
# 실시간 로그
docker-compose logs -f

# 최근 100줄만 보기
docker-compose logs --tail=100

# 특정 서비스 컨테이너 접속
docker-compose exec backend bash
docker-compose exec postgres psql -U secuser -d securitydb
```

### 업데이트

```bash
# 코드 변경 후 재빌드
docker-compose up -d --build backend

# Open WebUI 이미지 업데이트
docker-compose pull webui
docker-compose up -d webui
```

## 📦 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| postgres | 5433 | PostgreSQL 14 데이터베이스 |
| backend | 8000 | FastAPI 백엔드 + LangGraph 스캔 엔진 |
| webui | 3000 | Open WebUI 프론트엔드 |

## 🔧 환경 변수 설정

`.env` 파일을 만들어서 환경변수를 관리할 수 있습니다:

```bash
# .env 파일 예시
DATABASE_URL=postgresql://secuser:secpass@postgres:5432/securitydb
SECRET_KEY=your-secret-key-here-change-in-production
OPENAI_API_KEY=your-openai-api-key
DEBUG=True
```

docker-compose.yml에서 사용:

```yaml
env_file:
  - .env
```

## 🐛 트러블슈팅

### 포트 충돌

```bash
# 포트가 이미 사용 중이면 docker-compose.yml에서 포트 변경
# 예: "3000:8080" → "3001:8080"
```

### 데이터베이스 연결 오류

```bash
# 헬스체크 확인
docker-compose ps

# 데이터베이스 로그 확인
docker-compose logs postgres

# 데이터베이스 재시작
docker-compose restart postgres
```

### 백엔드 에러

```bash
# 로그 확인
docker-compose logs backend

# 컨테이너 재빌드
docker-compose up -d --build backend
```

## 🔒 보안 주의사항

### 프로덕션 배포 시:

1. **SECRET_KEY 변경 필수**:
   ```bash
   # 랜덤 키 생성
   openssl rand -hex 32
   ```

2. **환경변수로 민감정보 관리**:
   ```bash
   # .env 파일 사용 (.gitignore에 추가됨)
   ```

3. **포트 노출 최소화**:
   ```yaml
   # 외부 접근 불필요한 서비스는 포트 매핑 제거
   # ports 섹션 삭제
   ```

4. **HTTPS 사용**:
   - Nginx 리버스 프록시 + Let's Encrypt
   - 또는 클라우드 로드밸런서 사용

## 📚 추가 문서

- [Open WebUI 통합 가이드](docs/OPEN_WEBUI_INTEGRATION.md)
- [API 문서](http://localhost:8000/docs)
- [테스트 가이드](backend/TEST_GUIDE.md)
