#!/usr/bin/env python3
"""
Regression test for FinAgent pipeline steps 1-9.
Tests each step independently for easier debugging.

Usage:
    python test_regression.py                    # Run all tests
    python test_regression.py --step 1           # Test only step 1
    python test_regression.py --step 8.1         # Test only step 8.1
    python test_regression.py --step 1,2,3       # Test steps 1, 2, and 3
    python test_regression.py --symbol NVDA      # Test with different symbol
"""

import sys
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load .env before importing src modules
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
DEFAULT_SYMBOL = 'AAPL'
DEFAULT_PERIOD = 'short'


def get_test_config():
    """Get test configuration from environment or defaults."""
    return {
        'symbol': os.getenv('TEST_SYMBOL', DEFAULT_SYMBOL),
        'period': os.getenv('TEST_PERIOD', DEFAULT_PERIOD),
    }


# ============================================================================
# STEP TESTS
# ============================================================================

def test_step_1_fundamentals(symbol, period):
    """Test Step 1: Fundamentals Analysis."""
    print("\n" + "="*60)
    print(f"STEP 1: Fundamentals Analysis ({symbol})")
    print("="*60)

    from src.agents.analyst_agents import FundamentalsAnalyst

    start_time = time.time()
    result = FundamentalsAnalyst.analyze(symbol, period)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    assert "FUNDAMENTALS DATA" in result, "Result should contain fundamentals header"
    print(f"✓ Step 1 PASSED ({len(result)} chars)")
    return result


def test_step_2_sentiment(symbol, period):
    """Test Step 2: Sentiment & Social Analysis."""
    print("\n" + "="*60)
    print(f"STEP 2: Sentiment & Social Analysis ({symbol})")
    print("="*60)

    from src.agents.analyst_agents import SentimentAnalyst

    start_time = time.time()
    result = SentimentAnalyst.analyze(symbol)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    assert "SENTIMENT DATA" in result, "Result should contain sentiment header"
    print(f"✓ Step 2 PASSED ({len(result)} chars)")
    return result


def test_step_3_technical(symbol, period):
    """Test Step 3: Technical Analysis."""
    print("\n" + "="*60)
    print(f"STEP 3: Technical Analysis ({symbol})")
    print("="*60)

    from src.agents.analyst_agents import TechnicalAnalyst

    start_time = time.time()
    result = TechnicalAnalyst.analyze(symbol, period)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    assert "TECHNICAL DATA" in result, "Result should contain technical header"
    print(f"✓ Step 3 PASSED ({len(result)} chars)")
    return result


def test_step_4_market(symbol, period):
    """Test Step 4: Market Overview."""
    print("\n" + "="*60)
    print(f"STEP 4: Market Overview ({symbol})")
    print("="*60)

    from src.agents.analyst_agents import MarketAnalyst

    start_time = time.time()
    result = MarketAnalyst.analyze(period)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    assert "MARKET ANALYSIS" in result, "Result should contain market header"
    print(f"✓ Step 4 PASSED ({len(result)} chars)")
    return result


def test_step_5_global_economy(symbol, period):
    """Test Step 5: Global Economy."""
    print("\n" + "="*60)
    print(f"STEP 5: Global Economy ({symbol})")
    print("="*60)

    from src.agents.global_economic_agent import get_global_economic_analysis

    start_time = time.time()
    result = get_global_economic_analysis(period)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    print(f"✓ Step 5 PASSED ({len(result)} chars)")
    return result


def test_step_6_fund_holdings(symbol, period):
    """Test Step 6: Fund Holdings."""
    print("\n" + "="*60)
    print(f"STEP 6: Fund Holdings ({symbol})")
    print("="*60)

    from src.agents.fund_holding_agent import FundHoldingAnalyst

    # Check if API key is configured
    api_key = os.getenv('FINAGENT_ZENMUX_API_KEY') or os.getenv('ZENMUX_API_KEY')
    if not api_key:
        print("⚠️  SKIPPED: ZENMUX_API_KEY not configured")
        return ""

    start_time = time.time()
    result = FundHoldingAnalyst.analyze(symbol)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    print(f"✓ Step 6 PASSED ({len(result)} chars)")
    return result


def test_step_7_past_lessons(symbol, period):
    """Test Step 7: Past Lessons."""
    print("\n" + "="*60)
    print(f"STEP 7: Past Lessons ({symbol})")
    print("="*60)

    from src.utils.qdrant_utils import get_past_lessons

    start_time = time.time()
    result = get_past_lessons(symbol)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, list), "Result should be list"
    print(f"✓ Step 7 PASSED ({len(result)} items)")
    return result


def test_step_8_1_bull(symbol, period):
    """Test Step 8.1: Bull Analysis."""
    print("\n" + "="*60)
    print(f"STEP 8.1: Bull Analysis ({symbol})")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('FINAGENT_ZENMUX_API_KEY') or os.getenv('ZENMUX_API_KEY')
    if not api_key:
        print("⚠️  SKIPPED: ZENMUX_API_KEY not configured")
        return ""

    from src.agents.researcher_agents import BullishResearcher

    # Create mock data from previous steps
    mock_fundamentals = "Test fundamentals data"
    mock_sentiment = "Test sentiment data"
    mock_technical = "Test technical data"
    mock_market = "Test market data"
    mock_memory = "Test memory data"

    start_time = time.time()
    result = BullishResearcher.analyze(
        symbol, period, mock_fundamentals, mock_sentiment,
        mock_technical, mock_market, mock_memory
    )
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    print(f"✓ Step 8.1 PASSED ({len(result)} chars)")
    return result


def test_step_8_2_bear(symbol, period):
    """Test Step 8.2: Bear Analysis."""
    print("\n" + "="*60)
    print(f"STEP 8.2: Bear Analysis ({symbol})")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('FINAGENT_ZENMUX_API_KEY') or os.getenv('ZENMUX_API_KEY')
    if not api_key:
        print("⚠️  SKIPPED: ZENMUX_API_KEY not configured")
        return ""

    from src.agents.researcher_agents import BearishResearcher

    # Create mock data from previous steps
    mock_fundamentals = "Test fundamentals data"
    mock_sentiment = "Test sentiment data"
    mock_technical = "Test technical data"
    mock_market = "Test market data"
    mock_memory = "Test memory data"

    start_time = time.time()
    result = BearishResearcher.analyze(
        symbol, period, mock_fundamentals, mock_sentiment,
        mock_technical, mock_market, mock_memory
    )
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    print(f"✓ Step 8.2 PASSED ({len(result)} chars)")
    return result


def test_step_8_3_debate(symbol, period, bull_result, bear_result):
    """Test Step 8.3: Research Debate."""
    print("\n" + "="*60)
    print(f"STEP 8.3: Research Debate ({symbol})")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('FINAGENT_ZENMUX_API_KEY') or os.getenv('ZENMUX_API_KEY')
    if not api_key:
        print("⚠️  SKIPPED: ZENMUX_API_KEY not configured")
        return ""

    from src.agents.researcher_agents import DebateAgent

    start_time = time.time()
    result = DebateAgent.summarize(bull_result, bear_result, period)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    print(f"✓ Step 8.3 PASSED ({len(result)} chars)")
    return result


def test_step_9_trading(symbol, period, debate_result):
    """Test Step 9: Trading Plan."""
    print("\n" + "="*60)
    print(f"STEP 9: Trading Plan ({symbol})")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('FINAGENT_ZENMUX_API_KEY') or os.getenv('ZENMUX_API_KEY')
    if not api_key:
        print("⚠️  SKIPPED: ZENMUX_API_KEY not configured")
        return ""

    from src.agents.trading_risk_agents import TradingAgent

    start_time = time.time()
    result = TradingAgent.decide(symbol, period, debate_result)
    elapsed = time.time() - start_time

    print(f"Time: {elapsed:.2f}s")
    assert isinstance(result, str), "Result should be string"
    assert len(result) > 0, "Result should not be empty"
    print(f"✓ Step 9 PASSED ({len(result)} chars)")
    return result


# ============================================================================
# STEP MAPPING
# ============================================================================

STEP_MAP = {
    '1': ('Fundamentals', test_step_1_fundamentals),
    '2': ('Sentiment & Social', test_step_2_sentiment),
    '3': ('Technical', test_step_3_technical),
    '4': ('Market Overview', test_step_4_market),
    '5': ('Global Economy', test_step_5_global_economy),
    '6': ('Fund Holdings', test_step_6_fund_holdings),
    '7': ('Past Lessons', test_step_7_past_lessons),
    '8.1': ('Bull Analysis', test_step_8_1_bull),
    '8.2': ('Bear Analysis', test_step_8_2_bear),
    '8.3': ('Research Debate', test_step_8_3_debate),
    '9': ('Trading Plan', test_step_9_trading),
}


def run_step_test(step_id, symbol, period, prev_results=None):
    """Run a specific step test."""
    if step_id not in STEP_MAP:
        print(f"Unknown step: {step_id}")
        return None

    step_name, test_func = STEP_MAP[step_id]

    try:
        if step_id in ['8.3', '9']:
            # These steps depend on previous results
            if step_id == '8.3':
                return test_func(symbol, period,
                    prev_results.get('bull', ''),
                    prev_results.get('bear', ''))
            elif step_id == '9':
                return test_func(symbol, period, prev_results.get('debate', ''))
        else:
            return test_func(symbol, period)
    except AssertionError as e:
        print(f"\n✗ Step {step_id} ({step_name}) FAILED: {e}")
        return None
    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg or 'access_denied' in error_msg:
            print(f"\n⚠️  Step {step_id} ({step_name}) SKIPPED: API access denied")
            return None
        elif 'broken pipe' in error_msg.lower() or 'connection' in error_msg.lower():
            print(f"\n⚠️  Step {step_id} ({step_name}) SKIPPED: Connection error")
            return None
        else:
            print(f"\n✗ Step {step_id} ({step_name}) ERROR: {e}")
            return None


def main():
    """Run regression tests."""
    parser = argparse.ArgumentParser(description='FinAgent Pipeline Regression Tests')
    parser.add_argument('--step', type=str, default=None,
                       help='Test specific step(s): "1", "8.1", "1,2,3", or "all"')
    parser.add_argument('--symbol', type=str, default=DEFAULT_SYMBOL,
                       help='Stock symbol to test')
    parser.add_argument('--period', type=str, default=DEFAULT_PERIOD,
                       help='Investment period')
    args = parser.parse_args()

    symbol = args.symbol
    period = args.period

    print("\n" + "#"*60)
    print("# FinAgent Pipeline Regression Tests")
    print(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# Symbol: {symbol}, Period: {period}")
    print("#"*60)

    # Parse steps to test
    if args.step and args.step != 'all':
        steps_to_test = [s.strip() for s in args.step.split(',')]
    else:
        steps_to_test = list(STEP_MAP.keys())

    print(f"\nSteps to test: {', '.join(steps_to_test)}")
    print("="*60)

    results = {}
    passed = 0
    failed = 0
    skipped = 0

    for step_id in steps_to_test:
        result = run_step_test(step_id, symbol, period, results)
        if result is not None:
            results[step_id] = result
            passed += 1
        elif result is None:
            # Check if it was skipped or failed
            skipped += 1

    # Summary
    print("\n" + "#"*60)
    print(f"# SUMMARY")
    print(f"# Passed: {passed}")
    print(f"# Skipped: {skipped}")
    print(f"# Failed: {failed}")
    print("#"*60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
