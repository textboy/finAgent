#!/usr/bin/env python3

import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.data_fetchers import DataFetcher

def main():
    fetcher = DataFetcher()
    symbol = 'AAPL'  # Test with Apple
    data, meta = fetcher.get_company_overview(symbol)
    print(f"Company overview data for {symbol}:")
    print(f"Shape: {data.shape}")
    # print(data['Name'][0])
    # company_df = pd.DataFrame(data)
    # print(company_df['Name'][0])
    print("\nTest completed successfully.")

if __name__ == "__main__":
    main()
