#!/usr/bin/env python3
"""
Test script for get_news_sentiment method in src/utils/data_fetchers.py
"""

import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.data_fetchers import DataFetcher

def main():
    fetcher = DataFetcher()
    symbol = 'AAPL'  # Test with Apple
    data, meta = fetcher.get_news_sentiment(symbol)
    print(f"News sentiment data for {symbol}:")
    print(f"Shape: {data.shape}")
    print(data['ticker_sentiment'][1])
    # news_df = pd.DataFrame(data)
    # print(news_df['ticker_sentiment'][1])
    print("\nMetadata:")
    print(meta)
    print("\nTest completed successfully.")

if __name__ == "__main__":
    main()
