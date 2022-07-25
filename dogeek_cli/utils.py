import os
import os.path
from pathlib import Path
import tarfile
import textwrap
import subprocess
from typing import Callable

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
