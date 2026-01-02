from langchain_core.tools import tool
from typing import Optional
import pandas as pd
from ..utils.data_fetchers import DataFetcher
from ..utils.technical_indicators import calculate_macd, calculate_vwap, get_latest_indicators

fetcher = DataFetcher()

def get_company_overview(symbol: str) -> str:
    """Get company overview and financial ratios from AlphaVantage."""
    data, meta = fetcher.get_company_overview(symbol)
    return f"Data (latest):\\n{pd.concat([data.iloc[0]]).to_string() if not data.empty else 'No data'}\\nFull Data shape: {data.shape}"

def get_income_statement(symbol: str) -> str:
    """Get annual and quarterly income statements."""
    data, meta = fetcher.get_income_statement(symbol)
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_balance_sheet(symbol: str) -> str:
    """Get annual and quarterly balance sheets."""
    data, meta = fetcher.get_balance_sheet(symbol)
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_cash_flow(symbol: str) -> str:
    """Get annual and quarterly cash flow statements."""
    data, meta = fetcher.get_cash_flow(symbol)
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_earnings(symbol: str) -> str:
    """Get earnings data."""
    data, meta = fetcher.get_earnings(symbol)
    return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"

def get_dividends(symbol: str) -> str:
    """Get dividend historical distributions."""
    data, meta = fetcher.get_dividends(symbol)
    return f"Data shape: {data.shape}\\nRecent: {data.tail(5).to_dict() if not data.empty else 'No data'}"

def get_etf_profile(symbol: str) -> str:
    """Get ETF profile (using overview)."""
    return get_company_overview(symbol)

def get_news_sentiment(symbol: str, days_back: int = 14) -> str:
    """Get news sentiment for the stock."""
    data, meta = fetcher.get_news_sentiment(symbol, days_back)
    return f"Sentiment score: {meta.get('sentiment_score_definition', 'N/A')}\\nData shape: {data.shape}"

def get_sma(symbol: str, interval: str, time_period: int) -> str:
    """Get Simple Moving Average."""
    data, meta = fetcher.get_sma(symbol, interval, time_period)
    return f"Latest SMA: {data['SMA'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_ema(symbol: str, interval: str, time_period: int) -> str:
    """Get Exponential Moving Average."""
    data, meta = fetcher.get_ema(symbol, interval, time_period)
    return f"Latest EMA: {data['EMA'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_rsi(symbol: str, interval: str, time_period: int = 14) -> str:
    """Get RSI."""
    data, meta = fetcher.get_rsi(symbol, interval, time_period)
    return f"Latest RSI: {data['RSI'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_bbands(symbol: str, interval: str, time_period: int = 20) -> str:
    """Get Bollinger Bands."""
    data, meta = fetcher.get_bbands(symbol, interval, time_period)
    latest = data.iloc[-1]
    return f"Latest BB: Upper {latest.get('Real Upper Band', 'N/A')}, Middle {latest.get('Real Middle Band', 'N/A')}, Lower {latest.get('Real Lower Band', 'N/A')}"

def get_macd(symbol: str, interval: str = 'daily', period: str = '2y') -> str:
    """Calculate MACD using yfinance data."""
    hist = fetcher.get_yf_history(symbol, period=period, interval=interval)
    hist = calculate_macd(hist)
    latest = get_latest_indicators(hist)['macd']
    return f"Latest MACD: {latest}, Signal: {get_latest_indicators(hist)['macd_signal']}"

def get_vwap(symbol: str, interval: str = 'daily', period: str = '2y') -> str:
    """Calculate VWAP using yfinance data."""
    hist = fetcher.get_yf_history(symbol, period=period, interval=interval)
    hist = calculate_vwap(hist)
    latest = get_latest_indicators(hist)['vwap']
    return f"Latest VWAP: {latest}"

def get_close_price(symbol: str) -> str:
    """Get latest close price from yfinance."""
    price = fetcher.get_close_price(symbol)
    return f"{price}"

# List of tools for analysts
fundamentals_tools = [get_company_overview, get_income_statement, get_balance_sheet, get_cash_flow, get_earnings, get_dividends, get_etf_profile]
sentiment_tools = [get_news_sentiment]
technical_tools = [get_sma, get_ema, get_rsi, get_bbands, get_macd, get_vwap]
special_tools = [get_close_price]  # insider?
# add get_insider_transactions if needed

def get_insider_transactions(symbol: str) -> str:
    """Get insider transactions."""
    data, meta = fetcher.get_insider_transactions(symbol)
    return f"Data shape: {data.shape}\\nRecent: {data.tail(3).to_dict() if not data.empty else 'No data'}"

special_tools.append(get_insider_transactions)