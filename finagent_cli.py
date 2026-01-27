#!/usr/bin/env python3

import os
import click
from datetime import datetime
from dotenv import load_dotenv
from finagent import main as core_main

load_dotenv(os.path.join('config', '.env'))
terminal_width = os.get_terminal_size().columns
INFO_SIZE = 1200

@click.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol (e.g. AAPL)')
@click.option('--period', '-p', type=click.Choice(['short+', 'short', 'medium', 'long']), default='medium', help='Investment period')
def cli(symbol: str, period: str):
    print(f"Analyzing {symbol} for {period} term investment...")
    title = f"{'#' * 40}      FinAgent      {'#' * 40}"
    header_line = '=' * 10
    header_color = 'yellow'
    state, result_file = core_main(symbol, period)
    
    # Print title
    click.secho(title.center(terminal_width), fg=header_color)
    # Print summaries
    click.echo()
    click.secho(f"{header_line} Analyst Insights {header_line}", fg=header_color, bold=True)
    for key, value in state['analyst_insights'].items():
        print(f"{key.title()}: {value[:INFO_SIZE]}")
        print('...') if len(value) > INFO_SIZE else None
    
    click.echo()
    click.secho(f"{header_line} Researcher Debate {header_line}", fg=header_color, bold=True)
    for key, value in state['researcher_results'].items():
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
    
    click.echo()
    click.echo()
    print(f"Full report saved to {result_file}")
    print("Analysis complete. Check results directory.")

if __name__ == '__main__':
    cli()