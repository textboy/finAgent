import os
from dotenv import load_dotenv
from ..tools.analyst_tools import *

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
        macro_news_sentiment = get_macro_news_sentiment("economy_fiscal,economy_monetary,economy_macro")

        return f"""=== SENTIMENT DATA: {symbol} ===

NEWS SENTIMENT:
{news_sentiment}

MACRO NEWS SENTIMENT:
{macro_news_sentiment}
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

def analyst_team(symbol: str, investment_period: str) -> dict:
    """Run all analyst agents and return raw API data (no LLM calls)."""
    return {
        'fundamentals': FundamentalsAnalyst.analyze(symbol, investment_period),
        'sentiment': SentimentAnalyst.analyze(symbol),
        'technical': TechnicalAnalyst.analyze(symbol, investment_period),
    }
