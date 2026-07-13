import os
from dotenv import load_dotenv
from ..tools.analyst_tools import (
    get_company_overview,
    get_income_statement,
    get_balance_sheet,
    get_cash_flow,
    get_news_sentiment,
    get_reddit_sentiment,
    download_yf_data,
    get_sma,
    get_ema,
    get_rsi,
    get_bbands,
    get_macd,
    get_vwap
)

load_dotenv(os.path.join('config', '.env'))

class FundamentalsAnalyst:
    @staticmethod
    def analyze(symbol: str, investment_period: str) -> str:
        """Fetch fundamental data from APIs without LLM processing."""
        overview = get_company_overview(symbol)
        income_statement = get_income_statement(symbol)
        balance_sheet = get_balance_sheet(symbol)
        cash_flow = get_cash_flow(symbol)

        return f"""=== FUNDAMENTALS DATA: {symbol} ===

COMPANY OVERVIEW:
{overview}

INCOME STATEMENT:
{income_statement}

BALANCE SHEET:
{balance_sheet}

CASH FLOW:
{cash_flow}
"""

class SentimentAnalyst:
    @staticmethod
    def analyze(symbol: str) -> str:
        """Fetch sentiment data from APIs without LLM processing."""
        news_sentiment = get_news_sentiment(symbol)
        reddit_sentiment = get_reddit_sentiment(symbol)

        return f"""=== SENTIMENT DATA: {symbol} ===

NEWS SENTIMENT:
{news_sentiment}

SOCIAL MEDIA (Reddit):
{reddit_sentiment}
"""

class TechnicalAnalyst:
    @staticmethod
    def analyze(symbol: str, investment_period: str) -> str:
        """Fetch technical indicator data from APIs without LLM processing."""
        data = download_yf_data(symbol)
        sma50 = get_sma(data, 50)
        sma100 = get_sma(data, 100)
        ema10 = get_ema(data, 10)
        rsi = get_rsi(data)
        bbands = get_bbands(data)
        macd_out = get_macd(symbol, investment_period)
        vwap_out = get_vwap(symbol, investment_period)

        return f"""=== TECHNICAL DATA: {symbol} ===

SMA-50: {sma50}
SMA-100: {sma100}
EMA-10: {ema10}
RSI: {rsi}
BOLLINGER BANDS: {bbands}
MACD: {macd_out}
VWAP: {vwap_out}
"""

class MarketAnalyst:
    @staticmethod
    def analyze(investment_period: str) -> str:
        """Fetch market-level data from yfinance API."""
        from ..utils.yfinance_compat import YahooFinanceCompat
        import pandas as pd

        # Get period string for yfinance
        period_map = {
            "short+": "5d",
            "short": "1mo",
            "medium": "6mo",
            "long": "2y"
        }
        period = period_map.get(investment_period, "6mo")

        # Major indices — fetch in parallel
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            spy_future = executor.submit(YahooFinanceCompat("SPY").get_history, period=period)
            qqq_future = executor.submit(YahooFinanceCompat("QQQ").get_history, period=period)
            vix_future = executor.submit(YahooFinanceCompat("^VIX").get_history, period="5d")
            spy_hist = spy_future.result()
            qqq_hist = qqq_future.result()
            vix_hist = vix_future.result()

        # S&P 500 analysis
        spy_current = spy_hist['Close'].iloc[-1] if not spy_hist.empty else "N/A"
        spy_change = ((spy_hist['Close'].iloc[-1] - spy_hist['Close'].iloc[0]) / spy_hist['Close'].iloc[0] * 100) if len(spy_hist) > 1 else 0
        spy_sma50 = spy_hist['Close'].rolling(50).mean().iloc[-1] if len(spy_hist) >= 50 else "N/A"
        spy_sma200 = spy_hist['Close'].rolling(200).mean().iloc[-1] if len(spy_hist) >= 200 else "N/A"

        # NASDAQ analysis
        qqq_current = qqq_hist['Close'].iloc[-1] if not qqq_hist.empty else "N/A"
        qqq_change = ((qqq_hist['Close'].iloc[-1] - qqq_hist['Close'].iloc[0]) / qqq_hist['Close'].iloc[0] * 100) if len(qqq_hist) > 1 else 0

        # VIX (Volatility Index)
        vix_current = vix_hist['Close'].iloc[-1] if not vix_hist.empty else "N/A"
        vix_prev = vix_hist['Close'].iloc[0] if len(vix_hist) > 1 else vix_current

        # Market breadth (simplified - skip component symbols to avoid crashes)
        breadth = "Market breadth data unavailable (simplified mode)"

        # Sector performance (XLK, XLF, XLV, XLE, XLI, XLC, XLY, XLP, XLU, XLRE, XLB)
        from concurrent.futures import ThreadPoolExecutor, as_completed
        sectors = {
            "XLK": "Technology",
            "XLF": "Financials",
            "XLV": "Healthcare",
            "XLE": "Energy",
            "XLI": "Industrials",
            "XLC": "Communication",
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLU": "Utilities",
            "XLRE": "Real Estate",
            "XLB": "Materials"
        }

        def _fetch_sector_perf(ticker, name):
            try:
                compat = YahooFinanceCompat(ticker)
                h = compat.get_history(period="1mo")
                if len(h) >= 2:
                    perf = (h['Close'].iloc[-1] - h['Close'].iloc[0]) / h['Close'].iloc[0] * 100
                    return f"{name}: {perf:.2f}%"
            except:
                pass
            return None

        sector_perf = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(_fetch_sector_perf, t, n): n for t, n in sectors.items()}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    sector_perf.append(result)

        # Interest rates (10-year Treasury) — already fetched in parallel above if needed
        try:
            tnx_hist = YahooFinanceCompat("^TNX").get_history(period="1mo")
            rate_10y = tnx_hist['Close'].iloc[-1] if not tnx_hist.empty else "N/A"
        except:
            rate_10y = "N/A"

        # Format values for display
        spy_sma50_str = f"${spy_sma50:.2f}" if isinstance(spy_sma50, float) else "N/A"
        spy_sma200_str = f"${spy_sma200:.2f}" if isinstance(spy_sma200, float) else "N/A"
        trend = "Bullish (above SMA-200)" if isinstance(spy_sma200, float) and spy_current > spy_sma200 else "Bearish (below SMA-200)" if isinstance(spy_sma200, float) else "N/A"
        vix_status = "High Volatility (>30)" if isinstance(vix_current, (int, float)) and vix_current > 30 else "Normal (15-30)" if isinstance(vix_current, (int, float)) and vix_current > 15 else "Low Volatility (<15)"
        rate_10y_str = f"{rate_10y:.2f}%" if isinstance(rate_10y, float) else str(rate_10y)

        return f"""=== MARKET ANALYSIS ===

S&P 500 (SPY):
- Current Price: ${spy_current:.2f}
- Period Change: {spy_change:.2f}%
- SMA-50: {spy_sma50_str}
- SMA-200: {spy_sma200_str}
- Trend: {trend}

NASDAQ (QQQ):
- Current Price: ${qqq_current:.2f}
- Period Change: {qqq_change:.2f}%

VIX (Volatility Index):
- Current Level: {vix_current:.2f}
- Status: {vix_status}

Market Breadth:
{breadth}

Sector Performance (1 Month):
{chr(10).join(sector_perf[:6])}

Interest Rates:
- 10-Year Treasury Yield: {rate_10y_str}
"""

def analyst_team(symbol: str, investment_period: str) -> dict:
    """Run all analyst agents and return raw API data (no LLM calls)."""
    return {
        'fundamentals': FundamentalsAnalyst.analyze(symbol, investment_period),
        'sentiment': SentimentAnalyst.analyze(symbol),
        'technical': TechnicalAnalyst.analyze(symbol, investment_period),
        'market': MarketAnalyst.analyze(investment_period),
    }
