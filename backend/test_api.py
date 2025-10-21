"""
API 엔드포인트 테스트 스크립트
Phase 2.3 검증용
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_scan_api():
    """스캔 API 전체 흐름 테스트"""
    print("=" * 60)
    print("LangGraph API 엔드포인트 테스트")
    print("=" * 60)

    # 1. 스캔 시작
    print("\n1. POST /langgraph/scan - 스캔 시작")
    print("-" * 60)
    scan_request = {
        "target": "127.0.0.1",
        "scan_type": "quick"
    }
    print(f"Request: {json.dumps(scan_request, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/langgraph/scan",
        json=scan_request
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    session_id = result.get("session_id")
    if not session_id:
        print("ERROR: No session_id returned")
        return

    # 2. 스캔 상태 조회
    print(f"\n2. GET /langgraph/scan/{session_id} - 스캔 상태 조회")
    print("-" * 60)
    response = requests.get(f"{BASE_URL}/langgraph/scan/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # 3. 스캔 결과 조회
    print(f"\n3. GET /langgraph/scan/{session_id}/result - 스캔 결과 조회")
    print("-" * 60)
    response = requests.get(f"{BASE_URL}/langgraph/scan/{session_id}/result")
    print(f"Status: {response.status_code}")
    result = response.json()

    # 결과가 너무 길 수 있으므로 요약 출력
    print("Response (summary):")
    print(f"  - session_id: {result.get('session_id')}")
    print(f"  - target: {result.get('target')}")
    print(f"  - scan_type: {result.get('scan_type')}")
    print(f"  - ports found: {len(result.get('ports', []))}")
    print(f"  - vulnerabilities: {len(result.get('vulnerabilities', []))}")
    print(f"  - risk_assessment: {bool(result.get('risk_assessment'))}")
    print(f"  - remediation: {bool(result.get('remediation'))}")
    print(f"  - report length: {len(result.get('report', ''))}")

    # 포트 정보 출력
    if result.get('ports'):
        print("\nPorts:")
        for port in result.get('ports', []):
            print(f"  - {port.get('port')}/{port.get('protocol')}: {port.get('service')} ({port.get('state')})")

    # 4. 세션 목록 조회
    print(f"\n4. GET /langgraph/sessions - 세션 목록 조회")
    print("-" * 60)
    response = requests.get(f"{BASE_URL}/langgraph/sessions")
    print(f"Status: {response.status_code}")
    sessions = response.json()
    print(f"Total sessions: {len(sessions)}")
    for session in sessions:
        print(f"  - {session.get('session_id')}: {session.get('target')} ({session.get('status')})")

    # 5. 세션 삭제
    print(f"\n5. DELETE /langgraph/scan/{session_id} - 세션 삭제")
    print("-" * 60)
    response = requests.delete(f"{BASE_URL}/langgraph/scan/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # 6. 삭제 확인
    print(f"\n6. GET /langgraph/sessions - 삭제 확인")
    print("-" * 60)
    response = requests.get(f"{BASE_URL}/langgraph/sessions")
    print(f"Status: {response.status_code}")
    sessions = response.json()
    print(f"Total sessions: {len(sessions)}")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_scan_api()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Make sure the server is running.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
