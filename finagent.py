#!/usr/bin/env python3
"""FinAgent CLI - Financial Analysis Agent"""
import os
import click
from datetime import datetime
from dotenv import load_dotenv
from src.workflow import run_workflow
from src.utils.qdrant_utils import store_entry

load_dotenv()

@click.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol (e.g. AAPL)')
@click.option('--period', '-p', type=click.Choice(['short', 'medium', 'long']), default='medium', help='Investment period')
def cli(symbol: str, period: str):
    """Run FinAgent analysis for a stock."""
    print(f"Analyzing {symbol} for {period} term investment...")
    
    state = run_workflow(symbol, period)
    
    # Create results dir
    os.makedirs('results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    result_file = f'results/result_{timestamp}.log'
    
    # Print summaries (limit ~500 words)
    print("\\n=== Analyst Insights ===")
    for key, value in state['analyst_insights'].items():
        print(f"{key.title()}: {value[:500]}...")
    
    print("\\n=== Researcher Debate ===")
    print(f"Bull: {state['researcher_results']['bull'][:300]}...")
    print(f"Bear: {state['researcher_results']['bear'][:300]}...")
    print(f"Debate: {state['researcher_results']['debate'][:500]}...")
    
    print("\\n=== Trading Plan ===")
    print(state['trader_plan'][:800] + '...')
    
    print("\\n=== Risk Management ===")
    print(state['risk_plan'][:800] + '...')
    
    # Save full report to file
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(f"# FinAgent Analysis Report\\n")
        f.write(f"Symbol: {symbol}\\n")
        f.write(f"Period: {period}\\n")
        f.write(f"Timestamp: {state['timestamp']}\\n\\n")
        
        f.write("## Analyst Team\\n")
        for key, value in state['analyst_insights'].items():
            f.write(f"### {key.title()}\\n{value}\\n\\n")
        
        f.write("## Researcher Team\\n")
        for key, value in state['researcher_results'].items():
            f.write(f"### {key.title()}\\n{value}\\n\\n")
        
        f.write("## Trading Team\\n")
        f.write(f"{state['trader_plan']}\\n\\n")
        
        f.write("## Risk Management Team\\n")
        f.write(f"{state['risk_plan']}")
    
    # Store to Milvus
    final_content = state['risk_plan']
    store_entry(
        symbol, 
        'report', 
        final_content, 
        state['timestamp'], 
        {
            'period': period,
            'analyst_insights': state['analyst_insights'],
            'researcher_results': state['researcher_results'],
            'trader_plan': state['trader_plan']
        }
    )
    
    print(f"\\nFull report saved to {result_file}")
    print("Analysis complete. Check results directory.")

if __name__ == '__main__':
    cli()