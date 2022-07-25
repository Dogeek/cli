from http import HTTPStatus
from pathlib import Path
from typing import Optional

import typer

from dogeek_cli import Logger
from dogeek_cli.config import plugins_registry
from dogeek_cli.utils import do_import, make_tarball
from dogeek_cli.client import Client


app = typer.Typer()
logger = Logger('cli.plugins.registry')


@app.command()
def publish(
    plugin_name: str,
    registry: str = typer.Option('cli.dogeek.me', '--registry', '-r')
) -> int:
    '''Publish a plugin to the registry.'''
    metadata = plugins_registry[plugin_name]
    module_path = Path(metadata['path'])
    module_name = f'plugins.{plugin_name}'
    plugin_module = do_import(module_name, module_path)
    client = Client(registry)
    version = getattr(plugin_module, '__version__', '1.0.0')

    # List plugin versions
    response = client.get(f'/v1/plugins/{plugin_name}/versions')
    logger.debug('Status : %s, Versions : %s', response.status_code, response.json())
    if response.status_code == HTTPStatus.NOT_FOUND:
        # Initial release
        logger.info('Initial release of plugin %s, creating plugin on registry.', plugin_name)
        client.post('/v1/plugins', json={'name': plugin_name}, do_sign=True)
        response = client.get(f'/v1/plugins/{plugin_name}/versions')
    available_versions = [v['version'] for v in response.json()['data']]
    if version in available_versions:
        logger.error('Plugin %s version %s already exists', plugin_name, version)
        raise typer.Exit(1)

    data = make_tarball(module_path)
    response = client.post(
        f'/v1/plugins/{plugin_name}/versions/{version}',
        do_sign=True, json={"tarball": data},
    )
    if response.status_code == HTTPStatus.FORBIDDEN:
        print(response.json()['detail'])
    return 0


@app.command()
def add_maintainer(
    plugin_name: str, maintainer_public_key: str, maintainer_email: str,
    registry: str = typer.Option('cli.dogeek.me', '--registry', '-r'),
):
    '''Adds a maintainer to the plugin.'''
    client = Client(registry)
    response = client.post(
        f'/v1/plugins/{plugin_name}/maintainers',
        json={'ssh_key': maintainer_public_key, 'email': maintainer_email},
        do_sign=True
    )
    if response.status_code == HTTPStatus.OK:
        return 0
    print(response.json()['detail'])
    raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Option('', '-q', '--query'),
    registry: str = typer.Option('cli.dogeek.me', '--registry', '-r')
) -> int:
    '''Search available plugins on a given registry.'''


@app.command()
def delete(
    plugin_name: str,
    version: Optional[str] = typer.Option(None, '--version', '-v'),
    force: bool = typer.Option(False, '--force', '-f'),
    registry: str = typer.Option('cli.dogeek.me', '--registry', '-r'),
) -> int:
    '''Deletes a plugin from the plugin registry.'''
