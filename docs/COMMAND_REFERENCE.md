# 3VI 프로젝트 - 주요 명령어 정리

## 📚 목차
1. [Docker 명령어](#docker-명령어)
2. [Docker Compose 명령어](#docker-compose-명령어)
3. [Git 명령어](#git-명령어)
4. [Python/FastAPI 명령어](#pythonfastapi-명령어)
5. [네트워크 디버깅](#네트워크-디버깅)
6. [프로세스 관리](#프로세스-관리)
7. [PostgreSQL 명령어](#postgresql-명령어)

---

## Docker 명령어

### 1. 이미지 빌드
```bash
docker build -t 3vi-backend .
```
**의미**: 현재 디렉토리의 Dockerfile을 사용하여 `3vi-backend`라는 이름의 이미지 생성
- `-t`: 태그(이름) 지정
- `.`: 현재 디렉토리를 빌드 컨텍스트로 사용

### 2. 컨테이너 실행
```bash
docker run -d \
  --name 3vi-backend \
  --network 3vi-network \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://secuser:secpass@3vi-postgres:5432/securitydb \
  -e SECRET_KEY=your-secret-key \
  3vi-backend
```
**의미**: 백엔드 컨테이너를 백그라운드에서 실행
- `-d`: detached 모드 (백그라운드 실행)
- `--name`: 컨테이너 이름 지정
- `--network`: Docker 네트워크에 연결
- `-p 8000:8000`: 호스트의 8000번 포트를 컨테이너의 8000번 포트로 매핑
- `-e`: 환경변수 설정

### 3. 컨테이너 로그 확인
```bash
docker logs 3vi-backend
docker logs -f 3vi-backend          # 실시간으로 로그 따라가기
docker logs --tail 50 3vi-backend   # 최근 50줄만 보기
docker logs 3vi-backend 2>&1 | grep ERROR  # 에러만 필터링
```
**의미**: 컨테이너의 stdout/stderr 출력 확인
- `-f`: follow (실시간 갱신)
- `--tail N`: 마지막 N줄만 출력
- `2>&1`: stderr를 stdout으로 리다이렉트

### 4. 컨테이너 관리
```bash
docker ps                    # 실행 중인 컨테이너 목록
docker ps -a                 # 모든 컨테이너 목록 (중지된 것 포함)
docker stop 3vi-backend      # 컨테이너 중지
docker start 3vi-backend     # 컨테이너 시작
docker restart 3vi-backend   # 컨테이너 재시작
docker rm 3vi-backend        # 컨테이너 삭제
```

### 5. 컨테이너 내부 접속
```bash
docker exec -it 3vi-backend bash
```
**의미**: 실행 중인 컨테이너 내부로 들어가서 bash 실행
- `-i`: interactive (입력 가능)
- `-t`: TTY 할당 (터미널)

### 6. 컨테이너에서 명령 실행
```bash
docker exec 3vi-backend curl -s http://localhost:8000/api/v1/health
```
**의미**: 컨테이너 내부에서 curl 명령 실행

### 7. Docker 네트워크
```bash
docker network create 3vi-network               # 네트워크 생성
docker network ls                               # 네트워크 목록
docker network inspect 3vi-network              # 네트워크 상세 정보
docker network connect 3vi-network 3vi-postgres # 컨테이너를 네트워크에 연결
```
**의미**: Docker 컨테이너 간 통신을 위한 가상 네트워크 관리

### 8. Docker 볼륨
```bash
docker volume ls                  # 볼륨 목록
docker volume inspect open-webui  # 볼륨 상세 정보
docker volume rm open-webui       # 볼륨 삭제
```
**의미**: 컨테이너의 데이터를 영구 저장하기 위한 볼륨 관리

### 9. 이미지 관리
```bash
docker images                     # 이미지 목록
docker rmi 3vi-backend           # 이미지 삭제
docker image prune               # 사용하지 않는 이미지 정리
```

---

## Docker Compose 명령어

### 1. 전체 스택 실행
```bash
docker-compose up -d --build
```
**의미**: docker-compose.yml의 모든 서비스를 빌드하고 백그라운드에서 실행
- `up`: 컨테이너 생성 및 시작
- `-d`: detached 모드
- `--build`: 이미지를 강제로 다시 빌드

### 2. 전체 스택 중지
```bash
docker-compose down           # 컨테이너 중지 및 제거
docker-compose down -v        # 볼륨까지 삭제
```
**의미**: 모든 컨테이너, 네트워크 제거
- `-v`: 볼륨까지 함께 삭제 (데이터 초기화)

### 3. 특정 서비스만 관리
```bash
docker-compose restart backend        # 백엔드만 재시작
docker-compose logs -f backend        # 백엔드 로그만 보기
docker-compose up -d --build backend  # 백엔드만 재빌드
```

### 4. 서비스 상태 확인
```bash
docker-compose ps           # 서비스 상태 목록
docker-compose top          # 각 컨테이너의 프로세스 확인
```

### 5. 로그 확인
```bash
docker-compose logs               # 모든 서비스 로그
docker-compose logs -f            # 실시간 로그
docker-compose logs --tail=100    # 최근 100줄
```

---

## Git 명령어

### 1. 상태 확인
```bash
git status                     # 변경사항 확인
git status --porcelain         # 간단한 형식으로 출력
git diff                       # 변경된 내용 상세
git diff --stat                # 변경된 파일 통계
```

### 2. 파일 추가 및 커밋
```bash
git add -A                     # 모든 변경사항 스테이징
git add .                      # 현재 디렉토리 이하 변경사항 스테이징
git add backend/               # 특정 디렉토리만 스테이징

git commit -m "커밋 메시지"    # 커밋 생성
```

### 3. 커밋 히스토리
```bash
git log                        # 전체 커밋 히스토리
git log --oneline              # 한 줄로 간단히
git log --oneline -5           # 최근 5개만
git log --graph --all          # 그래프로 시각화
```

### 4. 파일 제거
```bash
git rm --cached filename       # Git 추적만 제거 (파일은 유지)
git rm filename                # Git 추적 및 파일 삭제
```

### 5. 원격 저장소
```bash
git remote -v                  # 원격 저장소 확인
git push origin main           # 원격 저장소에 푸시
git pull origin main           # 원격 저장소에서 가져오기
```

### 6. .gitignore
```bash
cat >> .gitignore << 'EOF'
node_modules/
*.log
EOF
```
**의미**: .gitignore 파일에 내용 추가 (heredoc 사용)

---

## Python/FastAPI 명령어

### 1. 가상환경
```bash
python3 -m venv venv           # 가상환경 생성
source venv/bin/activate       # 가상환경 활성화 (Linux/Mac)
deactivate                     # 가상환경 비활성화
```

### 2. 패키지 관리
```bash
pip install -r requirements.txt   # 의존성 설치
pip freeze > requirements.txt     # 현재 패키지 목록 저장
pip list                          # 설치된 패키지 목록
```

### 3. FastAPI 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
**의미**: FastAPI 애플리케이션 실행
- `app.main:app`: app/main.py 파일의 app 객체 실행
- `--host 0.0.0.0`: 모든 네트워크 인터페이스에서 접속 허용
- `--port 8000`: 8000번 포트 사용

```bash
uvicorn app.main:app --reload
```
**의미**: 개발 모드 - 코드 변경 시 자동 재시작
- `--reload`: 파일 변경 감지하여 자동 재시작

---

## 네트워크 디버깅

### 1. 포트 확인
```bash
lsof -i :8000                  # 8000번 포트 사용 중인 프로세스
netstat -tlnp | grep 8000      # 8000번 포트 리스닝 확인
```
**의미**: 특정 포트를 사용 중인 프로세스 확인
- `-i :8000`: 8000번 포트
- `-t`: TCP
- `-l`: listening
- `-n`: 숫자로 표시
- `-p`: 프로세스 정보

### 2. IP 주소 확인
```bash
ip -4 addr show eth0                           # IPv4 주소 확인
ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'  # IP만 추출
```
**의미**: 네트워크 인터페이스의 IP 주소 확인

### 3. 연결 테스트
```bash
curl http://localhost:8000/api/v1/health       # HTTP 요청
curl -s http://localhost:8000/api/v1/health    # 진행상황 숨김
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool  # JSON 포맷팅
```
**의미**: API 엔드포인트 테스트
- `-s`: silent (진행바 숨김)
- `| python3 -m json.tool`: JSON을 예쁘게 출력

### 4. POST 요청
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"3vi-scanner","messages":[{"role":"user","content":"127.0.0.1 스캔"}]}'
```
**의미**: JSON 데이터를 POST로 전송
- `-X POST`: HTTP POST 메서드
- `-H`: 헤더 설정
- `-d`: 데이터 (request body)

---

## 프로세스 관리

### 1. 프로세스 찾기
```bash
ps aux | grep uvicorn                    # uvicorn 프로세스 찾기
ps aux | grep -E "uvicorn|python"        # 여러 패턴 OR 검색
ps aux | grep -v grep                    # grep 자신은 제외
```
**의미**: 실행 중인 프로세스 검색
- `ps aux`: 모든 프로세스 목록
- `|`: 파이프 (이전 명령의 출력을 다음 명령의 입력으로)
- `grep`: 패턴 검색

### 2. 프로세스 종료
```bash
kill -9 12345                            # PID 12345 강제 종료
pkill -9 -f uvicorn                      # uvicorn 프로세스 모두 강제 종료
```
**의미**: 프로세스 종료
- `-9`: SIGKILL (강제 종료)
- `-f`: 전체 명령줄에서 패턴 검색

### 3. 프로세스 종료 (파이프라인)
```bash
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill -9
```
**의미**: 파이프라인으로 프로세스 찾아서 종료
1. `ps aux`: 모든 프로세스
2. `grep uvicorn`: uvicorn 포함된 줄만
3. `grep -v grep`: grep 자신은 제외
4. `awk '{print $2}'`: 2번째 컬럼(PID)만 추출
5. `xargs kill -9`: 각 PID를 kill 명령의 인자로 전달

### 4. 백그라운드 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```
**의미**: 명령을 백그라운드에서 실행
- `&`: 백그라운드 실행

```bash
nohup uvicorn app.main:app > server.log 2>&1 &
```
**의미**: 터미널 종료 후에도 계속 실행
- `nohup`: 터미널 종료 신호 무시
- `> server.log`: stdout을 파일로 리다이렉트
- `2>&1`: stderr를 stdout으로 리다이렉트

---

## PostgreSQL 명령어

### 1. psql 접속
```bash
docker exec -it 3vi-postgres psql -U secuser -d securitydb
```
**의미**: PostgreSQL 컨테이너에 접속하여 psql 실행
- `-U secuser`: secuser로 접속
- `-d securitydb`: securitydb 데이터베이스 선택

### 2. psql 내부 명령어
```sql
\l              -- 데이터베이스 목록
\c securitydb   -- securitydb로 전환
\dt             -- 테이블 목록
\d scan_sessions  -- scan_sessions 테이블 구조
\du             -- 사용자 목록
\q              -- 종료
```

### 3. SQL 쿼리
```sql
-- 테이블 조회
SELECT * FROM scan_sessions ORDER BY created_at DESC LIMIT 10;

-- 스캔 세션 개수
SELECT COUNT(*) FROM scan_sessions;

-- 상태별 집계
SELECT status, COUNT(*) FROM scan_sessions GROUP BY status;
```

### 4. 컨테이너 외부에서 실행
```bash
docker exec 3vi-postgres psql -U secuser -d securitydb -c "SELECT COUNT(*) FROM scan_sessions;"
```
**의미**: 컨테이너에 접속하지 않고 SQL 실행
- `-c`: 명령어 실행 후 종료

---

## 유용한 조합 명령어

### 1. JSON 응답 포맷팅
```bash
curl -s http://localhost:8000/api/v1/models | python3 -m json.tool
```
**의미**: API 응답을 예쁘게 출력

### 2. 실시간 로그 + 필터링
```bash
docker logs -f 3vi-backend 2>&1 | grep ERROR
```
**의미**: 실시간 로그에서 에러만 필터링

### 3. 파일 내용 추가 (heredoc)
```bash
cat >> .gitignore << 'EOF'
RedOpsAI-web/
package-lock.json
EOF
```
**의미**: 여러 줄을 파일에 추가
- `>>`: 파일 끝에 추가 (append)
- `<<'EOF'`: EOF까지의 내용을 입력으로 사용

### 4. 조건부 명령 실행
```bash
docker stop 3vi-backend 2>/dev/null && docker rm 3vi-backend 2>/dev/null || echo "Container not found"
```
**의미**: 조건부 실행
- `&&`: 이전 명령 성공 시 다음 명령 실행
- `||`: 이전 명령 실패 시 다음 명령 실행
- `2>/dev/null`: 에러 메시지 숨김

### 5. 여러 명령 순차 실행
```bash
docker stop 3vi-backend && docker rm 3vi-backend && docker run -d --name 3vi-backend 3vi-backend
```
**의미**: 여러 명령을 순서대로 실행 (하나라도 실패하면 중단)

---

## 쉘 리다이렉션

### stdout/stderr 리다이렉션
```bash
command > output.log              # stdout을 파일로 (덮어쓰기)
command >> output.log             # stdout을 파일로 (추가)
command 2> error.log              # stderr을 파일로
command > output.log 2>&1         # stdout과 stderr 모두 파일로
command 2>&1 | grep ERROR         # stderr도 파이프로 전달
```

### /dev/null (휴지통)
```bash
command > /dev/null               # stdout 버림
command 2> /dev/null              # stderr 버림
command > /dev/null 2>&1          # 모든 출력 버림
```

---

## Grep 패턴

```bash
grep "pattern" file.txt                    # 패턴 검색
grep -i "pattern" file.txt                 # 대소문자 무시
grep -v "pattern" file.txt                 # 패턴 제외
grep -E "pattern1|pattern2" file.txt       # OR 검색
grep -r "pattern" directory/               # 디렉토리 재귀 검색
grep -n "pattern" file.txt                 # 라인 번호 표시
grep -A 5 "pattern" file.txt               # 매칭 후 5줄 표시
grep -B 5 "pattern" file.txt               # 매칭 전 5줄 표시
grep -C 5 "pattern" file.txt               # 매칭 전후 5줄 표시
```

---

## 주요 개념 정리

### Docker 네트워크
- **bridge**: 기본 네트워크. 같은 네트워크의 컨테이너끼리 컨테이너 이름으로 통신 가능
- **host**: 컨테이너가 호스트 네트워크를 직접 사용
- **none**: 네트워크 없음

### 포트 매핑
```
-p 호스트포트:컨테이너포트
-p 3000:8080  → localhost:3000으로 접속하면 컨테이너의 8080 포트로 연결
```

### 환경변수
```bash
-e KEY=VALUE              # Docker run에서 환경변수 설정
export KEY=VALUE          # 쉘에서 환경변수 설정
printenv                  # 모든 환경변수 출력
echo $KEY                 # 특정 환경변수 출력
```

### WSL 특이사항
- `host.docker.internal`이 WSL에서 제대로 동작하지 않을 수 있음
- 해결: Docker 네트워크 사용 또는 WSL IP 직접 사용
- WSL IP 확인: `ip -4 addr show eth0`

---

## 디버깅 체크리스트

### API가 응답하지 않을 때
1. 서버가 실행 중인가? → `docker ps` 또는 `ps aux | grep uvicorn`
2. 포트가 열려있나? → `lsof -i :8000`
3. 로그 확인 → `docker logs 3vi-backend`
4. 헬스체크 → `curl http://localhost:8000/api/v1/health`

### Docker 컨테이너가 시작되지 않을 때
1. 로그 확인 → `docker logs 컨테이너명`
2. 이미지 문제인가? → `docker images`
3. 포트 충돌인가? → `lsof -i :포트번호`
4. 환경변수가 제대로 설정되었나? → `docker inspect 컨테이너명`

### 데이터베이스 연결 실패
1. PostgreSQL 컨테이너 실행 중? → `docker ps | grep postgres`
2. 헬스체크 통과? → `docker ps` (healthy 표시 확인)
3. 연결 정보 확인 → DATABASE_URL 환경변수
4. 직접 연결 테스트 → `docker exec -it 3vi-postgres psql -U secuser -d securitydb`

---

## 참고 자료

- Docker 공식 문서: https://docs.docker.com/
- Docker Compose 문서: https://docs.docker.com/compose/
- FastAPI 문서: https://fastapi.tiangolo.com/
- PostgreSQL 문서: https://www.postgresql.org/docs/

---

**작성일**: 2025-10-22
**프로젝트**: 3VI Security Scanner
**Phase**: 3 (Open WebUI 통합 완료)
