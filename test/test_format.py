import os
import click

title = "FinAgent"
format_line = '=' * 10
colors = [
        'black', 'red', 'green', 'yellow', 'blue',
        'magenta', 'cyan', 'white', 'bright_black', 'bright_red',
        'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta',
        'bright_cyan', 'bright_white', 'reset'
    ]

terminal_width = os.get_terminal_size().columns
click.secho(title.center(terminal_width), fg='yellow')

click.echo()
for color in colors:
    click.secho(f"{format_line} Researcher Debate {format_line}", fg=color, bold=True)