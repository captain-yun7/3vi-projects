"""
LangGraph 고급 PoC - AI 기능 포함
실제 OpenAI API를 사용하여 취약점 분석 및 해결 방안 제시
"""

import os
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 상태 정의
class AdvancedSecurityScanState(TypedDict):
    """고급 보안 스캔 상태"""
    target: str
    scan_type: str
    port_scan_result: list
    vulnerability_found: list
    risk_level: str
    ai_analysis: str  # AI가 생성한 분석
    recommendations: str  # AI가 제시한 해결 방안
    report: str
    steps: Annotated[list, operator.add]


# AI 모델 초기화
def get_llm():
    """OpenAI LLM 가져오기"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=0.7)


# 노드 1: 입력 분석
def analyze_input(state: AdvancedSecurityScanState) -> AdvancedSecurityScanState:
    """사용자 입력을 분석하여 스캔 타입 결정"""
    print("\n🔍 [1단계] 입력 분석 중...")
    print(f"   대상: {state['target']}")

    state["scan_type"] = "comprehensive_scan"
    state["steps"].append("입력 분석 완료")

    print(f"   스캔 타입: {state['scan_type']}")
    return state


# 노드 2: 실제 포트 스캔 (python-nmap 사용)
def port_scan(state: AdvancedSecurityScanState) -> AdvancedSecurityScanState:
    """
    실제 포트 스캔 (python-nmap 사용)

    nmap이 설치되어 있지 않거나 오류 발생 시 시뮬레이션 모드로 전환
    """
    print("\n🔌 [2단계] 포트 스캔 중...")

    try:
        import nmap

        # nmap 스캐너 생성
        nm = nmap.PortScanner()

        target = state['target']
        ports = '21,22,80,443,3306,8080'  # 스캔할 포트

        print(f"   대상: {target}")
        print(f"   포트: {ports}")
        print(f"   방식: nmap 실제 스캔")
        print(f"   (스캔에 10-30초 소요될 수 있습니다...)")

        # 실제 nmap 스캔 실행
        # -sV: 서비스 버전 감지
        # -T4: 빠른 스캔
        # --open: 열린 포트만 표시
        nm.scan(
            hosts=target,
            ports=ports,
            arguments='-sV -T4 --open'
        )

        # 결과 파싱
        scan_results = []
        for host in nm.all_hosts():
            if nm[host].state() == 'up':
                for proto in nm[host].all_protocols():
                    port_list = sorted(nm[host][proto].keys())
                    for port in port_list:
                        port_info = nm[host][proto][port]

                        if port_info['state'] == 'open':
                            scan_results.append({
                                "port": port,
                                "status": "open",
                                "service": port_info.get('name', 'unknown'),
                                "version": f"{port_info.get('product', '')} {port_info.get('version', '')}".strip()
                            })

        if scan_results:
            state["port_scan_result"] = scan_results
            state["steps"].append("포트 스캔 완료 (nmap 실제 스캔)")
            print(f"\n   ✅ 실제 스캔 완료! {len(scan_results)}개 포트 발견")
        else:
            # 열린 포트가 없거나 호스트가 다운된 경우
            print(f"\n   ⚠️  열린 포트를 찾을 수 없습니다.")
            print(f"   호스트가 다운되어 있거나 방화벽이 막고 있을 수 있습니다.")
            print(f"   시뮬레이션 데이터로 전환합니다...")

            # 시뮬레이션 데이터 사용
            state["port_scan_result"] = [
                {"port": 22, "status": "open", "service": "SSH", "version": "OpenSSH 7.4"},
                {"port": 80, "status": "open", "service": "HTTP", "version": "Apache 2.4.6"}
            ]
            state["steps"].append("포트 스캔 완료 (시뮬레이션 - 호스트 응답 없음)")

    except ImportError:
        print(f"   ⚠️  python-nmap이 설치되지 않았습니다.")
        print(f"   설치: pip install python-nmap")
        print(f"   시뮬레이션 모드로 전환합니다...\n")

        # 시뮬레이션 데이터
        state["port_scan_result"] = [
            {"port": 21, "status": "open", "service": "FTP", "version": "vsftpd 2.3.4"},
            {"port": 22, "status": "open", "service": "SSH", "version": "OpenSSH 7.4"},
            {"port": 80, "status": "open", "service": "HTTP", "version": "Apache 2.4.6"},
            {"port": 443, "status": "open", "service": "HTTPS", "version": "Apache 2.4.6"},
            {"port": 3306, "status": "open", "service": "MySQL", "version": "5.7.33"},
            {"port": 8080, "status": "open", "service": "HTTP-Proxy", "version": "Tomcat 8.5"}
        ]
        state["steps"].append("포트 스캔 완료 (시뮬레이션 - nmap 미설치)")

    except nmap.PortScannerError as e:
        print(f"   ❌ nmap 오류: {e}")
        print(f"   nmap이 설치되어 있나요? sudo apt install nmap")
        print(f"   시뮬레이션 모드로 전환합니다...\n")

        # 시뮬레이션 데이터
        state["port_scan_result"] = [
            {"port": 22, "status": "open", "service": "SSH", "version": "OpenSSH 7.4"},
            {"port": 80, "status": "open", "service": "HTTP", "version": "Apache 2.4.6"}
        ]
        state["steps"].append("포트 스캔 완료 (시뮬레이션 - nmap 오류)")

    except Exception as e:
        print(f"   ❌ 스캔 오류: {e}")
        print(f"   시뮬레이션 모드로 전환합니다...\n")

        # 시뮬레이션 데이터
        state["port_scan_result"] = [
            {"port": 22, "status": "open", "service": "SSH", "version": "OpenSSH 7.4"},
            {"port": 80, "status": "open", "service": "HTTP", "version": "Apache 2.4.6"}
        ]
        state["steps"].append("포트 스캔 완료 (시뮬레이션 - 오류 발생)")

    # 결과 출력
    print(f"\n   발견된 포트:")
    for port_info in state["port_scan_result"]:
        version_str = f" - {port_info['version']}" if port_info['version'] else ""
        print(f"   포트 {port_info['port']}: {port_info['status']} ({port_info['service']}{version_str})")

    return state


# 노드 3: 취약점 분석
def vulnerability_analysis(state: AdvancedSecurityScanState) -> AdvancedSecurityScanState:
    """취약점 분석 시뮬레이션"""
    print("\n🛡️  [3단계] 취약점 분석 중...")

    vulnerabilities = []

    for port_info in state["port_scan_result"]:
        if port_info["port"] == 21 and "vsftpd 2.3.4" in port_info["version"]:
            vulnerabilities.append({
                "type": "Backdoor Command Execution",
                "severity": "Critical",
                "port": 21,
                "service": "FTP",
                "cve": "CVE-2011-2523",
                "description": "vsftpd 2.3.4에 백도어가 존재하여 원격 코드 실행 가능"
            })
        elif port_info["port"] == 22:
            vulnerabilities.append({
                "type": "SSH Brute Force Risk",
                "severity": "Medium",
                "port": 22,
                "service": "SSH",
                "cve": "N/A",
                "description": "SSH 서비스가 기본 포트에서 실행되어 무차별 대입 공격에 노출"
            })
        elif port_info["port"] == 3306:
            vulnerabilities.append({
                "type": "Exposed Database Service",
                "severity": "High",
                "port": 3306,
                "service": "MySQL",
                "cve": "N/A",
                "description": "MySQL이 외부 네트워크에 노출되어 있음"
            })
        elif port_info["port"] == 8080:
            vulnerabilities.append({
                "type": "Known Tomcat Vulnerabilities",
                "severity": "High",
                "port": 8080,
                "service": "Tomcat",
                "cve": "Multiple",
                "description": "Tomcat 8.5 버전에 알려진 취약점 존재 가능"
            })

    state["vulnerability_found"] = vulnerabilities
    state["steps"].append("취약점 분석 완료")

    print(f"   발견된 취약점: {len(vulnerabilities)}개")
    for vuln in vulnerabilities:
        print(f"   - [{vuln['severity']}] {vuln['type']} (포트 {vuln['port']})")

    return state


# 노드 4: AI 기반 위험도 평가
def ai_risk_assessment(state: AdvancedSecurityScanState) -> AdvancedSecurityScanState:
    """AI를 활용한 위험도 평가"""
    print("\n🤖 [4단계] AI 기반 위험도 평가 중...")

    try:
        llm = get_llm()

        # AI에게 취약점 정보 전달
        vulnerabilities_text = "\n".join([
            f"- [{v['severity']}] {v['type']}: {v['description']} (포트 {v['port']})"
            for v in state["vulnerability_found"]
        ])

        prompt = f"""
다음은 보안 스캔 결과입니다:

대상 시스템: {state['target']}
발견된 취약점:
{vulnerabilities_text}

위 취약점들을 종합적으로 분석하여:
1. 전체 위험도 수준 (Critical/High/Medium/Low)
2. 가장 위험한 취약점 3가지
3. 공격자가 이 취약점들을 어떻게 악용할 수 있는지

간결하게 분석해주세요.
"""

        response = llm.invoke(prompt)
        state["ai_analysis"] = response.content

        # 위험도 결정 (AI 응답 기반)
        if "Critical" in response.content or any(v["severity"] == "Critical" for v in state["vulnerability_found"]):
            state["risk_level"] = "CRITICAL"
        elif any(v["severity"] == "High" for v in state["vulnerability_found"]):
            state["risk_level"] = "HIGH"
        else:
            state["risk_level"] = "MEDIUM"

        state["steps"].append("AI 위험도 평가 완료")

        print(f"   전체 위험도: {state['risk_level']}")
        print(f"   AI 분석 완료 ({len(response.content)} 문자)")

    except Exception as e:
        print(f"   ⚠️  AI 분석 실패: {e}")
        state["ai_analysis"] = "AI 분석을 사용할 수 없습니다."
        state["risk_level"] = "HIGH"
        state["steps"].append("AI 위험도 평가 실패 (기본 평가 사용)")

    return state


# 노드 5: AI 기반 해결 방안 제시
def ai_recommendations(state: AdvancedSecurityScanState) -> AdvancedSecurityScanState:
    """AI를 활용한 해결 방안 제시"""
    print("\n💡 [5단계] AI 기반 해결 방안 생성 중...")

    try:
        llm = get_llm()

        vulnerabilities_text = "\n".join([
            f"- [{v['severity']}] {v['type']} (포트 {v['port']}): {v['description']}"
            for v in state["vulnerability_found"]
        ])

        prompt = f"""
다음 취약점들에 대한 구체적이고 실행 가능한 해결 방안을 제시해주세요:

{vulnerabilities_text}

각 취약점별로:
1. 즉시 조치할 사항
2. 중장기 개선 방안
3. 예방 조치

우선순위와 함께 실무에서 바로 적용 가능한 방법으로 작성해주세요.
"""

        response = llm.invoke(prompt)
        state["recommendations"] = response.content
        state["steps"].append("AI 해결 방안 생성 완료")

        print(f"   해결 방안 생성 완료 ({len(response.content)} 문자)")

    except Exception as e:
        print(f"   ⚠️  해결 방안 생성 실패: {e}")
        state["recommendations"] = "AI 기반 해결 방안을 생성할 수 없습니다."
        state["steps"].append("AI 해결 방안 생성 실패")

    return state


# 노드 6: 최종 보고서 생성
def generate_report(state: AdvancedSecurityScanState) -> AdvancedSecurityScanState:
    """최종 보고서 생성"""
    print("\n📝 [6단계] 최종 보고서 생성 중...")

    report = f"""
{'='*70}
🔒 보안 스캔 상세 보고서 (AI 분석 포함)
{'='*70}

🎯 스캔 대상: {state['target']}
📅 스캔 타입: {state['scan_type']}
⚠️  전체 위험도: {state['risk_level']}

{'='*70}
🔌 포트 스캔 결과
{'='*70}
"""
    for port_info in state["port_scan_result"]:
        report += f"  포트 {port_info['port']:5d}: {port_info['status']:6s} | {port_info['service']:15s} | {port_info['version']}\n"

    report += f"""
{'='*70}
🛡️  발견된 취약점: {len(state['vulnerability_found'])}개
{'='*70}
"""
    for i, vuln in enumerate(state["vulnerability_found"], 1):
        report += f"""
[취약점 {i}] {vuln['type']}
  심각도: {vuln['severity']}
  포트: {vuln['port']} ({vuln['service']})
  CVE: {vuln['cve']}
  설명: {vuln['description']}
"""

    report += f"""
{'='*70}
🤖 AI 기반 위험도 분석
{'='*70}
{state['ai_analysis']}

{'='*70}
💡 AI 추천 해결 방안
{'='*70}
{state['recommendations']}

{'='*70}
✅ 실행된 단계
{'='*70}
"""
    for i, step in enumerate(state['steps'], 1):
        report += f"  {i}. {step}\n"

    report += f"\n{'='*70}\n"

    state["report"] = report
    state["steps"].append("최종 보고서 생성 완료")

    print("   보고서 생성 완료!")

    return state


# LangGraph 구성
def create_advanced_graph():
    """고급 보안 스캔 워크플로우 그래프 생성"""

    workflow = StateGraph(AdvancedSecurityScanState)

    # 노드 추가
    workflow.add_node("analyze", analyze_input)
    workflow.add_node("port_scan", port_scan)
    workflow.add_node("vulnerability", vulnerability_analysis)
    workflow.add_node("ai_risk", ai_risk_assessment)
    workflow.add_node("ai_recommendations", ai_recommendations)
    workflow.add_node("report", generate_report)

    # 엣지 추가 (흐름 정의)
    workflow.add_edge("analyze", "port_scan")
    workflow.add_edge("port_scan", "vulnerability")
    workflow.add_edge("vulnerability", "ai_risk")
    workflow.add_edge("ai_risk", "ai_recommendations")
    workflow.add_edge("ai_recommendations", "report")
    workflow.add_edge("report", END)

    # 시작점 설정
    workflow.set_entry_point("analyze")

    return workflow.compile()


# 실행 함수
def run_advanced_poc():
    """고급 PoC 실행"""
    print("=" * 70)
    print("🚀 LangGraph 고급 보안 스캔 PoC 시작 (AI 기능 포함)")
    print("=" * 70)

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일을 생성하고 API 키를 설정하세요.")
        print("   AI 기능 없이 기본 스캔만 실행됩니다.\n")
        return

    # 그래프 생성
    app = create_advanced_graph()

    # 초기 상태 설정
    initial_state = {
        "target": "192.168.1.100",
        "scan_type": "",
        "port_scan_result": [],
        "vulnerability_found": [],
        "risk_level": "",
        "ai_analysis": "",
        "recommendations": "",
        "report": "",
        "steps": []
    }

    # 실행
    result = app.invoke(initial_state)

    # 최종 보고서 출력
    print("\n" + "=" * 70)
    print("✅ 스캔 완료!")
    print("=" * 70)
    print(result["report"])

    # 보고서를 파일로 저장
    report_path = "/home/k8s-admin/3vi-v1/poc/scan_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(result["report"])
    print(f"\n💾 보고서가 저장되었습니다: {report_path}")

    return result


if __name__ == "__main__":
    run_advanced_poc()
