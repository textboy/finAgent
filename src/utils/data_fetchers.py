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

load_dotenv()

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
        # Get company overview.
        data, meta = self.fd.get_company_overview(symbol=symbol)
        return data, meta

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

    def get_earnings(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        ticker = yf.Ticker(symbol)
        data = ticker.quarterly_earnings
        meta = {'source': 'yfinance'}
        return data, meta

    def get_dividends(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        ticker = yf.Ticker(symbol)
        dividends = ticker.dividends
        data = pd.DataFrame(dividends).tail(10) if not dividends.empty else pd.DataFrame()
        meta = {'source': 'yfinance', 'recent_dividends': len(dividends)}
        return data, meta

    def get_etf_profile(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        # Note: AlphaVantage may not have direct ETF_PROFILE, using overview for now
        data, meta = self.fd.get_company_overview(symbol=symbol)
        return data, meta

    def get_insider_transactions(self, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        time.sleep(1.2)
        data, meta = self.fd.get_insider_transactions(symbol=symbol)
        return data, meta

    def get_news_sentiment(self, symbol: str, days_back: int = 14, limit: int = 30) -> Tuple[pd.DataFrame, Dict]:
        time.sleep(1.2)
        time_to = datetime.now()
        time_from = time_to - timedelta(days=days_back)
        data, meta = self.ns.get_news_sentiment(
            tickers=symbol,
            time_from=time_from.strftime('%Y%m%dT%H%M'),
            time_to=time_to.strftime('%Y%m%dT%H%M'),
            sort='LATEST',
            limit=limit
        )
        return data, meta

    def get_sma(self, symbol: str, interval: str, time_period: int) -> Tuple[pd.DataFrame, Dict]:
        time.sleep(1.2)
        data, meta = self.ti.get_sma(symbol=symbol, interval=interval, time_period=time_period)
        return data, meta

    def get_ema(self, symbol: str, interval: str, time_period: int) -> Tuple[pd.DataFrame, Dict]:
        time.sleep(1.2)
        data, meta = self.ti.get_ema(symbol=symbol, interval=interval, time_period=time_period)
        return data, meta

    def get_rsi(self, symbol: str, interval: str, time_period: int = 14) -> Tuple[pd.DataFrame, Dict]:
        time.sleep(1.2)
        data, meta = self.ti.get_rsi(symbol=symbol, interval=interval, time_period=time_period)
        return data, meta

    def get_bbands(self, symbol: str, interval: str, time_period: int = 20) -> Tuple[pd.DataFrame, Dict]:
        time.sleep(1.2)
        data, meta = self.ti.get_bbands(symbol=symbol, interval=interval, time_period=time_period)
        return data, meta

    def get_yf_history(self, symbol: str, period: str = '2y', interval: str = '1d') -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        return hist

    def get_close_price(self, symbol: str) -> float:
        hist = self.get_yf_history(symbol, period='5d', interval='1d')
        return hist['Close'].iloc[-1]