import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..tools.analyst_tools import *

DEFAULT_MODEL_NAME = 'x-ai/grok-beta'
load_dotenv(os.path.join('config', '.env'))
print(f'Calling model: {os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)}')

llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME', DEFAULT_MODEL_NAME),
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url=os.getenv('OPENROUTER_BASE_URL'),
    temperature=0.1,
)

class FundamentalsAnalyst:
    @staticmethod
    def analyze(symbol: str, investment_period: str) -> str:
        for tool in fundamentals_tools:
            if tool.__name__ == 'get_company_overview':
                overview = tool(symbol)
            elif tool.__name__ == 'get_income_statement':
                income_statement = tool(symbol)
            elif tool.__name__ == 'get_balance_sheet':
                balance_sheet = tool(symbol)
            elif tool.__name__ == 'get_cash_flow':
                cash_flow = tool(symbol)
        # print(f'DEBUG: overview -- {overview}')
        # print(f'DEBUG: income_statement -- {income_statement}')
        # print(f'DEBUG: balance_sheet -- {balance_sheet}')
        # print(f'DEBUG: cash_flow -- {cash_flow}')

        user_prompt = f"""Summarize the financial data of {{symbol}} based on the outputs of below MRC tools:
- {{outputOfOverview}},
- {{outputOfIncomeStatement}},
- {{outputOfBalanceSheet}},
- {{outputOfCashFlow}}.
If outputOfOverview is not None, then focus on:
- Name
- EBITDA
- PERatio
- PEGRatio
- BookValue
- DividendPerShare
- DividendYield
- EPS
- RevenuePerShareTTM
- ProfitMargin
- DilutedEPSTTM
- ReturnOnAssetsTTM
- ReturnOnEquityTTM
- RevenueTTM
- AnalystTargetPrice
- AnalystRatingStrongBuy
- AnalystRatingBuy
- AnalystRatingHold
- AnalystRatingSell
- AnalystRatingStrongSell
- DividendDate
- ExDividendDate
""".format(
            symbol=symbol,
            outputOfOverview=overview,
            outputOfIncomeStatement=income_statement,
            outputOfBalanceSheet=balance_sheet,
            outputOfCashFlow=cash_flow
        )

        messages = [
            SystemMessage(content="You are a helpful AI assistant."),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

class SentimentAnalyst:
    @staticmethod
    def analyze(symbol: str) -> str:
        news_sentiment = get_news_sentiment(symbol)
        macro_news_sentiment = get_macro_news_sentiment("economy_fiscal,economy_monetary,economy_macro")
        # print(f'DEBUG: news_sentiment -- {news_sentiment}')
        # print(f"DEBUG: macro_news_sentiment -- {macro_news_sentiment}")
        
        user_prompt = f"""Sentiment analysis to stock market based on the outputs of below information: 
1) news_sentiment: {news_sentiment}
Summary from the url, and perform sentiment analysis relates to {symbol} (e.g. Alphabet Inc relates to either GOOGL or GOOG).
2) macro_news_sentiment: {macro_news_sentiment}
Summary from the url, and perform sentiment analysis base on macro economic and political factors, consider the following topics:
U.S. breaking news
foreign exchange (forex)
oil/gold/soybeans
Geopolitics/Tariffs
U.S. inflation/CPI
U.S. GDP/unemployment/PMI/government budget
international breaking news
U.S. military actions/Multinational Summits
Bonds
"""

        messages = [
            SystemMessage(content="You are a news sentiment researcher tasked with analyzing news and trends."),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

class TechnicalAnalyst:
    @staticmethod
    def analyze(symbol: str, investment_period: str) -> str:
        # get history closed price
        data = download_yf_data(symbol)
        for tool in technical_tools:
            if tool.__name__ == 'get_sma':
                sma50 = tool(data, 50)
                sma100 = tool(data, 100)
            elif tool.__name__ == 'get_ema':
                ema10 = tool(data, 10)
            elif tool.__name__ == 'get_rsi':
                rsi = tool(data)
            elif tool.__name__ == 'get_bbands':
                bbands = tool(data)
            elif tool.__name__ == 'get_macd':
                macd_out = tool(symbol, investment_period)
            elif tool.__name__ == 'get_vwap':
                vwap_out = tool(symbol, investment_period)
        # print(f'DEBUG: sma50 -- {sma50}')
        # print(f'DEBUG: sma100 -- {sma100}')
        # print(f'DEBUG: ema10 -- {ema10}')
        # print(f'DEBUG: rsi -- {rsi}')
        # print(f'DEBUG: bbands -- {bbands}')
        # print(f'DEBUG: macd -- {macd_out}')
        # print(f'DEBUG: vwap -- {vwap_out}')

        user_prompt = f"""Technical analysis based on the outputs of below MRC tools
- SMA50: {sma50},
- SMA100: {sma100},
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
        'fundamentals': FundamentalsAnalyst.analyze(symbol, investment_period),
        'sentiment': SentimentAnalyst.analyze(symbol),
        'technical': TechnicalAnalyst.analyze(symbol, investment_period),
        # 'special': SpecialAnalyst.analyze(symbol),
    }
