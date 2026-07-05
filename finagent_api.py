#!/usr/bin/env python3

import os
import json
import time
import logging
import markdown
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from src.workflow_parallel import run_single_ticket_pipeline, run_batch_pipeline
import uvicorn

# Setup logging
os.makedirs('logs', exist_ok=True)
log_filename = f"logs/finagent_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger('finagent')

load_dotenv(os.path.join('config', '.env'))

RUN_MODE = os.getenv("RUN_MODE", "local")
SUPPORTED_MODES = ["local"]
if RUN_MODE not in SUPPORTED_MODES:
    raise ValueError(f"Unsupported RUN_MODE '{RUN_MODE}'. Supported modes: {SUPPORTED_MODES}")

SERVER_HOST = os.getenv("SERVER_HOST")
UVICORN_PORT = os.getenv("UVICORN_PORT")
logger.info(f"SERVER_HOST:{SERVER_HOST}, UVICORN_PORT:{UVICORN_PORT}")
try:
    UVICORN_PORT = int(UVICORN_PORT)
except (ValueError, TypeError) as e:
    logger.error(f"Error converting UVICORN_PORT to an integer: {e}")
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


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinAgent Analysis Report - {symbol}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #a855f7, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            border-bottom: 2px solid #334155;
            padding-bottom: 1rem;
        }}
        h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #94a3b8;
            margin: 2rem 0 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #8b5cf6;
        }}
        h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #cbd5e1;
            margin: 1.5rem 0 0.75rem 0;
        }}
        p {{
            margin-bottom: 1rem;
            color: #94a3b8;
        }}
        strong {{
            color: #f1f5f9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #334155;
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            color: #e2e8f0;
        }}
        td {{
            padding: 0.75rem 1rem;
            border-top: 1px solid #334155;
            color: #94a3b8;
        }}
        tr:hover td {{
            background: #334155;
        }}
        ul, ol {{
            margin: 1rem 0;
            padding-left: 2rem;
            color: #94a3b8;
        }}
        li {{
            margin-bottom: 0.5rem;
        }}
        code {{
            background: #334155;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            color: #22d3ee;
        }}
        pre {{
            background: #1e293b;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid #334155;
        }}
        pre code {{
            background: none;
            padding: 0;
            color: #e2e8f0;
        }}
        blockquote {{
            border-left: 4px solid #8b5cf6;
            padding-left: 1rem;
            margin: 1rem 0;
            color: #94a3b8;
            font-style: italic;
        }}
        hr {{
            border: none;
            border-top: 1px solid #334155;
            margin: 2rem 0;
        }}
        .meta {{
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: #1e293b;
            border-radius: 8px;
            color: #64748b;
        }}
        .meta span {{
            font-size: 0.875rem;
        }}
        a {{
            color: #22d3ee;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 FinAgent Analysis Report</h1>
        <div class="meta">
            <span>Symbol: <strong>{symbol}</strong></span>
            <span>Period: <strong>{period}</strong></span>
            <span>Generated: <strong>{timestamp}</strong></span>
        </div>
        {content}
    </div>
</body>
</html>"""


def md_to_html(md_content: str, symbol: str, period: str, timestamp: str) -> str:
    """Convert markdown content to styled HTML."""
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    return HTML_TEMPLATE.format(
        symbol=symbol,
        period=period,
        timestamp=timestamp,
        content=html_content
    )


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
    timestamp_in_report = datetime.now().strftime('%Y-%m-%d %H:%M')
    investment_period = pipeline_result.get('investment_period', 'N/A')

    # Build markdown content
    md_content = f"# FinAgent Analysis Report\n"
    md_content += f"Symbol: {symbol}, "
    md_content += f"Period: {investment_period}, "
    md_content += f"Timestamp: {timestamp_in_report}\n\n"

    for key, value in reports.items():
        md_content += f"## {key}\n\n"
        md_content += f"{value}\n\n"

    # Add timing info
    md_content += f"""---

## Execution Info

| Metric | Value |
|--------|-------|
| **Started** | {pipeline_result.get('start_time', 'N/A')} |
| **Ended** | {pipeline_result.get('end_time', 'N/A')} |
| **Duration** | {pipeline_result.get('duration_minutes', 'N/A')} minutes |
"""

    # Save markdown file
    md_file = f'results/result_{symbol}_{timestamp}.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # Convert to HTML and save
    html_file = f'results/result_{symbol}_{timestamp}.html'
    html_content = md_to_html(md_content, symbol, investment_period, timestamp_in_report)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return {
        "symbol": symbol,
        "reports": reports,
        "report_path": f"/static/{os.path.basename(html_file)}",
        "timing": {
            "start": pipeline_result.get("start_time"),
            "end": pipeline_result.get("end_time"),
            "duration_minutes": pipeline_result.get("duration_minutes")
        },
        "step_logs": pipeline_result.get("step_logs", []),
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