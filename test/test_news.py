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
    # print(f"News sentiment data for {symbol}:")
    # data, meta = fetcher.get_news_sentiment(symbol)
    # print(f"Shape: {data.shape}")
    # print(data['ticker_sentiment'][1])
    
    data, meta = fetcher.get_news_sentiment_by_topic("economy_fiscal,economy_monetary,economy_macro")
    print(f"Shape: {data.shape}")
    print(data.columns)
    print(data.title.iloc[1])
    print(data.overall_sentiment_label.iloc[1])
    print(data.topics.iloc[1])

    print("\nTest completed successfully.")

if __name__ == "__main__":
    main()
