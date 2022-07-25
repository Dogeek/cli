'''
Convenient way to set application-wide configuration values.
'''

import errno

from rich.console import Console
from rich.table import Table
import typer

from dogeek_cli.config import config, DefaultConfig


app = typer.Typer()
console = Console()


@app.command('ls')
def ls() -> int:
    '''Lists configuration keys and values'''
    table = Table()
    table.add_column('KEY')
    table.add_column('VALUE')
    for key, value in config.flat().items():
        table.add_row(str(key), str(value))
    console.print(table)
    return 0


@app.command()
def get(key: str) -> int:
    '''Gets the value for a given key from the config.'''
    if key in config:
        print(f'{key} : {config[key]}')
        return 0
    print(f'Key {key} not found in config.')
    return errno.ENODATA


@app.command()
def set(key: str, value: str) -> int:
    '''Sets the value for a config key.'''
    config[key] = value
    return 0


@app.command()
def reset() -> int:
    '''Resets the configuration file to its default state.'''
    for key, value in DefaultConfig._DEFAULTS.items():
        config[key] = value
