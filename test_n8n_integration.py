"""
Test script for n8n integration
Validates that all API endpoints work correctly
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds


def test_health_check():
    """Test health check endpoint"""
    print("\n📊 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Status: {data['status']}")
        print(f"   Agents loaded: {data['agents_loaded']}")
        print(f"   Data available: {data['data_available']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_get_current_state():
    """Test get current state endpoint"""
    print("\n📊 Testing get current state...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/state/current?index=500", timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Get state passed")
        print(f"   Timestamp: {data['timestamp']}")
        print(f"   L1: {data['L1']:.2f}m")
        print(f"   F1: {data['F1']:.0f} m³/15min")
        print(f"   Price (normal): {data['electricity_price_normal']:.3f} EUR/kWh")
        return data
    except Exception as e:
        print(f"❌ Get state failed: {e}")
        return None


def test_individual_agent(agent_name, state):
    """Test individual agent endpoint"""
    print(f"\n🤖 Testing {agent_name} agent...")
    try:
        payload = {
            "timestamp": state['timestamp'],
            "L1": state['L1'],
            "V": state['V'],
            "F1": state['F1'],
            "F2": state['F2'],
            "electricity_price": state['electricity_price_normal'],
            "price_scenario": "normal",
            "current_index": state['current_index']
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/assess/{agent_name}",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ {agent_name} agent passed")
        print(f"   Priority: {data['priority']}")
        print(f"   Confidence: {data['confidence']:.2f}")
        print(f"   Reasoning: {data['reasoning'][:100]}...")
        return True
    except Exception as e:
        print(f"❌ {agent_name} agent failed: {e}")
        return False


def test_synthesize_decision(state):
    """Test full synthesis endpoint"""
    print(f"\n🧠 Testing complete decision synthesis...")
    try:
        payload = {
            "timestamp": state['timestamp'],
            "L1": state['L1'],
            "V": state['V'],
            "F1": state['F1'],
            "F2": state['F2'],
            "electricity_price": state['electricity_price_normal'],
            "price_scenario": "normal",
            "current_index": state['current_index']
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/synthesize",
            json=payload,
            timeout=TIMEOUT * 2  # Longer timeout for synthesis
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ Decision synthesis passed")
        print(f"   Timestamp: {data['timestamp']}")
        print(f"   Priority: {data['priority_applied']}")
        print(f"   Confidence: {data['confidence']:.2f}")
        print(f"   Estimated flow: {data['estimated_flow_m3h']:.0f} m³/h")
        print(f"   Estimated cost: {data['estimated_cost_eur_per_hour']:.2f} EUR/h")
        print(f"   Active pumps: {len([cmd for cmd in data['pump_commands'] if cmd['start']])}")
        print(f"   Reasoning: {data['coordinator_reasoning'][:150]}...")

        # Show pump commands
        print(f"\n   Pump Commands:")
        for cmd in data['pump_commands']:
            if cmd['start']:
                print(f"     {cmd['pump_id']}: {cmd['frequency']:.1f} Hz")

        return True
    except Exception as e:
        print(f"❌ Decision synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_webhook_price_alert():
    """Test price alert webhook"""
    print(f"\n📡 Testing price alert webhook...")
    try:
        payload = {
            "timestamp": datetime.now().isoformat(),
            "new_price": 0.08,
            "old_price": 0.05,
            "change_percent": 60.0,
            "scenario": "high"
        }

        response = requests.post(
            f"{API_BASE_URL}/webhooks/price_alert",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ Price alert webhook passed")
        print(f"   Status: {data['status']}")
        print(f"   Is significant: {data['is_significant']}")
        print(f"   Message: {data['message']}")
        return True
    except Exception as e:
        print(f"❌ Price alert webhook failed: {e}")
        return False


def test_webhook_emergency():
    """Test emergency webhook"""
    print(f"\n🚨 Testing emergency webhook...")
    try:
        payload = {
            "timestamp": datetime.now().isoformat(),
            "emergency_type": "overflow",
            "current_L1": 7.8,
            "message": "Water level approaching maximum"
        }

        response = requests.post(
            f"{API_BASE_URL}/webhooks/emergency",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ Emergency webhook passed")
        print(f"   Status: {data['status']}")
        print(f"   Emergency type: {data['emergency_type']}")
        print(f"   Message: {data['message']}")
        return True
    except Exception as e:
        print(f"❌ Emergency webhook failed: {e}")
        return False


def test_metrics():
    """Test metrics endpoint"""
    print(f"\n📈 Testing metrics endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/metrics", timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        print(f"✅ Metrics endpoint passed")
        print(f"   Total decisions: {data['total_decisions']}")
        print(f"   Uptime: {data['uptime_hours']:.2f} hours")
        print(f"   Avg water level: {data['avg_water_level']:.2f}m")
        return True
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("n8n Integration Test Suite")
    print("="*60)

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health_check()))

    # Test 2: Get current state
    state = test_get_current_state()
    results.append(("Get Current State", state is not None))

    if state is None:
        print("\n❌ Cannot continue tests - failed to get system state")
        print_results(results)
        return

    # Test 3: Individual agents
    agents = ['inflow', 'cost', 'efficiency', 'safety', 'smoothness', 'compliance']
    for agent in agents:
        results.append((f"{agent.title()} Agent", test_individual_agent(agent, state)))

    # Test 4: Full synthesis
    results.append(("Decision Synthesis", test_synthesize_decision(state)))

    # Test 5: Webhooks
    results.append(("Price Alert Webhook", test_webhook_price_alert()))
    results.append(("Emergency Webhook", test_webhook_emergency()))

    # Test 6: Metrics
    results.append(("Metrics Endpoint", test_metrics()))

    # Print results
    print_results(results)


def print_results(results):
    """Print test results summary"""
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")

    print("="*60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! n8n integration is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")


if __name__ == "__main__":
    main()
