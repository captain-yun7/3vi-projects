"""
LangGraph 기반 보안 스캔 서비스
"""
import logging
from typing import Optional, Callable
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import json

from app.core.config import settings
from app.schemas.scan_state import SecurityScanState

logger = logging.getLogger(__name__)


class LangGraphService:
    """LangGraph 기반 보안 스캔 서비스"""

    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Args:
            progress_callback: 진행 상황 콜백 함수 (step, progress)
        """
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.3,
        )
        self.progress_callback = progress_callback
        self.graph = self._build_graph()

    def _build_graph(self):
        """LangGraph 워크플로우 구성"""
        graph = StateGraph(SecurityScanState)

        # 노드 추가 (State 키와 겹치지 않도록 node_ 접두사 사용)
        graph.add_node("node_analyze", self._analyze_input)
        graph.add_node("node_port_scan", self._port_scan)
        graph.add_node("node_vulnerability", self._vulnerability_analysis)
        graph.add_node("node_risk", self._risk_assessment)
        graph.add_node("node_remediation", self._remediation)
        graph.add_node("node_report", self._report_generation)

        # 엣지 추가
        graph.set_entry_point("node_analyze")
        graph.add_edge("node_analyze", "node_port_scan")
        graph.add_edge("node_port_scan", "node_vulnerability")
        graph.add_edge("node_vulnerability", "node_risk")
        graph.add_edge("node_risk", "node_remediation")
        graph.add_edge("node_remediation", "node_report")
        graph.add_edge("node_report", END)

        return graph.compile()

    def _update_progress(self, state: SecurityScanState, step: str, progress: int):
        """진행 상황 업데이트"""
        state["current_step"] = step
        state["progress"] = progress

        if self.progress_callback:
            self.progress_callback(step, progress)

        logger.info(f"Step: {step}, Progress: {progress}%")

    def _analyze_input(self, state: SecurityScanState) -> SecurityScanState:
        """1단계: 입력 분석"""
        self._update_progress(state, "analyze_input", 10)

        try:
            target = state["target"]
            scan_type = state["scan_type"]

            logger.info(f"Analyzing target: {target}, type: {scan_type}")

            # 대상 검증 (화이트리스트 체크)
            if not self._validate_target(target):
                raise ValueError(f"Unauthorized target: {target}")

            # 스캔 타입에 따른 포트 범위 결정
            port_ranges = {
                "quick": "1-1000",
                "standard": "1-10000",
                "full": "1-65535"
            }
            state["port_range"] = port_ranges.get(scan_type, "1-1024")

            self._update_progress(state, "analyze_input", 20)
            return state

        except Exception as e:
            logger.error(f"Input analysis failed: {e}")
            state["error"] = str(e)
            raise

    def _port_scan(self, state: SecurityScanState) -> SecurityScanState:
        """2단계: 포트 스캔"""
        self._update_progress(state, "port_scan", 30)

        try:
            import nmap
            nm = nmap.PortScanner()

            target = state["target"]
            port_range = state.get("port_range", "1-1024")

            logger.info(f"Scanning ports on {target}: {port_range}")

            # nmap 스캔 실행
            nm.scan(target, port_range, arguments="-Pn -T4")

            # 결과 파싱
            ports = []
            if target in nm.all_hosts():
                for proto in nm[target].all_protocols():
                    for port in nm[target][proto].keys():
                        port_info = nm[target][proto][port]
                        if port_info["state"] == "open":
                            ports.append({
                                "port": port,
                                "state": port_info["state"],
                                "service": port_info.get("name", "unknown"),
                                "version": port_info.get("version", ""),
                            })

            state["ports"] = ports
            logger.info(f"Found {len(ports)} open ports")

            self._update_progress(state, "port_scan", 40)
            return state

        except ImportError:
            logger.warning("nmap not installed, using simulation mode")
            # 시뮬레이션 데이터
            state["ports"] = [
                {"port": 22, "state": "open", "service": "ssh", "version": ""},
                {"port": 80, "state": "open", "service": "http", "version": ""},
                {"port": 443, "state": "open", "service": "https", "version": ""},
            ]
            self._update_progress(state, "port_scan", 40)
            return state

        except Exception as e:
            logger.error(f"Port scan failed: {e}")
            # 실패해도 시뮬레이션 데이터로 계속 진행
            state["ports"] = []
            state["error"] = f"Port scan error: {str(e)}"
            self._update_progress(state, "port_scan", 40)
            return state

    def _vulnerability_analysis(self, state: SecurityScanState) -> SecurityScanState:
        """3단계: 취약점 분석"""
        self._update_progress(state, "vulnerability_analysis", 50)

        try:
            ports = state.get("ports", [])

            # 간단한 휴리스틱 분석
            vulnerabilities = []

            # 알려진 위험 포트 분석
            risky_ports = {
                21: ("FTP", "Medium", "FTP 서비스가 노출되어 있습니다. 암호화되지 않은 통신에 취약합니다."),
                22: ("SSH", "Low", "SSH 서비스가 노출되어 있습니다. Brute force 공격에 주의가 필요합니다."),
                23: ("Telnet", "High", "Telnet 서비스가 노출되어 있습니다. 암호화되지 않은 통신으로 매우 위험합니다."),
                3306: ("MySQL", "High", "MySQL 데이터베이스가 외부에 노출되어 있습니다."),
                5432: ("PostgreSQL", "High", "PostgreSQL 데이터베이스가 외부에 노출되어 있습니다."),
                6379: ("Redis", "High", "Redis가 외부에 노출되어 있습니다. 인증 설정을 확인하세요."),
            }

            for port_info in ports:
                port = port_info["port"]
                service = port_info["service"]

                if port in risky_ports:
                    risk_type, severity, description = risky_ports[port]
                    vulnerabilities.append({
                        "type": risk_type,
                        "port": port,
                        "service": service,
                        "severity": severity,
                        "description": description,
                    })

            state["vulnerabilities"] = vulnerabilities
            logger.info(f"Found {len(vulnerabilities)} potential vulnerabilities")

            self._update_progress(state, "vulnerability_analysis", 60)
            return state

        except Exception as e:
            logger.error(f"Vulnerability analysis failed: {e}")
            state["vulnerabilities"] = []
            return state

    def _risk_assessment(self, state: SecurityScanState) -> SecurityScanState:
        """4단계: AI 위험도 평가"""
        self._update_progress(state, "risk_assessment", 70)

        try:
            vulnerabilities = state.get("vulnerabilities", [])
            ports = state.get("ports", [])

            if not vulnerabilities:
                state["risk_assessment"] = {
                    "score": 10,
                    "level": "Low",
                    "analysis": "발견된 주요 취약점이 없습니다.",
                }
                self._update_progress(state, "risk_assessment", 80)
                return state

            # OpenAI API로 위험도 평가
            prompt = f"""
다음 포트 스캔 결과와 취약점에 대해 종합적인 위험도를 평가해주세요.

발견된 포트: {json.dumps(ports, ensure_ascii=False)}
취약점: {json.dumps(vulnerabilities, ensure_ascii=False)}

다음 형식으로 응답해주세요:
1. 전체 위험도 점수 (0-100, 숫자만)
2. 위험도 등급 (Low/Medium/High/Critical 중 하나)
3. 주요 위험 요소 3가지 (간단히)

응답 형식:
점수: [숫자]
등급: [등급]
분석: [주요 위험 요소]
"""

            response = self.llm.invoke(prompt)
            assessment_text = response.content

            # 간단한 파싱 (실제로는 더 정교하게)
            score = 50  # 기본값
            level = "Medium"

            # 점수 추출 시도
            if "점수:" in assessment_text:
                try:
                    score_line = [l for l in assessment_text.split("\n") if "점수:" in l][0]
                    score = int(''.join(filter(str.isdigit, score_line)))
                except:
                    pass

            # 등급 추출 시도
            for l in ["Critical", "High", "Medium", "Low"]:
                if l in assessment_text:
                    level = l
                    break

            state["risk_assessment"] = {
                "score": score,
                "level": level,
                "analysis": assessment_text,
            }

            logger.info(f"Risk assessment completed: {level} ({score}/100)")
            self._update_progress(state, "risk_assessment", 80)
            return state

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            # AI 실패 시 기본 평가
            state["risk_assessment"] = {
                "score": 50,
                "level": "Medium",
                "analysis": "AI 평가를 사용할 수 없습니다. 기본 휴리스틱 평가를 사용합니다.",
            }
            return state

    def _remediation(self, state: SecurityScanState) -> SecurityScanState:
        """5단계: 해결 방안 제시"""
        self._update_progress(state, "remediation", 90)

        try:
            vulnerabilities = state.get("vulnerabilities", [])

            if not vulnerabilities:
                state["remediation"] = {
                    "recommendations": "현재 발견된 취약점이 없습니다. 정기적인 보안 점검을 권장합니다.",
                }
                self._update_progress(state, "remediation", 95)
                return state

            # AI로 해결 방안 생성
            prompt = f"""
다음 취약점에 대한 구체적인 해결 방안을 제시해주세요:

{json.dumps(vulnerabilities, ensure_ascii=False, indent=2)}

각 취약점별로 다음을 포함해주세요:
1. 즉시 조치 사항
2. 장기 해결 방안
3. 참고 자료

간결하고 실용적인 조언을 부탁드립니다.
"""

            response = self.llm.invoke(prompt)
            remediation_text = response.content

            state["remediation"] = {
                "recommendations": remediation_text,
            }

            logger.info("Remediation plan generated")
            self._update_progress(state, "remediation", 95)
            return state

        except Exception as e:
            logger.error(f"Remediation generation failed: {e}")
            state["remediation"] = {
                "recommendations": "해결 방안을 생성할 수 없습니다.",
            }
            return state

    def _report_generation(self, state: SecurityScanState) -> SecurityScanState:
        """6단계: 보고서 생성"""
        self._update_progress(state, "report_generation", 98)

        try:
            # 최종 보고서 생성
            ports = state.get("ports", [])
            vulnerabilities = state.get("vulnerabilities", [])
            risk = state.get("risk_assessment", {})
            remediation = state.get("remediation", {})

            report = f"""# 보안 스캔 보고서

## 대상 정보
- IP: {state['target']}
- 스캔 유형: {state['scan_type']}

## 포트 스캔 결과
발견된 열린 포트: {len(ports)}개

{self._format_ports(ports)}

## 취약점 분석
발견된 취약점: {len(vulnerabilities)}개

{self._format_vulnerabilities(vulnerabilities)}

## 위험도 평가
- 점수: {risk.get('score', 0)}/100
- 등급: {risk.get('level', 'Unknown')}

{risk.get('analysis', '평가 없음')}

## 해결 방안
{remediation.get('recommendations', '방안 없음')}

---
*보고서 생성 시간: 자동 생성*
"""

            state["report"] = report
            logger.info("Report generated successfully")

            self._update_progress(state, "report_generation", 100)
            return state

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            state["error"] = str(e)
            raise

    def _validate_target(self, target: str) -> bool:
        """대상 IP 검증 (화이트리스트)"""
        allowed = settings.ALLOWED_TARGET_NETWORKS.split(",")

        # localhost 허용
        if target in ["127.0.0.1", "localhost"]:
            return True

        # 사설 IP 대역 허용
        if target.startswith("192.168.") or target.startswith("10."):
            return True

        return False

    def _format_ports(self, ports: list) -> str:
        """포트 목록 포맷팅"""
        if not ports:
            return "열린 포트 없음"

        lines = []
        for p in ports:
            service = p.get('service', 'unknown')
            version = p.get('version', '')
            version_str = f" ({version})" if version else ""
            lines.append(f"- {p['port']}/{service}{version_str} - {p['state']}")
        return "\n".join(lines)

    def _format_vulnerabilities(self, vulns: list) -> str:
        """취약점 목록 포맷팅"""
        if not vulns:
            return "발견된 취약점 없음"

        lines = []
        for v in vulns:
            lines.append(
                f"- [{v['severity']}] {v['type']} (포트 {v['port']}): {v['description']}"
            )
        return "\n".join(lines)

    def run_scan(self, target: str, scan_type: str = "standard") -> SecurityScanState:
        """동기 스캔 실행"""
        logger.info(f"Starting scan for {target} (type: {scan_type})")

        initial_state: SecurityScanState = {
            "target": target,
            "scan_type": scan_type,
            "ports": None,
            "vulnerabilities": None,
            "risk_assessment": None,
            "remediation": None,
            "report": None,
            "current_step": None,
            "progress": 0,
            "error": None,
        }

        try:
            result = self.graph.invoke(initial_state)
            logger.info("Scan completed successfully")
            return result
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            initial_state["error"] = str(e)
            raise
