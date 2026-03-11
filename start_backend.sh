#!/bin/bash
cd /app/workspace/finAgent
source finagent/bin/activate
exec /app/workspace/finAgent/finagent/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker finagent_api:app --bind 0.0.0.0:8000 --timeout 480 --log-level debug
