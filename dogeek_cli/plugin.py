from base64 import b85encode, b85decode
from dataclasses import dataclass
from http import HTTPStatus
import importlib.util
import os
from pathlib import Path
import json
import shutil
import sys
from urllib.parse import urlparse
import gzip
import io
import tarfile
import secrets
import textwrap
from types import ModuleType

from gitignore_parser import parse_gitignore
import typer

from dogeek_cli.client import Client
from dogeek_cli.config import plugins_registry, plugins_path, config, tmp_dir
from dogeek_cli.logging import Logger
from dogeek_cli.utils import clean_help_string, cliignore_filter_factory
from dogeek_cli.meta import make_cmd, make_callback


@dataclass
class PluginMetadata:
    name: str
    help: str


class Plugin:
    def __init__(self, plugin_name: str) -> None:
        self.plugin_name = plugin_name
        self._module = None
        self._client = None

    @property
    def exists(self):
        return (
            self.plugin_name in plugins_registry or
            any(fp.name.split('.')[0] == self.plugin_name for fp in plugins_path.glob('*'))
        )

    @property
    def client(self) -> Client:
        return Client(self.installed_from)

    @property
    def path(self) -> Path:
        return Path(plugins_registry[self.plugin_name]['path'])

    @path.setter
    def path(self, path: str | Path) -> None:
        plugins_registry[self.plugin_name]['path'] = Path(path)
        return

    @property
    def is_dir(self) -> bool:
        if self.plugin_name not in plugins_registry and self.exists:
            path = plugins_path / self.plugin_name
            return path.exists() and path.is_dir()
        return plugins_registry[self.plugin_name]['is_dir']

    @is_dir.setter
    def is_dir(self, is_directory: bool) -> None:
        plugins_registry[self.plugin_name]['is_dir'] = bool(is_directory)
        return

    @property
    def logger(self) -> str:
        return plugins_registry[self.plugin_name]['logger']

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(**plugins_registry[self.plugin_name]['metadata'])

    @property
    def version_string(self) -> str:
        return plugins_registry[self.plugin_name]['version']

    @property
    def version(self) -> tuple[int]:
        return tuple(
            int(c)
            for c in self.version_string.split('.')
        )

    @property
    def installed_from(self) -> str:
        return plugins_registry[self.plugin_name]['installed_from']

    @installed_from.setter
    def installed_from(self, registry: str) -> None:
        if self.installed_from is not None:
            return
        plugins_registry[self.plugin_name]['installed_from'] = registry
        return

    @property
    def upgrade_available(self) -> str:
        if self.installed_from is None:
            return '🔵'

        latest_version: str = self.client.get(
            f'/v1/plugins/{self.plugin_name}/versions/latest'
        ).json()['version']
        latest_version: tuple[int] = tuple(int(c) for c in latest_version.split('.'))
        for i, (current, latest) in enumerate(zip(self.version, latest_version)):
            if current < latest:
                return ['🔴', '🟠', '🟢'][i]
        return '✅'

    @property
    def enabled(self) -> bool:
        '''Checks if the specified plugin is enabled.'''
        enabled = config[f'plugins.{self.plugin_name}.enabled']
        return isinstance(enabled, bool) and enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError(f'Plugin.enabled => should be a boolean, is {type(value)}')
        config[f'plugins.{self.plugin_name}.enabled'] = value

    @property
    def module(self) -> ModuleType:
        if self._module is not None:
            return self._module
        if self.path.is_dir():
            path = self.path / '__init__.py'
        else:
            path = self.path

        if not self.path.exists():
            raise FileNotFoundError(f'Plugin not found at path {path}')
        spec = importlib.util.spec_from_file_location(
            f'plugins.{self.plugin_name}', str(path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self._module = module
        return module

    @property
    def tarball(self) -> str:
        output_filename = secrets.token_hex(8)
        out_path = tmp_dir / output_filename
        cliignore = None
        if len(list(self.path.glob('**/.cliignore'))) > 0:
            # There is a .cliignore file to process
            cliignore = parse_gitignore(next(self.path.glob('**/.cliignore')))

        with tarfile.open(out_path, "w:gz") as tar:
            tar.add(
                self.path,
                arcname=os.path.basename(self.path),
                recursive=True,
                filter=cliignore_filter_factory(self.path, cliignore)
            )

        with open(out_path, 'rb') as fp:
            data = fp.read()
        os.remove(out_path)
        return b85encode(data).decode('utf8')

    @property
    def short_help(self) -> str:
        return textwrap.shorten(self.metadata.help, 40)

    def cache_plugin_metadata(self, module_path: Path, installed_from: str | None) -> None:
        plugin_name = (
            module_path.name.split('.')[0]
            if not module_path.is_dir()
            else module_path.name
        )
        self.path = module_path
        default_metadata = {
            'help': clean_help_string(self.module.__doc__),
            'name': plugin_name,
        }
        metadata = getattr(self.module, 'metadata', {})
        for k, v in default_metadata.items():
            if k not in metadata:
                metadata[k] = v

        for variable_name in dir(self.module):
            if isinstance(getattr(self.module, variable_name), Logger):
                logger_name = getattr(self.module, variable_name).logger_name
                break
        else:
            logger_name = plugin_name
        plugins_registry[plugin_name] = {
            'path': str(module_path),
            'is_dir': module_path.is_dir(),
            'logger': logger_name,
            'metadata': metadata,
            'version': getattr(self.module, '__version__', '1.0.0'),
            'installed_from': installed_from
        }
        config[f'plugins.{plugin_name}.enabled'] = True
        return

    def upgrade(self, new_version: str) -> int:
        if self.installed_from is None:
            print('Cannot upgrade a local plugin')
            return 1

        response = self.client.get(f'/v1/plugins/{self.plugin_name}/versions/{new_version}')
        if response.status_code == HTTPStatus.NOT_FOUND:
            print(response.json()['detail'])
            return 1

        self.remove_files()
        # Install the new plugin version
        return self.install(
            response.json()['data']['file'],
            urlparse(response.request.url).hostname
        )

    def install(self, encoded_file: str, registry: str) -> int:
        file_ = io.BytesIO(gzip.decompress(b85decode(encoded_file)))
        archive = tarfile.TarFile(fileobj=file_)
        archive.extractall(plugins_path)
        filename = archive.getnames()[0]
        archive.close()
        self.cache_plugin_metadata(
            plugins_path / filename, installed_from=registry
        )
        return 0

    def remove_files(self) -> None:
        # Remove the current plugin
        if self.is_dir:
            shutil.rmtree(self.path)
        else:
            os.remove(self.path)
        return

    def uninstall(self) -> None:
        self.remove_files()
        del plugins_registry[self.plugin_name]
        return

    def make_meta(self, force_update: bool = False) -> None:
        path = Path(config.app_path) / f'plugin_meta/{self.plugin_name}.meta'
        path.parent.mkdir(exist_ok=True, parents=True)
        if not force_update and path.exists():
            return

        app: typer.Typer = self.module.app
        meta = vars(self.metadata)

        meta['commands'] = [
            make_cmd(command) for command in app.registered_commands
        ]
        meta['callback'] = make_callback(app.registered_callback)

        path.write_text(json.dumps(meta, indent=2))
