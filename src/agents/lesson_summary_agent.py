import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from ..utils.llm_client import get_llm_client

load_dotenv(os.path.join('config', '.env'))


def get_llm():
    return get_llm_client('LESSON_MODEL', 'LESSON_URL', 'Lesson Summary')


LESSON_SUMMARY_SYSTEM_PROMPT = """You are a senior financial analyst responsible for creating concise learning summaries from investment analyses.

Your task is to create a structured lesson summary that captures the key insights, decisions, and reasoning from an investment analysis. This summary will be stored in a vector database for future reference when analyzing the same stock.

Create a summary that includes:
1. **Key Findings**: Main insights from the analysis
2. **Investment Thesis**: Bull vs Bear arguments summary
3. **Decision Rationale**: Why the final recommendation was made
4. **Risk Factors**: Key risks identified
5. **Lessons Learned**: What can be applied to future analyses

Keep the summary under 800 words. Use clear, actionable language that will be useful for future reference.

Format the output as a structured markdown document."""


class LessonSummaryAgent:
    @staticmethod
    def generate_summary(
        symbol: str,
        investment_period: str,
        debate_result: str,
        trading_plan: str,
        analysis_start_time: str
    ) -> str:
        """Generate a lesson summary from debate and trading plan."""
        print(f'DEBUG: LessonSummaryAgent generating summary for {symbol}')

        user_prompt = f"""Based on the following investment analysis for **{symbol}**, create a concise lesson summary.

**Investment Period:** {investment_period}
**Analysis Start Time:** {analysis_start_time}

**Debate Result:**
{debate_result[:3000]}

**Trading Plan:**
{trading_plan[:2000]}

Please create a structured lesson summary under 800 words that captures the key insights and decision rationale for future reference."""

        messages = [
            SystemMessage(content=LESSON_SUMMARY_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = get_llm().invoke(messages)
            return response.content
        except Exception as e:
            print(f"ERROR: LessonSummaryAgent failed: {e}")
            return f"Lesson summary generation failed: {str(e)}"
