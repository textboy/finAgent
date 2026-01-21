#!/usr/bin/env python3
"""
Test script for get_macd method in src/tools/analyst_tools.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.analyst_tools import *

def test_macd(symbol, investment_period):
    result = get_macd(symbol, investment_period)
    print(f"MACD result for {symbol} ({investment_period}):")
    return result

def test_sma(data):
    result = get_sma(data, 2)
    return result

def main():
    symbol = 'AAPL'  # Test with Apple
    investment_period = 'medium'
    # result = test_macd(symbol, investment_period)

    data = download_yf_data(symbol)
    print(data)
    result = test_sma(data)
    print(f"result~: {result}")

    print("\nTest completed successfully.")

if __name__ == "__main__":
    main()
