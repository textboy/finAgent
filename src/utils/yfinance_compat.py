"""
Yahoo Finance Compatibility Layer

This module provides a wrapper around yfinance to handle compatibility issues
with Python 3.13 and newer versions of yfinance.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta


class YahooFinanceCompat:
    """Compatibility wrapper for Yahoo Finance data fetching."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def get_history(self, period: str = '1mo', interval: str = '1d') -> pd.DataFrame:
        """Get historical price data using direct API."""
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{self.symbol}'
            params = {'range': period, 'interval': interval}
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                chart = data.get('chart', {}).get('result', [{}])[0]
                timestamps = chart.get('timestamp', [])
                quotes = chart.get('indicators', {}).get('quote', [{}])[0]

                if timestamps and quotes:
                    df = pd.DataFrame()
                    df['Open'] = quotes.get('open', [])
                    df['High'] = quotes.get('high', [])
                    df['Low'] = quotes.get('low', [])
                    df['Close'] = quotes.get('close', [])
                    df['Volume'] = quotes.get('volume', [])
                    return df.dropna()
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching history for {self.symbol}: {e}")
            return pd.DataFrame()

    def get_info(self) -> dict:
        """Get stock info using yfinance with fallback."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(self.symbol)
            return ticker.info
        except Exception as e:
            print(f"Error fetching info for {self.symbol}: {e}")
            return {}

    def get_financials(self, statement_type: str = 'income_stmt') -> pd.DataFrame:
        """Get financial statements - returns empty DataFrame due to yfinance compatibility issues."""
        # yfinance financials() crashes on Python 3.13
        # Return empty DataFrame with a note
        print(f"WARNING: {statement_type} not available due to yfinance compatibility issues")
        return pd.DataFrame()
