import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from ..tools.analyst_tools import get_close_price
from ..utils.llm_client import get_llm_client, invoke_llm_with_retry

load_dotenv(os.path.join('config', '.env'))


def get_llm():
    # Precise, disciplined financial decisions — low creativity, tight sampling
    return get_llm_client('TRADING_MODEL', 'TRADING_URL', 'Trading Plan', temperature=0.3, top_p=0.9, provider_env_var='TRADING_PROVIDER')


INFO_SIZE = 1500

def get_forecast_period(investmentPeriod: str) -> str:
    """Convert period code to descriptive timeframe."""
    interval_map = {
        "short+": "Short+ (1-7 days)",
        "short": "Short (1-4 weeks)",
        "medium": "Medium (1-6 months)",
        "long": "Long (6+ months)"
    }
    try:
        return interval_map[investmentPeriod]
    except KeyError:
        print(f"WARNING: The key {investmentPeriod} is not correct")
        return "Medium (1-6 months)"

class TradingAgent:
    @staticmethod
    def decide(symbol: str, investment_period: str, debate_result: str) -> str:
        forecast_period = get_forecast_period(investment_period)
        close_price_str = get_close_price(symbol)
        close_price = float(close_price_str)
        print(f'DEBUG: forecast_period -- {forecast_period}')
        print(f'DEBUG: close_price -- {close_price:.2f}')

        system_prompt = f"""You are a trading agent analyzing market data to make investment decisions.

## OUTPUT FORMAT

Generate a trading plan with EXACTLY these bullet points in order:

### Trading Plan

**1. Proposal:** [HOLD/BUY/SELL]

**2. Final Target Price:** $[VALUE]
- For HOLD/BUY: Target price within ±30% of last close (${close_price:.2f})
- For SELL: If same as last close, means sell all immediately at market price

**3. Exit Price:** $[VALUE] (optional, based on strategy)
- Exit 50% of position at this price
- Consolidates FTA (First Trouble Area) and 0.9R rule
- Only include if there's a clear intermediate exit level
- Omit if no suitable exit point identified

**4. Stop Loss:** $[VALUE] (HOLD/BUY only, not for SELL)
- Maximum acceptable loss level
- Based on support levels and ATR

**5. Forecast Period:** {forecast_period}

**6. Confidence:** [0.00 - 1.00]

**7. Risk Score:** [0.00 - 1.00] (0=low risk, 1=high risk)

**8. Last Close Price:** ${close_price:.2f}

**9. Rationale:** [2-3 sentences explaining the decision]

## EXIT STRATEGY RULES

### FTA (First Trouble Area)
- First significant resistance (for longs) or support (for shorts)
- Exit 50% position just before this level (0.5-1% buffer)

### 0.9R Rule
- R = Initial Risk (Entry - Stop Loss)
- When trade reaches 0.9R profit, sell 50% and move stop to breakeven
- Let remaining position run with trailing stop

### Time Stop
- Max holding period: {forecast_period}
- Exit if target not reached within timeframe

## EXAMPLE OUTPUT

### Trading Plan

**1. Proposal:** BUY

**2. Final Target Price:** $345.00

**3. Exit Price:** $325.00
- Exit 50% at first resistance (FTA)

**4. Stop Loss:** $305.00

**5. Forecast Period:** {forecast_period}

**6. Confidence:** 0.72

**7. Risk Score:** 0.35

**8. Last Close Price:** ${close_price:.2f}

**9. Rationale:** Technical indicators show bullish momentum with RSI at 58 and MACD crossover. Volume analysis confirms accumulation phase. Fundamental strength supports 8-10% upside to target.

---

Target Price Calculation Guidelines:
- Based on valuation data from fundamental analysis
- Reference support and resistance levels from technical analysis
- Consider industry average valuations
- Incorporate market sentiment and news impact
- Even if market sentiment is overheated, target prices should be based on reasonable valuations.
- Forecast period is {forecast_period}, short+ focus on short-term technical analysis and latest news sentiment analysis and breaking macro news sentiment analysis,
short focus on short/long-term technical analysis and news sentiment analysis and macro news sentiment analysis,
medium focus on fundamental analysis and long-term technical analysis and macro news sentiment analysis,
long focus on fundamental analysis and macro news sentiment analysis."""

        user_prompt = f"provide trader_plan including:\\n    - trading signal: BUY/SELL/HOLD\\n    - trading timing: when/what price to BUY/SELL\\n    - reason for trading\\nDebate result: {debate_result}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        return invoke_llm_with_retry(get_llm(), messages, "Trading Plan")