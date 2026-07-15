#!/usr/bin/env python3

import os
import json
import time
import logging
import markdown
import threading
import uuid
from datetime import datetime, timedelta
from typing import List
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from src.workflow_parallel import run_single_ticket_pipeline, run_batch_pipeline
import uvicorn

# Hardcoded credentials
VALID_USERNAME = "carina666"
VALID_PASSWORD = "calcutta"
SESSION_COOKIE_NAME = "finagent_session"
SESSION_EXPIRY_DAYS = 30

# Background job storage
from src.job_store import _jobs, _jobs_lock

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
SUPPORTED_MODES = ["local", "production"]
if RUN_MODE not in SUPPORTED_MODES:
    raise ValueError(f"Unsupported RUN_MODE '{RUN_MODE}'. Supported modes: {SUPPORTED_MODES}")

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0" if RUN_MODE == "production" else "localhost")
PRODUCTION_HOST = os.getenv("PRODUCTION_HOST", "5ngc.s.time4vps.cloud")
UVICORN_PORT = os.getenv("UVICORN_PORT")
logger.info(f"RUN_MODE:{RUN_MODE}, SERVER_HOST:{SERVER_HOST}, PRODUCTION_HOST:{PRODUCTION_HOST}, UVICORN_PORT:{UVICORN_PORT}")
try:
    UVICORN_PORT = int(UVICORN_PORT)
except (ValueError, TypeError) as e:
    logger.error(f"Error converting UVICORN_PORT to an integer: {e}")
    UVICORN_PORT = 8000

app = FastAPI(title="FinAgent API")

# CORS configuration - allow all origins (public API, no auth)
cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Authentication ============

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def login(req: LoginRequest, response: Response):
    """Login with hardcoded credentials. Sets session cookie."""
    if req.username == VALID_USERNAME and req.password == VALID_PASSWORD:
        session_token = str(uuid.uuid4())
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            max_age=SESSION_EXPIRY_DAYS * 24 * 3600,  # 30 days
            httponly=True,
            samesite="lax",
        )
        return {"status": "ok", "username": req.username}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/session")
async def get_session(request: Request):
    """Check if user is logged in via session cookie."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return {"status": "ok", "username": VALID_USERNAME}
    raise HTTPException(status_code=401, detail="Not logged in")

@app.post("/api/logout")
async def logout(response: Response):
    """Clear session cookie."""
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"status": "ok"}

app.mount("/static", StaticFiles(directory="results"), name="static")

# Mount frontend build files (if exists)
WEB_DIST_DIR = os.path.join(os.path.dirname(__file__), "web", "dist")
WEB_PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "web", "public")
if os.path.exists(WEB_DIST_DIR):
    # Mount assets directory for CSS/JS files
    app.mount("/assets", StaticFiles(directory=os.path.join(WEB_DIST_DIR, "assets")), name="assets")
    # Mount public directory for ticket_mapping.json etc
    if os.path.exists(WEB_PUBLIC_DIR):
        app.mount("/public", StaticFiles(directory=WEB_PUBLIC_DIR), name="public")
    # Mount root for index.html
    app.mount("/app", StaticFiles(directory=WEB_DIST_DIR, html=True), name="frontend")


@app.get("/")
async def root():
    """Root endpoint - serves frontend or returns API status."""
    if os.path.exists(WEB_DIST_DIR):
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(WEB_DIST_DIR, "index.html"))
    return {
        "name": "FinAgent API",
        "version": "1.0.0",
        "status": "running",
        "run_mode": RUN_MODE,
        "endpoints": {
            "analyze": "/analyze",
            "analyze_batch": "/analyze-batch",
            "history_reports": "/api/history-reports",
            "docs": "/docs",
            "static_reports": "/static/",
            "frontend": "/app" if os.path.exists(WEB_DIST_DIR) else None
        },
        "production_url": f"http://{PRODUCTION_HOST}:{UVICORN_PORT}" if RUN_MODE == "production" else None
    }


class AnalyzeRequest(BaseModel):
    symbols: List[str]
    period: str


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinAgent Analysis Report - {symbol}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%);
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}
        /* Glass panel effect */
        .glass-panel {{
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(51, 65, 85, 0.5);
        }}
        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.1));
            border-radius: 1rem;
            border: 1px solid rgba(139, 92, 246, 0.3);
        }}
        .header h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #a855f7, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }}
        .meta {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #94a3b8;
            font-size: 0.875rem;
        }}
        .meta-item strong {{
            color: #e2e8f0;
        }}
        .meta-icon {{
            width: 1.25rem;
            height: 1.25rem;
            opacity: 0.7;
        }}
        /* Section panels */
        .section {{
            margin-bottom: 0.75rem;
            border-radius: 0.75rem;
            overflow: hidden;
            border: 1px solid rgba(51, 65, 85, 0.5);
            transition: border-color 0.2s;
        }}
        .section:hover {{
            border-color: rgba(71, 85, 105, 0.5);
        }}
        .section-header {{
            padding: 0.75rem 1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
            user-select: none;
        }}
        .section-header:hover {{
            background: rgba(51, 65, 85, 0.4);
        }}
        .section-header-left {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        .section-icon {{
            width: 1.75rem;
            height: 1.75rem;
            border-radius: 0.375rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
            flex-shrink: 0;
        }}
        .section-title {{
            font-size: 0.75rem;
            font-weight: 700;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        .section-arrow {{
            color: #94a3b8;
            transition: transform 0.2s;
            width: 14px;
            height: 14px;
        }}
        .section.open .section-arrow {{
            transform: rotate(180deg);
        }}
        .section-content {{
            padding: 1rem 1.25rem;
            border-top: 1px solid rgba(51, 65, 85, 0.3);
            background: linear-gradient(180deg, rgba(2, 6, 23, 0.5), rgba(15, 23, 42, 0.3));
        }}
        /* Section colors - match homepage panel colors */
        .section .section-header {{ background: linear-gradient(90deg, rgba(51, 65, 85, 0.4), rgba(71, 85, 105, 0.2)); }}
        .section .section-icon {{ background: linear-gradient(135deg, #475569, #334155); }}
        .section-quant .section-header {{ background: linear-gradient(90deg, rgba(51, 65, 85, 0.4), rgba(6, 182, 212, 0.2)); }}
        .section-quant .section-icon {{ background: linear-gradient(135deg, #475569, #0891b2); }}
        .section-trading .section-header {{ background: linear-gradient(90deg, rgba(71, 85, 105, 0.3), rgba(6, 182, 212, 0.3)); border-left: 3px solid #06b6d4; }}
        .section-trading .section-icon {{ background: linear-gradient(135deg, #475569, #0891b2); }}
        /* Content styling */
        h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(51, 65, 85, 0.5);
        }}
        h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #e2e8f0;
            margin: 1.5rem 0 0.75rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        h2::before {{
            content: '';
            width: 0.5rem;
            height: 0.5rem;
            background: #8b5cf6;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        h3 {{
            font-size: 1rem;
            font-weight: 500;
            color: #cbd5e1;
            margin: 1rem 0 0.5rem 0;
        }}
        p {{
            margin-bottom: 0.75rem;
            color: #94a3b8;
            font-size: 0.875rem;
            line-height: 1.7;
        }}
        strong {{
            color: #f1f5f9;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            border-radius: 0.5rem;
            overflow: hidden;
            border: 1px solid rgba(51, 65, 85, 0.5);
        }}
        thead {{
            background: rgba(15, 23, 42, 0.6);
        }}
        th {{
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            color: #cbd5e1;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid rgba(51, 65, 85, 0.5);
        }}
        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid rgba(51, 65, 85, 0.3);
            color: #94a3b8;
            font-size: 0.875rem;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover td {{
            background: rgba(51, 65, 85, 0.2);
        }}
        ul, ol {{
            margin: 0.75rem 0;
            padding-left: 1.5rem;
            color: #94a3b8;
            font-size: 0.875rem;
        }}
        li {{
            margin-bottom: 0.375rem;
            line-height: 1.6;
        }}
        code {{
            background: rgba(51, 65, 85, 0.5);
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8125rem;
            color: #22d3ee;
            border: 1px solid rgba(51, 65, 85, 0.5);
        }}
        pre {{
            background: rgba(15, 23, 42, 0.8);
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid rgba(51, 65, 85, 0.5);
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
        /* Collapsible sections */
        details {{
            margin: 1rem 0;
            border: 1px solid #334155;
            border-radius: 8px;
            overflow: hidden;
        }}
        details summary {{
            padding: 1rem 1.5rem;
            background: #1e293b;
            cursor: pointer;
            font-weight: 600;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            user-select: none;
            transition: background 0.2s;
        }}
        details summary:hover {{
            background: #334155;
        }}
        details summary::marker {{
            content: '';
        }}
        details summary::before {{
            content: '▶';
            font-size: 0.75rem;
            transition: transform 0.2s;
        }}
        details[open] summary::before {{
            transform: rotate(90deg);
        }}
        details .content {{
            padding: 1rem 1.5rem;
            border-top: 1px solid #334155;
        }}
        /* Trading plan always open */
        details.trading-plan {{
            border-color: #8b5cf6;
        }}
        details.trading-plan summary {{
            background: linear-gradient(90deg, rgba(139, 92, 246, 0.2), rgba(6, 182, 212, 0.2));
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 FinAgent Analysis Report</h1>
            <div class="meta">
                <div class="meta-item">
                    <svg class="meta-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"></path><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                    <span>Symbol: <strong>{symbol}</strong></span>
                </div>
                <div class="meta-item">
                    <svg class="meta-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    <span>Period: <strong>{period}</strong></span>
                </div>
                <div class="meta-item">
                    <svg class="meta-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    <span>Generated: <strong>{timestamp}</strong></span>
                </div>
            </div>
        </div>
        {content}
        <footer style="text-align: center; padding: 2rem 0; color: #475569; font-size: 0.75rem; border-top: 1px solid rgba(51, 65, 85, 0.3); margin-top: 2rem;">
            <p>© 2026 FinAgent. AI-Powered Financial Analysis Platform.</p>
            <p style="margin-top: 0.5rem; color: #334155;">All analysis is generated by AI and should be used for informational purposes only.</p>
        </footer>
    </div>
    <script>
    document.querySelectorAll('.section-header').forEach(header => {{
        header.addEventListener('click', () => {{
            const section = header.parentElement;
            section.classList.toggle('open');
            const content = section.querySelector('.section-content');
            if (content) {{
                content.style.display = section.classList.contains('open') ? 'block' : 'none';
            }}
        }});
    }});
    // Open trading plan by default
    const tradingSection = document.querySelector('.section-trading');
    if (tradingSection) {{
        tradingSection.classList.add('open');
        const content = tradingSection.querySelector('.section-content');
        if (content) content.style.display = 'block';
    }}
    </script>
</body>
</html>"""


def md_to_html(md_content: str, symbol: str, period: str, timestamp: str) -> str:
    """Convert markdown content to styled HTML with collapsible sections."""
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

    # Wrap h2 sections in collapsible div tags
    import re

    # Section mapping: keyword -> (css class, icon emoji)
    # Only main h2 sections are mapped here
    section_mapping = {
        'fundamentals': ('section-fundamentals', '📊'),
        'sentiment': ('section-sentiment', '💬'),
        'technical': ('section-technical', '📈'),
        'market overview': ('section-market', '🌍'),
        'global economic': ('section-global', '🌐'),
        'global economy': ('section-global', '🌐'),
        'fund holding': ('section-fundholding', '🏦'),
        'past lesson': ('section-pastlessons', '📚'),
        'research debate': ('section-research', '🧠'),
        'research': ('section-research', '🧠'),
        'quant': ('section-quant', '📐'),
        'trading plan': ('section-trading', '🎯'),
        'trader plan': ('section-trading', '🎯'),
        'trading': ('section-trading', '🎯'),
        'execution info': ('section-trading', '🎯'),
        'decision summary': ('section-trading', '🎯'),
        'rationale': ('section-trading', '🎯'),
    }

    # Helper to find section class for a header
    def find_section_class(header_text):
        for keyword, (css_class, icon) in section_mapping.items():
            if keyword in header_text:
                return css_class, icon
        return None, '📄'

    # Process content - group h2 sections and nest h3 inside them
    wrapped_content = ''
    current_section = None
    current_section_content = ''
    current_section_icon = '📄'

    # Split by h1 and h2 headers
    h_pattern = r'(<h[12][^>]*>.*?</h[12]>)'
    parts = re.split(h_pattern, html_content, flags=re.DOTALL)

    i = 0
    while i < len(parts):
        part = parts[i]

        if part.startswith('<h1') or part.startswith('<h2'):
            # Extract header text
            header_text = re.sub(r'<[^>]+>', '', part).lower().strip()
            section_class, section_icon = find_section_class(header_text)

            if section_class:
                # Clean header text
                clean_header = re.sub(r'<h[12][^>]*>', '', part)
                clean_header = re.sub(r'</h[12]>', '', clean_header)

                # If same section class, merge content instead of creating new section
                if current_section == section_class:
                    current_section_content += part
                else:
                    # Close previous section if exists
                    if current_section:
                        wrapped_content += f'<div class="section-content" style="display: none;">{current_section_content}</div>'
                        wrapped_content += '</div>'

                    # Start new section
                    current_section = section_class
                    current_section_content = ''
                    current_section_icon = section_icon
                    wrapped_content += f'<div class="section {section_class}">'
                    wrapped_content += f'<div class="section-header">'
                    wrapped_content += f'<div class="section-header-left">'
                    wrapped_content += f'<div class="section-icon">{section_icon}</div>'
                    wrapped_content += f'<span class="section-title">{clean_header}</span>'
                    wrapped_content += f'</div>'
                    wrapped_content += f'<svg class="section-arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>'
                    wrapped_content += f'</div>'
            else:
                # No matching section - close previous and output directly
                if current_section:
                    wrapped_content += f'<div class="section-content" style="display: none;">{current_section_content}</div>'
                    wrapped_content += '</div>'
                    current_section = None
                    current_section_content = ''
                wrapped_content += part

        else:
            # Regular content (includes h3 and everything else)
            if current_section:
                current_section_content += part
            else:
                wrapped_content += part

        i += 1

    # Close last section if exists
    if current_section:
        wrapped_content += f'<div class="section-content" style="display: none;">{current_section_content}</div>'
        wrapped_content += '</div>'

    return HTML_TEMPLATE.format(
        symbol=symbol,
        period=period,
        timestamp=timestamp,
        content=wrapped_content
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
        "quant": steps.get("quant", "No data"),
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
        "quant": "Step 8.Q: Quant Analysis",
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

    # Sanitize period for filename (replace spaces with hyphens, lowercase)
    period_slug = investment_period.lower().replace(' ', '-').replace('+', 'plus') if investment_period != 'N/A' else 'unknown'

    # Build markdown content
    md_content = f"# FinAgent Analysis Report\n"
    md_content += f"Symbol: {symbol}, "
    md_content += f"Period: {investment_period}, "
    md_content += f"Timestamp: {timestamp_in_report}\n\n"

    # Report section display names
    section_names = {
        "fundamentals": "Fundamentals Analysis",
        "sentiment": "Sentiment & Social Analysis",
        "technical": "Technical Analysis",
        "market": "Market Overview",
        "globalEconomic": "Global Economy Analysis",
        "fundHolding": "Fund Holdings Analysis",
        "pastLessons": "Past Lessons",
        "research": "Research Debate (Bull vs Bear)",
        "quant": "Quant Signals (Triple-Barrier & Trend)",
        "trading": "Trading Plan",
    }

    for key, value in reports.items():
        display_name = section_names.get(key, key)
        md_content += f"## {display_name}\n\n"
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
    md_file = f'results/result_{symbol}_{period_slug}_{timestamp}.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # Convert to HTML and save
    html_file = f'results/result_{symbol}_{period_slug}_{timestamp}.html'
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
        "success": pipeline_result.get("success", False),
        "cost_summary": pipeline_result.get("cost_summary", {
            "total_cost": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "by_model": {}
        })
    }


@app.post("/analyze-batch")
async def analyze_batch(req: AnalyzeRequest):
    if len(req.symbols) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 symbols allowed")

    if not req.symbols:
        raise HTTPException(status_code=400, detail="At least one symbol is required")

    # Create job and run in background
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {"status": "running", "result": None, "error": None, "step_logs": [], "progress": {}}

    def _run_job():
        try:
            pipeline_results = run_batch_pipeline(req.symbols, req.period, job_id=job_id)
            results = [format_pipeline_result(pr) for pr in pipeline_results]
            with _jobs_lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = results
        except Exception as e:
            with _jobs_lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = str(e)

    thread = threading.Thread(target=_run_job, daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "running"}


@app.get("/analyze-status/{job_id}")
async def analyze_status(job_id: str):
    """Poll for analysis job status. No-cache headers prevent mobile browser caching."""
    from fastapi.responses import JSONResponse

    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        with _jobs_lock:
            _jobs.pop(job_id, None)
        return JSONResponse(
            content={"status": "completed", "results": job["result"]},
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
    elif job["status"] == "failed":
        with _jobs_lock:
            _jobs.pop(job_id, None)
        return JSONResponse(
            content={"status": "failed", "error": job["error"]},
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
    else:
        return JSONResponse(
            content={"status": "running", "step_logs": job.get("step_logs", []), "progress": job.get("progress", {})},
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if len(req.symbols) == 1:
        symbol = req.symbols[0].strip().upper()
        pipeline_result = run_single_ticket_pipeline(symbol, req.period)
        return format_pipeline_result(pipeline_result)
    else:
        return await analyze_batch(req)


@app.get("/api/history-reports")
async def get_history_reports():
    """Get list of all HTML reports in the results folder."""
    results_dir = "results"
    if not os.path.exists(results_dir):
        return {"reports": []}

    reports = []
    for filename in sorted(os.listdir(results_dir), reverse=True):
        if filename.endswith(".html"):
            # Extract info from filename: result_SYMBOL_PERIOD_YYYYMMDD_HHMM.html
            # or old format: result_SYMBOL_YYYYMMDD_HHMM.html
            parts = filename.replace("result_", "").replace(".html", "").split("_")

            if len(parts) >= 4:
                # New format: SYMBOL_PERIOD_YYYYMMDD_HHMM
                symbol = parts[0]
                # Period might contain underscores, so join middle parts
                time_str = parts[-1]  # HHMM
                date = parts[-2]  # YYYYMMDD
                period = "_".join(parts[1:-2])  # Everything between symbol and date
                display = f"{symbol} - {period} - {date[:4]}-{date[4:6]}-{date[6:]} {time_str[:2]}:{time_str[2:]}"
            elif len(parts) >= 3:
                # Old format: SYMBOL_YYYYMMDD_HHMM
                symbol = parts[0]
                date = parts[1]
                time_str = parts[2]
                display = f"{symbol} - {date[:4]}-{date[4:6]}-{date[6:]} {time_str[:2]}:{time_str[2:]}"
            else:
                display = filename
                symbol = parts[0] if len(parts) >= 1 else "Unknown"
                date = "Unknown"

            reports.append({
                "filename": filename,
                "display": display,
                "symbol": symbol,
                "date": f"{date[:4]}-{date[4:6]}-{date[6:]}" if len(parts) >= 3 else "Unknown",
            })

    return {"reports": reports[:50]}  # Limit to 50 most recent


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=UVICORN_PORT)