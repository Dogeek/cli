'''
Convenient way to pass environments to CLI parameters.
'''

import errno
import json
from typing import Optional

from rich import print
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
import typer

from dogeek_cli.config import config, env
from dogeek_cli.state import state


app = typer.Typer(help=__doc__)
console = Console()


@app.command()
def add(name: str, environment: str) -> int:
    '''Add a new environment to the CLI.'''
    environ = json.loads(environment)
    if name in env:
        environ = env[name].update(environ)
    env[name] = environ
    return 0


@app.command()
def mv(original_name: str, new_name: str) -> int:
    '''Rename an existing environment.'''
    if original_name not in env:
        raise typer.Exit(errno.ENODATA)
    environ = env[original_name].copy()
    del env[original_name]
    env[new_name] = environ
    return 0


@app.command()
def ls(
    filter: Optional[str] = typer.Option(
        None, '-f', '--filter', help='Filter environments by name.'
    )
) -> int:
    '''Lists available environments.'''
    the_env = {
        k: v
        for k, v in sorted(env.items(), key=lambda x: x[0])
        if filter is None or filter in k
    }
    columns = set([v.keys() for v in the_env.values()])
    table = Table('name', *columns)
    for name, environ in the_env.items():
        table.add_row(name, *[str(e) for e in environ.values()])
    console.print(table)
    return 0


@app.command()
def rm(name: str) -> int:
    '''Removes an environment if it exists.'''
    if name in env:
        del env[name]
        return 0
    return errno.ENODATA


@app.command()
def get(name: str) -> int:
    '''Gets a configured environment from the config.'''
    if state['json']:
        console.print(
            Syntax(
                json.dumps(env[name], indent=2),
                'json',
                theme=config['app.theme']
            )
        )
        return 0
    print(f'[b blue]{name}: [/]')
    for key, value in env[name].items():
        print(f'🔷 {key}: {value}')
    return 0
