import json
from backend.stress_logic import run_stress_scenario
from backend.mock_data import MOCK_PORTFOLIO

def test_stress_logic():
    print("[*] Testing local stress test logic...")
    for sc_id in range(1, 6):
        res = run_stress_scenario(sc_id, MOCK_PORTFOLIO)
        assert res["scenario_id"] == sc_id
        assert len(res["positions"]) == len(MOCK_PORTFOLIO)
        assert "worst_hit_positions" in res
        print(f"  [+] Scenario {sc_id} test passed. PnL: ${res['pnl']:+,.2f} ({res['pnl_percentage']:.2f}%)")

if __name__ == "__main__":
    print("=== Running Backend Automated Tests ===")
    test_stress_logic()
    print("=== All Tests Completed Successfully ===")
