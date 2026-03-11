#!/bin/bash
cd /app/workspace/finAgent
source finagent/bin/activate
exec python finagent_api.py
