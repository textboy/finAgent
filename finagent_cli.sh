#!/bin/bash
# Sample commands:
#   ./finagent_cli.sh AAPL medium
#   ./finagent_cli.sh AAPL,GOOG,MSFT medium
#   ./finagent_cli.sh "AAPL GOOG MSFT" medium

if [ -z "$1" ]; then
    echo "Missing stock symbol(s) (e.g., AAPL or AAPL,GOOG,MSFT)"
    exit 1
elif [ -z "$2" ]; then
    echo "Missing period ('short+' within 2 weeks; 'short' from 2 weeks to 1 month; 'medium' from 1 month to 1 year; 'long' from 1 year to 2 years)"
    exit 1
elif [ "$2" != "short+" ] && [ "$2" != "short" ] && [ "$2" != "medium" ] && [ "$2" != "long" ]; then
    echo "Invalid period. Please use 'short+', 'short', 'medium', or 'long'."
    exit 1
else
    # Normalize symbols: replace spaces and semicolons with commas, convert to uppercase
    SYMBOLS=$(echo "$1" | tr ' ' ',' | tr ';' ',' | tr '[:lower:]' '[:upper:]')

    # Validate symbol count (max 5)
    IFS=',' read -ra SYMBOL_ARRAY <<< "$SYMBOLS"
    if [ ${#SYMBOL_ARRAY[@]} -gt 5 ]; then
        echo "Warning: Maximum 5 symbols allowed. Only first 5 will be analyzed."
        SYMBOLS=$(IFS=','; echo "${SYMBOL_ARRAY[*]:0:5}")
    fi

    echo "Analyzing: $SYMBOLS"
    echo "Period: $2"
    echo ""

    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR" || exit 1

    # Set API key from FINAGENT_ZENMUX_API_KEY (always prefer this)
    if [ -n "$FINAGENT_ZENMUX_API_KEY" ]; then
        export ZENMUX_API_KEY="$FINAGENT_ZENMUX_API_KEY"
    fi

    # Activate virtual environment if it exists
    if [ -f "finagent/bin/activate" ]; then
        source finagent/bin/activate
    fi

    python finagent_cli.py --symbol "$SYMBOLS" --period "$2"

    # Deactivate virtual environment if it was activated
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
fi
