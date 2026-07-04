#!/usr/bin/env python3
"""
Regression test for FinAgent base functionality.
Tests the complete workflow with sample input: AAPL, medium period.
"""

import sys
import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Load .env before importing src modules
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.workflow import run_workflow, create_workflow
from src.agents.analyst_agents import analyst_team
from src.agents.researcher_agents import researcher_team
from src.agents.trading_risk_agents import TradingAgent

# Test configuration
TEST_SYMBOL = 'AAPL'
TEST_PERIOD = 'medium'

def test_analyst_team():
    """Test analyst team returns raw API data without LLM calls."""
    print("\n" + "="*60)
    print("TEST 1: Analyst Team (API Data Collection)")
    print("="*60)

    start_time = time.time()
    result = analyst_team(TEST_SYMBOL, TEST_PERIOD)
    elapsed = time.time() - start_time

    print(f"Symbol: {TEST_SYMBOL}")
    print(f"Period: {TEST_PERIOD}")
    print(f"Time: {elapsed:.2f}s")
    print(f"\nKeys returned: {list(result.keys())}")

    # Verify all required keys exist
    required_keys = ['fundamentals', 'sentiment', 'technical']
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
        assert isinstance(result[key], str), f"Key {key} should be string"
        assert len(result[key]) > 0, f"Key {key} should not be empty"
        print(f"  ✓ {key}: {len(result[key])} chars")

    print("\n✓ Analyst Team Test PASSED")
    return result

def test_researcher_team(analyst_insights):
    """Test researcher team processes analyst data."""
    print("\n" + "="*60)
    print("TEST 2: Researcher Team (LLM Processing)")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('LLM_API_KEY', '')
    if not api_key or api_key == 'your_openrouter_api_key_here':
        print("⚠️  SKIPPED: LLM_API_KEY not configured in .env")
        print("   Set LLM_API_KEY in config/.env to enable LLM tests")
        return {'bull': '', 'bear': '', 'debate': ''}

    try:
        start_time = time.time()
        result = researcher_team(analyst_insights, TEST_SYMBOL, "")
        elapsed = time.time() - start_time
    except Exception as e:
        error_msg = str(e)
        if 'html' in error_msg.lower() or '<!' in error_msg:
            print("⚠️  SKIPPED: LLM API returned HTML (authentication/endpoint issue)")
            print("   Check LLM_API_KEY and LLM_BASE_URL in config/.env")
            return {'bull': '', 'bear': '', 'debate': ''}
        raise

    print(f"Time: {elapsed:.2f}s")
    print(f"\nKeys returned: {list(result.keys())}")

    # Verify all required keys exist
    required_keys = ['bull', 'bear', 'debate']
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
        assert isinstance(result[key], str), f"Key {key} should be string"
        assert len(result[key]) > 0, f"Key {key} should not be empty"
        print(f"  ✓ {key}: {len(result[key])} chars")

    print("\n✓ Researcher Team Test PASSED")
    return result

def test_trading_agent(researcher_results):
    """Test trading agent generates trade plan."""
    print("\n" + "="*60)
    print("TEST 3: Trading Agent (LLM Processing)")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('LLM_API_KEY', '')
    if not api_key or api_key == 'your_openrouter_api_key_here':
        print("⚠️  SKIPPED: LLM_API_KEY not configured in .env")
        print("   Set LLM_API_KEY in config/.env to enable LLM tests")
        return ''

    try:
        start_time = time.time()
        plan = TradingAgent.decide(TEST_SYMBOL, TEST_PERIOD, researcher_results['debate'], "")
        elapsed = time.time() - start_time
    except Exception as e:
        error_msg = str(e)
        if 'html' in error_msg.lower() or '<!' in error_msg:
            print("⚠️  SKIPPED: LLM API returned HTML (authentication/endpoint issue)")
            print("   Check LLM_API_KEY and LLM_BASE_URL in config/.env")
            return ''
        raise

    print(f"Time: {elapsed:.2f}s")
    print(f"\nPlan length: {len(plan)} chars")
    assert isinstance(plan, str), "Plan should be string"
    assert len(plan) > 0, "Plan should not be empty"
    print(f"\nPlan preview:\n{plan[:500]}...")

    print("\n✓ Trading Agent Test PASSED")
    return plan

def test_workflow_skip_risk():
    """Test complete workflow with risk management skipped."""
    print("\n" + "="*60)
    print("TEST 4: Complete Workflow (Risk Skipped)")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('LLM_API_KEY', '')
    if not api_key or api_key == 'your_openrouter_api_key_here':
        print("⚠️  SKIPPED: LLM_API_KEY not configured in .env")
        print("   Set LLM_API_KEY in config/.env to enable workflow tests")
        return None

    try:
        start_time = time.time()
        final_state = run_workflow(TEST_SYMBOL, TEST_PERIOD)
        elapsed = time.time() - start_time
    except Exception as e:
        error_msg = str(e)
        if 'html' in error_msg.lower() or '<!' in error_msg:
            print("⚠️  SKIPPED: LLM API returned HTML (authentication/endpoint issue)")
            print("   Check LLM_API_KEY and LLM_BASE_URL in config/.env")
            return None
        raise

    print(f"Time: {elapsed:.2f}s")
    print(f"\nFinal state keys: {list(final_state.keys())}")

    # Verify required fields
    assert final_state['symbol'] == TEST_SYMBOL
    assert final_state['investment_period'] == TEST_PERIOD
    assert len(final_state['analyst_insights']) > 0, "Analyst insights should not be empty"
    assert len(final_state['researcher_results']) > 0, "Researcher results should not be empty"
    assert len(final_state['trader_plan']) > 0, "Trader plan should not be empty"
    assert final_state['risk_plan'] == '', "Risk plan should be empty when skipped"

    print(f"  ✓ symbol: {final_state['symbol']}")
    print(f"  ✓ period: {final_state['investment_period']}")
    print(f"  ✓ analyst_insights: {len(final_state['analyst_insights'])} keys")
    print(f"  ✓ researcher_results: {len(final_state['researcher_results'])} keys")
    print(f"  ✓ trader_plan: {len(final_state['trader_plan'])} chars")
    print(f"  ✓ risk_plan: {len(final_state['risk_plan'])} chars (skipped)")

    print("\n✓ Complete Workflow Test PASSED")
    return final_state

def test_workflow_enable_risk():
    """Test complete workflow with risk management enabled."""
    print("\n" + "="*60)
    print("TEST 5: Complete Workflow (Risk Enabled)")
    print("="*60)

    # Check if API key is configured
    api_key = os.getenv('LLM_API_KEY', '')
    if not api_key or api_key == 'your_openrouter_api_key_here':
        print("⚠️  SKIPPED: LLM_API_KEY not configured in .env")
        print("   Set LLM_API_KEY in config/.env to enable workflow tests")
        return None

    # Temporarily enable risk
    os.environ['SKIP_RISK_MANAGEMENT'] = 'false'

    try:
        start_time = time.time()
        final_state = run_workflow(TEST_SYMBOL, TEST_PERIOD)
        elapsed = time.time() - start_time
    except Exception as e:
        os.environ['SKIP_RISK_MANAGEMENT'] = 'true'  # Reset
        error_msg = str(e)
        if 'html' in error_msg.lower() or '<!' in error_msg:
            print("⚠️  SKIPPED: LLM API returned HTML (authentication/endpoint issue)")
            print("   Check LLM_API_KEY and LLM_BASE_URL in config/.env")
            return None
        raise

    # Reset to default
    os.environ['SKIP_RISK_MANAGEMENT'] = 'true'

    print(f"Time: {elapsed:.2f}s")
    print(f"\nFinal state keys: {list(final_state.keys())}")

    # Verify required fields
    assert final_state['symbol'] == TEST_SYMBOL
    assert final_state['investment_period'] == TEST_PERIOD
    assert len(final_state['analyst_insights']) > 0
    assert len(final_state['researcher_results']) > 0
    assert len(final_state['trader_plan']) > 0
    assert len(final_state['risk_plan']) > 0, "Risk plan should not be empty when enabled"

    print(f"  ✓ symbol: {final_state['symbol']}")
    print(f"  ✓ period: {final_state['investment_period']}")
    print(f"  ✓ analyst_insights: {len(final_state['analyst_insights'])} keys")
    print(f"  ✓ researcher_results: {len(final_state['researcher_results'])} keys")
    print(f"  ✓ trader_plan: {len(final_state['trader_plan'])} chars")
    print(f"  ✓ risk_plan: {len(final_state['risk_plan'])} chars (enabled)")

    print("\n✓ Complete Workflow (Risk Enabled) Test PASSED")
    return final_state

def main():
    """Run all regression tests."""
    print("\n" + "#"*60)
    print("# FinAgent Regression Test Suite")
    print(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# Test Input: {TEST_SYMBOL}, {TEST_PERIOD}")
    print("#"*60)

    tests_passed = 0
    tests_skipped = 0
    tests_failed = 0

    try:
        # Test 1: Analyst Team
        analyst_insights = test_analyst_team()
        tests_passed += 1

        # Test 2: Researcher Team
        researcher_results = test_researcher_team(analyst_insights)
        if researcher_results and researcher_results.get('bull'):
            tests_passed += 1
        else:
            tests_skipped += 1

        # Test 3: Trading Agent
        trader_plan = test_trading_agent(researcher_results)
        if trader_plan:
            tests_passed += 1
        else:
            tests_skipped += 1

        # Test 4: Complete Workflow (Risk Skipped)
        result4 = test_workflow_skip_risk()
        if result4:
            tests_passed += 1
        else:
            tests_skipped += 1

        # Test 5: Complete Workflow (Risk Enabled)
        result5 = test_workflow_enable_risk()
        if result5:
            tests_passed += 1
        else:
            tests_skipped += 1

        print("\n" + "#"*60)
        print(f"# SUMMARY: {tests_passed} passed, {tests_skipped} skipped, {tests_failed} failed")
        if tests_skipped > 0:
            print("# Note: LLM tests skipped - configure LLM_API_KEY in .env")
        print("#"*60)

    except AssertionError as e:
        tests_failed += 1
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
