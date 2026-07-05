#!/bin/bash
cd /app/workspace/finAgent
source finagent/bin/activate

# API Keys
export ZENMUX_API_KEY="${FINAGENT_ZENMUX_API_KEY}"
export AGNES_API_KEY="${AGNES_API_KEY}"
export NVIDIA_API_KEY="${NVIDIA_API_KEY}"

# Validation
if [ -n "$ZENMUX_API_KEY" ]; then
  echo "ZenMux API Key OK"
else
  echo "ERROR: ZenMux API Key is not set"
  exit 1
fi

if [ -n "$AGNES_API_KEY" ]; then
  echo "Agnes API Key OK"
else
  echo "WARNING: Agnes API Key is not set"
fi

if [ -n "$NVIDIA_API_KEY" ]; then
  echo "NVIDIA API Key OK"
else
  echo "WARNING: NVIDIA API Key is not set"
fi

exec python finagent_api.py
