from langchain_core.tools import tool
from typing import Optional
import pandas as pd
from ..utils.data_fetchers import DataFetcher
from ..utils.technical_indicators import calculate_macd, calculate_vwap

fetcher = DataFetcher()

def get_alpha_vantage_interval(investmentPeriod: str) -> str:
    interval_map = {
        "short+": "30min",
        "short": "daily",
        "medium": "weekly",
        "long": "monthly"
    }
    try:
        return interval_map[investmentPeriod]
    except KeyError:
        print(f"WARNING: The key {investmentPeriod} is not correct in get_alpha_vantage_interval")
        return "weekly"

def get_yf_interval(investmentPeriod: str) -> str:
    interval_map = {
        "short+": "30m",
        "short": "1d",
        "medium": "1wk",
        "long": "1mo"
    }
    try:
        return interval_map[investmentPeriod]
    except KeyError:
        print(f"WARNING: The key {investmentPeriod} is not correct in get_yf_interval")
        return "1wk"

def get_yf_period(investmentPeriod: str) -> str:
    period_map = {
        "short+": "3d",
        "short": "30d",
        "medium": "9mo",
        "long": "3y"
    }
    try:
        return period_map[investmentPeriod]
    except KeyError:
        print(f"WARNING: The key {investmentPeriod} is not correct in get_yf_period")
        return "9mo"
    
def get_company_overview(symbol: str) -> str:
    """Get company overview and financial ratios from AlphaVantage."""
    data, meta = fetcher.get_company_overview(symbol)
    if data is None:
        return None
    return f"Data (latest):\\n{pd.concat([data.iloc[0]]).to_string() if not data.empty else 'No data'}\\nFull Data shape: {data.shape}"

def get_income_statement(symbol: str) -> str:
    """Get annual and quarterly income statements."""
    data, meta = fetcher.get_income_statement(symbol)
    if data is None:
        return "No data"
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_balance_sheet(symbol: str) -> str:
    """Get annual and quarterly balance sheets."""
    data, meta = fetcher.get_balance_sheet(symbol)
    if data is None:
        return "No data"
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_cash_flow(symbol: str) -> str:
    """Get annual and quarterly cash flow statements."""
    data, meta = fetcher.get_cash_flow(symbol)
    if data is None:
        return "No data"
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_earnings(symbol: str) -> str:
    """Get earnings data."""
    data, meta = fetcher.get_earnings(symbol)
    if data is None:
        return "No data"
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_news_sentiment(symbol: str) -> str:
    """Get news sentiment for the stock."""
    print(f'DEBUG: get_news_sentiment(yFinance) with symbol {symbol}')
    data, meta = fetcher.get_news_sentiment(symbol)
    if data is None:
        return "No data"
    return data

def get_macro_news_sentiment(topic: str) -> str:
    """Get news sentiment for the stock."""
    print(f'DEBUG: get_news_sentiment_by_topic(Alpha Vantage) with topic {topic}')
    data, meta = fetcher.get_macro_news_sentiment(topic)
    if data is None:
        return "No data"
    return f"{data['url']}"

def download_yf_data(symbol: str) -> pd.DataFrame:
    print(f'DEBUG: Download historical market data from yFinance - symbol {symbol}')
    data = fetcher.download_yf_data(symbol)
    return data

def get_sma(data: pd.DataFrame, time_period: int = 36) -> str:
    """Get Simple Moving Average."""
    data, meta = fetcher.get_sma(data, time_period)
    if data is None or data.empty:
        return "No data"
    return f"SMA-{time_period}: {data}"

def get_ema(data: pd.DataFrame, time_period: int = 36) -> str:
    """Get Exponential Moving Average."""
    data, meta = fetcher.get_ema(data, time_period)
    if data is None or data.empty:
        return "No data"
    return f"EMA-{time_period}: {data}"

def get_rsi(data: pd.DataFrame, time_period: int = 36) -> str:
    """Get RSI."""
    data, meta = fetcher.get_rsi(data, time_period)
    if data is None or data.empty:
        return "No data"
    return f"RSI: {data}"

def get_bbands(data: pd.DataFrame, time_period: int = 36) -> str:
    """Get Bollinger Bands."""
    data, meta = fetcher.get_bbands(data, time_period)
    if data is None or data.empty:
        return "No data"
    return f"BB: {data}"

def get_macd(symbol: str, investmentPeriod: str) -> str:
    """Calculate MACD using yfinance data."""
    interval = get_yf_interval(investmentPeriod)
    period = get_yf_period(investmentPeriod)
    print(f'DEBUG: get_macd(yFinance) interval {interval}, period {period}')
    hist = fetcher.get_yf_history(symbol, interval=interval, period=period)
    hist = calculate_macd(hist)
    # latest = hist.iloc[-1]['macd']
    return f"Latest MACD: {hist['MACD']}, Signal: {hist['MACD_signal']}"

def get_vwap(symbol: str, investmentPeriod: str) -> str:
    """Calculate VWAP using yfinance data."""
    interval = get_yf_interval(investmentPeriod)
    period = get_yf_period(investmentPeriod)
    hist = fetcher.get_yf_history(symbol, interval=interval, period=period)
    hist = calculate_vwap(hist)
    # latest = hist.iloc[-1]['VWAP']
    return f"Latest VWAP: {hist['VWAP']},"

def get_close_price(symbol: str) -> str:
    """Get latest close price from yfinance."""
    price = fetcher.get_close_price(symbol)
    return f"{price}"

# (bypass first)
def get_insider_transactions(symbol: str) -> str:
    """Get insider transactions."""
    data, meta = fetcher.get_insider_transactions(symbol)
    if data is None:
        return "No data"
    return f"Data shape: {data.shape}\\nRecent: {data.tail(3).to_dict() if not data.empty else 'No data'}"

# List of tools for analysts
fundamentals_tools = [get_company_overview, get_income_statement, get_balance_sheet, get_cash_flow, get_earnings]
sentiment_tools = [get_news_sentiment, get_macro_news_sentiment]
technical_tools = [get_sma, get_ema, get_rsi, get_bbands, get_macd, get_vwap]
special_tools = [get_insider_transactions]

