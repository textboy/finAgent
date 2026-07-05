# FinAgents
***
AI-Powered Financial Analysis Platform with Multi-Stock Parallel Processing

## Overview
FinAgents is a multi-agent trading framework that mirrors real-world trading firms. By deploying LLM-powered agents: from fundamental analysts, sentiment experts, and technical analysts, to trader, risk management team, the platform collaboratively evaluates market conditions and informs trading decisions.

![Flow Design](./design/finAgentFlow.png)

## Key Features

### 🚀 Parallel Processing
- **Multi-Stock Analysis**: Analyze 1-5 stocks simultaneously
- **Inner Parallelism**: Steps 1-7 run in parallel per stock
- **Bull/Bear Parallel**: Step 8.1 and 8.2 run concurrently

### 🔍 Searchable Ticker Input
- Type company name, alias, or ticker to search
- Example: "google" → shows GOOG, GOOGL
- Keyboard navigation (↑/↓/Enter)
- Supports comma/semicolon separators

### 📊 10-Step Analysis Pipeline
| Step | Name | Data Source | LLM |
|------|------|-------------|-----|
| 1 | Fundamentals | yfinance | - |
| 2 | Sentiment & Social | yfinance + Reddit | - |
| 3 | Technical | yfinance | - |
| 4 | Market Overview | yfinance | - |
| 5 | Global Economy | World Bank API | - |
| 6 | Fund Holdings | - | ✅ agnes-2.0-flash |
| 7 | Past Lessons | Qdrant DB | - |
| 8.1 | Bull Analysis | - | ✅ xiaomi/mimo-v2.5 |
| 8.2 | Bear Analysis | - | ✅ anthropic/claude-sonnet-5-free |
| 8.3 | Research Debate | - | ✅ anthropic/claude-fable-5-free |
| 9 | Trading Plan | - | ✅ anthropic/claude-fable-5-free |
| 10 | Lesson Summary | - | ✅ agnes-2.0-flash (background) |

### 🤖 Multi-Provider LLM Support
- **ZenMux**: https://zenmux.ai/api/v1
- **Agnes AI**: https://apihub.agnes-ai.com/v1
- **NVIDIA**: https://integrate.api.nvidia.com/v1
- API key automatically selected based on URL prefix

### 📈 Additional Features
- Warren Buffett's 5 core principles for long-term analysis
- Reddit sentiment integration
- HTML report generation
- Step progress logs in UI
- Stop button for analysis cancellation
- Server-side logging

## Installation

### Environment Setup

#### Windows
```cmd
./setup.cmd
```

#### Linux/Mac
```shell
./setup.sh
```

#### Frontend
```shell
cd web
npm install
```

### Vector DB Setup (Optional)

#### Windows
```cmd
./vector-db-setup.cmd
```

#### Linux/Mac
```shell
./vector-db-setup.sh
```

## Configuration

### 1. Copy and edit .env file
```shell
cp config/.env.example config/.env
```

### 2. API Keys (Environment Variables)
```shell
# Required
export ZENMUX_API_KEY="your-zenmux-api-key"

# Optional (for additional providers)
export AGNES_API_KEY="your-agnes-api-key"
export NVIDIA_API_KEY="your-nvidia-api-key"
```

### 3. LLM Configuration (config/.env)
Each step can use different models and providers:

```env
# Step 6: Fund Holdings
FUND_HOLDING_MODEL=agnes-2.0-flash
FUND_HOLDING_URL=https://apihub.agnes-ai.com/v1

# Step 8.1: Bull Analysis
BULL_MODEL=xiaomi/mimo-v2.5
BULL_URL=https://zenmux.ai/api/v1

# Step 8.2: Bear Analysis
BEAR_MODEL=anthropic/claude-sonnet-5-free
BEAR_URL=https://zenmux.ai/api/v1

# ... etc
```

## Execution

### Web UI

#### Backend
```shell
# Development
python finagent_api.py

# Production
./start_backend.sh
```
- http://localhost:8000

#### Frontend
```shell
cd web

# Development
npm run dev

# Production
npm run build
npm run preview
```
- http://localhost:3001

### CLI
```shell
# Python
python finagent.py --symbol AAPL,GOOG --period medium

# Shell
./finagent.sh AAPL,GOOG medium
```

**Parameters:**
- **symbol**: Stock ticker(s), comma-separated (max 5)
- **period**: 
  - `short+` - 1-7 days
  - `short` - 1-4 weeks
  - `medium` - 1-6 months
  - `long` - 6+ months (includes Warren Buffett principles)

## API Endpoints

### POST /analyze-batch
Analyze multiple stocks in parallel.

**Request:**
```json
{
  "symbols": ["AAPL", "GOOG", "MSFT"],
  "period": "medium"
}
```

**Response:**
```json
{
  "results": [
    {
      "symbol": "AAPL",
      "reports": { ... },
      "report_path": "/static/result_AAPL_20260705_1200.html",
      "timing": { "start": "...", "end": "...", "duration_minutes": 2.5 },
      "step_logs": ["✅ [AAPL] Fundamentals completed (0.18 min)", ...],
      "errors": [],
      "success": true
    }
  ]
}
```

## Project Structure
```
finAgent/
├── config/
│   └── .env              # Configuration
├── src/
│   ├── agents/
│   │   ├── analyst_agents.py
│   │   ├── fund_holding_agent.py
│   │   ├── global_economic_agent.py
│   │   ├── lesson_summary_agent.py
│   │   ├── researcher_agents.py
│   │   └── trading_risk_agents.py
│   ├── tools/
│   │   └── analyst_tools.py
│   ├── utils/
│   │   ├── api_key_selector.py
│   │   ├── data_fetchers.py
│   │   └── qdrant_utils.py
│   └── workflow_parallel.py
├── web/
│   ├── public/
│   │   └── ticket_mapping.json
│   └── src/
│       └── App.jsx
├── logs/                  # Server logs
├── results/               # Analysis reports (HTML)
├── finagent_api.py        # FastAPI backend
└── requirements.txt
```

## Logging
Server logs are stored in `logs/` folder:
```
logs/finagent_20260705.log
```

## Reports
Analysis reports are generated in both Markdown and HTML formats:
```
results/result_AAPL_20260705_1200.md
results/result_AAPL_20260705_1200.html
```

## Disclaimer
Trading performance may vary based on many factors, including the chosen backbone language models, model temperature, trading periods, the quality of data, and other non-deterministic factors. It is not intended as financial, investment, or trading advice.
