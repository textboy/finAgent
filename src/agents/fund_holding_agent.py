import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv(os.path.join('config', '.env'))

DEFAULT_MODEL_NAME = 'x-ai/grok-beta'

# Lazy initialization of LLM to ensure env vars are loaded
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        # Try primary LLM first, then fall back to backup
        primary_key = os.getenv('LLM_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        backup_key = os.getenv('BK_LLM_API_KEY')

        # Try primary LLM
        try:
            print(f"DEBUG: FundHolding - Trying primary LLM: {os.getenv('LLM_BASE_MODEL')} @ {os.getenv('LLM_BASE_URL')}")
            _llm = ChatOpenAI(
                model=os.getenv('LLM_BASE_MODEL', DEFAULT_MODEL_NAME),
                api_key=primary_key,
                base_url=os.getenv('LLM_BASE_URL'),
                temperature=0.1,
            )
            # Test the connection
            _llm.invoke([{"role": "user", "content": "hi"}])
            print(f"DEBUG: FundHolding - Primary LLM OK")
        except Exception as e:
            print(f"DEBUG: FundHolding - Primary LLM failed: {e}")
            print(f"DEBUG: FundHolding - Trying backup LLM: {os.getenv('LLM_BACKUP_MODEL')} @ {os.getenv('LLM_BACKUP_URL')}")
            try:
                _llm = ChatOpenAI(
                    model=os.getenv('LLM_BACKUP_MODEL', DEFAULT_MODEL_NAME),
                    api_key=backup_key,
                    base_url=os.getenv('LLM_BACKUP_URL'),
                    temperature=0.1,
                )
                # Test the connection
                _llm.invoke([{"role": "user", "content": "hi"}])
                print(f"DEBUG: FundHolding - Backup LLM OK")
            except Exception as e2:
                print(f"DEBUG: FundHolding - Backup LLM also failed: {e2}")
                raise Exception(f"Both LLM providers failed. Primary: {e}, Backup: {e2}")
    return _llm


FUND_HOLDING_SYSTEM_PROMPT = """You are a senior quantitative financial analyst and fund research expert, fluent in regulatory disclosure systems across global and Chinese markets (such as US SEC 13F and Form N-PORT filings, Chinese mutual fund quarterly/semi-annual reports, and major third-party private fund data platforms).

Your task is to conduct a deep-dive investigation into the portfolio holding changes made by mutual funds and private funds regarding a specific stock over the past month (30 days).

Focus your output on the following core dimensions:

1. **Global Overview of Position Changes:**
   - Over the past month, did institutional investors as a whole (broken down by mutual funds vs. private funds) show a net increase, net decrease, or flat positioning in this stock?
   - What are the approximate total shares traded, the change in market value, and the percentage of the stock's total free float that these changes represent?

2. **Top Mutual Fund Movements (Top 3-5):**
   - Which major mutual funds or asset management firms (e.g., Vanguard, BlackRock, Fidelity for global markets; or E Fund, GF Fund for the Chinese market) made significant moves on this stock over the past month?
   - Please list the specific number of shares increased/decreased and their latest ownership percentages.

3. **Star/Top Private Funds & Hedge Funds Movements (Top 3-5):**
   - Track the latest actions or disclosure dynamics of well-known private funds and hedge funds (e.g., Berkshire Hathaway, Bridgewater Associates, Renaissance Technologies, Citadel, or top-tier domestic private funds) regarding this stock over the past month.

4. **Key Drivers & Market Sentiment Analysis:**
   - What are the core driving factors behind the collective buying or selling by these top-tier funds? (e.g., earnings performance, supply chain adjustments, overvaluation, macroeconomic shifts, industry cycle rotation, etc.)
   - What kind of market outlook and expectations do these institutional holding changes reflect?

Delivery Requirements:
- Base your analysis strictly on the latest available public data, block trades, institutional investor surveys, major shareholder equity change announcements, or regulatory filings closest to the past month's window.
- If certain data features regulatory disclosure lags (such as the 45-day lag for 13F filings), please integrate the past month's market block flows, analyst tracking data, and fund NAV anomalies to provide a reasonable estimation. Clearly specify your data sources or underlying derivation logic.
- Ensure the response is logically structured, utilizing data tables and structured bullet points for analysis."""


class FundHoldingAnalyst:
    @staticmethod
    def analyze(symbol: str, company_name: str = None) -> str:
        """Analyze institutional fund holding changes using LLM."""
        print(f'DEBUG: FundHoldingAnalyst analyzing {symbol}')

        display_name = f"{company_name} ({symbol})" if company_name else symbol

        user_prompt = f"""Please conduct a comprehensive analysis of institutional fund holding changes for:

**Stock Name/Ticker: {display_name}**

Analyze the portfolio holding changes made by mutual funds and private funds (including private equity and hedge funds) regarding this stock over the past month (30 days).

Please provide your analysis following the structured format outlined in your system instructions, including:
1. Global overview of position changes
2. Top mutual fund movements
3. Top private/hedge fund movements
4. Key drivers and market sentiment analysis

Use markdown tables and bullet points for clear presentation."""

        messages = [
            SystemMessage(content=FUND_HOLDING_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = get_llm().invoke(messages)
            return response.content
        except Exception as e:
            print(f"ERROR: FundHoldingAnalyst failed: {e}")
            return f"Fund holding analysis unavailable: {str(e)}"
