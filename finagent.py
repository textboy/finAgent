#!/usr/bin/env python3
"""FinAgent CLI - Financial Analysis Agent"""
import os
import click
from datetime import datetime
from dotenv import load_dotenv
from src.workflow import run_workflow
from src.utils.qdrant_utils import store_entry
from googletrans import Translator

load_dotenv(os.path.join('config', '.env'))
terminal_width = os.get_terminal_size().columns
INFO_SIZE = 1200

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
    timestampInReport = datetime.now().strftime('%Y-%m-%d %H:%M')
    result_file = f'results/result_{timestamp}.md'

    # Print title
    click.secho(title.center(terminal_width), fg=header_color)
    # Print summaries
    click.echo()
    click.secho(f"{header_line} Analyst Insights {header_line}", fg=header_color, bold=True)
    for key, value in state['analyst_insights'].items():
        print(f"DEBUG: {value}")
        print(f"{key.title()}: {value[:INFO_SIZE]}")
        print('...') if len(value) > INFO_SIZE else None
    
    click.echo()
    click.secho(f"{header_line} Researcher Debate {header_line}", fg=header_color, bold=True)
    for key, value in state['researcher_results'].items():
        # value: bull, bear, debate
        print(f"{key.title()}: {value[:INFO_SIZE]}")
        print('...') if len(value) > INFO_SIZE else None
        print()

    click.echo()
    click.secho(f"{header_line} Trading Plan {header_line}", fg=header_color, bold=True)
    print(state['trader_plan'][:INFO_SIZE])
    print('...') if len(state['trader_plan']) > INFO_SIZE else None
    print()

    click.echo()
    click.secho(f"{header_line} Risk Management {header_line}", fg=header_color, bold=True)
    print(state['risk_plan'][:INFO_SIZE])
    print('...') if len(state['risk_plan']) > INFO_SIZE else None
    print()

    # Save full report to file
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(f"# <span style='color: #cfa923;'>FinAgent Analysis Report</span> \n")
        f.write(f"Symbol: {symbol}, ")
        f.write(f"Period: {period}, ")
        f.write(f"Timestamp: {timestampInReport}\n\n")

        f.write("## <span style='color: #cfa923;'>1. Analyst Insights</span> \n")
        for key, value in state['analyst_insights'].items():
            f.write(f"### <span style='color: #326ba8;'>{key.title()}</span>\n")
            f.write(f"<hr style='height: 1px; background-color: #ccc; opacity: 0.5;' />\n")
            f.write(f"{value}\n\n")

        f.write("## <span style='color: #cfa923;'>2. Researcher Debate</span>\n")
        for key, value in state['researcher_results'].items():
            f.write(f"### <span style='color: #326ba8;'>{key.title()}</span>\n")
            f.write(f"<hr style='height: 1px; background-color: #ccc; opacity: 0.5;' />\n")
            f.write(f"{value}\n\n")

        f.write("## <span style='color: #cfa923;'>3. Trading Plan</span>\n")
        f.write(f"{state['trader_plan']}\n\n")

        f.write("## <span style='color: #cfa923;'>4. Risk Management</span>\n")
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
            'trader_plan': state['trader_plan'],
            'risk_plan': state['risk_plan']
        }
    )
    
    click.echo()
    click.echo()
    print(f"Full report saved to {result_file}")
    print("Analysis complete. Check results directory.")

if __name__ == '__main__':
    cli()