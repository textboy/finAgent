from langchain_core.tools import tool
from typing import Optional
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import time
from ..utils.data_fetchers import DataFetcher
from ..utils.technical_indicators import calculate_macd, calculate_vwap
from ..utils.yfinance_compat import YahooFinanceCompat

fetcher = DataFetcher()

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
    """Get company overview and financial ratios from yfinance."""
    data, meta = fetcher.get_company_overview(symbol)
    if data is None:
        return None
    return f"Data (latest):\\n{pd.concat([data.iloc[0]]).to_string() if not data.empty else 'No data'}\\nFull Data shape: {data.shape}"

def get_income_statement(symbol: str) -> str:
    """Get annual and quarterly income statements."""
    try:
        yf_compat = YahooFinanceCompat(symbol)
        data = yf_compat.get_financials('income_stmt')
        if data is None or data.empty:
            return "No data"
        return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"
    except Exception as e:
        print(f"Error getting income statement for {symbol}: {e}")
        return "No data"

def get_balance_sheet(symbol: str) -> str:
    """Get annual and quarterly balance sheets."""
    try:
        yf_compat = YahooFinanceCompat(symbol)
        data = yf_compat.get_financials('balance_sheet')
        if data is None or data.empty:
            return "No data"
        return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"
    except Exception as e:
        print(f"Error getting balance sheet for {symbol}: {e}")
        return "No data"

def get_cash_flow(symbol: str) -> str:
    """Get annual and quarterly cash flow statements."""
    try:
        yf_compat = YahooFinanceCompat(symbol)
        data = yf_compat.get_financials('cashflow')
        if data is None or data.empty:
            return "No data"
        return f"Data shape: {data.shape}\\nLatest: {data.iloc[0].to_dict() if not data.empty else 'No data'}"
    except Exception as e:
        print(f"Error getting cash flow for {symbol}: {e}")
        return "No data"

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

def get_reddit_sentiment(symbol: str) -> str:
    """Get social media sentiment from Reddit for the stock."""
    print(f'DEBUG: get_reddit_sentiment(Reddit RSS) with symbol {symbol}')

    subreddits = ['wallstreetbets', 'stocks', 'investing']
    all_posts = []

    def _fetch_subreddit(sub):
        posts = []
        try:
            url = f'https://www.reddit.com/r/{sub}/search.rss?q={symbol}&restrict_sr=1&limit=5'
            headers = {'User-Agent': 'FinAgent/1.0 (Financial Analysis Bot)'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns)

                for entry in entries[:3]:
                    title = entry.find('atom:title', ns).text or 'N/A'
                    posts.append(f"r/{sub}: {title}")
            else:
                print(f'WARNING: Reddit r/{sub} returned HTTP {response.status_code}')
        except Exception as e:
            print(f'WARNING: Could not fetch from r/{sub}: {str(e)[:50]}')
        return posts

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_fetch_subreddit, sub): sub for sub in subreddits}
        for future in as_completed(futures):
            all_posts.extend(future.result())

    if not all_posts:
        return "No Reddit data available"

    return '\n'.join(all_posts)

def get_macro_news_sentiment(topic: str) -> str:
    """Get macro news sentiment using yfinance."""
    print(f'DEBUG: get_macro_news_sentiment(yFinance) with topic {topic}')
    data, meta = fetcher.get_macro_news_sentiment(topic)
    if not data:
        return "No data"
    # Format the news data
    news_items = []
    for item in data[:10]:  # Limit to 10 items
        news_items.append(f"- {item.get('title', 'N/A')} ({item.get('source', '')})")
    return "\n".join(news_items)

def download_yf_data(symbol: str) -> pd.DataFrame:
    """Download historical market data using compatibility layer."""
    print(f'DEBUG: Download historical market data - symbol {symbol}')
    try:
        yf_compat = YahooFinanceCompat(symbol)
        data = yf_compat.get_history(period='1y', interval='1d')
        if data.empty:
            print(f"WARNING: No data returned for {symbol}")
        return data
    except Exception as e:
        print(f"Error downloading data for {symbol}: {e}")
        return pd.DataFrame()

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

