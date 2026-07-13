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

        system_prompt = f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, always include the following key information in your analysis:
1. **PROPOSAL**: **BUY/HOLD/SELL**' to confirm your recommendation.
2. **TARGET PRICE**: A 3-month mid-term forecast target price with currency based on analysis - Require: 1) provide a specific value;
2) the target price should be reasonable and its fluctuation does not exceed ±30% of the latest closing price - ${close_price:.2f}.
3. **FORECAST PERIOD**: {forecast_period}
4. **CONFIDENCE**: The degree of confidence in the decision (between 0 and 1)
5. **RISK SCORE**: Investment risk level (between 0 and 1, 0 is low risk and 1 is high risk)
6. **LAST CLOSE PRICE**: ${close_price:.2f}
7. **RATIONALE**: A brief explanation of the reasoning behind the decision.

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