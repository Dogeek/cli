'''Manages CLI plugins.'''
from base64 import b85decode
import errno
from http import HTTPStatus
import io
import os
from pathlib import Path
import subprocess
import tarfile
import gzip
import textwrap
from typing import Optional

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from rich.console import Console
from rich.table import Table
import typer

from cli.client import Client
from cli.config import (
    config, plugins_path, plugins_registry, RESERVED_COMMANDS, logs_path,
)
from cli.logging import Logger
from cli.utils import clean_help_string, do_import, is_plugin_enabled, make_tarball


app = typer.Typer()
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
            plugin_name = module_path.name.split('.')[0]
            module_name = f'plugins.{plugin_name}'
            module = do_import(module_name, module_path)
            default_metadata = {
                'help': clean_help_string(module.__doc__),
                'name': plugin_name,
            }
            metadata = getattr(module, 'metadata', {})
            for k, v in default_metadata.items():
                if k not in metadata:
                    metadata[k] = v

            for variable_name in dir(module):
                if isinstance(getattr(module, variable_name), Logger):
                    logger_name = getattr(module, variable_name).logger_name
                    break
            else:
                logger_name = plugin_name
            plugins_registry[plugin_name] = {
                'path': str(module_path),
                'is_dir': module_path.is_dir(),
                'logger': logger_name,
                'metadata': metadata,
                'version': getattr(module, '__version__', '1.0.0')
            }
            config[f'plugins.{plugin_name}.enabled'] = True
    return 0


@app.command()
def edit(plugin_name: str):
    '''Edits a plugin in your favorite text editor'''
    if plugin_name not in plugins_registry:
        raise typer.Exit(errno.ENODATA)
    editor = config['app.editor.name']
    if editor is None:
        if config['app.editor.prefer_visual']:
            editor = os.getenv('VISUAL', os.getenv('EDITOR'))
        else:
            editor = os.getenv('EDITOR', os.getenv('VISUAL'))
    path = plugins_path / plugin_name
    editor_flags = config['app.editor.flags'] or []
    args = [editor] + editor_flags + [str(path.resolve())]
    subprocess.call(args)
    return 0


@app.command()
def logs(plugin_name: str) -> int:
    '''Pages on the latest log for provided plugin name.'''
    if plugin_name not in plugins_registry:
        raise typer.Exit(errno.ENODATA)
    pager = config['app.pager.name'] or os.getenv('PAGER', 'less')
    path: Path = logs_path / plugins_registry[plugin_name]['logger']
    filepath: Path = None
    try:
        filepath = next(sorted(path.iterdir(), reverse=True))
    except StopIteration:
        raise typer.Exit(errno.ENOENT)

    pager_flags = config['app.pager.flags'] or []
    subprocess.call([pager] + pager_flags + [str(filepath.resolve())])
    return 0


@app.command()
def enable(plugin_name: str) -> int:
    '''Enables the specified plugin.'''
    config[f'plugins.{plugin_name}.enabled'] = True
    return 0


@app.command()
def disable(plugin_name: str) -> int:
    '''Disables the specified plugin.'''
    config[f'plugins.{plugin_name}.enabled'] = False
    return 0


@app.command()
def ls():
    '''Lists available plugins.'''
    table = Table('plugin_name', 'enabled', 'description')
    for plugin_name, plugin_meta in plugins_registry.items():
        enabled = '✅' if is_plugin_enabled(plugin_name) else '❌'
        description = textwrap.shorten(plugin_meta['metadata.help'], 40)
        table.add_row(
            textwrap.shorten(plugin_name, 10),
            enabled,
            description,
        )
    console.print(table)
    return 0


@app.command()
def install(
    plugin_name: str,
    version: str = typer.Option('latest', '--version', '-v')
) -> int:
    '''Installs a plugin from the CLI plugin registry.'''
    logger.info('Installing plugin %s v%s', plugin_name, version)
    client = Client()
    registries = config['app.registries'] or []
    registries.append('cli.dogeek.me')
    for registry in registries:
        response = client.get(
            f'https://{registry}/v1/plugins/{plugin_name}/versions/{version}'
        )
        if response.status_code == HTTPStatus.OK:
            break
    else:
        logger.error(
            'No plugin %s v%s found in registries %s : %s',
            plugin_name, version, registries, response.json()['message']
        )
        raise typer.Exit()

    data = response.json()['data']
    file_ = io.BytesIO(gzip.decompress(b85decode(data['file'])))
    archive = tarfile.TarFile(fileobj=file_)
    archive.extractall(plugins_path)
    archive.close()
    print(f'Plugin {plugin_name} v{version} has been installed.')
    return 0


@app.command()
def publish(
    plugin_name: str,
    registry: str = typer.Option('cli.dogeek.me', '--registry')
) -> int:
    '''Publish a plugin to the registry.'''
    metadata = plugins_registry[plugin_name]
    module_path = Path(metadata['path'])
    module_name = f'plugins.{plugin_name}'
    plugin_module = do_import(module_name, module_path)
    client = Client()
    version = getattr(plugin_module, '__version__', '1.0.0')

    # List plugin versions
    response = client.get(f'https://{registry}/v1/plugins/{plugin_name}/versions')
    logger.debug('Status : %s, Versions : %s', response.status_code, response.json())
    if response.status_code == HTTPStatus.NOT_FOUND:
        # Initial release
        logger.info('Initial release of plugin %s, creating plugin on registry.', plugin_name)
        client.post(
            f'https://{registry}/v1/plugins',
            json={'name': plugin_name}, do_sign=True,
        )
    available_versions = [v['version'] for v in response.json()['data']]
    if version in available_versions:
        logger.error('Plugin %s version %s already exists', plugin_name, version)
        raise typer.Exit()

    data = make_tarball(module_path)
    files = {
        'file': (
            f'{version}.tar.gz',
            data,
            'application/tar+gzip'
        )
    }
    client.post(
        f'https://{registry}/v1/plugins/{plugin_name}/versions/{version}',
        do_sign=True, files=files,
    )
    return 0


@app.command()
def uninstall(plugin_name: str):
    '''Uninstalls a plugin completely.'''


@app.command()
def add_maintainer(plugin_name: str, maintainer_public_key: str, maintainer_email: str):
    '''Adds a maintainer to the plugin.'''


@app.command()
def upgrade(
    plugin_name: Optional[str] = typer.Option(None, '--plugin', '-p'),
    version: str = typer.Option('latest', '--version')
):
    '''Upgrades one or all plugins to the desired version.'''
