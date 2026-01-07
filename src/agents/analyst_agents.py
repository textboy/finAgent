import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..tools.analyst_tools import *


DEFAULT_MODEL_NAME = 'x-ai/grok-beta'
load_dotenv(os.path.join('config', '.env'))
print(f'Calling model: {os.getenv('MODEL_NAME', DEFAULT_MODEL_NAME)}')

llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME', DEFAULT_MODEL_NAME),
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url=os.getenv('OPENROUTER_BASE_URL'),
    temperature=0.1,
)

class FundamentalsAnalyst:
    @staticmethod
    def analyze(symbol: str) -> str:
        overview = get_company_overview(symbol)
        etf_profile = get_etf_profile(symbol)
        dividends = get_dividends(symbol)
        income_statement = get_income_statement(symbol)
        balance_sheet = get_balance_sheet(symbol)
        cash_flow = get_cash_flow(symbol)

        print(f'DEBUG: overview -- {overview}')
        print(f'DEBUG: etf_profile -- {etf_profile}')
        print(f'DEBUG: dividends -- {dividends}')
        print(f'DEBUG: income_statement -- {income_statement}')
        print(f'DEBUG: balance_sheet -- {balance_sheet}')
        print(f'DEBUG: cash_flow -- {cash_flow}')

        user_prompt = f"""Please summarize the financial data of {{symbol}} based on the outputs of below MRC tools:
- {{outputOfOverview}},
- {{outputOfETFProfile}},
- {{outputOfDividends}},
- {{outputOfIncomeStatement}},
- {{outputOfBalanceSheet}},
- {{outputOfCashFlow}}.""".format(
            symbol=symbol,
            outputOfOverview=overview,
            outputOfETFProfile=etf_profile,
            outputOfDividends=dividends,
            outputOfIncomeStatement=income_statement,
            outputOfBalanceSheet=balance_sheet,
            outputOfCashFlow=cash_flow
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
        print(f'DEBUG: news_sentiment -- {news_sentiment}')
        
        user_prompt = f"Please sentiment analysis based on the outputs of below MRC tools: - {news_sentiment}."
        
        messages = [
            SystemMessage(content="You are a news sentiment researcher tasked with analyzing news and trends."),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

class TechnicalAnalyst:
    @staticmethod
    def analyze(symbol: str, investment_period: str) -> str:
        sma50 = get_sma(symbol, investment_period, 50)
        sma200 = get_sma(symbol, investment_period, 200)
        ema10 = get_ema(symbol, investment_period, 10)
        rsi = get_rsi(symbol, investment_period)
        bbands = get_bbands(symbol, investment_period)
        macd_out = get_macd(symbol, investment_period)
        vwap_out = get_vwap(symbol, investment_period)
        print(f'DEBUG: sma50 -- {sma50}')
        print(f'DEBUG: sma200 -- {sma200}')
        print(f'DEBUG: ema10 -- {ema10}')
        print(f'DEBUG: rsi -- {rsi}')
        print(f'DEBUG: bbands -- {bbands}')
        print(f'DEBUG: macd -- {macd_out}')
        print(f'DEBUG: vwap -- {vwap_out}')

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
        print(f'DEBUG: insider -- {insider}')
        
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