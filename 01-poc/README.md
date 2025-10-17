# LangGraph PoC - 보안 스캔 자동화

LangGraph를 사용하여 보안 스캔 워크플로우를 자동화하는 개념 증명(PoC)

---

## 파일 구조

```
poc/
├── requirements.txt    # 필수 라이브러리 목록
├── simple_poc.py       # 간단한 예제 (AI 없음)
├── advanced_poc.py     # 고급 예제 (OpenAI API 사용)
├── .env                # API 키 설정
└── README.md           # 이 문서
```

---

## 설치 및 실행

### 1. 가상환경 생성 및 활성화
```bash
cd /home/k8s-admin/3vi-v1
python3 -m venv venv
source venv/bin/activate
```

### 2. 시스템 패키지 설치 (nmap)
```bash
sudo apt update
sudo apt install nmap
```

### 3. 라이브러리 설치
```bash
pip install -r poc/requirements.txt
```

### 4. API 키 설정
`poc/.env` 파일에 OpenAI API 키를 설정하세요:
```
OPENAI_API_KEY=your-api-key-here
```

### 5. 실행

**간단한 예제 (AI 없음, 시뮬레이션)**
```bash
python3 poc/simple_poc.py
```

**고급 예제 (AI + 실제 nmap 포트 스캔)**
```bash
python3 poc/advanced_poc.py
```
> advanced_poc.py는 실제 nmap을 사용하여 포트 스캔을 수행합니다.
> 대상: 127.0.0.1 (localhost)를 스캔하려면 코드 수정 필요

### 가상환경 종료
```bash
deactivate
```

---

## 워크플로우

### Simple PoC (5단계)
```
입력 분석 → 포트 스캔 → 취약점 분석 → 위험도 평가 → 보고서 생성
```

### Advanced PoC (6단계)
```
입력 분석 → 실제 nmap 포트 스캔 → 취약점 분석 → AI 위험도 평가 → AI 해결방안 → 보고서 생성
```
**특징:**
- 실제 python-nmap을 사용한 포트 스캔
- OpenAI API를 통한 AI 분석
- nmap 미설치 시 자동으로 시뮬레이션 모드로 전환

---
