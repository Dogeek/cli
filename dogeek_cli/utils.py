import io
import gzip
from base64 import b85encode, b85decode
import importlib.util
import os
import os.path
from pathlib import Path
import secrets
import sys
import tarfile
import textwrap
from urllib.parse import urlparse
from http import HTTPStatus
import shutil

from requests import Response

from dogeek_cli.config import config, tmp_dir, plugins_registry, plugins_path
from dogeek_cli.client import Client
from dogeek_cli import Logger


def do_import(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def clean_help_string(help_string: str) -> str:
    return textwrap.dedent(help_string.strip())


def is_plugin_enabled(plugin_name: str) -> bool:
    '''Checks if the specified plugin is enabled.'''
    enabled = config[f'plugins.{plugin_name}.enabled']
    return isinstance(enabled, bool) and enabled


def make_tarball(source_dir: Path) -> str:
    '''Makes a tarball from a file or directory.'''
    output_filename = secrets.token_hex(8)
    out_path = tmp_dir / output_filename
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    with open(out_path, 'rb') as fp:
        data = fp.read()
    os.remove(out_path)
    return b85encode(data).decode('utf8')


def cache_plugin_metadata(module_path: Path, installed_from=None):
    plugin_name = (
        module_path.name.split('.')[0]
        if not module_path.is_dir()
        else module_path.name
    )
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
        'version': getattr(module, '__version__', '1.0.0'),
        'installed_from': installed_from
    }
    config[f'plugins.{plugin_name}.enabled'] = True


def do_install(response: Response):
    data = response.json()['data']
    file_ = io.BytesIO(gzip.decompress(b85decode(data['file'])))
    archive = tarfile.TarFile(fileobj=file_)
    archive.extractall(plugins_path)
    filename = archive.getnames()[0]
    archive.close()
    registry = urlparse(response.request.url).hostname
    cache_plugin_metadata(plugins_path / filename, installed_from=registry)
    return


def remove_plugin_files(plugin_name: str) -> None:
    # Remove the current plugin
    if plugins_registry[plugin_name]['is_dir']:
        shutil.rmtree(plugins_registry[plugin_name]['path'])
    else:
        os.remove(plugins_registry[plugin_name]['path'])
    return


def do_upgrade(plugin_name: str, version: str):
    registry = plugins_registry[plugin_name]['installed_from']
    if registry is None:
        print('Cannot upgrade a local plugin')
        return 1

    client = Client(registry)
    response = client.get(f'/v1/plugins/{plugin_name}/versions/{version}')
    if response.status_code == HTTPStatus.NOT_FOUND:
        print(response.json()['detail'])
        return 1

    remove_plugin_files(plugin_name)
    # Install the new plugin version
    do_install(response)


def plugin_has_upgrade(plugin_name: str, current_version: str, installed_from: str | None) -> str:
    if installed_from is None:
        return '🔵'

    client = Client(installed_from)
    current_version: tuple[int] = tuple(int(c) for c in current_version.split('.'))
    latest_version: str = client.get(
        f'/v1/plugins/{plugin_name}/versions/latest'
    ).json()['version']
    latest_version: tuple[int] = tuple(int(c) for c in latest_version.split('.'))
    for i, (current, latest) in enumerate(zip(current_version, latest_version)):
        if current < latest:
            return ['🔴', '🟠', '🟢'][i]
    return '✅'
