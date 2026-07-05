#!/usr/bin/env python3

import os
import json
import time
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from src.workflow_parallel import run_single_ticket_pipeline, run_batch_pipeline
import uvicorn

load_dotenv(os.path.join('config', '.env'))

RUN_MODE = os.getenv("RUN_MODE", "local")
SUPPORTED_MODES = ["local"]
if RUN_MODE not in SUPPORTED_MODES:
    raise ValueError(f"Unsupported RUN_MODE '{RUN_MODE}'. Supported modes: {SUPPORTED_MODES}")

SERVER_HOST = os.getenv("SERVER_HOST")
UVICORN_PORT = os.getenv("UVICORN_PORT")
print(f"DEBUG: SERVER_HOST:{SERVER_HOST}, UVICORN_PORT:{UVICORN_PORT}")
try:
    UVICORN_PORT = int(UVICORN_PORT)
except (ValueError, TypeError) as e:
    print(f"Error converting UVICORN_PORT to an integer: {e}")
    UVICORN_PORT = 8000

app = FastAPI(title="FinAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="results"), name="static")


class AnalyzeRequest(BaseModel):
    symbols: List[str]
    period: str


def format_trading_plan(raw: str) -> str:
    """Format trading plan JSON to readable markdown."""
    try:
        json_str = raw
        if '```json' in raw:
            json_str = raw.split('```json')[1].split('```')[0].strip()
        elif '```' in raw:
            json_str = raw.split('```')[1].split('```')[0].strip()

        plan = json.loads(json_str)
        proposal = plan.get('PROPOSAL', 'N/A')
        target_price = plan.get('TARGET_PRICE', 'N/A')
        forecast = plan.get('FORECAST_PERIOD', 'N/A')
        confidence = plan.get('CONFIDENCE', 'N/A')
        risk = plan.get('RISK_SCORE', 'N/A')
        close = plan.get('LAST_CLOSE_PRICE', 'N/A')
        rationale = plan.get('RATIONALE', 'N/A')
        proposal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(proposal, '⚪')

        return f"""## Trading Plan

### {proposal_emoji} Recommendation: **{proposal}**

| Metric | Value |
|--------|-------|
| **Target Price** | {target_price} |
| **Forecast Period** | {forecast} |
| **Confidence** | {confidence} |
| **Risk Score** | {risk} |
| **Last Close** | {close} |

### Rationale

{rationale}
"""
    except (json.JSONDecodeError, TypeError, IndexError):
        return raw


def format_pipeline_result(pipeline_result: dict) -> dict:
    """Convert pipeline result to API response format."""
    symbol = pipeline_result.get("symbol", "UNKNOWN")
    steps = pipeline_result.get("steps", {})
    errors = pipeline_result.get("errors", [])

    # Format trading plan
    trading_raw = steps.get("trading", "")
    trading_formatted = format_trading_plan(trading_raw) if not trading_raw.startswith("[ERROR]") else trading_raw

    reports = {
        "fundamentals": steps.get("fundamentals", "No data"),
        "sentiment": steps.get("sentiment", "No data"),
        "technical": steps.get("technical", "No data"),
        "market": steps.get("market", "No data"),
        "globalEconomic": steps.get("global_economic", "No data"),
        "fundHolding": steps.get("fund_holding", "No data"),
        "pastLessons": steps.get("past_lessons", "No data"),
        "research": steps.get("debate", "No data"),
        "trading": trading_formatted,
        # Note: lessonSummary runs in background, stored in Qdrant for next analysis
    }

    # Collect step-level errors for system logs
    step_errors = []
    step_names = {
        "fundamentals": "Step 1: Fundamentals",
        "sentiment": "Step 2: Sentiment & Social",
        "technical": "Step 3: Technical",
        "market": "Step 4: Market Overview",
        "global_economic": "Step 5: Global Economy",
        "fund_holding": "Step 6: Fund Holdings",
        "past_lessons": "Step 7: Past Lessons",
        "bull": "Step 8.1: Bull Analysis",
        "bear": "Step 8.2: Bear Analysis",
        "debate": "Step 8.3: Debate",
        "trading": "Step 9: Trading Plan",
    }

    for step_key, step_name in step_names.items():
        step_value = steps.get(step_key, "")
        if isinstance(step_value, str) and step_value.startswith("[ERROR]"):
            error_msg = step_value.replace("[ERROR] ", "")
            step_errors.append(f"❌ {step_name}: {error_msg}")

    # Add pipeline-level errors
    for error in errors:
        if error not in [e.split(": ", 1)[-1] for e in step_errors]:
            step_errors.append(f"⚠️ {error}")

    # Create markdown report file
    os.makedirs('results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    result_file = f'results/result_{symbol}_{timestamp}.md'
    timestamp_in_report = datetime.now().strftime('%Y-%m-%d %H:%M')

    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(f"# FinAgent Analysis Report\n")
        f.write(f"Symbol: {symbol}, ")
        f.write(f"Period: {pipeline_result.get('investment_period', 'N/A')}, ")
        f.write(f"Timestamp: {timestamp_in_report}\n\n")

        for key, value in reports.items():
            f.write(f"## {key}\n\n")
            f.write(f"{value}\n\n")

        # Add timing info
        f.write(f"""---

## Execution Info

| Metric | Value |
|--------|-------|
| **Started** | {pipeline_result.get('start_time', 'N/A')} |
| **Ended** | {pipeline_result.get('end_time', 'N/A')} |
| **Duration** | {pipeline_result.get('duration_minutes', 'N/A')} minutes |
""")

    return {
        "symbol": symbol,
        "reports": reports,
        "report_path": f"/static/{os.path.basename(result_file)}",
        "timing": {
            "start": pipeline_result.get("start_time"),
            "end": pipeline_result.get("end_time"),
            "duration_minutes": pipeline_result.get("duration_minutes")
        },
        "errors": step_errors,
        "success": pipeline_result.get("success", False)
    }


@app.post("/analyze-batch")
async def analyze_batch(req: AnalyzeRequest):
    if len(req.symbols) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 symbols allowed")

    if not req.symbols:
        raise HTTPException(status_code=400, detail="At least one symbol is required")

    # Run parallel pipeline
    pipeline_results = run_batch_pipeline(req.symbols, req.period)

    # Format results
    results = [format_pipeline_result(pr) for pr in pipeline_results]

    return {"results": results}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if len(req.symbols) == 1:
        symbol = req.symbols[0].strip().upper()
        pipeline_result = run_single_ticket_pipeline(symbol, req.period)
        return format_pipeline_result(pipeline_result)
    else:
        return await analyze_batch(req)


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=UVICORN_PORT)