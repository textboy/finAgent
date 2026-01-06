from langchain_core.tools import tool
from typing import Optional
import pandas as pd
from ..utils.data_fetchers import DataFetcher
from ..utils.technical_indicators import calculate_macd, calculate_vwap

fetcher = DataFetcher()

def get_alpha_vantage_interval(investmentPeriod: str) -> str:
    interval_map = {
        "short": "30min",
        "medium": "daily",
        "long": "weekly"
    }
    try:
        return interval_map[investmentPeriod]
    except KeyError:
        print(f"WARNING: The key {investmentPeriod} is not correct in get_alpha_vantage_interval")
        return "daily"

def get_yf_period(investmentPeriod: str) -> str:
    interval_map = {
        "short": "1d",
        "medium": "1wk",
        "long": "1mo"
    }
    try:
        return interval_map[investmentPeriod]
    except KeyError:
        print(f"WARNING: The key {investmentPeriod} is not correct in get_yf_period")
        return "1wk"
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

def get_dividends(symbol: str, investmentPeriod: str = "medium") -> str:
    """Get dividend historical distributions."""
    interval = get_yf_period(investmentPeriod)
    data, meta = fetcher.get_dividends(symbol, interval)
    if data is None:
        return "No data"
    return f"Data shape: {data.shape}\\nRecent: {data.tail(5).to_dict() if not data.empty else 'No data'}"

def get_etf_profile(symbol: str) -> str:
    """Get ETF profile (using overview)."""
    return get_company_overview(symbol)

def get_news_sentiment(symbol: str, days_back: int = 14) -> str:
    """Get news sentiment for the stock."""
    data, meta = fetcher.get_news_sentiment(symbol, days_back)
    if data is None or meta is None:
        return "No data"
    return f"Sentiment score: {meta.get('sentiment_score_definition', 'N/A')}\\nData shape: {data.shape}"

def get_sma(symbol: str, investmentPeriod: str, time_period: int) -> str:
    """Get Simple Moving Average."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    data, meta = fetcher.get_sma(symbol, interval, time_period)
    if data is None:
        return "No data"
    return f"Latest SMA: {data['SMA'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_ema(symbol: str, investmentPeriod: str, time_period: int) -> str:
    """Get Exponential Moving Average."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    data, meta = fetcher.get_ema(symbol, interval, time_period)
    if data is None:
        return "No data"
    return f"Latest EMA: {data['EMA'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_rsi(symbol: str, investmentPeriod: str, time_period: int = 14) -> str:
    """Get RSI."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    data, meta = fetcher.get_rsi(symbol, interval, time_period)
    if data is None:
        return "No data"
    return f"Latest RSI: {data['RSI'].iloc[-1] if not data.empty else 'N/A'}\\nShape: {data.shape}"

def get_bbands(symbol: str, investmentPeriod: str = 'medium', time_period: int = 20) -> str:
    """Get Bollinger Bands."""
    interval = get_alpha_vantage_interval(investmentPeriod)
    data, meta = fetcher.get_bbands(symbol, interval, time_period)
    if data is None:
        return "No data"
    latest = data.iloc[-1]
    return f"Latest BB: Upper {latest.get('Real Upper Band', 'N/A')}, Middle {latest.get('Real Middle Band', 'N/A')}, Lower {latest.get('Real Lower Band', 'N/A')}"

def get_macd(symbol: str, investmentPeriod: str = 'medium', period: str = '2y') -> str:
    """Calculate MACD using yfinance data."""
    interval = get_yf_period(investmentPeriod)
    hist = fetcher.get_yf_history(symbol, period=period, interval=interval)
    hist = calculate_macd(hist)
    # latest = hist.iloc[-1]['macd']
    return f"Latest MACD: {hist['MACD']}, Signal: {hist['MACD_signal']}"

def get_vwap(symbol: str, investmentPeriod: str = 'medium', period: str = '2y') -> str:
    """Calculate VWAP using yfinance data."""
    interval = get_yf_period(investmentPeriod)
    hist = fetcher.get_yf_history(symbol, period=period, interval=interval)
    hist = calculate_vwap(hist)
    # latest = hist.iloc[-1]['VWAP']
    return f"Latest VWAP: {hist['VWAP']},"

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
    if data is None:
        return "No data"
    return f"Data shape: {data.shape}\\nRecent: {data.tail(3).to_dict() if not data.empty else 'No data'}"

special_tools.append(get_insider_transactions)