#!/bin/bash
cd /app/workspace/finAgent
source finagent/bin/activate
export OPENROUTER_API_KEY="${AGNES_API_KEY}"
export ALPHA_VANTAGE_API_KEY="${ALPHA_VANTAGE_API_KEY}"
if [ -n "$OPENROUTER_API_KEY" ]; then
  echo "LLM API Key OK"
else
  echo "ERROR: LLM API Key is not set"
  exit 1
fi
exec /app/workspace/finAgent/finagent/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker finagent_api:app --bind 0.0.0.0:8000 --timeout 480 --log-level debug
