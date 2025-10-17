"""
LangGraph 간단한 PoC
보안 스캔 워크플로우를 시뮬레이션하는 기본 예제
"""

# ============================================================================
# 라이브러리 임포트
# ============================================================================
from typing import TypedDict, Annotated  # 타입 �힌트를 위한 임포트
import operator  # 리스트 연산을 위한 operator
from langgraph.graph import StateGraph, END  # LangGraph의 핵심 클래스


# ============================================================================
# 상태 정의 (State)
# ============================================================================
# LangGraph에서는 모든 노드가 공유하는 "상태(State)"를 정의합니다.
# 각 노드는 이 상태를 읽고, 수정하고, 다음 노드로 전달합니다.
class SecurityScanState(TypedDict):
    """
    보안 스캔 상태를 저장하는 구조

    TypedDict: 딕셔너리지만 각 키의 타입이 명시되어 있음
    이 상태 객체는 모든 노드 함수에서 공유됩니다.
    """
    target: str  # 스캔 대상 IP 또는 도메인 (예: "192.168.1.100")
    scan_type: str  # 스캔 타입 (예: "full_scan", "quick_scan")
    port_scan_result: list  # 포트 스캔 결과 리스트 (각 포트 정보를 딕셔너리로 저장)
    vulnerability_found: list  # 발견된 취약점 리스트
    risk_level: str  # 전체 위험도 레벨 (예: "HIGH", "MEDIUM", "LOW")
    report: str  # 최종 보고서 텍스트

    # Annotated[list, operator.add]:
    # - 이 필드는 리스트이고, 노드 간에 자동으로 합쳐집니다 (append가 아닌 extend)
    # - operator.add를 사용하면 각 노드에서 추가한 항목들이 누적됩니다
    steps: Annotated[list, operator.add]  # 실행된 단계들을 기록


# ============================================================================
# 노드 함수들 (Nodes)
# ============================================================================
# 각 노드는 다음과 같은 특징을 가집니다:
# 1. 입력: SecurityScanState 타입의 state 딕셔너리
# 2. 처리: state를 읽고 수정
# 3. 출력: 수정된 state를 반환
# 4. LangGraph가 자동으로 다음 노드에 state를 전달

# 노드 1: 입력 분석
def analyze_input(state: SecurityScanState) -> SecurityScanState:
    """
    첫 번째 단계: 사용자 입력을 분석하여 스캔 타입 결정

    Args:
        state: 현재 상태 (target 필드에 스캔 대상이 들어있음)

    Returns:
        수정된 상태 (scan_type 필드가 채워짐)
    """
    print("\n🔍 [1단계] 입력 분석 중...")
    print(f"   대상: {state['target']}")

    # 분석 로직: 여기서는 간단히 "full_scan"으로 고정
    # 실제로는 대상의 특성에 따라 스캔 타입을 동적으로 결정할 수 있습니다
    state["scan_type"] = "full_scan"

    # steps 리스트에 현재 단계 기록
    # Annotated[list, operator.add] 덕분에 자동으로 누적됩니다
    state["steps"].append("입력 분석 완료")

    print(f"   스캔 타입: {state['scan_type']}")
    return state  # 수정된 state를 반환


# 노드 2: 포트 스캔
def port_scan(state: SecurityScanState) -> SecurityScanState:
    """
    두 번째 단계: 포트 스캔 시뮬레이션

    실제 환경에서는 nmap, masscan 같은 도구를 사용하지만,
    이 PoC에서는 미리 정의된 결과를 반환합니다.

    Args:
        state: 현재 상태 (target과 scan_type이 설정되어 있음)

    Returns:
        수정된 상태 (port_scan_result 필드가 채워짐)
    """
    print("\n🔌 [2단계] 포트 스캔 중...")

    # 포트 스캔 결과 시뮬레이션
    # 실제로는 subprocess를 통해 nmap을 실행하거나 python-nmap 라이브러리 사용
    # 예: subprocess.run(["nmap", "-p-", state["target"]])
    state["port_scan_result"] = [
        {"port": 22, "status": "open", "service": "SSH"},
        {"port": 80, "status": "open", "service": "HTTP"},
        {"port": 443, "status": "open", "service": "HTTPS"},
        {"port": 3306, "status": "open", "service": "MySQL"}
    ]

    # 진행 상황 기록
    state["steps"].append("포트 스캔 완료")

    # 결과 출력
    for port_info in state["port_scan_result"]:
        print(f"   포트 {port_info['port']}: {port_info['status']} ({port_info['service']})")

    return state


# 노드 3: 취약점 분석
def vulnerability_analysis(state: SecurityScanState) -> SecurityScanState:
    """
    세 번째 단계: 포트 스캔 결과를 기반으로 취약점 분석

    각 열린 포트에 대해 알려진 취약점을 체크합니다.
    실제로는 CVE 데이터베이스를 조회하거나 전문 스캐너를 사용합니다.

    Args:
        state: 현재 상태 (port_scan_result가 채워져 있음)

    Returns:
        수정된 상태 (vulnerability_found 필드가 채워짐)
    """
    print("\n🛡️  [3단계] 취약점 분석 중...")

    # 발견된 취약점을 저장할 리스트
    vulnerabilities = []

    # 각 열린 포트를 확인하여 알려진 취약점 체크
    for port_info in state["port_scan_result"]:
        # SSH 포트(22)가 기본 포트에서 실행 중이면 취약점으로 판단
        if port_info["port"] == 22:
            vulnerabilities.append({
                "type": "Weak SSH Configuration",  # 취약점 유형
                "severity": "Medium",  # 심각도 (Critical/High/Medium/Low)
                "port": 22,
                "description": "SSH 서비스가 기본 포트에서 실행 중"
            })

        # MySQL 포트(3306)가 외부에 노출되어 있으면 위험
        elif port_info["port"] == 3306:
            vulnerabilities.append({
                "type": "Exposed Database",
                "severity": "High",  # 데이터베이스 노출은 High 위험
                "port": 3306,
                "description": "MySQL이 외부에 노출되어 있음"
            })

    # 발견된 취약점을 state에 저장
    state["vulnerability_found"] = vulnerabilities
    state["steps"].append("취약점 분석 완료")

    # 결과 출력
    print(f"   발견된 취약점: {len(vulnerabilities)}개")
    for vuln in vulnerabilities:
        print(f"   - [{vuln['severity']}] {vuln['type']}")

    return state


# 노드 4: 위험도 평가
def risk_assessment(state: SecurityScanState) -> SecurityScanState:
    """
    네 번째 단계: 발견된 취약점들을 종합하여 전체 위험도 평가

    취약점의 심각도(severity)를 기준으로 시스템 전체의 위험도를 판단합니다.

    평가 기준:
    - High 취약점이 1개 이상 → 전체 위험도 HIGH
    - Medium 취약점만 있음 → 전체 위험도 MEDIUM
    - 취약점 없음 → 전체 위험도 LOW

    Args:
        state: 현재 상태 (vulnerability_found가 채워져 있음)

    Returns:
        수정된 상태 (risk_level 필드가 채워짐)
    """
    print("\n📊 [4단계] 위험도 평가 중...")

    # 심각도별 취약점 개수 계산
    # sum() + generator expression을 사용한 간결한 카운팅
    high_count = sum(1 for v in state["vulnerability_found"] if v["severity"] == "High")
    medium_count = sum(1 for v in state["vulnerability_found"] if v["severity"] == "Medium")

    # 전체 위험도 판단 로직
    if high_count > 0:
        state["risk_level"] = "HIGH"
    elif medium_count > 0:
        state["risk_level"] = "MEDIUM"
    else:
        state["risk_level"] = "LOW"

    state["steps"].append("위험도 평가 완료")

    # 평가 결과 출력
    print(f"   전체 위험도: {state['risk_level']}")
    print(f"   (High: {high_count}, Medium: {medium_count})")

    return state


# 노드 5: 보고서 생성
def generate_report(state: SecurityScanState) -> SecurityScanState:
    """
    다섯 번째 단계: 모든 분석 결과를 종합하여 최종 보고서 생성

    지금까지 수집한 모든 정보를 읽기 쉬운 형태로 포맷팅합니다.
    실제 환경에서는 PDF, HTML, JSON 등 다양한 형식으로 출력할 수 있습니다.

    Args:
        state: 모든 정보가 채워진 최종 상태

    Returns:
        수정된 상태 (report 필드가 채워짐)
    """
    print("\n📝 [5단계] 보고서 생성 중...")

    # 보고서 헤더 작성
    report = f"""
{'='*60}
보안 스캔 보고서
{'='*60}

🎯 스캔 대상: {state['target']}
📅 스캔 타입: {state['scan_type']}

🔌 포트 스캔 결과:
"""

    # 포트 스캔 결과 추가
    for port_info in state["port_scan_result"]:
        report += f"  - 포트 {port_info['port']}: {port_info['status']} ({port_info['service']})\n"

    # 취약점 정보 추가
    report += f"\n🛡️  발견된 취약점: {len(state['vulnerability_found'])}개\n"
    for vuln in state["vulnerability_found"]:
        report += f"  - [{vuln['severity']}] {vuln['type']}\n"
        report += f"    포트: {vuln['port']}, 설명: {vuln['description']}\n"

    # 전체 위험도 추가
    report += f"\n📊 전체 위험도: {state['risk_level']}\n"

    # 실행 단계 추가
    report += f"\n✅ 실행된 단계:\n"
    for i, step in enumerate(state['steps'], 1):
        report += f"  {i}. {step}\n"

    # 보고서 푸터
    report += f"\n{'='*60}\n"

    # 생성된 보고서를 state에 저장
    state["report"] = report
    state["steps"].append("보고서 생성 완료")

    print("   보고서 생성 완료!")

    return state


# ============================================================================
# LangGraph 워크플로우 구성
# ============================================================================
def create_security_scan_graph():
    """
    보안 스캔 워크플로우 그래프 생성

    LangGraph의 핵심 개념:
    1. Node (노드): 실제 작업을 수행하는 함수
    2. Edge (엣지): 노드 간의 연결, 실행 순서를 정의
    3. State (상태): 노드 간에 공유되는 데이터

    Returns:
        컴파일된 LangGraph 애플리케이션
    """

    # 1. StateGraph 객체 생성
    # SecurityScanState를 상태 타입으로 지정
    workflow = StateGraph(SecurityScanState)

    # 2. 노드 추가
    # workflow.add_node(노드_이름, 실행할_함수)
    # 노드 이름은 문자열, 함수는 위에서 정의한 함수들
    workflow.add_node("analyze", analyze_input)  # 입력 분석 노드
    workflow.add_node("port_scan", port_scan)  # 포트 스캔 노드
    workflow.add_node("vulnerability", vulnerability_analysis)  # 취약점 분석 노드
    workflow.add_node("risk", risk_assessment)  # 위험도 평가 노드
    workflow.add_node("report", generate_report)  # 보고서 생성 노드

    # 3. 엣지 추가 (실행 흐름 정의)
    # workflow.add_edge(시작_노드, 끝_노드)
    # 순차적으로 실행되도록 연결합니다
    #
    # 흐름: analyze → port_scan → vulnerability → risk → report → END
    workflow.add_edge("analyze", "port_scan")  # 분석 후 포트 스캔
    workflow.add_edge("port_scan", "vulnerability")  # 포트 스캔 후 취약점 분석
    workflow.add_edge("vulnerability", "risk")  # 취약점 분석 후 위험도 평가
    workflow.add_edge("risk", "report")  # 위험도 평가 후 보고서 생성
    workflow.add_edge("report", END)  # 보고서 생성 후 종료 (END는 특수 노드)

    # 4. 시작점 설정
    # 워크플로우가 시작할 첫 번째 노드 지정
    workflow.set_entry_point("analyze")

    # 5. 그래프 컴파일
    # 정의된 워크플로우를 실행 가능한 형태로 변환
    # 컴파일 후에는 .invoke()로 실행할 수 있습니다
    return workflow.compile()


# ============================================================================
# 실행 함수
# ============================================================================
def run_poc():
    """
    PoC 실행 함수

    전체 워크플로우를 실행하고 결과를 출력합니다.

    실행 순서:
    1. 그래프 생성 (워크플로우 정의)
    2. 초기 상태 설정 (빈 값들로 초기화)
    3. 그래프 실행 (invoke)
    4. 결과 출력
    """
    print("=" * 60)
    print("🚀 LangGraph 보안 스캔 PoC 시작")
    print("=" * 60)

    # 1. 워크플로우 그래프 생성
    app = create_security_scan_graph()

    # 2. 초기 상태 설정
    # SecurityScanState의 모든 필드를 초기화합니다
    # target만 값을 넣고, 나머지는 빈 값으로 시작
    # 각 노드가 실행되면서 점점 채워집니다
    initial_state = {
        "target": "192.168.1.100",  # 스캔할 대상 (여기만 미리 설정)
        "scan_type": "",  # 1단계에서 채워짐
        "port_scan_result": [],  # 2단계에서 채워짐
        "vulnerability_found": [],  # 3단계에서 채워짐
        "risk_level": "",  # 4단계에서 채워짐
        "report": "",  # 5단계에서 채워짐
        "steps": []  # 각 단계마다 자동으로 누적됨
    }

    # 3. 그래프 실행
    # invoke()는 초기 상태를 받아서 전체 워크플로우를 실행하고
    # 최종 상태를 반환합니다
    result = app.invoke(initial_state)

    # 4. 최종 결과 출력
    print("\n" + "=" * 60)
    print("✅ 스캔 완료!")
    print("=" * 60)
    print(result["report"])  # 최종 보고서 출력

    return result  # 전체 결과 반환 (필요시 추가 처리 가능)


# ============================================================================
# 메인 실행부
# ============================================================================
if __name__ == "__main__":
    # 이 파일이 직접 실행될 때만 run_poc() 호출
    # import 되어 사용될 때는 실행되지 않음
    run_poc()
