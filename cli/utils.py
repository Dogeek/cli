import importlib.util
import os
import os.path
from pathlib import Path
import secrets
import sys
import tarfile
import textwrap

from cli.config import config, tmp_dir


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


def make_tarball(source_dir: Path) -> bytes:
    '''Makes a tarball from a file or directory.'''
    output_filename = secrets.token_hex(8)
    out_path = tmp_dir / output_filename
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    with open(out_path, 'rb') as fp:
        data = fp.read()
    os.remove(out_path)
    return data
