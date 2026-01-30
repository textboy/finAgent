#!/bin/bash
cd /app/workspace/finAgent
source finagent/bin/activate
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker finagent_api:app --bind 0.0.0.0:8000
