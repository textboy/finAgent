import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..utils.qdrant_utils import get_past_lessons

load_dotenv(os.path.join('config', '.env'))

DEFAULT_MODEL_NAME = 'x-ai/grok-beta'

def get_period_description(investment_period: str) -> str:
    """Convert period code to descriptive timeframe."""
    period_map = {
        "short+": "Short+ (1-7 days)",
        "short": "Short (1-4 weeks)",
        "medium": "Medium (1-6 months)",
        "long": "Long (6+ months)"
    }
    return period_map.get(investment_period, investment_period)

# Lazy initialization of LLM to ensure env vars are loaded
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        # Try LLM_API_KEY first, then fall back to OPENROUTER_API_KEY
        api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        print(f"DEBUG: LLM API key type: {type(api_key)}, set: {bool(api_key)}")
        _llm = ChatOpenAI(
            model=os.getenv('LLM_BASE_MODEL', DEFAULT_MODEL_NAME),
            api_key=api_key,
            base_url=os.getenv('LLM_BASE_URL'),
            temperature=0.1,
        )
    return _llm

BULL_SYSTEM_PROMPT = """You are a Bull Analyst advocating for investing in the stock. Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.

Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability.
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly and showing why the bull perspective holds stronger merit.
- Engagement: Present your argument in a conversational style, engaging directly with the bear analyst's points and debating effectively rather than just listing data."""

BEAR_SYSTEM_PROMPT = """You are a Bear Analyst making the case against investing in the stock. Your goal is to present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Leverage the provided research and data to highlight potential downsides and counter bullish arguments effectively.

Key points to focus on:
- Risks and Challenges: Highlight factors like market saturation, financial instability, or macroeconomic threats that could hinder the stock's performance.
- Competitive Weaknesses: Emphasize vulnerabilities such as weaker market positioning, declining innovation, or threats from competitors.
- Negative Indicators: Use evidence from financial data, market trends, or recent adverse news to support your position.
- Bull Counterpoints: Critically analyze the bull argument with specific data and sound reasoning, exposing weaknesses or over-optimistic assumptions.
- Engagement: Present your argument in a conversational style, directly engaging with the bull analyst's points and debating effectively rather than simply listing facts.
"""

class BullishResearcher:
    @staticmethod
    def analyze(symbol: str, investment_period: str, fundamentals_report: str, sentiment_report: str, technical_report: str, market_report: str, memory: str = "") -> str:
        period_desc = get_period_description(investment_period)
        user_prompt = f"""provide a bullish analysis for {symbol} with analysis period: {period_desc}
Resources available:
Company fundamentals report: {fundamentals_report}
News sentiment report: {sentiment_report}
Technical analysis report: {technical_report}
Market overview report: {market_report}
Report history of the debate: {memory}
Use this information to deliver a compelling bull argument, refute the bear's concerns, and engage in a dynamic debate that demonstrates the strengths of the bull position. You must also address reflections and learn from lessons and mistakes you made in the past.
Consider the overall market conditions (S&P 500, NASDAQ, VIX, sector performance) when making your case.
Focus your analysis on the {period_desc} timeframe.
"""

        messages = [
            SystemMessage(content=BULL_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        return get_llm().invoke(messages).content

class BearishResearcher:
    @staticmethod
    def analyze(symbol: str, investment_period: str, fundamentals_report: str, sentiment_report: str, technical_report: str, market_report: str, memory: str = "") -> str:
        period_desc = get_period_description(investment_period)
        user_prompt = f"""provide a bearish analysis for {symbol} with analysis period: {period_desc}
Resources available:
Company fundamentals report: {fundamentals_report}
News sentiment report: {sentiment_report}
Technical analysis report: {technical_report}
Market overview report: {market_report}
Report history of the debate: {memory}
Use this information to deliver a compelling bear argument, refute the bull's claims, and engage in a dynamic debate that demonstrates the risks and weaknesses of investing in the stock. You must also address reflections and learn from lessons and mistakes you made in the past.
Consider the overall market conditions (S&P 500, NASDAQ, VIX, sector performance) when making your case.
Focus your analysis on the {period_desc} timeframe.
"""

        messages = [
            SystemMessage(content=BEAR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        return get_llm().invoke(messages).content

class DebateAgent:
    @staticmethod
    def summarize(bull_analysis: str, bear_analysis: str, investment_period: str) -> str:
        period_desc = get_period_description(investment_period)
        user_prompt = f"""provide debate result based on both bullish analysis and bearish analysis for {period_desc} timeframe.
Bull: {bull_analysis[:3000]}
Bear: {bear_analysis[:3000]}"""

        messages = [
            SystemMessage(content="You are a debate moderator. Summarize the key points from both sides and provide a balanced debate result."),
            HumanMessage(content=user_prompt)
        ]
        return get_llm().invoke(messages).content

def researcher_team(analyst_insights: dict, symbol: str, investment_period: str, past_lessons: str = "") -> dict:
    print('DEBUG: researcher_team')
    fundamentals = analyst_insights['fundamentals']
    sentiment = analyst_insights['sentiment']
    technical = analyst_insights['technical']
    market = analyst_insights.get('market', '')

    memory = past_lessons  # or accumulate debate history

    bull = BullishResearcher.analyze(symbol, investment_period, fundamentals, sentiment, technical, market, memory)
    bear = BearishResearcher.analyze(symbol, investment_period, fundamentals, sentiment, technical, market, memory + f"\\nPrevious bull: {bull[-500:]}")  # simple memory

    debate = DebateAgent.summarize(bull, bear, investment_period)

    return {
        'bull': bull,
        'bear': bear,
        'debate': debate
    }