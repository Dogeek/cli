'''Manages CLI plugins.'''
import errno
import os
from pathlib import Path
import subprocess

import typer

from cli.config import (
    config, plugins_path, plugins_registry, RESERVED_COMMANDS, logs_path,
)
from cli.logging import Logger
from cli.utils import clean_help_string, do_import


app = typer.Typer()


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
            plugins_registry[module_path.name.split('.')[0]] = {
                'path': str(module_path),
                'is_dir': module_path.is_dir(),
                'logger': logger_name,
                'metadata': metadata,
            }
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
