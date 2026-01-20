#!/bin/bash
# sample command: .\finagent.sh GLD short

if [ -z "$1" ]; then
    echo "Missing stock symbol (e.g., GOOG)"
    exit 1
elif [ -z "$2" ]; then
    echo "Missing period ('short+' within 2 weeks; 'short' from 2 weeks to 1 month; 'medium' from 1 month to 1 year; 'long' from 1 year to 2 years)"
    exit 1
elif [ "$2" != "short+" ] && [ "$2" != "short" ] && [ "$2" != "medium" ] && [ "$2" != "long" ]; then
    echo "Invalid period. Please use 'short+', 'short', 'medium', or 'long'."
    exit 1
else
    # configure your workspace
    cd /app/workspace/finAgent || exit 1
    source finagent/bin/activate
    python finagent.py --symbol "$1" --period "$2"
    deactivate
fi