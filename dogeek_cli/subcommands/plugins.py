'''Manages CLI plugins.'''
import errno
from http import HTTPStatus
from pathlib import Path
import textwrap
from typing import Optional

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from mako.lookup import TemplateLookup
from mako.template import Template
from rich.console import Console
from rich.table import Table
import typer

from dogeek_cli.client import Client
from dogeek_cli.config import (
    config, plugins_path, plugins_registry, RESERVED_COMMANDS, logs_path,
    root_path,
)
from dogeek_cli.logging import Logger
from dogeek_cli.utils import open_editor, open_pager
from dogeek_cli.subcommands.registry import app as registry_app
from dogeek_cli.plugin import Plugin

app = typer.Typer()
app.add_typer(registry_app, name='registry')
console = Console()
logger = Logger('cli.plugins')


@app.callback()
def callback():
    if len(list(config.app_path.glob('key*'))) > 0:
        # Public / Private key pairs are already generated
        return

    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )

    with open(config.app_path / 'key.pub', 'wb') as filehandler:
        filehandler.write(public_key)
    with open(config.app_path / 'key', 'wb') as filehandler:
        filehandler.write(private_key)
    return


@app.command()
def update() -> int:
    '''Updates the plugins cache with new plugins in the plugins directory.'''
    for module_path in plugins_path.iterdir():
        if module_path.is_dir() or module_path.name.endswith('.py'):
            if module_path.name in RESERVED_COMMANDS:
                # Do not import plugins named with the same
                # name as reserved CLI commands
                continue
            if module_path.name == '__pycache__':
                continue
            if module_path.name.startswith('.'):
                continue
            plugin = Plugin(module_path.name)
            plugin.cache_plugin_metadata(module_path, None)
    return 0


@app.command()
def edit(plugin_name: str):
    '''Edits a plugin in your favorite text editor'''
    plugin = Plugin(plugin_name)
    if not plugin.exists:
        path = plugins_path / plugin_name
        path.mkdir(exist_ok=True, parents=True)
        lookup = TemplateLookup([str(root_path / 'templates')])
        for filepath in (root_path / 'templates/plugin').glob('*'):
            parts = (
                filepath.parts[
                    len(filepath.parts) - filepath.parts[::-1].index('templates'):
                ]
            )
            uri = '/'.join(parts)
            template: Template = lookup.get_template(uri)
            out_uri = '/'.join(parts[1:]).rsplit('.', 1)[0]
            (path / out_uri).write_text(
                template.render()
            )
        logger.info('Creating plugin %s from templates.', plugin_name)
        open_editor(path)
        return 0

    path = (
        plugins_path / plugin_name
        if plugin.is_dir
        else plugins_path / f'{plugin_name}.py'
    )
    logger.info('Editing plugin %s', plugin_name)
    open_editor(path)
    return 0


@app.command()
def logs(plugin_name: str) -> int:
    '''Pages on the latest log for provided plugin name.'''
    if plugin_name not in plugins_registry:
        raise typer.Exit(errno.ENODATA)
    plugin = Plugin(plugin_name)
    path: Path = logs_path / plugin.logger
    filepath: Path = None
    try:
        filepath = next(sorted(path.iterdir(), reverse=True))
    except StopIteration:
        raise typer.Exit(errno.ENOENT)
    open_pager(filepath)
    return 0


@app.command()
def enable(plugin_name: str) -> int:
    '''Enables the specified plugin.'''
    Plugin(plugin_name).enabled = True
    return 0


@app.command()
def disable(plugin_name: str) -> int:
    '''Disables the specified plugin.'''
    Plugin(plugin_name).enabled = False
    return 0


@app.command()
def ls():
    '''Lists available plugins.'''
    table = Table('plugin_name', 'enabled', 'description', 'upgrade_avail')
    for plugin_name in plugins_registry:
        plugin = Plugin(plugin_name)
        enabled = '✅' if plugin.enabled else '❌'
        table.add_row(
            textwrap.shorten(plugin_name, 10),
            enabled,
            plugin.short_help,
            plugin.upgrade_available,
        )
    console.print(table)
    return 0


@app.command()
def install(
    plugin_name: str,
    version: str = typer.Option('latest', '--version', '-v'),
) -> int:
    '''Installs a plugin from the CLI plugin registry.'''
    logger.info('Installing plugin %s v%s', plugin_name, version)
    plugin = Plugin(plugin_name)
    registries = config['app.registries'] or []
    registries.append('cli.dogeek.me')
    for registry in registries:
        client = Client(registry)
        response = client.get(
            f'/v1/plugins/{plugin_name}/versions/{version}'
        )
        if response.status_code == HTTPStatus.OK:
            break
    else:
        logger.error(
            'No plugin %s v%s found in registries %s : %s',
            plugin_name, version, registries, response.json()['message']
        )
        raise typer.Exit()
    plugin.install(response.json()['data']['file'], registry)
    print(f'Plugin {plugin_name} v{version} has been installed.')
    return 0


@app.command()
def uninstall(plugin_name: str):
    '''Uninstalls a plugin completely.'''
    if plugin_name not in plugins_registry:
        raise typer.Exit(errno.ENODATA)
    plugin = Plugin(plugin_name)
    plugin.uninstall()
    return 0


@app.command()
def upgrade(
    plugin_name: Optional[str] = typer.Option(None, '--plugin', '-p'),
    version: str = typer.Option('latest', '--version')
) -> int:
    '''Upgrades one or all plugins to the desired version.'''
    if plugin_name is None:
        # Upgrade all the plugins to the latest version
        if version != 'latest':
            print('Cannot upgrade all plugins with a specific version.')
            raise typer.Exit(1)
        for plugin_name in plugins_registry:
            plugin = Plugin(plugin_name)
            plugin.upgrade('latest')
        return 0

    if plugin_name not in plugins_registry:
        raise typer.Exit(errno.ENODATA)

    plugin = Plugin(plugin_name)
    return_code = plugin.upgrade(version)
    if return_code == 0:
        return 0
    raise typer.Exit(return_code)
