#!/bin/bash

if [ -z "$1" ]; then
    echo "Missing stock symbol"
    return
fi

if [ -z "$2" ]; then
    echo "Missing period ('short+' within 2 weeks; 'short' from 2 weeks to 1 month; 'medium' from 1 month to 1 year; 'long' from 1 year to 2 years)"
    return
fi
cd /app/workspace/finAgent || return
source finagent/bin/activate
python finagent.py --symbol "$1" --period "$2"
deactivate