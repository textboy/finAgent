import os
from dotenv import load_dotenv
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from datetime import datetime, timedelta
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.alphaintelligence import AlphaIntelligence
import yfinance as yf
import time

load_dotenv(os.path.join('config', '.env'))

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

class DataFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ALPHA_VANTAGE_API_KEY
        if not self.api_key:
            raise ValueError('ALPHA_VANTAGE_API_KEY not set')
        self.fd = FundamentalData(key=self.api_key, output_format='pandas')
        self.ti = TechIndicators(key=self.api_key, output_format='pandas')
        self.ts = TimeSeries(key=self.api_key, output_format='pandas')
        self.ns = AlphaIntelligence(key=self.api_key, output_format='pandas')

    def get_company_overview(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        # Get company overview. Some symbol no company overview, e.g. GLD
        time.sleep(1.2)
        try:
            data, meta = self.fd.get_company_overview(symbol=symbol)
            return data, meta
        except ValueError as e:
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
    
    def get_macro_news_sentiment(self, topic: str, days_back: int = 30, limit: int = 20) -> Tuple[pd.DataFrame, Dict]:
        time.sleep(1.2)
        time_to = datetime.now()
        time_from = time_to - timedelta(days=days_back)
        data, meta = self.ns.get_news_sentiment(
            topics=topic,
            time_from=time_from.strftime('%Y%m%dT%H%M'),
            time_to=time_to.strftime('%Y%m%dT%H%M'),
            sort='LATEST',
            limit=limit
        )
        return data, meta

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
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        return hist

    def get_close_price(self, symbol: str) -> float:
        hist = self.get_yf_history(symbol, interval='1d', period='5d')
        return hist['Close'].iloc[-1]