'''
CLI application supporting plugins to centralize
scripts and other odds and ends.
'''
import logging

import typer

from cli.config import plugins_registry, state  # noqa
from cli.logging import Logger
from cli.subcommands import env
from cli.subcommands import config as cfg
from cli.subcommands import plugins
from cli.utils import clean_help_string, do_import


logging.setLoggerClass(Logger)
logger = Logger('cli')


def add_plugins_hook(app: typer.Typer):
    for module_name, cached_module in plugins_registry.items():
        # Cached module is in the form {"path": "...", "metadata": {...}}
        logger.info(
            'Loading plugin %s into context with data %s',
            module_name, cached_module
        )
        module = do_import(module_name, cached_module['path'])
        app.add_typer(module.app, **cached_module['metadata'])
    return app


app = typer.Typer(help=__doc__)
app = add_plugins_hook(app)


@app.callback()
def callback(
    json: bool = typer.Option(False, '--json', help='Format the output as JSON.'),
    toml: bool = typer.Option(False, '--toml', help='Format the output as TOML.'),
    csv: bool = typer.Option(False, '--csv', help='Format the output as CSV.'),
    yaml: bool = typer.Option(False, '--yaml', '--yml', help='Format the output as YAML.')
) -> None:
    global state
    state['json'] = json
    state['toml'] = toml
    state['csv'] = csv
    state['yaml'] = yaml
    return


app.add_typer(env.app, name='env', help=clean_help_string(env.__doc__))
app.add_typer(cfg.app, name='config', help=clean_help_string(cfg.__doc__))
app.add_typer(plugins.app, name='plugins', help=clean_help_string(plugins.__doc__))

typer_click_object = typer.main.get_command(app)


def main():
    typer_click_object()


if __name__ == '__main__':
    main()
