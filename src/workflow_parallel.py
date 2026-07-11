"""
Parallel Pipeline for FinAgent Analysis

Architecture:
- Outer parallelism: 1-5 stock tickets in 5 threads
- Inner parallelism per ticket:
  - Steps 1-7 run in parallel
  - Steps 8.1 (Bull) and 8.2 (Bear) run in parallel after steps 1-7
  - Step 8.3 (Debate) runs after 8.1 and 8.2
  - Step 9 (Trading) runs after 8.3
  - Step 10 (Lesson Summary) runs in BACKGROUND after Step 9 (non-blocking)
"""

import os
import sys
import time
import signal
import logging
import threading
import traceback
from typing import Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Get logger for this module
logger = logging.getLogger('finagent')


# Signal handler for segmentation faults
def _segfault_handler(signum, frame):
    """Handle segmentation fault gracefully."""
    logger.error("Segmentation fault detected. This may be caused by threading issues or memory problems.")
    logger.error("Try reducing parallel workers or running fewer symbols at once.")
    # Don't exit, let the error propagate naturally


# Install segfault handler
signal.signal(signal.SIGSEGV, _segfault_handler)

from .agents.analyst_agents import (
    FundamentalsAnalyst,
    SentimentAnalyst,
    TechnicalAnalyst,
    MarketAnalyst
)
from .agents.global_economic_agent import get_global_economic_analysis
from .agents.fund_holding_agent import FundHoldingAnalyst
from .agents.researcher_agents import BullishResearcher, BearishResearcher, DebateAgent
from .agents.trading_risk_agents import TradingAgent
from .agents.lesson_summary_agent import LessonSummaryAgent
from .agents.quant_agent import QuantAgent
from .utils.qdrant_utils import get_past_lessons, store_entry
from .utils.cost_tracker import cost_tracker

# Configuration
STEP_TIMEOUT = 180  # seconds per step
MAX_WORKERS_INNER = 3  # parallel steps 1-7
MAX_WORKERS_BULL_BEAR = 2  # parallel bull/bear


class StepResult:
    """Wrapper for step results with error handling."""
    def __init__(self, result: Any = None, error: Optional[str] = None, duration: float = 0):
        self.result = result
        self.error = error
        self.duration = duration
        self.success = error is None

    def __repr__(self):
        if self.success:
            return f"StepResult(success, {self.duration:.1f}s)"
        return f"StepResult(error: {self.error[:50]}, {self.duration:.1f}s)"


def _run_step_with_timeout(func, *args, timeout: int = STEP_TIMEOUT, **kwargs) -> StepResult:
    """Run a function with timeout and error handling."""
    start = time.time()
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start
        return StepResult(result=result, duration=duration)
    except MemoryError:
        duration = time.time() - start
        error_msg = "MemoryError: Not enough memory to complete this step"
        logger.error(f" Step failed (memory): {error_msg}")
        return StepResult(error=error_msg, duration=duration)
    except Exception as e:
        duration = time.time() - start
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f" Step failed after {duration:.1f}s: {error_msg}")
        traceback.print_exc()
        return StepResult(error=error_msg, duration=duration)


def _step_1_fundamentals(symbol: str, investment_period: str) -> Tuple[str, StepResult]:
    """Step 1: Fundamentals Analysis."""
    def _run():
        return FundamentalsAnalyst.analyze(symbol, investment_period)
    return ("fundamentals", _run_step_with_timeout(_run))


def _step_2_sentiment(symbol: str) -> Tuple[str, StepResult]:
    """Step 2: Sentiment & Social Analysis."""
    def _run():
        return SentimentAnalyst.analyze(symbol)
    return ("sentiment", _run_step_with_timeout(_run))


def _step_3_technical(symbol: str, investment_period: str) -> Tuple[str, StepResult]:
    """Step 3: Technical Analysis."""
    def _run():
        return TechnicalAnalyst.analyze(symbol, investment_period)
    return ("technical", _run_step_with_timeout(_run))


def _step_4_market(investment_period: str) -> Tuple[str, StepResult]:
    """Step 4: Market Overview."""
    def _run():
        return MarketAnalyst.analyze(investment_period)
    return ("market", _run_step_with_timeout(_run))


def _step_5_global_economic(investment_period: str) -> Tuple[str, StepResult]:
    """Step 5: Global Economy."""
    def _run():
        return get_global_economic_analysis(investment_period)
    return ("global_economic", _run_step_with_timeout(_run))


def _step_6_fund_holding(symbol: str) -> Tuple[str, StepResult]:
    """Step 6: Fund Holdings."""
    def _run():
        return FundHoldingAnalyst.analyze(symbol)
    return ("fund_holding", _run_step_with_timeout(_run))


def _step_7_past_lessons(symbol: str) -> Tuple[str, StepResult]:
    """Step 7: Past Lessons."""
    def _run():
        try:
            lessons = get_past_lessons(symbol)
            if lessons:
                return "\n".join(lessons)
            else:
                return "No past lessons found. (Qdrant may not be available)"
        except Exception as e:
            logger.warning(f"Past lessons unavailable: {str(e)}")
            return "Past lessons unavailable. (Qdrant may not be running)"
    return ("past_lessons", _run_step_with_timeout(_run))


def _step_quant(symbol: str, investment_period: str, phase1_data: Dict) -> Tuple[str, StepResult]:
    """Quant Analysis: Triple-barrier + trend analysis."""
    def _run():
        agent = QuantAgent()
        return agent.analyze(symbol, investment_period, phase1_data)
    return ("quant", _run_step_with_timeout(_run))


def _run_steps_1_to_7(symbol: str, investment_period: str, step_logs: list) -> Dict[str, StepResult]:
    """Run steps 1-7 in parallel."""
    logger.debug(f" [{symbol}] Running steps 1-7 in parallel")
    start = time.time()

    step_display_names = {
        "fundamentals": "Fundamentals",
        "sentiment": "Sentiment & Social",
        "technical": "Technical",
        "market": "Market Overview",
        "global_economic": "Global Economy",
        "fund_holding": "Fund Holdings",
        "past_lessons": "Past Lessons",
    }

    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_INNER) as executor:
        futures = {
            executor.submit(_step_1_fundamentals, symbol, investment_period): "fundamentals",
            executor.submit(_step_2_sentiment, symbol): "sentiment",
            executor.submit(_step_3_technical, symbol, investment_period): "technical",
            executor.submit(_step_4_market, investment_period): "market",
            executor.submit(_step_5_global_economic, investment_period): "global_economic",
            executor.submit(_step_6_fund_holding, symbol): "fund_holding",
            executor.submit(_step_7_past_lessons, symbol): "past_lessons",
        }

        for future in as_completed(futures):
            step_name = futures[future]
            try:
                name, result = future.result(timeout=STEP_TIMEOUT + 10)
                results[name] = result
                status = "✓" if result.success else "✗"
                duration_min = round(result.duration / 60, 2)
                display_name = step_display_names.get(step_name, step_name)
                step_logs.append(f"✅ [{symbol}] {display_name} completed ({duration_min} min)")
                logger.debug(f" [{symbol}] Step {step_name} {status} ({result.duration:.1f}s)")
            except MemoryError:
                results[step_name] = StepResult(error="MemoryError: Not enough memory")
                step_logs.append(f"❌ [{symbol}] {step_display_names.get(step_name, step_name)} failed (memory)")
                logger.error(f" [{symbol}] Step {step_name} ✗ (memory error)")
            except Exception as e:
                error_msg = f"Future error: {type(e).__name__}: {str(e)}"
                results[step_name] = StepResult(error=error_msg)
                step_logs.append(f"❌ [{symbol}] {step_display_names.get(step_name, step_name)} failed")
                logger.debug(f" [{symbol}] Step {step_name} ✗ ({error_msg})")

    duration = time.time() - start
    logger.debug(f" [{symbol}] Steps 1-7 completed in {duration:.1f}s")
    return results


def _step_8_1_bull(symbol: str, investment_period: str, steps_1_to_7: Dict[str, StepResult]) -> Tuple[str, StepResult]:
    """Step 8.1: Bullish Analysis."""
    def _run():
        # Extract individual step outputs
        fundamentals = steps_1_to_7.get("fundamentals", StepResult()).result or ""
        sentiment = steps_1_to_7.get("sentiment", StepResult()).result or ""
        technical = steps_1_to_7.get("technical", StepResult()).result or ""
        market = steps_1_to_7.get("market", StepResult()).result or ""
        global_economic = steps_1_to_7.get("global_economic", StepResult()).result or ""
        fund_holding = steps_1_to_7.get("fund_holding", StepResult()).result or ""
        past_lessons = steps_1_to_7.get("past_lessons", StepResult()).result or ""

        # Build memory context from all steps
        memory = f"""=== GLOBAL ECONOMIC DATA ===
{global_economic}

=== FUND HOLDING CHANGES ===
{fund_holding}

=== PAST LESSONS ===
{past_lessons}"""

        return BullishResearcher.analyze(
            symbol,
            investment_period,
            fundamentals,
            sentiment,
            technical,
            market,
            memory
        )
    return ("bull", _run_step_with_timeout(_run))


def _step_8_2_bear(symbol: str, investment_period: str, steps_1_to_7: Dict[str, StepResult]) -> Tuple[str, StepResult]:
    """Step 8.2: Bearish Analysis."""
    def _run():
        # Extract individual step outputs
        fundamentals = steps_1_to_7.get("fundamentals", StepResult()).result or ""
        sentiment = steps_1_to_7.get("sentiment", StepResult()).result or ""
        technical = steps_1_to_7.get("technical", StepResult()).result or ""
        market = steps_1_to_7.get("market", StepResult()).result or ""
        global_economic = steps_1_to_7.get("global_economic", StepResult()).result or ""
        fund_holding = steps_1_to_7.get("fund_holding", StepResult()).result or ""
        past_lessons = steps_1_to_7.get("past_lessons", StepResult()).result or ""

        # Build memory context from all steps
        memory = f"""=== GLOBAL ECONOMIC DATA ===
{global_economic}

=== FUND HOLDING CHANGES ===
{fund_holding}

=== PAST LESSONS ===
{past_lessons}"""

        return BearishResearcher.analyze(
            symbol,
            investment_period,
            fundamentals,
            sentiment,
            technical,
            market,
            memory
        )
    return ("bear", _run_step_with_timeout(_run))


def _run_steps_8_1_and_8_2(symbol: str, investment_period: str, steps_1_to_7: Dict[str, StepResult]) -> Dict[str, StepResult]:
    """Run bull and bear analyses in parallel."""
    logger.debug(f" [{symbol}] Running steps 8.1 (bull) and 8.2 (bear) in parallel")
    start = time.time()

    step_display_names = {
        "bull": "Bull Analysis",
        "bear": "Bear Analysis",
    }

    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_BULL_BEAR) as executor:
        futures = {
            executor.submit(_step_8_1_bull, symbol, investment_period, steps_1_to_7): "bull",
            executor.submit(_step_8_2_bear, symbol, investment_period, steps_1_to_7): "bear",
        }

        for future in as_completed(futures):
            step_name = futures[future]
            try:
                name, result = future.result(timeout=STEP_TIMEOUT + 10)
                results[name] = result
                status = "✓" if result.success else "✗"
                logger.debug(f" [{symbol}] Step {step_name} {status} ({result.duration:.1f}s)")
            except Exception as e:
                error_msg = f"Future error: {type(e).__name__}: {str(e)}"
                results[step_name] = StepResult(error=error_msg)
                logger.debug(f" [{symbol}] Step {step_name} ✗ ({error_msg})")
                # Add specific error context for common errors
                if "broken pipe" in str(e).lower():
                    detail = "Connection closed by server. Possible causes: timeout, server overload, or network issue."
                    step_logs.append(f"❌ [{symbol}] {step_display_names.get(step_name, step_name)} failed: {detail}")
                elif "timeout" in str(e).lower():
                    detail = f"Request timed out after {STEP_TIMEOUT}s"
                    step_logs.append(f"❌ [{symbol}] {step_display_names.get(step_name, step_name)} failed: {detail}")
                elif "connection" in str(e).lower():
                    detail = "Network connection issue"
                    step_logs.append(f"❌ [{symbol}] {step_display_names.get(step_name, step_name)} failed: {detail}")
                else:
                    step_logs.append(f"❌ [{symbol}] {step_display_names.get(step_name, step_name)} failed: {error_msg}")

    duration = time.time() - start
    logger.debug(f" [{symbol}] Steps 8.1-8.2 completed in {duration:.1f}s")
    return results


def _step_8_3_debate(bull_result: str, bear_result: str, investment_period: str) -> Tuple[str, StepResult]:
    """Step 8.3: Debate Summary."""
    def _run():
        # Append Warren Buffett's core thinkings for long-term analysis
        buffett_context = ""
        if investment_period == "long":
            buffett_context = """

---

## Warren Buffett's 5 Core Investment Principles (Long-Term Analysis)

When evaluating this long-term investment, please consider Warren Buffett's foundational investment philosophy:

**1. Buy a Business, Not a Stock**
- Evaluate the underlying business fundamentals, not just stock price movements
- Focus on the company's ability to generate cash and profits over time

**2. Prioritize Quality and "Economic Moats"**
- Look for companies with sustainable competitive advantages (brand, network effects, switching costs, cost advantages)
- Strong moats protect profits from competitors over the long term

**3. Only Operate Within Your "Circle of Competence"**
- Invest in businesses you thoroughly understand
- Avoid complex or rapidly changing industries where prediction is difficult

**4. Have a "Forever" Holding Period and Embrace Patience**
- Buy with the intention to hold indefinitely
- Time in the market beats timing the market
- Allow compound interest to work its magic

**5. Demand a "Margin of Safety" and Be Contrarian**
- Buy at a significant discount to intrinsic value
- Be greedy when others are fearful, fearful when others are greedy
- Protect downside through conservative valuations

---
Please incorporate these principles into your long-term investment debate summary."""
        return DebateAgent.summarize(bull_result, bear_result + buffett_context, investment_period)
    return ("debate", _run_step_with_timeout(_run))


def _step_9_trading(symbol: str, investment_period: str, debate_result: str,
                    quant_result: str = None) -> Tuple[str, StepResult]:
    """Step 9: Trading Plan (with optional quant data)."""
    def _run():
        # Combine debate and quant for comprehensive trading decision
        combined_input = debate_result
        if quant_result and quant_result != "[ERROR] Quant analysis failed":
            combined_input = f"""{debate_result}

---

## QUANT SIGNALS (Objective Rules-Based Analysis)

{quant_result}

---

Please incorporate the above quant signals into your trading decision. The quant analysis provides:
- Triple-barrier entry/stop/target levels
- Trend regime (trending vs ranging)
- Volatility regime
- Support/resistance levels
- Meta-label confidence scores

Use this data to validate or adjust your qualitative analysis."""
        return TradingAgent.decide(symbol, investment_period, combined_input)
    return ("trading", _run_step_with_timeout(_run))


def _step_10_lesson_summary(
    symbol: str,
    investment_period: str,
    debate_result: str,
    trading_plan: str,
    analysis_start_time: str
) -> Tuple[str, StepResult]:
    """Step 10: Lesson Summary - Generate and store lesson in Qdrant."""
    def _run():
        # Generate lesson summary
        summary = LessonSummaryAgent.generate_summary(
            symbol,
            investment_period,
            debate_result,
            trading_plan,
            analysis_start_time
        )

        # Store in Qdrant
        store_entry(
            symbol=symbol,
            report_type="lesson",
            content=summary,
            analysis_datetime=analysis_start_time,
            metadata={
                "investment_period": investment_period,
                "analysis_type": "lesson_summary",
                "source_steps": ["debate", "trading"]
            }
        )

        return summary
    return ("lesson_summary", _run_step_with_timeout(_run))


def run_single_ticket_pipeline(symbol: str, investment_period: str) -> Dict[str, Any]:
    """
    Run the complete analysis pipeline for a single stock ticket.

    Returns:
        Dict with all results including timing, errors, and step logs.
    """
    pipeline_start = time.time()
    step_logs = []
    # Reset cost tracker for this analysis run
    cost_tracker.reset()
    logger.info(f"PIPELINE START: {symbol} ({investment_period})")

    step_display_names = {
        "bull": "Bull Analysis",
        "bear": "Bear Analysis",
        "debate": "Research Debate",
        "trading": "Trading Plan",
    }

    result = {
        "symbol": symbol,
        "investment_period": investment_period,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "steps": {},
        "step_logs": step_logs,
        "errors": [],
        "success": True
    }

    # Phase 1: Run steps 1-7 in parallel
    try:
        steps_1_to_7 = _run_steps_1_to_7(symbol, investment_period, step_logs)
        result["steps"].update({k: v.result if v.success else f"[ERROR] {v.error}"
                               for k, v in steps_1_to_7.items()})

        # Check for critical failures
        critical_steps = ["fundamentals", "technical"]
        for step in critical_steps:
            if not steps_1_to_7.get(step, StepResult()).success:
                result["errors"].append(f"Critical step {step} failed")
                result["success"] = False
    except MemoryError:
        result["errors"].append("Phase 1 failed: Out of memory")
        result["success"] = False
        result["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["duration_minutes"] = round((time.time() - pipeline_start) / 60, 2)
        return result
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        result["errors"].append(f"Phase 1 failed: {error_msg}")
        result["success"] = False
        result["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["duration_minutes"] = round((time.time() - pipeline_start) / 60, 2)
        return result

    # Phase 2+Quant: Run bull/bear AND quant in parallel (requires steps 1-7)
    logger.info(f" [{symbol}] Phase 2+Quant: Starting Bull/Bear + Quant analysis...")
    step_logs.append(f"🔄 [{symbol}] Starting Bull/Bear + Quant analysis...")
    bull_result = StepResult(error="Not started")
    bear_result = StepResult(error="Not started")
    quant_result = StepResult(error="Not started")

    try:
        # Run bull/bear and quant in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_step_8_1_bull, symbol, investment_period, steps_1_to_7): "bull",
                executor.submit(_step_8_2_bear, symbol, investment_period, steps_1_to_7): "bear",
                executor.submit(_step_quant, symbol, investment_period, steps_1_to_7): "quant",
            }

            for future in as_completed(futures):
                step_name = futures[future]
                try:
                    name, step_result = future.result(timeout=STEP_TIMEOUT + 10)
                    if step_name == "bull":
                        bull_result = step_result
                        result["steps"]["bull"] = step_result.result if step_result.success else f"[ERROR] {step_result.error}"
                    elif step_name == "bear":
                        bear_result = step_result
                        result["steps"]["bear"] = step_result.result if step_result.success else f"[ERROR] {step_result.error}"
                    elif step_name == "quant":
                        quant_result = step_result
                        result["steps"]["quant"] = step_result.result if step_result.success else f"[ERROR] {step_result.error}"

                    status = "✓" if step_result.success else "✗"
                    logger.debug(f" [{symbol}] Step {step_name} {status} ({step_result.duration:.1f}s)")
                except Exception as e:
                    error_msg = f"Future error: {type(e).__name__}: {str(e)}"
                    if step_name == "bull":
                        bull_result = StepResult(error=error_msg)
                    elif step_name == "bear":
                        bear_result = StepResult(error=error_msg)
                    elif step_name == "quant":
                        quant_result = StepResult(error=error_msg)
                    logger.debug(f" [{symbol}] Step {step_name} ✗ ({error_msg})")

        # Log completion
        if bull_result.success:
            step_logs.append(f"✅ [{symbol}] Bull Analysis completed ({round(bull_result.duration / 60, 2)} min)")
        else:
            error_detail = bull_result.error[:200] if bull_result.error else "Unknown error"
            step_logs.append(f"❌ [{symbol}] Bull Analysis failed: {error_detail}")

        if bear_result.success:
            step_logs.append(f"✅ [{symbol}] Bear Analysis completed ({round(bear_result.duration / 60, 2)} min)")
        else:
            error_detail = bear_result.error[:200] if bear_result.error else "Unknown error"
            step_logs.append(f"❌ [{symbol}] Bear Analysis failed: {error_detail}")

        if quant_result.success:
            step_logs.append(f"✅ [{symbol}] Quant Analysis completed ({round(quant_result.duration / 60, 2)} min)")
        else:
            error_detail = quant_result.error[:200] if quant_result.error else "Unknown error"
            step_logs.append(f"❌ [{symbol}] Quant Analysis failed: {error_detail}")

        if not bull_result.success or not bear_result.success:
            if not bull_result.success and not bear_result.success:
                result["errors"].append("Both Bull and Bear analysis failed")
            elif not bull_result.success:
                result["errors"].append("Bull analysis failed, Bear may have partial results")
            else:
                result["errors"].append("Bear analysis failed, Bull may have partial results")
    except MemoryError:
        result["errors"].append("Phase 2+Quant failed: Out of memory")
        bull_result = StepResult(error="MemoryError")
        bear_result = StepResult(error="MemoryError")
        quant_result = StepResult(error="MemoryError")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        result["errors"].append(f"Phase 2+Quant failed: {error_msg}")
        bull_result = StepResult(error=error_msg)
        bear_result = StepResult(error=error_msg)

    # Phase 3: Debate (requires bull/bear)
    logger.info(f" [{symbol}] Phase 3: Starting Research Debate...")
    step_logs.append(f"🔄 [{symbol}] Starting Research Debate...")
    debate_result = StepResult(error="Skipped")
    try:
        if bull_result.success and bear_result.success:
            debate_name, debate_result = _step_8_3_debate(
                bull_result.result, bear_result.result, investment_period
            )
            result["steps"]["debate"] = debate_result.result if debate_result.success else f"[ERROR] {debate_result.error}"

            if debate_result.success:
                step_logs.append(f"✅ [{symbol}] Research Debate completed ({round(debate_result.duration / 60, 2)} min)")
            else:
                error_detail = debate_result.error[:200] if debate_result.error else "Unknown error"
                step_logs.append(f"❌ [{symbol}] Research Debate failed: {error_detail}")
                result["errors"].append(f"Debate failed: {debate_result.error}")
        else:
            result["steps"]["debate"] = "[ERROR] Skipped due to bull/bear failure"
            debate_result = StepResult(error="Skipped")
            if not bull_result.success:
                step_logs.append(f"❌ [{symbol}] Research Debate skipped (bull failed)")
            else:
                step_logs.append(f"❌ [{symbol}] Research Debate skipped (bear failed)")
    except MemoryError:
        result["errors"].append("Phase 3 failed: Out of memory")
        debate_result = StepResult(error="MemoryError")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        result["errors"].append(f"Phase 3 failed: {error_msg}")
        debate_result = StepResult(error=error_msg)

    # Phase 4: Trading Plan (requires debate + quant)
    logger.info(f" [{symbol}] Phase 4: Starting Trading Plan...")
    step_logs.append(f"🔄 [{symbol}] Starting Trading Plan...")
    try:
        if debate_result.success:
            # Get quant result (may have failed)
            quant_text = quant_result.result if quant_result.success else None
            trading_name, trading_result = _step_9_trading(
                symbol, investment_period, debate_result.result, quant_text
            )
            result["steps"]["trading"] = trading_result.result if trading_result.success else f"[ERROR] {trading_result.error}"

            if trading_result.success:
                step_logs.append(f"✅ [{symbol}] Trading Plan completed ({round(trading_result.duration / 60, 2)} min)")
            else:
                error_detail = trading_result.error[:200] if trading_result.error else "Unknown error"
                step_logs.append(f"❌ [{symbol}] Trading Plan failed: {error_detail}")
                result["errors"].append(f"Trading plan failed: {trading_result.error}")
        else:
            result["steps"]["trading"] = "[ERROR] Skipped due to debate failure"
            trading_result = StepResult(error="Skipped")
            step_logs.append(f"❌ [{symbol}] Trading Plan skipped (debate failed)")
    except MemoryError:
        result["errors"].append("Phase 4 failed: Out of memory")
        trading_result = StepResult(error="MemoryError")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        result["errors"].append(f"Phase 4 failed: {error_msg}")
        trading_result = StepResult(error=error_msg)

    # Phase 5: Lesson Summary (runs in background, non-blocking)
    # Launch background thread for lesson summary
    def _run_lesson_summary_background():
        try:
            if debate_result.success and trading_result.success:
                logger.debug(f" [{symbol}] Starting background lesson summary...")
                _step_10_lesson_summary(
                    symbol,
                    investment_period,
                    debate_result.result,
                    trading_result.result,
                    result["start_time"]
                )
                logger.debug(f" [{symbol}] Background lesson summary completed")
            else:
                logger.debug(f" [{symbol}] Skipping lesson summary (debate/trading failed)")
        except Exception as e:
            logger.warning(f" [{symbol}] Background lesson summary failed: {str(e)}")

    # Start background thread (non-blocking)
    lesson_thread = threading.Thread(
        target=_run_lesson_summary_background,
        daemon=True,
        name=f"lesson-{symbol}"
    )
    lesson_thread.start()
    logger.debug(f" [{symbol}] Lesson summary thread started (background)")

    result["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result["duration_minutes"] = round((time.time() - pipeline_start) / 60, 2)
    result["cost_summary"] = cost_tracker.get_summary()

    print(f"\n{'='*60}")
    print(f"  PIPELINE END: {symbol} ({result['duration_minutes']} min)")
    print(f"  Success: {result['success']}, Errors: {len(result['errors'])}")
    print(f"{'='*60}\n")

    return result


def run_batch_pipeline(symbols: list, investment_period: str) -> list:
    """
    Run analysis pipeline for multiple stock tickets in parallel.

    Args:
        symbols: List of stock symbols (max 5)
        investment_period: Investment period

    Returns:
        List of results, one per symbol
    """
    if len(symbols) > 5:
        raise ValueError("Maximum 5 symbols allowed")

    if not symbols:
        raise ValueError("At least one symbol required")

    print(f"\n{'#'*60}")
    print(f"  BATCH PIPELINE: {len(symbols)} symbols")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Period: {investment_period}")
    print(f"{'#'*60}\n")

    batch_start = time.time()
    results = []

    # Outer parallelism: run each symbol in parallel
    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(run_single_ticket_pipeline, symbol.strip().upper(), investment_period): symbol
                for symbol in symbols
            }

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result(timeout=600)  # 10 min timeout per ticket
                    results.append(result)
                    print(f"BATCH: {symbol} completed ({result['duration_minutes']} min)")
                except Exception as e:
                    results.append({
                        "symbol": symbol.strip().upper(),
                        "error": str(e),
                        "success": False,
                        "steps": {},
                        "errors": [str(e)]
                    })
                    print(f"BATCH: {symbol} failed: {str(e)[:50]}")
    except Exception as e:
        print(f"BATCH ERROR: {str(e)}")
        # Return partial results if any
        if not results:
            results = [{
                "symbol": "UNKNOWN",
                "error": str(e),
                "success": False,
                "steps": {},
                "errors": [str(e)]
            }]

    # Sort results by original order
    symbol_order = {s.strip().upper(): i for i, s in enumerate(symbols)}
    results.sort(key=lambda x: symbol_order.get(x['symbol'], 0))

    batch_duration = round((time.time() - batch_start) / 60, 2)
    print(f"\nBATCH COMPLETE: {len(results)} symbols in {batch_duration} min\n")

    return results
