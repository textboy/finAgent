import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv(os.path.join('config', '.env'))

DEFAULT_MODEL_NAME = 'x-ai/grok-beta'

# Lazy initialization of LLM
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        primary_key = os.getenv('LLM_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        backup_key = os.getenv('BK_LLM_API_KEY')

        try:
            print(f"DEBUG: LessonSummary - Trying primary LLM: {os.getenv('LLM_BASE_MODEL')}")
            _llm = ChatOpenAI(
                model=os.getenv('LLM_BASE_MODEL', DEFAULT_MODEL_NAME),
                api_key=primary_key,
                base_url=os.getenv('LLM_BASE_URL'),
                temperature=0.1,
            )
            _llm.invoke([{"role": "user", "content": "hi"}])
            print(f"DEBUG: LessonSummary - Primary LLM OK")
        except Exception as e:
            print(f"DEBUG: LessonSummary - Primary LLM failed: {e}")
            try:
                _llm = ChatOpenAI(
                    model=os.getenv('LLM_BACKUP_MODEL', DEFAULT_MODEL_NAME),
                    api_key=backup_key,
                    base_url=os.getenv('LLM_BACKUP_URL'),
                    temperature=0.1,
                )
                _llm.invoke([{"role": "user", "content": "hi"}])
                print(f"DEBUG: LessonSummary - Backup LLM OK")
            except Exception as e2:
                print(f"DEBUG: LessonSummary - Backup LLM also failed: {e2}")
                raise Exception(f"Both LLM providers failed. Primary: {e}, Backup: {e2}")
    return _llm


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
