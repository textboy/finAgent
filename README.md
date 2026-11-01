# FinAgents
***
AI-Powered Financial Analysis Platform with Multi-Stock Parallel Processing

## Overview
FinAgents is a multi-agent trading framework that mirrors real-world trading firms. By deploying LLM-powered agents: from fundamental analysts, sentiment experts, and technical analysts, to trader, risk management team, the platform collaboratively evaluates market conditions and informs trading decisions.

![Flow Design](./design/finAgentFlow.png)

## Key Features

### 🚀 Parallel Processing
- **Multi-Stock Analysis**: Analyze 1-5 stocks simultaneously
- **Inner Parallelism**: Steps 1-7 run in parallel per stock (7 workers)
- **Bull/Bear Parallel**: Step 8.1 and 8.2 run concurrently

### 🔍 Searchable Ticker Input
- Type company name, alias, or ticker to search
- Example: "google" → shows GOOG, GOOGL
- Keyboard navigation (↑/↓/Enter/Tab)
- Supports comma/semicolon separators
- Maximum 5 symbols per analysis

### 📊 10-Step Analysis Pipeline
| Step | Name | Data Source | LLM Provider |
|------|------|-------------|--------------|
| 1 | Fundamentals | yfinance | - |
| 2 | Sentiment & Social | yfinance + Reddit | - |
| 3 | Technical | yfinance (SMA/EMA/RSI/MACD/BB/VWAP/Volume) | - |
| 4 | Market Overview | yfinance | - |
| 5 | Global Economy | World Bank API | - |
| 6 | Fund Holdings | - | sapiens-ai/agnes-2.5-flash (ZenMux) |
| 7 | Past Lessons | Qdrant DB | - |
| 8.1 | Bull Analysis | - | xiaomi/mimo-v2.6-flash (ZenMux) |
| 8.2 | Bear Analysis | - | minimax/minimax-h3 (ZenMux) |
| 8.3 | Research Debate | - | openai/gpt-6-luna (Azure) |
| 9 | Trading Plan | - | openai/gpt-6-luna (Azure) |
| 10 | Lesson Summary | - | sapiens-ai/agnes-2.5-flash (ZenMux, background) |

#### Technical Indicators (Step 3)
- **Trend**: SMA-50, SMA-100, EMA-10
- **Momentum**: RSI, MACD + Signal line
- **Volatility**: Bollinger Bands, VWAP
- **Volume**: Volume SMA-10/20/50, Relative Volume (RVOL), Volume Spike Detection, Price-Volume Divergence

#### Trading Plan Exit Strategy (Step 9)
| Rule | Description |
|------|-------------|
| FTA Exit | Cut trades at First Trouble Area (resistance/support) |
| Time Stop | Exit if target not reached within max holding period |
| 0.9R Rule | Take partial profits at 0.9R gain, move stop to breakeven |

### 🤖 Multi-Provider LLM Support
| Provider | URL | API Key |
|----------|-----|---------|
| ZenMux | https://zenmux.ai/api/v1 | FINAGENT_ZENMUX_API_KEY |
| Agnes AI | https://apihub.agnes-ai.com/v1 | AGNES_API_KEY |
| NVIDIA | https://integrate.api.nvidia.com/v1 | NVIDIA_API_KEY |

- API key automatically selected based on URL prefix
- Each step can use different models/providers

### 📱 Mobile Responsive UI
- Responsive design for iOS/Android devices
- Touch-friendly buttons (48px minimum)
- Collapsible panels for easy navigation
- Floating "Go to Top" button

### 📈 Additional Features
- Warren Buffett's 5 core principles for long-term analysis
- Reddit sentiment integration
- HTML report generation with collapsible sections
- Step progress logs in System Logs
- Stop button for analysis cancellation
- Server-side logging
- History reports viewer

## Installation

### Quick Start (Linux/Mac)
```shell
# Clone repository
git clone https://github.com/textboy/finAgent.git
cd finAgent

# Run local server (handles everything)
./start_server.sh local
```

### Quick Start (Windows)
```cmd
finagent_cli.cmd
```

### Prerequisites
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download) (Python 3.12 managed by conda)
- Node.js (for frontend build)

#### Production Only
- [Nginx](https://nginx.org/) (reverse proxy for HTTPS and static assets)

```shell
# Ubuntu/Debian
sudo apt update && sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx

# macOS (via Homebrew)
brew install nginx
```

### Manual Setup

#### Conda Environment
```shell
# Create conda environment with Python 3.12
conda create -n finagent python=3.12
conda activate finagent

# Install dependencies
pip install -r requirements.txt
```

#### Frontend
```shell
cd web
npm install
npm run build
```

#### Nginx Setup (Production)

Create a snippet for each project:
```shell
sudo nano /etc/nginx/snippets/finagent.conf
```

```nginx
# FinAgent — streams analysis logs over Server-Sent Events (EventSource)
location /finagent/ {
    proxy_pass http://127.0.0.1:8001/finagent/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;

    # SSE: don't buffer/gzip the stream or events arrive in bursts.
    # (Eggplant uses a WebSocket for the mic and needs Connection "upgrade";
    #  FinAgent uses SSE and wants Connection ''.)
    proxy_buffering off;
    proxy_cache off;
    gzip off;
    proxy_set_header Connection '';

    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
}

location = /finagent {
    return 301 /finagent/;
}
```

Main server block (`/etc/nginx/sites-available/default-server`).
TLS is terminated by nginx (Let's Encrypt certificates); FinAgent is proxied to
Gunicorn on `127.0.0.1:8001` over both HTTP and HTTPS:

```nginx
# HTTP: ACME challenge (cert issuance/renewal) + FinAgent
server {
    listen 80;
    server_name 62.146.234.147;

    # Let's Encrypt ACME challenge
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    include /etc/nginx/snippets/finagent.conf;
    # include /etc/nginx/snippets/other-project.conf;
}

# HTTPS: FinAgent served over TLS
server {
    listen 443 ssl;
    server_name 62.146.234.147;

    ssl_certificate     /etc/letsencrypt/live/62.146.234.147/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/62.146.234.147/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    include /etc/nginx/snippets/finagent.conf;
    # include /etc/nginx/snippets/other-project.conf;
}
```

```shell
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/default-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Access: https://62.146.234.147/finagent/

> When hosting multiple projects on the same server, add each project's snippet
> (`include /etc/nginx/snippets/<project>.conf;`) to **both** the `80` and `443`
> blocks so every project is reachable over HTTPS.

##### Hardening (optional)

Enable HTTP/2 and add TLS/security-header hardening in the `443` block:

```nginx
server {
    listen 443 ssl http2;   # nginx >= 1.25.1: use "listen 443 ssl;" + "http2 on;"
    server_name 62.146.234.147;

    ssl_certificate     /etc/letsencrypt/live/62.146.234.147/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/62.146.234.147/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    add_header X-Content-Type-Options nosniff                         always;
    add_header X-Frame-Options        SAMEORIGIN                      always;
    add_header Referrer-Policy        strict-origin-when-cross-origin always;
    # HSTS is ignored by browsers on a bare-IP host; enable once on a domain:
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    server_tokens off;

    include /etc/nginx/snippets/finagent.conf;
    include /etc/nginx/snippets/eggplant.conf;
}
```

To force all HTTP (except ACME) to HTTPS, replace the app includes in the `80`
block with:

```nginx
location / { return 301 https://$host$request_uri; }
```

Enable gzip in `http {}` (e.g. `/etc/nginx/conf.d/gzip.conf`). Keep
`text/event-stream` out of `gzip_types` so SSE isn't buffered:

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 5;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;
```

Rate-limit login brute-force attempts. In `http {}`:

```nginx
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
```

then in the `443` block, before `include finagent.conf;`:

```nginx
location = /finagent/api/login {
    limit_req zone=login_limit burst=5 nodelay;
    proxy_pass http://127.0.0.1:8001/finagent/api/login;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

> **Note:** on a bare-IP host, browsers ignore HSTS and OCSP stapling adds little.
> A real domain name unlocks auto-renewing Let's Encrypt certs, HSTS, and OCSP.

#### Qdrant (Optional)
FinAgent uses a lightweight file-based Qdrant by default (no Docker needed).
To run a standalone Qdrant server instead:
```shell
# Requires Docker
docker run -d --name qdrant-finagent -p 6333:6333 qdrant/qdrant:1.16.0
```

## Configuration

### 1. Environment Variables
```shell
# Required
export FINAGENT_ZENMUX_API_KEY="your-zenmux-api-key"

# Optional (for additional providers)
export AGNES_API_KEY="your-agnes-api-key"
export NVIDIA_API_KEY="your-nvidia-api-key"
```

### 2. LLM Configuration (config/.env)
Each step can use different models and providers:

```env
# Step 6: Fund Holdings
FUND_HOLDING_MODEL=sapiens-ai/agnes-2.5-flash
FUND_HOLDING_URL=https://zenmux.ai/api/v1

# Step 8.1: Bull Analysis
BULL_MODEL=xiaomi/mimo-v2.6-flash
BULL_URL=https://zenmux.ai/api/v1

# Step 8.2: Bear Analysis
BEAR_MODEL=minimax/minimax-h3
BEAR_URL=https://zenmux.ai/api/v1

# Step 8.3: Research Debate
DEBATE_MODEL=openai/gpt-6-luna
DEBATE_URL=https://zenmux.ai/api/v1

# Step 9: Trading Plan
TRADING_MODEL=openai/gpt-6-luna
TRADING_URL=https://zenmux.ai/api/v1

# Step 10: Lesson Summary
LESSON_MODEL=sapiens-ai/agnes-2.5-flash
LESSON_URL=https://zenmux.ai/api/v1
```

## Execution

### Web UI (Recommended)

#### Start Server
```shell
# Local development
./start_server.sh local

# Production (remote server)
./start_server.sh production
```

- **Backend**: http://localhost:8001 (local) or https://62.146.234.147/finagent/ (production with nginx)
- **Frontend**: Automatically built and served by backend

### CLI
```shell
# Single symbol
./finagent_cli.sh AAPL short

# Multiple symbols
./finagent_cli.sh AAPL,GOOG,MSFT medium

# Windows
finagent_cli.cmd AAPL short
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
      "report_path": "/static/result_AAPL_20260708_1200.html",
      "timing": { "start": "...", "end": "...", "duration_minutes": 2.5 },
      "step_logs": ["✅ [AAPL] Fundamentals completed (0.18 min)", ...],
      "errors": [],
      "success": true
    }
  ]
}
```

### GET /api/history-reports
List available HTML reports.

### GET /
API status and available endpoints.

## Project Structure
```
finAgent/
├── config/
│   └── .env                  # LLM & API configuration
├── src/
│   ├── agents/
│   │   ├── analyst_agents.py      # Steps 1-4: Data analysis
│   │   ├── fund_holding_agent.py  # Step 6: Fund holdings
│   │   ├── global_economic_agent.py # Step 5: Global economy
│   │   ├── lesson_summary_agent.py # Step 10: Lesson summary
│   │   ├── researcher_agents.py   # Steps 8.1-8.3: Bull/Bear/Debate
│   │   └── trading_risk_agents.py # Step 9: Trading plan
│   ├── tools/
│   │   └── analyst_tools.py   # Data fetching utilities
│   ├── utils/
│   │   ├── api_key_selector.py    # API key routing by URL
│   │   ├── data_fetchers.py       # yfinance wrapper
│   │   ├── llm_client.py          # Shared LLM client
│   │   ├── qdrant_utils.py        # Vector DB utilities
│   │   └── yfinance_compat.py     # yfinance compatibility
│   └── workflow_parallel.py   # Parallel pipeline orchestration
├── web/
│   ├── public/
│   │   └── ticket_mapping.json    # Ticker search database
│   └── src/
│       ├── App.jsx                # Main UI
│       ├── Introduction.jsx       # Pipeline documentation
│       └── main.jsx               # React entry
├── test/
│   └── test_regression.py     # Pipeline regression tests
├── logs/                       # Server logs (gitignored)
├── results/                    # Analysis reports (gitignored)
├── finagent_api.py             # FastAPI backend
├── finagent_cli.py             # CLI interface
├── finagent_cli.sh             # Shell wrapper
├── start_server.sh             # Server startup (local | production)
└── requirements.txt
```

## Testing

### Run Regression Tests
```shell
# All steps
python test/test_regression.py

# Specific steps
python test/test_regression.py --step 1,2,3
python test/test_regression.py --step 8.1,8.2

# Different symbol
python test/test_regression.py --symbol NVDA --period medium
```

### Available Test Steps
| Step | Name |
|------|------|
| 1 | Fundamentals |
| 2 | Sentiment & Social |
| 3 | Technical |
| 4 | Market Overview |
| 5 | Global Economy |
| 6 | Fund Holdings |
| 7 | Past Lessons |
| 8.1 | Bull Analysis |
| 8.2 | Bear Analysis |
| 8.3 | Research Debate |
| 9 | Trading Plan |

## Logging
Server logs are stored in `logs/` folder:
```
logs/finagent_20260708.log
```

## Reports
Analysis reports are generated in both Markdown and HTML formats:
```
results/result_AAPL_20260708_1200.md
results/result_AAPL_20260708_1200.html
```

## Disclaimer
Trading performance may vary based on many factors, including the chosen backbone language models, model temperature, trading periods, the quality of data, and other non-deterministic factors. It is not intended as financial, investment, or trading advice.
