# 모의해킹 기능 구현 제약사항 분석

## 개요
실제 모의해킹 시스템을 구현하는 데 있어서 법적, 기술적, 윤리적 제약사항을 분석하고 대응 방안을 수립합니다.

---

## 1. 법적 제약사항

### 1.1 정보통신망법 위반 가능성

#### 제약사항
**정보통신망 이용촉진 및 정보보호 등에 관한 법률** 제48조 (정보통신망 침해행위 등의 금지)

> 누구든지 정당한 접근권한 없이 또는 허용된 접근권한을 초과하여 정보통신망에 침입하여서는 아니 된다.

**위반 시 처벌**: 5년 이하의 징역 또는 5천만원 이하의 벌금

#### 해당 기능
- 무단 포트 스캔
- 취약점 스캔
- 패스워드 크래킹
- SQL Injection 테스트
- XSS 공격 시뮬레이션

#### 대응 방안
1. **명시적 허가**:
   - 스캔 대상에 대한 서면 승인 필요
   - 화이트리스트 기반 대상 제한

2. **제한적 스캔**:
   - 자체 시스템만 스캔 (localhost, 사설 IP)
   - 프로덕션 환경 제외

---

### 1.2 개인정보보호법 위반

#### 제약사항
스캔 과정에서 수집된 정보가 개인정보에 해당할 경우 **개인정보보호법** 위반 가능

#### 해당 정보
- 사용자 계정 정보
- 이메일 주소
- 로그 파일 내 개인정보

#### 대응 방안
1. **익명화**: 수집된 데이터의 개인정보 마스킹
2. **최소 수집**: 필요한 정보만 수집
3. **즉시 삭제**: 분석 완료 후 즉시 삭제

---

### 1.3 악성코드 배포 금지

#### 제약사항
**정보통신망법** 제48조의2 (악성프로그램 전달·유포 금지)

> 누구든지 악성프로그램을 전달 또는 유포하여서는 아니 된다.

#### 대응 방안
- 실제 악성코드 사용 금지
- 시뮬레이션 코드만 사용
- 격리된 환경(샌드박스)에서만 실행

---

## 2. 기술적 제약사항

### 2.1 네트워크 방화벽

#### 제약사항
- 클라우드 환경의 아웃바운드 스캔 차단
- 방화벽 정책에 의한 스캔 차단
- ISP의 포트 스캔 감지 및 차단

#### 영향
- 외부 네트워크 스캔 불가
- 특정 포트 스캔 제한

#### 대응 방안
1. **화이트리스트 네트워크**:
   ```python
   ALLOWED_NETWORKS = [
       "127.0.0.1",       # localhost
       "192.168.0.0/16",  # 사설 IP
       "10.0.0.0/8",      # 사설 IP
   ]
   ```

2. **VPN/Proxy 사용**: 제한적으로 허용된 경로만 사용

---

### 2.2 권한 부족

#### 제약사항
일부 스캔 기법은 root 권한 필요:
- **SYN 스캔** (`nmap -sS`)
- **Raw 소켓** 사용
- **패킷 캡처**

#### 영향
- 일반 사용자 권한으로는 제한적 스캔만 가능
- nmap의 고급 기능 사용 불가

#### 대응 방안
1. **비권한 스캔 사용**:
   ```bash
   # SYN 스캔 대신 Connect 스캔
   nmap -sT target
   ```

2. **Capabilities 부여** (개발 환경만):
   ```bash
   sudo setcap cap_net_raw,cap_net_admin+eip $(which nmap)
   ```

3. **대안 도구 사용**:
   - `masscan`: 빠른 포트 스캔 (권한 필요 없음)
   - Python socket 라이브러리: 기본 연결 테스트

---

### 2.3 성능 제약

#### 제약사항
- **전체 포트 스캔**: 65,535개 포트 스캔 시 수십 분 소요
- **타임아웃**: API 타임아웃 (보통 30초~2분)
- **리소스 부족**: CPU, 메모리 제한

#### 영향
- 실시간 스캔 불가
- 전체 스캔 완료 전 타임아웃

#### 대응 방안
1. **스캔 범위 제한**:
   ```python
   SCAN_TYPES = {
       "quick": "1-1000",      # 주요 포트만 (1초 이내)
       "standard": "1-10000",  # 일반 포트 (10초 이내)
       "full": "1-65535",      # 전체 포트 (비동기 처리)
   }
   ```

2. **비동기 처리**:
   - BackgroundTasks 또는 Celery 사용
   - 진행 상황 WebSocket으로 전송

3. **병렬 처리**:
   ```bash
   nmap -T4 --min-parallelism 100 target
   ```

---

### 2.4 도구 설치 제약

#### 제약사항
- **nmap**: 일부 환경에서 설치 불가 (컨테이너, 제한된 권한)
- **의존성 충돌**: 시스템 패키지와 충돌
- **클라우드 제약**: Heroku, AWS Lambda 등에서 커스텀 바이너리 제한

#### 영향
- nmap 사용 불가 시 스캔 불가능
- 배포 환경 제한

#### 대응 방안
1. **Fallback 모드**:
   ```python
   try:
       import nmap
       scanner = nmap.PortScanner()
   except ImportError:
       logger.warning("nmap not available, using simulation mode")
       scanner = SimulatedScanner()
   ```

2. **Python 네이티브 스캔**:
   ```python
   import socket

   def scan_port(host, port, timeout=1):
       try:
           sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           sock.settimeout(timeout)
           result = sock.connect_ex((host, port))
           sock.close()
           return result == 0  # 0이면 열림
       except:
           return False
   ```

---

## 3. AI/LLM 제약사항

### 3.1 할루시네이션 (Hallucination)

#### 제약사항
OpenAI 모델이 존재하지 않는 취약점이나 CVE를 생성할 수 있음

#### 예시
```json
{
  "cve": "CVE-2024-99999",  // 존재하지 않는 CVE
  "description": "이 포트는 원격 코드 실행 취약점이 있습니다." // 근거 없음
}
```

#### 대응 방안
1. **CVE 데이터베이스 검증**:
   ```python
   def verify_cve(cve_id: str) -> bool:
       """NVD API로 CVE 존재 여부 확인"""
       response = requests.get(f"https://services.nvd.nist.gov/rest/json/cve/1.0/{cve_id}")
       return response.status_code == 200
   ```

2. **교차 검증**:
   - AI 분석 결과 + 실제 스캔 결과 비교
   - 휴리스틱 검증

3. **신뢰도 점수**:
   ```json
   {
     "vulnerability": "SQL Injection",
     "confidence": 0.85,  // AI 신뢰도
     "verified": false    // 실제 검증 여부
   }
   ```

---

### 3.2 API 비용

#### 제약사항
- OpenAI API는 토큰당 과금
- 대량 스캔 시 비용 급증

#### 비용 예시
- GPT-4o-mini: $0.150 / 1M input tokens, $0.600 / 1M output tokens
- 스캔 1회당 평균 2,000 tokens 사용
- 1,000회 스캔 시 약 $1.50

#### 대응 방안
1. **캐싱**:
   ```python
   @lru_cache(maxsize=1000)
   def analyze_port_vulnerability(port: int, service: str) -> dict:
       # 동일한 포트/서비스 조합은 캐시 사용
       return openai_client.analyze(...)
   ```

2. **토큰 제한**:
   ```python
   response = openai_client.chat.completions.create(
       model="gpt-4o-mini",
       messages=[...],
       max_tokens=500,  # 출력 토큰 제한
   )
   ```

3. **선택적 AI 사용**:
   - 기본 분석은 휴리스틱
   - 복잡한 분석만 AI 사용

---

### 3.3 응답 시간

#### 제약사항
- OpenAI API 호출: 평균 2-5초
- 동기 호출 시 전체 스캔 지연

#### 대응 방안
1. **비동기 호출**:
   ```python
   async def analyze_async(prompt: str):
       response = await openai_client.async_chat(...)
       return response
   ```

2. **병렬 처리**:
   ```python
   tasks = [analyze_async(prompt) for prompt in prompts]
   results = await asyncio.gather(*tasks)
   ```

---

## 4. 윤리적 제약사항

### 4.1 책임 있는 공개 (Responsible Disclosure)

#### 원칙
발견된 취약점을 즉시 공개하지 않고 벤더에게 먼저 보고

#### 대응 방안
- 취약점 정보 암호화 저장
- 접근 권한 제한
- 자동 공개 금지

---

### 4.2 무차별 스캔 금지

#### 원칙
인터넷 전체를 무차별적으로 스캔하는 행위 금지

#### 대응 방안
- IP 범위 제한
- Rate limiting
- Shodan, Censys 등 기존 데이터 활용

---

## 5. 제약사항 요약표

| 제약사항 | 영향도 | 대응 방안 | 구현 우선순위 |
|---------|--------|---------|------------|
| 정보통신망법 위반 | 높음 | 화이트리스트, 명시적 허가 | High |
| 네트워크 방화벽 | 높음 | 사설 IP만 스캔 | High |
| root 권한 부족 | 중간 | Connect 스캔 사용 | Medium |
| 성능 제약 (타임아웃) | 높음 | 비동기 처리, 범위 제한 | High |
| nmap 미설치 | 중간 | Fallback 모드 | High |
| AI 할루시네이션 | 중간 | CVE 검증 | Medium |
| API 비용 | 낮음 | 캐싱, 토큰 제한 | Low |
| 응답 시간 | 중간 | 병렬 처리 | Medium |

---

## 6. 구현 권장사항

### 반드시 구현 (High Priority)
1. 화이트리스트 기반 대상 검증
2. 비동기 스캔 처리
3. 시뮬레이션 모드 (nmap 미설치 시)
4. 법적 고지문 (Terms of Service)

### 권장 구현 (Medium Priority)
5. CVE 검증 시스템
6. AI 신뢰도 점수
7. 캐싱 메커니즘

### 선택 구현 (Low Priority)
8. 비용 모니터링 대시보드
9. Rate limiting
10. 샌드박스 환경

---

**작성일**: 2025-10-21
**작성자**: 윤지수
**버전**: 1.0
