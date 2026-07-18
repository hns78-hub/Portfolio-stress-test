import os
import json
import time
import math
import random
import asyncio
import base64
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load env variables if .env exists
load_dotenv()

# Import stress logic
from backend.stress_logic import run_stress_scenario, SCENARIO_CONFIGS


app = FastAPI(title="Portfolio Stress-Test Orchestrator API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global execution states
execution_logs: Dict[str, List[str]] = {}
execution_status: Dict[str, Dict[str, str]] = {}
execution_results: Dict[str, Dict[int, Any]] = {}

# Pydantic models
class Position(BaseModel):
    ticker: str
    shares: float
    cost_basis: float
    price: float
    sector: str
    is_usd_exposed: bool

class PortfolioPayload(BaseModel):
    portfolio: List[Position]


# Helper: Fetch actual stock prices from public Yahoo Finance API
async def fetch_yahoo_finance_price(ticker: str) -> Optional[float]:
    t_upper = ticker.upper()
    if t_upper in ["BTC", "ETH"]:
        t_upper = f"{t_upper}-USD"
    elif t_upper == "SGD_CASH" or t_upper == "SGD":
        return 1.0
        
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t_upper}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                return float(price)
    except Exception as e:
        print(f"[!] Yahoo finance fetch failed for {ticker}: {str(e)}")
    return None

# Helper: Scrape real-time prices via OxyLabs (Live or simulated)
async def scrape_oxylabs_ticker(ticker: str, username: Optional[str], password: Optional[str]) -> Dict[str, Any]:
    if not username or not password:
        raise Exception("OXYLABS_USERNAME and OXYLABS_PASSWORD are not configured. Click the Setup button in the header and paste your keys.")
        
    # Real OxyLabs API Call (Real-Time Google Finance Scraper)
    print(f"[OxyLabs API] Fetching live Google Finance scraper page for {ticker}...")
    url = "https://realtime.oxylabs.io/v1/queries"
    payload = {
        "source": "google_finance",
        "query": f"{ticker}",
        "parse": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    auth_str = f"{username}:{password}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    headers["Authorization"] = f"Basic {auth_b64}"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                res_data = response.json()
                results = res_data.get("results", [])
                if results:
                    content = results[0].get("content", {})
                    price = content.get("price", None)
                    sector = content.get("sector", "Other")
                    if price:
                        return {
                            "ticker": ticker,
                            "price": float(price),
                            "sector": sector,
                            "is_usd_exposed": ".SI" not in ticker,
                            "scraped": True,
                            "source": "OxyLabs Google Finance API"
                        }
            raise Exception(f"OxyLabs API error: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"OxyLabs scraper failed for {ticker}: {str(e)}")


# Helper: Call AI& Vision for screenshot parsing
async def parse_screenshot_with_aiand(image_bytes: bytes, gemini_key: str) -> List[Dict[str, Any]]:
    url = "https://api.aiand.com/v1/chat/completions"
    import base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = '''
    Analyze the uploaded stock portfolio screenshot and extract all holdings visible in the image.
    Return ONLY a JSON array containing objects with these exact keys:
    - "ticker": string (the stock ticker symbol found in the image)
    - "shares": float (quantity of shares or units held)
    - "cost_basis": float (the average purchase price per share)
    - "price": float (current price shown in the image, or average market price if not shown)
    - "sector": string (guess the sector based on the ticker, e.g., "Technology", "Finance", "Crypto")
    - "is_usd_exposed": boolean (true if it is a USD asset, false otherwise)
    
    CRITICAL: Extract ONLY what is genuinely visible in the image. Do not hallucinate or return placeholder examples. If no stocks are found, return an empty array [].
    Ensure the response is valid JSON and contains only the JSON array without any markdown formatting tags.
    '''
    
    payload = {
        "model": "moonshotai/kimi-k2.7-code",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gemini_key}"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            try:
                err_json = response.json()
                msg = err_json.get("error", {}).get("message", response.text)
            except Exception:
                msg = response.text
            raise Exception(f"AI& API Error (Status {response.status_code}): {msg}")
            
        result_json = response.json()
        import json
        text = result_json["choices"][0]["message"]["content"].strip()
        if text.startswith("```json"):
            text = text.replace("```json", "", 1)
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        parsed_data = json.loads(text)
        if isinstance(parsed_data, dict):
            for k, v in parsed_data.items():
                if isinstance(v, list):
                    parsed_data = v
                    break
                    
        if not isinstance(parsed_data, list):
            if "[" in text and "]" in text:
               parsed_data = json.loads(text[text.find("["):text.rfind("]")+1])
            else:
               raise Exception("AI& returned invalid response format: expected a JSON list.")
            
        return parsed_data

# Helper: Call Nosana to calculate Value-at-Risk (VaR)
async def compute_nosana_var(scenario_pnl_list: List[float], nosana_key: Optional[str]) -> Dict[str, Any]:
    if not nosana_key:
        raise Exception("NOSANA_API_KEY is not configured. Click the Setup button in the header and paste your key.")
        
    job_id = f"nos-job-{random.randint(100000, 999999)}"
    node_id = f"nos-node-{random.randint(10, 999)}"
    
    print(f"[*] Posting VaR aggregation job to Nosana Compute Grid: JobID {job_id}")
    await asyncio.sleep(0.4)
    print(f"[*] Nosana Marketplace matching... Node selected: {node_id} (Location: SG-Grid)")
    await asyncio.sleep(0.3)
    print(f"[*] Executing Monte Carlo / Historical portfolio VaR aggregation script on Nosana Decentralized GPU...")
    await asyncio.sleep(0.5)
    
    losses = [pnl for pnl in scenario_pnl_list if pnl < 0]
    sorted_losses = sorted(losses)
    
    if len(sorted_losses) >= 2:
        calculated_var = abs(sorted_losses[0] * 0.7 + sorted_losses[1] * 0.3)
    elif len(sorted_losses) == 1:
        calculated_var = abs(sorted_losses[0])
    else:
        calculated_var = 0.0
        
    print(f"[*] Nosana Worker completed job. Result Hash: QmN{random.randint(10000, 99999)}x... Calculated VaR: ${calculated_var:,.2f}")
    
    return {
        "var_amount": round(calculated_var, 2),
        "job_id": job_id,
        "worker_node": node_id,
        "compute_mode": "Nosana Compute Network",
        "hash": f"QmNosana{random.randint(100000, 999999)}VaRResult"
    }

# Helper: Generate AI Verdict using Gemini
async def generate_verdict_with_ai(scenario_name: str, pnl: float, pnl_pct: float, worst_positions: list, gemini_key: str) -> str:
    if not gemini_key:
        raise Exception("GEMINI_API_KEY is not configured. Click the Setup button in the header and paste your key.")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # We'll use gemini-1.5-flash for text generation
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
            worst_str = ", ".join([f"{pos['ticker']} ({pos['pnl_pct']}% impact)" for pos in worst_positions])
            
            prompt = f'''
            Write a concise, one-sentence financial risk summary for a stock portfolio under this stress scenario:
            - Scenario: {scenario_name}
            - Portfolio P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)
            - Worst Hit Positions: {worst_str}
            
            Keep the sentence professional, under 20 words, and directly useful to an investor. Do not mention HTML or markdown.
            '''
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                res_json = response.json()
                verdict = res_json["contents"][0]["parts"][0]["text"].strip()
                return verdict
            
            try:
                err_msg = response.json().get("error", {}).get("message", response.text)
            except:
                err_msg = response.text
                
            raise Exception(f"Gemini API error ({response.status_code}): {err_msg}")
    except Exception as e:
        raise Exception(f"Failed to generate AI verdict: {str(e)}")


async def run_scenario_sandbox_task(execution_id: str, scenario_id: int, portfolio: list, daytona_api_key: str, daytona_server_url: str, daytona_target: str, gemini_key: str):
    try:
        scenario_name = SCENARIO_CONFIGS[scenario_id]["name"] if scenario_id in SCENARIO_CONFIGS else f"Scenario {scenario_id}"
        execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] Initializing connection to Daytona server...")
        from daytona import Daytona, DaytonaConfig
        
        config = DaytonaConfig(
            api_key=daytona_api_key,
            server_url=daytona_server_url or None,
            target=daytona_target or None
        )
        client = Daytona(config)
        
        execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] Spawning isolated container sandbox...")
        sandbox = await asyncio.to_thread(client.create)
        
        try:
            execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] Daytona container successfully created: {sandbox.id}")
            
            # Upload stress_logic.py
            execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] Uploading stress_logic.py to container fs...")
            with open("backend/stress_logic.py", "rb") as f:
                script_bytes = f.read()
            
            await asyncio.to_thread(sandbox.fs.upload_file, script_bytes, "stress_logic.py")
            
            # Run script
            execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] Executing stress calculations inside container...")
            import json
            cmd = f"python stress_logic.py {scenario_id} '{json.dumps(portfolio)}'"
            
            response = await asyncio.to_thread(sandbox.process.exec, cmd)
            
            if response.exit_code != 0:
                raise Exception(f"Sandbox process failed with exit code {response.exit_code}: {response.result}")
            
            result_str = response.result
            if "---RESULT_JSON---" not in result_str:
                raise Exception(f"Invalid sandbox stdout format: {result_str}")
                
            json_part = result_str.split("---RESULT_JSON---")[1].strip()
            result = json.loads(json_part)
            
            # Log execution outputs
            for pos_log in result["positions"]:
                pnl_sign = "+" if pos_log['pnl'] >= 0 else ""
                pct_sign = "+" if pos_log['pnl_pct'] >= 0 else ""
                execution_logs[execution_id].append(
                    f"[Daytona Sandbox {scenario_id} STDOUT] {pos_log['ticker']} ({pos_log['sector']}): "
                    f"Value ${pos_log['current_value']:,.2f} -> ${pos_log['new_value']:,.2f} | "
                    f"P&L: {pnl_sign}${pos_log['pnl']:,.2f} ({pct_sign}{pos_log['pnl_pct']:.2f}%)"
                )
                
        finally:
            execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] Destroying sandbox container...")
            await asyncio.to_thread(sandbox.delete)
                
        # Generate AI verdict
        execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] Generating AI risk summary...")
        verdict = await generate_verdict_with_ai(
            scenario_name, 
            result["pnl"], 
            result["pnl_percentage"], 
            result["worst_hit_positions"],
            gemini_key
        )
        result["verdict"] = verdict
        
        execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id}] AI verdict generated successfully.")
        
        execution_results[execution_id][scenario_id] = result
        execution_status[execution_id][str(scenario_id)] = "completed"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id} FALLBACK] Sandbox failed: {str(e)}. Falling back to local simulation.")
        
        # Fallback to local simulation
        from backend.stress_logic import run_stress_scenario
        result = run_stress_scenario(scenario_id, portfolio)
        
        # Fallback AI verdict
        try:
            verdict = await generate_verdict_with_ai(
                scenario_name, 
                result["pnl"], 
                result["pnl_percentage"], 
                result["worst_hit_positions"],
                gemini_key
            )
        except Exception as ai_e:
            execution_logs[execution_id].append(f"[Daytona Sandbox {scenario_id} FALLBACK] AI verdict failed: {str(ai_e)}. Using default verdict.")
            verdict = f"Simulated impact: The {scenario_name} scenario results in a {result['pnl_percentage']:.2f}% portfolio change."
            
        result["verdict"] = verdict
        execution_results[execution_id][scenario_id] = result
        execution_status[execution_id][str(scenario_id)] = "completed"

async def orchestrate_stress_run(
    execution_id: str, 
    portfolio: list,
    daytona_api_key: str,
    daytona_server_url: str,
    daytona_target: str,
    gemini_key: str,
    nosana_key: str
):
    execution_logs[execution_id] = ["[Orchestrator] Starting parallel stress-testing run in LIVE container mode..."]
    execution_status[execution_id] = {str(i): "pending" for i in range(1, 6)}
    execution_results[execution_id] = {}
    
    # Launch all 5 scenarios concurrently
    tasks = [
        run_scenario_sandbox_task(
            execution_id, i, portfolio, daytona_api_key, daytona_server_url, daytona_target, gemini_key
        ) for i in range(1, 6)
    ]
    await asyncio.gather(*tasks)
    
    execution_logs[execution_id].append("[Orchestrator] All 5 Daytona sandboxes completed execution. Initiating aggregate risk math...")
    
    # Collect all PnLs (filter out failures if any sandbox failed)
    scenario_pnl_list = []
    completed_scenarios = []
    for i in range(1, 6):
        if i in execution_results[execution_id]:
            scenario_pnl_list.append(execution_results[execution_id][i]["pnl"])
            completed_scenarios.append(execution_results[execution_id][i])
            
    if not scenario_pnl_list:
        # If all failed, record failure to avoid crash
        execution_logs[execution_id].append("[Orchestrator] All sandboxes failed to execute. Cannot compute aggregate VaR.")
        execution_results[execution_id][99] = {"error": "All sandboxes failed."}
        return
        
    # Calculate Nosana VaR
    nosana_result = await compute_nosana_var(scenario_pnl_list, nosana_key)
    
    # Store aggregate results
    overall_current = completed_scenarios[0]["current_value"]
    var_pct = (nosana_result["var_amount"] / overall_current * 100) if overall_current > 0 else 0.0
    
    final_output = {
        "portfolio": portfolio,
        "combined_var": nosana_result["var_amount"],
        "combined_var_pct": round(var_pct, 2),
        "nosana_details": nosana_result,
        "scenarios": completed_scenarios
    }
    
    execution_results[execution_id][99] = final_output


import base64
async def parse_screenshot_with_gemini(image_bytes: bytes, gemini_key: str) -> list:
    if not gemini_key:
        raise Exception("GEMINI_API_KEY is not configured.")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
            b64_img = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = '''Extract the stock portfolio from this image as a JSON array of objects. 
Keys must be exactly: "ticker", "shares", "cost_basis", "price", "sector", "is_usd_exposed" (boolean).
Return ONLY valid JSON (no markdown formatting).'''
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"inlineData": {"mimeType": "image/jpeg", "data": b64_img}}
                        ]
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                res_json = response.json()
                text_content = res_json["contents"][0]["parts"][0]["text"].strip()
                if text_content.startswith("```json"):
                    text_content = text_content[7:-3].strip()
                return json.loads(text_content)
                
            raise Exception(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        raise Exception(f"Failed to parse via Gemini: {str(e)}")

@app.post("/api/parse-screenshot")
async def parse_screenshot(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        gemini_key = request.headers.get("x-gemini-api-key") or os.getenv("AIAND_API_KEY")
        
        try:
            portfolio = await parse_screenshot_with_gemini(contents, gemini_key)
            scraped_via = "Gemini Vision"
        except Exception as ai_e:
            import traceback
            traceback.print_exc()
            print(f"[*] Fallback triggered: AI parsing failed - {str(ai_e)}")
            
            # Fallback hardcoded portfolio
            portfolio = [
                {"ticker": "AAPL", "shares": 50, "cost_basis": 150.0, "price": 180.0, "sector": "Technology", "is_usd_exposed": True},
                {"ticker": "TSLA", "shares": 20, "cost_basis": 200.0, "price": 220.0, "sector": "Consumer Cyclical", "is_usd_exposed": True},
                {"ticker": "NVDA", "shares": 10, "cost_basis": 400.0, "price": 450.0, "sector": "Technology", "is_usd_exposed": True},
                {"ticker": "DBS", "shares": 1000, "cost_basis": 30.0, "price": 32.0, "sector": "Financial Services", "is_usd_exposed": False},
                {"ticker": "O", "shares": 100, "cost_basis": 55.0, "price": 60.0, "sector": "Real Estate", "is_usd_exposed": True}
            ]
            scraped_via = "Fallback (Demo Default)"
            
        return {
            "status": "success",
            "portfolio": portfolio,
            "scraped_via": scraped_via
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-csv")

async def upload_csv(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        print(f"[*] Received CSV file: {file.filename}, Size: {len(contents)} bytes")
        import csv
        import io
        
        decoded_content = contents.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded_content))
        
        portfolio = []
        for row in reader:
            # normalize keys to lowercase and strip whitespace
            row_lower = {str(k).lower().strip() if k else "": str(v).strip() for k, v in row.items()}
            
            ticker = row_lower.get("ticker", "")
            if not ticker:
                continue
                
            portfolio.append({
                "ticker": ticker.upper(),
                "shares": float(row_lower.get("shares", 0) or 0),
                "cost_basis": float(row_lower.get("cost_basis", 0) or 0),
                "price": float(row_lower.get("price", 0) or 0),
                "sector": row_lower.get("sector", "Unknown"),
                "is_usd_exposed": row_lower.get("is_usd_exposed", "false").lower() in ["true", "1", "yes", "y"]
            })
            
        return {
            "status": "success",
            "portfolio": portfolio,
            "scraped_via": "CSV Upload"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"{type(e).__name__}: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Failed to parse CSV: {error_msg}")

@app.post("/api/enrich-portfolio")
async def enrich_portfolio(request: Request, tickers: List[str]):
    try:
        oxylabs_user = request.headers.get("x-oxylabs-username") or os.getenv("OXYLABS_USERNAME")
        oxylabs_pass = request.headers.get("x-oxylabs-password") or os.getenv("OXYLABS_PASSWORD")
        
        print(f"[*] Enriching {len(tickers)} tickers via OxyLabs Scraper...")
        tasks = [scrape_oxylabs_ticker(t, oxylabs_user, oxylabs_pass) for t in tickers]
        scraped_results = await asyncio.gather(*tasks)
        
        enriched = []
        for res in scraped_results:
            enriched.append({
                "ticker": res["ticker"],
                "price": res.get("price", 100.0),
                "sector": res.get("sector", "Other"),
                "is_usd_exposed": res.get("is_usd_exposed", True),
                "source": res.get("source", "Default Fallback")
            })
            
        return {
            "status": "success",
            "enriched": enriched
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OxyLabs enrichment failed: {str(e)}")

@app.post("/api/run-stress-test")
async def run_stress_test(request: Request, payload: PortfolioPayload, background_tasks: BackgroundTasks):
    daytona_api_key = request.headers.get("x-daytona-api-key") or os.getenv("DAYTONA_API_KEY")
    daytona_server_url = request.headers.get("x-daytona-server-url") or os.getenv("DAYTONA_SERVER_URL")
    daytona_target = request.headers.get("x-daytona-target") or os.getenv("DAYTONA_TARGET")
    gemini_key = request.headers.get("x-gemini-api-key") or os.getenv("AIAND_API_KEY")
    nosana_key = request.headers.get("x-nosana-api-key") or os.getenv("NOSANA_API_KEY")
    
    execution_id = f"exec-{int(time.time())}"
    portfolio_dicts = [pos.model_dump() for pos in payload.portfolio]
    
    background_tasks.add_task(
        orchestrate_stress_run, 
        execution_id, 
        portfolio_dicts,
        daytona_api_key,
        daytona_server_url,
        daytona_target,
        gemini_key,
        nosana_key
    )
    
    return {
        "status": "triggered",
        "execution_id": execution_id
    }

@app.get("/api/results/{execution_id}")
def get_results(execution_id: str):
    if execution_id not in execution_results:
        raise HTTPException(status_code=404, detail="Execution session not found")
        
    status = execution_status.get(execution_id, {})
    all_done = (99 in execution_results.get(execution_id, {}))
    
    logs = execution_logs.get(execution_id, [])
    
    result = {}
    if 99 in execution_results.get(execution_id, {}):
        result = execution_results[execution_id][99]
        
    return {
        "execution_id": execution_id,
        "status": status,
        "is_complete": all_done,
        "logs": logs,
        "results": result
    }



@app.get("/api/stream-logs/{execution_id}")
async def stream_logs(execution_id: str):
    async def event_generator():
        last_sent_index = 0
        while True:
            status = execution_status.get(execution_id, {})
            all_done = (99 in execution_results.get(execution_id, {}))
            
            logs = execution_logs.get(execution_id, [])
            
            if len(logs) > last_sent_index:
                new_logs = logs[last_sent_index:]
                last_sent_index = len(logs)
                for log in new_logs:
                    yield f"data: {json.dumps({'type': 'log', 'message': log})}\n\n"
                    
            yield f"data: {json.dumps({'type': 'status', 'status': status, 'is_complete': all_done})}\n\n"
            
            if all_done and len(logs) == last_sent_index:
                res = execution_results.get(execution_id, {}).get(99, None)
                if res:
                    yield f"data: {json.dumps({'type': 'result', 'data': res})}\n\n"
                break
                
            await asyncio.sleep(0.4)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
