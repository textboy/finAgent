import os
from dotenv import load_dotenv
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import time
from .yfinance_compat import YahooFinanceCompat

load_dotenv(os.path.join('config', '.env'))

class DataFetcher:
    def __init__(self, api_key: Optional[str] = None):
        # Alpha Vantage no longer required - using yfinance for all data
        pass

    def get_company_overview(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        """Get company overview using yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            # Convert info dict to a format similar to Alpha Vantage
            data = pd.DataFrame([info])
            meta = {'source': 'yfinance'}
            return data, meta
        except Exception as e:
            print(f"No company overview found for {symbol}, bypassing...")
            return None, {}

    def get_income_statement(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        ticker = yf.Ticker(symbol)
        data = ticker.quarterly_income_stmt
        meta = {'source': 'yfinance'}
        return data, meta

    def get_balance_sheet(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        ticker = yf.Ticker(symbol)
        data = ticker.quarterly_balance_sheet
        meta = {'source': 'yfinance'}
        return data, meta

    def get_cash_flow(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        ticker = yf.Ticker(symbol)
        data = ticker.quarterly_cash_flow
        meta = {'source': 'yfinance'}
        return data, meta

    def get_insider_transactions(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        ticker = yf.Ticker(symbol)
        data = ticker.get_insider_transactions()
        meta = {'source': 'yfinance'}
        return data, meta

    def get_news_sentiment(self, symbol: str, limit: int = 20) -> Tuple[pd.DataFrame, Dict]:
        urlList = []
        ticker = yf.Ticker(symbol)
        data = ticker.news[:limit]
        if data:
            for item in data:
                urlList.append(item['content']['canonicalUrl']['url'])
        meta = {'source': 'yfinance'}
        return urlList, meta
    
    def get_macro_news_sentiment(self, topic: str, days_back: int = 30, limit: int = 20) -> Tuple[list, Dict]:
        """Get macro news sentiment using yfinance (no Alpha Vantage needed)."""
        # Use yfinance to get market-related news
        macro_tickers = ['SPY', 'QQQ', 'DIA']  # Major indices
        all_news = []

        for ticker_symbol in macro_tickers:
            try:
                ticker = yf.Ticker(ticker_symbol)
                news = ticker.news[:limit//len(macro_tickers)]
                for item in news:
                    if 'content' in item and 'canonicalUrl' in item['content']:
                        all_news.append({
                            'title': item.get('title', ''),
                            'url': item['content']['canonicalUrl']['url'],
                            'source': ticker_symbol
                        })
            except Exception as e:
                print(f"Warning: Could not fetch news for {ticker_symbol}: {e}")

        meta = {'source': 'yfinance', 'topic': topic}
        return all_news[:limit], meta

    def download_yf_data(self, symbol: str) -> pd.DataFrame:
        # download 3 years data
        start_date = datetime.now() - timedelta(days=1095)
        start_date_str = start_date.strftime('%Y-%m-%d')
        data = yf.download(symbol, start=start_date_str)
        return data

    def get_sma(self, data: pd.DataFrame, time_period: int = 20) -> Tuple[pd.DataFrame, Dict]:
        sma = data['Close'].rolling(time_period).mean()
        sma = sma.dropna()
        meta = {'source': 'yfinance'}
        return sma, meta

    def get_ema(self, data: pd.DataFrame, time_period: int = 12) -> Tuple[pd.DataFrame, Dict]:
        ema = data['Close'].ewm(span=time_period, adjust=False).mean()
        meta = {'source': 'yfinance'}
        return ema, meta

    def get_rsi(self, data: pd.DataFrame, time_period: int = 14) -> Tuple[pd.DataFrame, Dict]:
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=time_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=time_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.dropna()
        meta = {'source': 'yfinance'}
        return rsi, meta

    def get_bbands(self, data: pd.DataFrame, time_period: int = 20) -> Tuple[pd.DataFrame, Dict]:
        rolling_mean = data['Close'].rolling(window=time_period).mean()
        rolling_std = data['Close'].rolling(window=time_period).std()
        upper = rolling_mean + (rolling_std * 2)
        lower = rolling_mean - (rolling_std * 2)
        bbands = pd.concat([upper, lower], axis=1)
        bbands = bbands.dropna()
        meta = {'source': 'yfinance'}
        return bbands, meta

    def get_yf_history(self, symbol: str, period: str = '2y', interval: str = '1d') -> pd.DataFrame:
        """Get historical data using YahooFinanceCompat for Python 3.13 compatibility."""
        try:
            yf_compat = YahooFinanceCompat(symbol)
            # Convert period format for YahooFinanceCompat
            period_map = {'1d': '1d', '5d': '5d', '1mo': '1mo', '3mo': '3mo', '6mo': '6mo', '1y': '1y', '2y': '2y', '5y': '5y', 'max': 'max'}
            yf_period = period_map.get(period, '1y')
            return yf_compat.get_history(period=yf_period, interval=interval)
        except Exception as e:
            print(f"Error in get_yf_history for {symbol}: {e}")
            return pd.DataFrame()

    def get_close_price(self, symbol: str) -> float:
        hist = self.get_yf_history(symbol, interval='1d', period='5d')
        if hist.empty:
            return 0.0
        return hist['Close'].iloc[-1]