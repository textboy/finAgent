#!/usr/bin/env python3

import os
import sys
import click
from datetime import datetime
from dotenv import load_dotenv
from finagent import main as core_main

load_dotenv(os.path.join('config', '.env'))

# Get terminal width safely (handle non-terminal environments)
try:
    terminal_width = os.get_terminal_size().columns
except OSError:
    terminal_width = 80  # Default width

INFO_SIZE = 1200

@click.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol(s), comma-separated (e.g. AAPL or AAPL,GOOG,MSFT)')
@click.option('--period', '-p', type=click.Choice(['short+', 'short', 'medium', 'long']), default='medium', help='Investment period')
def cli(symbol: str, period: str):
    # Parse symbols (split by comma, semicolon, or space)
    symbols = [s.strip().upper() for s in symbol.replace(';', ',').split(',') if s.strip()]

    if len(symbols) > 5:
        click.secho("Warning: Maximum 5 symbols allowed. Only first 5 will be analyzed.", fg='yellow')
        symbols = symbols[:5]

    symbol_list = ', '.join(symbols)
    click.secho(f"Analyzing {symbol_list} for {period} term investment...", fg='cyan')
    click.echo()

    title = f"{'#' * 40}      FinAgent      {'#' * 40}"
    header_line = '=' * 10
    header_color = 'yellow'

    for i, sym in enumerate(symbols):
        if len(symbols) > 1:
            click.secho(f"\n{'='*60}", fg='green')
            click.secho(f"  [{i+1}/{len(symbols)}] Analyzing {sym}", fg='green', bold=True)
            click.secho(f"{'='*60}\n", fg='green')

        try:
            state, result_file = core_main(sym, period)

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
            click.echo()
            print(f"Full report saved to {result_file}")

        except Exception as e:
            click.secho(f"Error analyzing {sym}: {str(e)}", fg='red')

        if i < len(symbols) - 1:
            click.echo()
            click.echo()

    click.echo()
    click.secho(f"Analysis complete for {len(symbols)} symbol(s). Check results directory.", fg='green')

if __name__ == '__main__':
    cli()
