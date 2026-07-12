import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from ..utils.llm_client import get_llm_client, invoke_llm_with_retry

load_dotenv(os.path.join('config', '.env'))


def get_llm():
    return get_llm_client('LESSON_MODEL', 'LESSON_URL', 'Lesson Summary', provider_env_var='LESSON_PROVIDER')


LESSON_SUMMARY_SYSTEM_PROMPT = """You are a senior financial analyst responsible for creating concise learning summaries from investment analyses.

Your task is to create a structured lesson summary that captures the key insights, decisions, and reasoning from an investment analysis. This summary will be stored in a vector database for future reference when analyzing the same stock.

IMPORTANT FORMAT:
- Use a SINGLE h1 heading for the main title: # Lesson Summary: [Symbol] [Period]
- Use h3 headings for ALL sub-sections inside:
  ### Key Findings
  ### Investment Thesis
  ### Decision Rationale
  ### Risk Factors
  ### Lessons Learned

Do NOT use h1 or h2 for sub-sections. Only use h1 for the main title. All other headings must be h3.

Keep the summary under 800 words. Use clear, actionable language that will be useful for future reference.

Format the output as a structured markdown document with the exact headings listed above."""


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
            return invoke_llm_with_retry(get_llm(), messages, "Lesson Summary")
        except Exception as e:
            print(f"ERROR: LessonSummaryAgent failed: {e}")
            return f"Lesson summary generation failed: {str(e)}"
