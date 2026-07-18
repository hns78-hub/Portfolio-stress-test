import sys
import json
import time

SCENARIO_CONFIGS = {
    1: {
        "name": "Rate Hike +100bps",
        "description": "Interest rates rise by 100 basis points. Yields spike, impacting bond-like instruments, REITs, and tech multiples, while banking margins improve slightly.",
        "shocks": {
            "REIT": -0.12,
            "Real Estate": -0.12,
            "Bonds": -0.10,
            "Utilities": -0.08,
            "Technology": -0.05,
            "Finance": 0.03,
            "Consumer": -0.02,
            "Crypto": -0.05,
            "Cash": 0.0,
            "Other": -0.03
        }
    },
    2: {
        "name": "Tech Sector Selloff -20%",
        "description": "A sharp valuation reset in mega-cap technology and high-growth equities due to regulatory tightening or earnings misses.",
        "shocks": {
            "Technology": -0.20,
            "REIT": 0.0,
            "Real Estate": 0.0,
            "Bonds": 0.0,
            "Utilities": 0.0,
            "Finance": -0.02,
            "Consumer": -0.01,
            "Crypto": -0.10,
            "Cash": 0.0,
            "Other": -0.02
        }
    },
    3: {
        "name": "Broad Market Correction -15%",
        "description": "A systemic global market sell-off triggered by macroeconomic recession fears, impacting all risk assets globally.",
        "shocks": {
            "Technology": -0.15,
            "REIT": -0.15,
            "Real Estate": -0.15,
            "Bonds": -0.05,
            "Utilities": -0.10,
            "Finance": -0.15,
            "Consumer": -0.12,
            "Crypto": -0.25,
            "Cash": 0.0,
            "Other": -0.15
        }
    },
    4: {
        "name": "Crypto Crash -40%",
        "description": "Deleverage event in the digital asset space. High volatility and sharp drop in cryptocurrencies and crypto-exposed equities.",
        "shocks": {
            "Crypto": -0.40,
            "Technology": -0.03,
            "REIT": 0.0,
            "Real Estate": 0.0,
            "Bonds": 0.0,
            "Utilities": 0.0,
            "Finance": -0.01,
            "Consumer": 0.0,
            "Cash": 0.0,
            "Other": 0.0
        }
    },
    5: {
        "name": "USD/SGD Shock -10%",
        "description": "10% depreciation of SGD currency value. Impacts assets that do not have USD exposure (SGD-denominated domestic equities or cash assets).",
        "shocks": {}  # Shock logic is dynamic: checks if the asset is non-USD exposed
    }
}

def get_sector_mapping(sector_str):
    if not sector_str:
        return "Other"
    sec = sector_str.strip().lower()
    if "tech" in sec or "software" in sec or "hardware" in sec or "semiconductor" in sec:
        return "Technology"
    if "reit" in sec or "real estate" in sec or "property" in sec:
        return "REIT"
    if "bond" in sec or "fixed income" in sec:
        return "Bonds"
    if "utility" in sec or "utilities" in sec or "power" in sec:
        return "Utilities"
    if "finance" in sec or "bank" in sec or "insurance" in sec:
        return "Finance"
    if "crypto" in sec or "coin" in sec or "digital" in sec or "web3" in sec:
        return "Crypto"
    if "consumer" in sec or "retail" in sec or "discretionary" in sec:
        return "Consumer"
    if "cash" in sec or "money market" in sec:
        return "Cash"
    return "Other"

def run_stress_scenario(scenario_id, portfolio):
    """
    Runs stress test calculation for a single scenario on a portfolio.
    Portfolio structure:
    List of Dicts: {
        "ticker": str,
        "shares": float,
        "cost_basis": float,
        "price": float,
        "sector": str,
        "is_usd_exposed": bool
    }
    """
    config = SCENARIO_CONFIGS.get(scenario_id)
    if not config:
        raise ValueError(f"Unknown scenario ID: {scenario_id}")

    print(f"[*] Starting stress-test sandbox execution for Scenario: '{config['name']}'...", flush=True)
    time.sleep(0.3)
    
    positions_pnl = []
    total_current_value = 0.0
    total_new_value = 0.0
    total_pnl = 0.0
    
    print(f"[*] Loading portfolio with {len(portfolio)} assets...", flush=True)
    time.sleep(0.2)
    
    for idx, pos in enumerate(portfolio):
        ticker = pos.get("ticker", "UNK")
        shares = float(pos.get("shares", 0.0))
        cost_basis = float(pos.get("cost_basis", 0.0))
        price = float(pos.get("price", 0.0))
        raw_sector = pos.get("sector", "Other")
        is_usd_exposed = bool(pos.get("is_usd_exposed", True))
        
        sector = get_sector_mapping(raw_sector)
        
        # Calculate shock percentage
        shock_pct = 0.0
        if scenario_id == 5:
            # USD/SGD Shock -10% applies specifically to assets that are NOT USD exposed
            if not is_usd_exposed:
                shock_pct = -0.10
                print(f"    [!] Ticker {ticker} has SGD exposure. Applying -10% FX shock.", flush=True)
            else:
                shock_pct = 0.0
                print(f"    [.] Ticker {ticker} has USD exposure. FX shock bypassed.", flush=True)
        else:
            shock_pct = config["shocks"].get(sector, config["shocks"].get("Other", 0.0))
        
        current_value = shares * price
        new_price = price * (1.0 + shock_pct)
        new_value = shares * new_price
        pnl = new_value - current_value
        pnl_pct = shock_pct * 100
        
        total_current_value += current_value
        total_new_value += new_value
        total_pnl += pnl
        
        positions_pnl.append({
            "ticker": ticker,
            "shares": shares,
            "cost_basis": cost_basis,
            "original_price": price,
            "new_price": round(new_price, 4),
            "current_value": round(current_value, 2),
            "new_value": round(new_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "sector": sector,
            "shock_applied": round(shock_pct * 100, 2)
        })
        print(f"    [+] Checked {ticker} ({sector}): Value ${current_value:,.2f} -> ${new_value:,.2f} | P&L: ${pnl:+,.2f} ({pnl_pct:+.2%})", flush=True)
        time.sleep(0.1)

    overall_pnl_pct = (total_pnl / total_current_value * 100) if total_current_value > 0 else 0.0
    
    # Sort positions by worst hit (lowest P&L, i.e. highest loss)
    worst_hit = sorted(positions_pnl, key=lambda x: x["pnl"])
    worst_hit_filtered = [pos for pos in worst_hit if pos["pnl"] < 0][:3]
    
    result = {
        "scenario_id": scenario_id,
        "scenario_name": config["name"],
        "description": config["description"],
        "current_value": round(total_current_value, 2),
        "new_value": round(total_new_value, 2),
        "pnl": round(total_pnl, 2),
        "pnl_percentage": round(overall_pnl_pct, 2),
        "positions": positions_pnl,
        "worst_hit_positions": [
            {
                "ticker": p["ticker"],
                "pnl": p["pnl"],
                "pnl_pct": p["pnl_pct"]
            } for p in worst_hit_filtered
        ]
    }
    
    print(f"[*] Scenario {config['name']} calculation complete.", flush=True)
    print(f"[*] Summary P&L: ${result['pnl']:+,.2f} ({result['pnl_percentage']:.2f}%)", flush=True)
    return result

if __name__ == "__main__":
    # Test block for direct sandbox runs
    if len(sys.argv) < 3:
        print("Usage: python stress_logic.py <scenario_id> '<portfolio_json>'")
        sys.exit(1)
    
    sc_id = int(sys.argv[1])
    port_data = json.loads(sys.argv[2])
    res = run_stress_scenario(sc_id, port_data)
    print("---RESULT_JSON---")
    print(json.dumps(res))
