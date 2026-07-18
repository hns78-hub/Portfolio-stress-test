MOCK_PORTFOLIO = [
    {
        "ticker": "AAPL",
        "shares": 50.0,
        "cost_basis": 175.0,
        "price": 189.30,
        "sector": "Technology",
        "is_usd_exposed": True
    },
    {
        "ticker": "MSFT",
        "shares": 30.0,
        "cost_basis": 380.0,
        "price": 420.55,
        "sector": "Technology",
        "is_usd_exposed": True
    },
    {
        "ticker": "COIN",
        "shares": 15.0,
        "cost_basis": 150.0,
        "price": 245.20,
        "sector": "Crypto/Tech",
        "is_usd_exposed": True
    },
    {
        "ticker": "BTC",
        "shares": 0.5,
        "cost_basis": 45000.0,
        "price": 67320.10,
        "sector": "Crypto",
        "is_usd_exposed": True
    },
    {
        "ticker": "D05.SI",
        "shares": 200.0,
        "cost_basis": 32.0,
        "price": 35.80,
        "sector": "Finance/Banking",
        "is_usd_exposed": False
    },
    {
        "ticker": "C38U.SI",
        "shares": 1000.0,
        "cost_basis": 1.90,
        "price": 2.05,
        "sector": "REIT/Real Estate",
        "is_usd_exposed": False
    },
    {
        "ticker": "SGD_CASH",
        "shares": 5000.0,
        "cost_basis": 1.0,
        "price": 1.0,
        "sector": "Cash",
        "is_usd_exposed": False
    }
]

MOCK_VERDICTS = {
    1: "Rates increase negatively impacts REIT holdings (−12.0%) and Tech valuations, partially offset by +3.0% yield margins in D05.SI.",
    2: "Tech drop triggers $3,803.00 loss in AAPL and MSFT; crypto holdings feel auxiliary selling pressure, but yield and REIT holdings act as cushions.",
    3: "Systemic selloff triggers a total loss of $11,364.55 flat across all risk categories; cash holds its value.",
    4: "Crypto shock causes BTC and COIN to plummet, shaving $14,934.02 off total value; tech exposure shows marginal correlation losses.",
    5: "SGD depreciation devalues local REIT and bank stocks in USD terms, resulting in a flat $1,421.00 currency translation loss."
}

MOCK_STRESS_RESULTS = {
    "portfolio": MOCK_PORTFOLIO,
    "combined_var": 13854.40,
    "combined_var_pct": 19.34,
    "scenarios": [
        {
            "scenario_id": 1,
            "scenario_name": "Rate Hike +100bps",
            "description": "Interest rates rise by 100 basis points. Yields spike, impacting bond-like instruments, REITs, and tech multiples, while banking margins improve slightly.",
            "current_value": 71606.15,
            "new_value": 68765.40,
            "pnl": -2840.75,
            "pnl_percentage": -3.97,
            "worst_hit_positions": [
                {"ticker": "C38U.SI", "pnl": -246.0, "pnl_pct": -12.0},
                {"ticker": "AAPL", "pnl": -473.25, "pnl_pct": -5.0},
                {"ticker": "MSFT", "pnl": -630.82, "pnl_pct": -5.0}
            ],
            "verdict": MOCK_VERDICTS[1],
            "logs": [
                "[*] Starting stress-test sandbox execution for Scenario: 'Rate Hike +100bps'...",
                "[*] Loading portfolio with 7 assets...",
                "    [+] Checked AAPL (Technology): Value $9,465.00 -> $8,991.75 | P&L: -$473.25 (-5.00%)",
                "    [+] Checked MSFT (Technology): Value $12,616.50 -> $11,985.68 | P&L: -$630.82 (-5.00%)",
                "    [+] Checked COIN (Crypto): Value $3,678.00 -> $3,494.10 | P&L: -$183.90 (-5.00%)",
                "    [+] Checked BTC (Crypto): Value $33,660.05 -> $31,977.05 | P&L: -$1,683.00 (-5.00%)",
                "    [+] Checked D05.SI (Finance): Value $7,160.00 -> $7,374.80 | P&L: +$214.80 (+3.00%)",
                "    [+] Checked C38U.SI (REIT): Value $2,050.00 -> $1,804.00 | P&L: -$246.00 (-12.00%)",
                "    [+] Checked SGD_CASH (Cash): Value $5,000.00 -> $5,000.00 | P&L: $0.00 (+0.00%)",
                "[*] Scenario Rate Hike +100bps calculation complete.",
                "[*] Summary P&L: -$2,840.75 (-3.97%)"
            ]
        },
        {
            "scenario_id": 2,
            "scenario_name": "Tech Sector Selloff -20%",
            "description": "A sharp valuation reset in mega-cap technology and high-growth equities due to regulatory tightening or earnings misses.",
            "current_value": 71606.15,
            "new_value": 67113.88,
            "pnl": -4492.27,
            "pnl_percentage": -6.27,
            "worst_hit_positions": [
                {"ticker": "AAPL", "pnl": -1893.00, "pnl_pct": -20.0},
                {"ticker": "MSFT", "pnl": -2523.30, "pnl_pct": -20.0},
                {"ticker": "COIN", "pnl": -73.56, "pnl_pct": -2.0}
            ],
            "verdict": MOCK_VERDICTS[2],
            "logs": [
                "[*] Starting stress-test sandbox execution for Scenario: 'Tech Sector Selloff -20%'...",
                "[*] Loading portfolio with 7 assets...",
                "    [+] Checked AAPL (Technology): Value $9,465.00 -> $7,572.00 | P&L: -$1893.00 (-20.00%)",
                "    [+] Checked MSFT (Technology): Value $12,616.50 -> $10,093.20 | P&L: -$2523.30 (-20.00%)",
                "    [+] Checked COIN (Crypto): Value $3,678.00 -> $3,604.44 | P&L: -$73.56 (-2.00%)",
                "    [+] Checked BTC (Crypto): Value $33,660.05 -> $33,660.05 | P&L: $0.00 (+0.00%)",
                "    [+] Checked D05.SI (Finance): Value $7,160.00 -> $7,160.00 | P&L: $0.00 (+0.00%)",
                "    [+] Checked C38U.SI (REIT): Value $2,050.00 -> $2,050.00 | P&L: $0.00 (+0.00%)",
                "    [+] Checked SGD_CASH (Cash): Value $5,000.00 -> $5,000.00 | P&L: $0.00 (+0.00%)",
                "[*] Scenario Tech Sector Selloff -20% calculation complete.",
                "[*] Summary P&L: -$4,492.27 (-6.27%)"
            ]
        },
        {
            "scenario_id": 3,
            "scenario_name": "Broad Market Correction -15%",
            "description": "A systemic global market sell-off triggered by macroeconomic recession fears, impacting all risk assets globally.",
            "current_value": 71606.15,
            "new_value": 60241.60,
            "pnl": -11364.55,
            "pnl_percentage": -15.87,
            "worst_hit_positions": [
                {"ticker": "BTC", "pnl": -8415.01, "pnl_pct": -25.0},
                {"ticker": "MSFT", "pnl": -1892.48, "pnl_pct": -15.0},
                {"ticker": "AAPL", "pnl": -1419.75, "pnl_pct": -15.0}
            ],
            "verdict": MOCK_VERDICTS[3],
            "logs": [
                "[*] Starting stress-test sandbox execution for Scenario: 'Broad Market Correction -15%'...",
                "[*] Loading portfolio with 7 assets...",
                "    [+] Checked AAPL (Technology): Value $9,465.00 -> $8,045.25 | P&L: -$1419.75 (-15.00%)",
                "    [+] Checked MSFT (Technology): Value $12,616.50 -> $10,724.02 | P&L: -$1892.48 (-15.00%)",
                "    [+] Checked COIN (Crypto): Value $3,678.00 -> $2,758.50 | P&L: -$919.50 (-25.00%)",
                "    [+] Checked BTC (Crypto): Value $33,660.05 -> $25,245.04 | P&L: -$8415.01 (-25.00%)",
                "    [+] Checked D05.SI (Finance): Value $7,160.00 -> $6,086.00 | P&L: -$1074.00 (-15.00%)",
                "    [+] Checked C38U.SI (REIT): Value $2,050.00 -> $1,742.50 | P&L: -$307.50 (-15.00%)",
                "    [+] Checked SGD_CASH (Cash): Value $5,000.00 -> $5,000.00 | P&L: $0.00 (+0.00%)",
                "[*] Scenario Broad Market Correction -15% calculation complete.",
                "[*] Summary P&L: -$11,364.55 (-15.87%)"
            ]
        },
        {
            "scenario_id": 4,
            "scenario_name": "Crypto Crash -40%",
            "description": "Deleverage event in the digital asset space. High volatility and sharp drop in cryptocurrencies and crypto-exposed equities.",
            "current_value": 71606.15,
            "new_value": 56672.13,
            "pnl": -14934.02,
            "pnl_percentage": -20.86,
            "worst_hit_positions": [
                {"ticker": "BTC", "pnl": -13464.02, "pnl_pct": -40.0},
                {"ticker": "COIN", "pnl": -1471.20, "pnl_pct": -40.0},
                {"ticker": "AAPL", "pnl": 0.0, "pnl_pct": 0.0}
            ],
            "verdict": MOCK_VERDICTS[4],
            "logs": [
                "[*] Starting stress-test sandbox execution for Scenario: 'Crypto Crash -40%'...",
                "[*] Loading portfolio with 7 assets...",
                "    [+] Checked AAPL (Technology): Value $9,465.00 -> $9,465.00 | P&L: $0.00 (+0.00%)",
                "    [+] Checked MSFT (Technology): Value $12,616.50 -> $12,616.50 | P&L: $0.00 (+0.00%)",
                "    [+] Checked COIN (Crypto): Value $3,678.00 -> $2,206.80 | P&L: -$1471.20 (-40.00%)",
                "    [+] Checked BTC (Crypto): Value $33,660.05 -> $20,196.03 | P&L: -$13464.02 (-40.00%)",
                "    [+] Checked D05.SI (Finance): Value $7,160.00 -> $7,160.00 | P&L: $0.00 (+0.00%)",
                "    [+] Checked C38U.SI (REIT): Value $2,050.00 -> $2,050.00 | P&L: $0.00 (+0.00%)",
                "    [+] Checked SGD_CASH (Cash): Value $5,000.00 -> $5,000.00 | P&L: $0.00 (+0.00%)",
                "[*] Scenario Crypto Crash -40% calculation complete.",
                "[*] Summary P&L: -$14,934.02 (-20.86%)"
            ]
        },
        {
            "scenario_id": 5,
            "scenario_name": "USD/SGD Shock -10%",
            "description": "10% depreciation of SGD currency value. Impacts assets that do not have USD exposure (SGD-denominated domestic equities or cash assets).",
            "current_value": 71606.15,
            "new_value": 70185.15,
            "pnl": -1421.00,
            "pnl_percentage": -1.98,
            "worst_hit_positions": [
                {"ticker": "D05.SI", "pnl": -716.0, "pnl_pct": -10.0},
                {"ticker": "SGD_CASH", "pnl": -500.0, "pnl_pct": -10.0},
                {"ticker": "C38U.SI", "pnl": -205.0, "pnl_pct": -10.0}
            ],
            "verdict": MOCK_VERDICTS[5],
            "logs": [
                "[*] Starting stress-test sandbox execution for Scenario: 'USD/SGD Shock -10%'...",
                "[*] Loading portfolio with 7 assets...",
                "    [.] Ticker AAPL has USD exposure. FX shock bypassed. Value: $9,465.00 -> $9,465.00",
                "    [.] Ticker MSFT has USD exposure. FX shock bypassed. Value: $12,616.50 -> $12,616.50",
                "    [.] Ticker COIN has USD exposure. FX shock bypassed. Value: $3,678.00 -> $3,678.00",
                "    [.] Ticker BTC has USD exposure. FX shock bypassed. Value: $33,660.05 -> $33,660.05",
                "    [!] Ticker D05.SI has SGD exposure. Applying -10% FX shock. Value $7,160.00 -> $6,444.00 | P&L: -$716.00 (-10.00%)",
                "    [!] Ticker C38U.SI has SGD exposure. Applying -10% FX shock. Value $2,050.00 -> $1,845.00 | P&L: -$205.00 (-10.00%)",
                "    [!] Ticker SGD_CASH has SGD exposure. Applying -10% FX shock. Value $5,000.00 -> $4,500.00 | P&L: -$500.00 (-10.00%)",
                "[*] Scenario USD/SGD Shock -10% calculation complete.",
                "[*] Summary P&L: -$1,421.00 (-1.98%)"
            ]
        }
    ]
}
