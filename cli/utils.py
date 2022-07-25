import importlib.util
from pathlib import Path
import sys
import textwrap


def do_import(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def clean_help_string(help_string: str) -> str:
    return textwrap.dedent(help_string.strip())
