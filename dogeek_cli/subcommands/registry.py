from http import HTTPStatus
from typing import Optional

import typer

from dogeek_cli import Logger
from dogeek_cli.plugin import Plugin


app = typer.Typer()
logger = Logger('cli.plugins.registry')


@app.command()
def publish(
    plugin_name: str,
    registry: str = typer.Option('cli.dogeek.me', '--registry', '-r')
) -> int:
    '''Publish a plugin to the registry.'''
    plugin = Plugin(plugin_name)
    plugin.installed_from = registry
    version = getattr(plugin.module, '__version__', '1.0.0')

    # List plugin versions
    response = plugin.client.get(f'/v1/plugins/{plugin_name}/versions')
    logger.debug('Status : %s, Versions : %s', response.status_code, response.json())
    if response.status_code == HTTPStatus.NOT_FOUND:
        # Initial release
        logger.info('Initial release of plugin %s, creating plugin on registry.', plugin_name)
        plugin.client.post('/v1/plugins', json={'name': plugin_name}, do_sign=True)
        response = plugin.client.get(f'/v1/plugins/{plugin_name}/versions')
    available_versions = [v['version'] for v in response.json()['data']]
    if version in available_versions:
        logger.error('Plugin %s version %s already exists', plugin_name, version)
        raise typer.Exit(1)

    response = plugin.client.post(
        f'/v1/plugins/{plugin_name}/versions/{version}',
        do_sign=True, json={"tarball": plugin.tarball},
    )
    if response.status_code == HTTPStatus.FORBIDDEN:
        print(response.json()['detail'])
    return 0


@app.command()
def add_maintainer(
    plugin_name: str, maintainer_public_key: str, maintainer_email: str,
):
    '''Adds a maintainer to the plugin.'''
    plugin = Plugin(plugin_name)
    response = plugin.client.post(
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
