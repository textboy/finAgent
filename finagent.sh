#!/bin/bash

if [ -z "$1" ]; then
    echo "Missing stock symbol"
    return
elif [ -z "$2" ]; then
    echo "Missing period ('short+' within 2 weeks; 'short' from 2 weeks to 1 month; 'medium' from 1 month to 1 year; 'long' from 1 year to 2 years)"
    return
elif [ "$2" != "short+" ] && [ "$2" != "short" ] && [ "$2" != "medium" ] && [ "$2" != "long" ]; then
    echo "Invalid period. Please use 'short+', 'short', 'medium', or 'long'."
    return
else
    # configure your workspace
    cd /app/workspace/finAgent || return
    source finagent/bin/activate
    python finagent.py --symbol "$1" --period "$2"
    deactivate
fi