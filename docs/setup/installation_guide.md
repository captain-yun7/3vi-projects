# 설치 가이드

## 개요
3VI 보안 스캐너 백엔드 시스템의 설치 및 실행 가이드입니다.

---

## 사전 요구사항

### 필수
- **Python**: 3.10 이상
- **PostgreSQL**: 14 이상
- **Redis**: 7 이상
- **nmap**: 최신 버전

### 선택 (개발 환경)
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상

---

## 설치 방법

### 방법 1: Docker Compose (권장)

가장 빠르고 간단한 방법입니다.

#### 1. 저장소 클론
```bash
cd /home/k8s-admin
git clone <repository-url> 3vi-v1
cd 3vi-v1
```

#### 2. 환경 변수 설정
```bash
cp .env.example .env
nano .env
```

**필수 설정**:
- `OPENAI_API_KEY`: OpenAI API 키 입력

#### 3. Docker Compose 실행
```bash
# PostgreSQL + Redis 시작
docker-compose up -d postgres redis

# 상태 확인
docker-compose ps
```

#### 4. 데이터베이스 확인
```bash
# PostgreSQL 접속
docker exec -it 3vi-postgres psql -U secuser -d securitydb

# 테이블 확인 (Phase 2에서 생성됨)
\dt
\q
```

---

### 방법 2: 로컬 설치

Docker 없이 직접 설치하는 방법입니다.

#### 1. PostgreSQL 설치 및 설정
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 데이터베이스 및 사용자 생성
sudo -u postgres psql
```

```sql
CREATE DATABASE securitydb;
CREATE USER secuser WITH PASSWORD 'secpass';
GRANT ALL PRIVILEGES ON DATABASE securitydb TO secuser;
\q
```

#### 2. Redis 설치 및 시작
```bash
# Ubuntu/Debian
sudo apt install redis-server

# Redis 시작
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 상태 확인
redis-cli ping  # 응답: PONG
```

#### 3. nmap 설치
```bash
sudo apt install nmap

# 버전 확인
nmap --version
```

#### 4. Python 가상환경 생성
```bash
cd /home/k8s-admin/3vi-v1/backend

# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

#### 5. 패키지 설치
```bash
# 프로덕션 의존성
pip install -r requirements.txt

# 개발 의존성 (선택)
pip install -r requirements-dev.txt
```

#### 6. 환경 변수 설정
```bash
cd /home/k8s-admin/3vi-v1
cp .env.example .env
nano .env
```

**설정 예시**:
```bash
DATABASE_URL=postgresql://secuser:secpass@localhost:5432/securitydb
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-api-key-here
```

---

## 검증

### 1. PostgreSQL 연결 테스트
```bash
# psql 접속
psql -U secuser -d securitydb -h localhost

# 성공 시
securitydb=>
```

### 2. Redis 연결 테스트
```bash
redis-cli ping
# 응답: PONG
```

### 3. Python 패키지 확인
```bash
# 가상환경 활성화 후
python -c "import fastapi, langgraph, openai; print('All packages installed')"
```

### 4. nmap 테스트
```bash
nmap -V
nmap localhost -p 80
```

---

## 실행

### Phase 1 단계 (현재)
Phase 1에서는 아직 백엔드 서버가 구현되지 않았으므로 PoC 코드만 실행 가능합니다.

```bash
# PoC 실행
cd /home/k8s-admin/3vi-v1
source venv/bin/activate
python 01-poc/simple_poc.py
python 01-poc/advanced_poc.py
```

### Phase 2 이후
```bash
cd /home/k8s-admin/3vi-v1/backend
source venv/bin/activate

# 개발 모드 (자동 재로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

**접속**:
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 헬스체크: http://localhost:8000/api/v1/health

---

## 트러블슈팅

### PostgreSQL 연결 실패
```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 로그 확인
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# 재시작
sudo systemctl restart postgresql
```

**pg_hba.conf 설정** (필요 시):
```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

다음 라인 추가:
```
host    securitydb      secuser         127.0.0.1/32            md5
```

```bash
sudo systemctl reload postgresql
```

---

### Redis 연결 실패
```bash
# Redis 상태 확인
sudo systemctl status redis-server

# 설정 파일 확인
sudo nano /etc/redis/redis.conf

# bind 주소 확인 (127.0.0.1)
# protected-mode yes 확인
```

---

### nmap 권한 에러
```bash
# nmap에 capabilities 부여
sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which nmap)

# 확인
getcap $(which nmap)
```

---

### Python 패키지 설치 실패

#### psycopg2 설치 에러
```bash
# libpq-dev 설치
sudo apt install libpq-dev python3-dev
pip install psycopg2-binary
```

#### 기타 의존성 에러
```bash
# 시스템 패키지 업데이트
sudo apt update
sudo apt install build-essential gcc

# pip 업그레이드
pip install --upgrade pip setuptools wheel
```

---

## 환경별 설정

### 개발 환경
```bash
# .env
DEBUG=True
LOG_LEVEL=DEBUG
RELOAD=True
```

### 프로덕션 환경
```bash
# .env
DEBUG=False
LOG_LEVEL=INFO
RELOAD=False
SECRET_KEY=<generate-secure-key>
```

**Secret Key 생성**:
```bash
openssl rand -hex 32
```

---

## Docker 환경 관리

### 서비스 시작
```bash
docker-compose up -d
```

### 로그 확인
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스
docker-compose logs -f postgres
docker-compose logs -f redis
```

### 서비스 중지
```bash
docker-compose down
```

### 데이터 초기화
```bash
# 볼륨까지 삭제 (주의: 데이터 손실)
docker-compose down -v
```

### 컨테이너 재시작
```bash
docker-compose restart postgres
docker-compose restart redis
```

---

## 다음 단계

Phase 1 완료 후:
1. [Phase 2: LangGraph 서비스화](../phases/phase2-langgraph-service.md)로 진행
2. 백엔드 API 서버 구현
3. DB 마이그레이션 실행

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
