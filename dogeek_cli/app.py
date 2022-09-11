'''
CLI application supporting plugins to centralize
scripts and other odds and ends.
'''
import logging

import typer

from dogeek_cli import __version__
from dogeek_cli.config import config, plugins_registry
from dogeek_cli.enums import OutputFormat
from dogeek_cli.logging import Logger
from dogeek_cli.state import State
from dogeek_cli.subcommands import env
from dogeek_cli.subcommands import config as cfg
from dogeek_cli.subcommands import plugins
from dogeek_cli.subcommands import system
from dogeek_cli.utils import clean_help_string, check_version
from dogeek_cli.plugin import Plugin

logging.setLoggerClass(Logger)
logger = Logger('cli')


def add_plugins_hook(app: typer.Typer):
    for module_name, cached_module in plugins_registry.items():
        # Cached module is in the form {"path": "...", "metadata": {...}}
        plugin = Plugin(module_name)
        plugin.make_meta()
        if not plugin.enabled:
            logger.info('Plugin %s is not enabled', module_name)
            continue
        logger.info(
            'Loading plugin %s into context with data %s',
            module_name, cached_module
        )
        plugin_app = getattr(plugin.module, 'app', None)
        if plugin_app is None:
            for variable_name in dir(plugin.module):
                variable = getattr(plugin.module, variable_name)
                if isinstance(variable, typer.Typer):
                    plugin_app = variable
                    break
            else:
                logger.error('Plugin %s does not export a typer.Typer instance.', module_name)
                continue
        app.add_typer(plugin_app, **cached_module['metadata'])
    return app


app = typer.Typer(help=__doc__)
app = add_plugins_hook(app)


@app.callback()
def callback(
    format: OutputFormat = typer.Option(
        OutputFormat.DEFAULT, '--format', '-f',
        help='Format the output into the given format.'
    ),
    verbosity: int = typer.Option(
        config['app.default_verbosity'], "--verbose", "-v", count=True, min=0,
        max=5, help='Set the verbosity level of the command.',
    ),
) -> None:
    state = State()
    state.format = format
    state.verbosity = verbosity
    if config['app.notify_new_version']:
        check_version(__version__)
    return


app.add_typer(env.app, name='env', help=clean_help_string(env.__doc__))
app.add_typer(cfg.app, name='config', help=clean_help_string(cfg.__doc__))
app.add_typer(plugins.app, name='plugins', help=clean_help_string(plugins.__doc__))
app.add_typer(system.app, name='system', help=clean_help_string(system.__doc__))
typer_click_object = typer.main.get_command(app)


def main():
    typer_click_object()


if __name__ == '__main__':
    main()
