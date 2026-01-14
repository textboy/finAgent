#!/usr/bin/env python3
"""FinAgent CLI - Financial Analysis Agent"""
import os
import click
from datetime import datetime
from dotenv import load_dotenv
from src.workflow import run_workflow
from src.utils.qdrant_utils import store_entry

load_dotenv(os.path.join('config', '.env'))
terminal_width = os.get_terminal_size().columns
NORMAL_INFO_SIZE = 800
MAJOR_INFO_SIZE = 1600

@click.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol (e.g. AAPL)')
@click.option('--period', '-p', type=click.Choice(['short+', 'short', 'medium', 'long']), default='medium', help='Investment period')
def cli(symbol: str, period: str):
    """Run FinAgent analysis for a stock."""
    print(f"Analyzing {symbol} for {period} term investment...")

    title = f"{'#' * 40}      FinAgent      {'#' * 40}"
    header_line = '=' * 10
    header_color = 'yellow'
    state = run_workflow(symbol, period)
    
    # Create results dir
    os.makedirs('results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    result_file = f'results/result_{timestamp}.log'

    # Print title
    click.secho(title.center(terminal_width), fg=header_color)
    # Print summaries
    click.echo()
    click.secho(f"{header_line} Analyst Insights {header_line}", fg=header_color, bold=True)
    for key, value in state['analyst_insights'].items():
        print(f"{key.title()}: {value[:NORMAL_INFO_SIZE]}...")
    
    click.echo()
    click.secho(f"{header_line} Researcher Debate {header_line}", fg=header_color, bold=True)
    print(f"Bull: {state['researcher_results']['bull'][:NORMAL_INFO_SIZE]}...")
    print(f"Bear: {state['researcher_results']['bear'][:NORMAL_INFO_SIZE]}...")
    print(f"Debate: {state['researcher_results']['debate'][:MAJOR_INFO_SIZE]}...")
    
    click.echo()
    click.secho(f"{header_line} Trading Plan {header_line}", fg=header_color, bold=True)
    print(state['trader_plan'][:MAJOR_INFO_SIZE] + '...')

    click.echo()
    click.secho(f"{header_line} Risk Management {header_line}", fg=header_color, bold=True)
    print(state['risk_plan'][:MAJOR_INFO_SIZE] + '...')
    
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
    
    # Store to Qdrant
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
    
    click.echo()
    click.echo()
    print(f"Full report saved to {result_file}")
    print("Analysis complete. Check results directory.")

if __name__ == '__main__':
    cli()