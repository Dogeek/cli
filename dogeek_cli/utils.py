import os
import os.path
import contextlib
from pathlib import Path
import tarfile
import textwrap
import subprocess
from typing import Callable
from http import HTTPStatus
import packaging.version

import requests
from rich.console import Console

from dogeek_cli.config import config


def clean_help_string(help_string: str | None) -> str:
    if help_string is None:
        return ''
    return textwrap.dedent(help_string.strip())


def cliignore_filter_factory(
    source_dir: Path,
    cliignore: Callable[[Path | str], bool] | None
) -> Callable[[tarfile.TarInfo], tarfile.TarInfo | None]:
    def filter(tarinfo: tarfile.TarInfo):
        nonlocal cliignore
        if cliignore is None:
            # No cliignore, no filtering
            return tarinfo
        if cliignore(source_dir.parent / tarinfo.name):
            return
        return tarinfo
    return filter


def open_editor(path: Path) -> None:
    editor = config['app.editor.name']
    if editor is None:
        if config['app.editor.prefer_visual']:
            editor = os.getenv('VISUAL', os.getenv('EDITOR'))
        else:
            editor = os.getenv('EDITOR', os.getenv('VISUAL'))
    editor_flags = config['app.editor.flags'] or []
    args = [editor] + editor_flags + [str(path.resolve())]
    subprocess.call(args)
    return


def open_pager(path: Path) -> None:
    pager = config['app.pager.name'] or os.getenv('PAGER', 'less')
    pager_flags = config['app.pager.flags'] or []
    subprocess.call([pager] + pager_flags + [str(path.resolve())])
    return


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def get_pypi_version(
    package: str, url_pattern: str | None = None
) -> packaging.version.Version | None:
    '''Returns version of package on pypi.python.org using json.'''
    if url_pattern is None:
        url_pattern = 'https://pypi.python.org/pypi/{package}/json'

    with contextlib.suppress(requests.exceptions.ConnectionError):
        response = requests.get(url_pattern.format(package=package))
        if response.status_code != HTTPStatus.OK:
            return

        latest = packaging.version.parse('0')
        data = response.json()
        releases = data.get('releases', [])
        for release in releases:
            release_version = packaging.version.parse(release)
            if not release_version.is_prerelease:
                latest = max(latest, release_version)
        return latest
    return None


def check_version(current_version: str) -> None:
    '''Checks if a new version of the package is available.'''
    latest_version = get_pypi_version('dogeek_cli')
    if latest_version is None:
        return

    current_version: packaging.version.Version = packaging.version.parse(current_version)
    color = None
    if current_version < latest_version:
        if current_version.major < latest_version.major:
            color = 'bright_red'
        elif current_version.minor < latest_version.minor:
            color = 'bright_yellow'
        elif current_version.micro < latest_version.micro:
            color = 'bright_green'

    if color is not None:
        # Color is only defined if the current version of the package is outdated.
        err_console = Console(stderr=True)
        err_console.print(f'[{color} bold]dogeek_cli v{str(latest_version)} is out![/]')
        # TODO: Make the command a clickable link that paste into the terminal
        err_console.print(
            (
                f'[{color} bold]Please upgrade by running [/]'
                '[grey54]pip3 install --upgrade dogeek_cli[/]'
            )
        )
    return
