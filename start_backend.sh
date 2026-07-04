#!/bin/bash
cd /app/workspace/finAgent
source finagent/bin/activate
export LLM_API_KEY="${AGNES_API_KEY}"
export BK_LLM_API_KEY="${BK_LLM_API_KEY}"
if [ -n "$LLM_API_KEY" ]; then
  echo "LLM API Key OK"
else
  echo "ERROR: LLM API Key is not set"
  exit 1
fi
exec /app/workspace/finAgent/finagent/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker finagent_api:app --bind 0.0.0.0:8000 --timeout 480 --log-level debug
