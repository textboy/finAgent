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
        return "No data"
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
    print(f'DEBUG: get_news_sentiment(Alpha Vantage) with symbol {symbol}')
    data, meta = fetcher.get_news_sentiment(symbol)
    if data is None:
        return "No data"
    return f"{data['ticker_sentiment']}"

def get_news_sentiment_by_topic(topic: str) -> str:
    """Get news sentiment for the stock."""
    print(f'DEBUG: get_news_sentiment_by_topic(Alpha Vantage) with topic {topic}')
    data, meta = fetcher.get_news_sentiment_by_topic(topic)
    if data is None:
        return "No data"
    return f"{data['url']}"

def get_sma(symbol: str, investmentPeriod: str, time_period: int = 36) -> str:
    """Get Simple Moving Average."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    print(f'DEBUG: get_sma(Alpha Vantage) interval {interval}, period {time_period}')
    data, meta = fetcher.get_sma(symbol, interval, time_period)
    if data is None:
        return "No data"
    return f"Latest SMA: {data['SMA'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_ema(symbol: str, investmentPeriod: str, time_period: int = 36) -> str:
    """Get Exponential Moving Average."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    data, meta = fetcher.get_ema(symbol, interval, time_period)
    if data is None:
        return "No data"
    return f"Latest EMA: {data['EMA'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_rsi(symbol: str, investmentPeriod: str, time_period: int = 36) -> str:
    """Get RSI."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    data, meta = fetcher.get_rsi(symbol, interval, time_period)
    if data is None:
        return "No data"
    return f"Latest RSI: {data['RSI'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_bbands(symbol: str, investmentPeriod: str, time_period: int = 36) -> str:
    """Get Bollinger Bands."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    data, meta = fetcher.get_bbands(symbol, interval, time_period)
    if data is None:
        return "No data"
    latest = data.iloc[-1]
    return f"Latest BB: Upper {latest.get('Real Upper Band', 'N/A')}, Middle {latest.get('Real Middle Band', 'N/A')}, Lower {latest.get('Real Lower Band', 'N/A')}"

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
sentiment_tools = [get_news_sentiment]
technical_tools = [get_sma, get_ema, get_rsi, get_bbands, get_macd, get_vwap]
special_tools = [get_insider_transactions]

