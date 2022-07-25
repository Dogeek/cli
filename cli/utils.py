import importlib.util
from pathlib import Path
import sys
import textwrap

from cli.config import config


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
