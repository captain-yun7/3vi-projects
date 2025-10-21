"""
LangGraph 서비스 직접 테스트 스크립트
"""
import sys
sys.path.insert(0, '/home/k8s-admin/3vi-v1/backend')

from app.services.langgraph_service import LangGraphService
import json

def main():
    print("=" * 60)
    print("LangGraph 서비스 테스트")
    print("=" * 60)

    try:
        # 서비스 생성
        print("\n1. 서비스 생성 중...")
        service = LangGraphService()
        print("✓ LangGraphService 생성 완료")

        # 스캔 실행
        print("\n2. 스캔 실행 중...")
        print("   대상: 127.0.0.1")
        print("   유형: quick")
        print()

        result = service.run_scan(
            target="127.0.0.1",
            scan_type="quick"
        )

        print("\n" + "=" * 60)
        print("스캔 결과")
        print("=" * 60)

        # 포트 스캔 결과
        print(f"\n📡 발견된 포트: {len(result.get('ports', []))}개")
        for port in result.get('ports', [])[:5]:
            print(f"  - 포트 {port['port']}: {port['service']} ({port['state']})")

        # 취약점
        print(f"\n⚠️  발견된 취약점: {len(result.get('vulnerabilities', []))}개")
        for vuln in result.get('vulnerabilities', [])[:3]:
            print(f"  - [{vuln['severity']}] {vuln['type']} (포트 {vuln['port']})")

        # 위험도
        risk = result.get('risk_assessment', {})
        print(f"\n🎯 위험도 평가")
        print(f"  - 점수: {risk.get('score', 0)}/100")
        print(f"  - 등급: {risk.get('level', 'Unknown')}")

        # 보고서 일부
        report = result.get('report', '')
        if report:
            print(f"\n📄 보고서 (일부):")
            print(report[:500] + "...")

        print("\n" + "=" * 60)
        print("✓ 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
