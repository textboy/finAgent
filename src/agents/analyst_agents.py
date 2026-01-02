import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..tools.analyst_tools import *

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME', 'x-ai/grok-beta'),
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url=os.getenv('OPENROUTER_BASE_URL'),
    temperature=0.1,
)

def get_interval(investment_period: str) -> str:
    period_lower = investment_period.lower()
    if 'short' in period_lower:
        return '30min'
    elif 'medium' in period_lower:
        return 'daily'
    else:
        return 'weekly'

class FundamentalsAnalyst:
    @staticmethod
    def analyze(symbol: str) -> str:
        overview = get_company_overview(symbol)
        etf_profile = get_etf_profile(symbol)
        dividends = get_dividends(symbol)
        income_statement = get_income_statement(symbol)
        balance_sheet = get_balance_sheet(symbol)
        cash_flow = get_cash_flow(symbol)
        earnings = get_earnings(symbol)
        
        user_prompt = f"""Please summarize the financial data of {{symbol}} based on the outputs of below MRC tools:
- {{outputOfOverview}},
- {{outputOfETFProfile}},
- {{outputOfDividends}},
- {{outputOfIncomeStatement}},
- {{outputOfBalanceSheet}},
- {{outputOfCashFlow}},
- {{outputOfEarningsEstimates}}.""".format(
            symbol=symbol,
            outputOfOverview=overview,
            outputOfETFProfile=etf_profile,
            outputOfDividends=dividends,
            outputOfIncomeStatement=income_statement,
            outputOfBalanceSheet=balance_sheet,
            outputOfCashFlow=cash_flow,
            outputOfEarningsEstimates=earnings
        )
        
        messages = [
            SystemMessage(content="You are a helpful AI assistant specialized in fundamental analysis."),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

class SentimentAnalyst:
    @staticmethod
    def analyze(symbol: str) -> str:
        news_sentiment = get_news_sentiment(symbol)
        
        user_prompt = f"Please sentiment analysis based on the outputs of below MRC tools: - {news_sentiment}."
        
        messages = [
            SystemMessage(content="You are a news sentiment researcher tasked with analyzing news and trends."),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

class TechnicalAnalyst:
    @staticmethod
    def analyze(symbol: str, investment_period: str) -> str:
        interval = get_interval(investment_period)
        sma50 = get_sma(symbol, interval, 50)
        sma200 = get_sma(symbol, interval, 200)
        ema10 = get_ema(symbol, interval, 10)
        rsi = get_rsi(symbol, interval)
        bbands = get_bbands(symbol, interval)
        macd_out = get_macd(symbol, interval)
        vwap_out = get_vwap(symbol, interval)
        
        user_prompt = f"""Please return the technical analysis report based on the outputs of below MRC tools
- SMA50: {sma50},
- SMA200: {sma200},
- EMA10: {ema10},
- MACD: {macd_out},
- RSI: {rsi},
- BBANDS: {bbands},
- VWAP: {vwap_out}
."""
        
        messages = [
            SystemMessage(content="You are a technical indicators researcher."),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

class SpecialAnalyst:
    @staticmethod
    def analyze(symbol: str) -> str:
        insider = get_insider_transactions(symbol)
        
        user_prompt = f"Assess insider transactions and special insights for {symbol}: {insider}"
        
        messages = [
            SystemMessage(content="You are a special analyst assessing insider activities and special topics."),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

def analyst_team(symbol: str, investment_period: str) -> dict:
    """Run all analyst agents and return insights."""
    return {
        'fundamentals': FundamentalsAnalyst.analyze(symbol),
        'sentiment': SentimentAnalyst.analyze(symbol),
        'technical': TechnicalAnalyst.analyze(symbol, investment_period),
        'special': SpecialAnalyst.analyze(symbol),
    }