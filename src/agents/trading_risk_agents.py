from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..tools.analyst_tools import get_close_price
from ..utils.qdrant_utils import get_past_lessons
from .analyst_agents import llm  # reuse


INFO_SIZE = 1200
def get_forecast_period(investmentPeriod: str) -> str:
    interval_map = {
        "short+": "within 2 weeks",
        "short": "2 weeks to 1 month",
        "medium": "from 1 month to 1 year",
        "long": "from 1 year to 2 years"
    }
    try:
        return interval_map[investmentPeriod]
    except KeyError:
        print(f"WARNING: The key {investmentPeriod} is not correct")
        return "1 year"

class TradingAgent:
    @staticmethod
    def decide(symbol: str, investment_period: str, debate_result: str, past_lessons: str = "") -> str:
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
long focus on fundamental analysis and macro news sentiment analysis.

Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_lessons}"""
        
        user_prompt = f"provide trader_plan including:\\n    - trading signal: BUY/SELL/HOLD\\n    - trading timing: when/what price to BUY/SELL\\n    - reason for trading\\nDebate result: {debate_result}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content

class RiskManagementAgent:
    @staticmethod
    def evaluate(symbol: str, investment_period: str, analyst_insights: dict, researcher_results: dict, trader_plan: str, past_lessons: str = "") -> str:
        print(f'DEBUG: past_lessons -- {past_lessons}')
        forecast_period = get_forecast_period(investment_period)
        insights_summary = f"Analyst insights: fundamentals={analyst_insights['fundamentals'][:INFO_SIZE]} sentiment={analyst_insights['sentiment'][:INFO_SIZE]} technical={analyst_insights['technical'][:INFO_SIZE]}"
        debate = researcher_results['debate']
        
        user_prompt = f"""provide risk_plan including:
- risky risk analysis
- neutral risk analysis
- safe risk analysis
- final risk evaluation: APPROVE/REJECT
- reason for risk evaluation
Insights: {insights_summary}
Debate: {debate}
Trader plan: {trader_plan}"""

        system_prompt = f"""As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three 
risk analysts—Risky, Neutral, and Safe. Determine the best course of action for the trader. Choose Hold only if strongly justified by specific arguments, 
not as a fallback when all sides seem valid. Strive for clarity and decisiveness.

Guidelines for Decision-Making:
1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
3. **Refine the Trader's Plan**: Start with the trader's original plan, `{trader_plan}`, and adjust it based on the analysts' insights.
4. **Learn from Past Mistakes**: Use lessons from `{past_lessons}` to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money.
5. **Forecast Period**: {forecast_period}, short+ focus on short-term technical analysis and latest news sentiment analysis and breaking macro news sentiment analysis, 
short focus on short/long-term technical analysis and news sentiment analysis and macro news sentiment analysis,
medium focus on fundamental analysis and long-term technical analysis and macro news sentiment analysis,
long focus on fundamental analysis and macro news sentiment analysis.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        return llm.invoke(messages).content