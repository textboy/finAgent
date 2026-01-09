#!/usr/bin/env python3
"""
Test script for get_macd method in src/tools/analyst_tools.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.analyst_tools import get_macd

def main():
    symbol = 'AAPL'  # Test with Apple
    investment_period = 'medium'
    result = get_macd(symbol, investment_period)
    print(f"MACD result for {symbol} ({investment_period}):")
    print(result)
    print("\nTest completed successfully.")

if __name__ == "__main__":
    main()
