#!/bin/bash
cd /app/workspace/finAgent
source finagent/bin/activate
export LLM_API_KEY="${AGNES_API_KEY}"
if [ -n "$LLM_API_KEY" ]; then
  echo "LLM API Key OK"
else
  echo "ERROR: LLM API Key is not set"
  exit 1
fi
exec python finagent_api.py
