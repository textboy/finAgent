#!/usr/bin/env python3

import os
import re
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from finagent import main as core_main
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
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001", f"http://{SERVER_HOST}:3001", f"http://{SERVER_HOST}:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="results"), name="static")

class AnalyzeRequest(BaseModel):
    symbol: str
    period: str

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    state, result_file = core_main(req.symbol, req.period)
    
    with open(result_file, 'r', encoding='utf-8') as f:
        content = f.read()
    def extract_analyst(title):
        return state['analyst_insights'][title]
    
    def extract_research(title):
        return state['researcher_results'][title]

    def extract_trading():
        return state['trader_plan']

    reports = {
        "fundamentals": extract_analyst('fundamentals'),
        "sentiment": extract_analyst('sentiment'),
        "technical": extract_analyst('technical'),
        "market": extract_analyst('market'),
        "pastLessons": state.get('past_lessons', ''),
        "research": extract_research('debate'),
        "trading": extract_trading(),
    }
    return {
        "reports": reports,
        "report_path": f"/static/{os.path.basename(result_file)}"
    }

if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=UVICORN_PORT)