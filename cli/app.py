import importlib.util
from pathlib import Path
import sys

import typer

from cli.config import plugins_path, plugins_registry, state  # noqa
from cli.subcommands import env
from cli.subcommands import config as cfg


def do_import(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def add_plugins_hook(app: typer.Typer):
    for module_name, cached_module in plugins_registry.items():
        # Cached module is in the form {"path": "...", "metadata": {...}}
        module = do_import(module_name, cached_module['path'])
        app.add_typer(module.app, **cached_module['metadata'])
    return app


app = add_plugins_hook(typer.Typer())


@app.command()
def cache_plugins():
    for module_path in plugins_path.iterdir():
        if module_path.isdir() or module_path.name.endswith('.py'):
            if module_path.name == '__pycache__':
                continue
            if module_path.name.startswith('.'):
                continue
            module_name = module_path.name.split('.')[0]
            module_name = f'plugins.{module_name}'
            module = do_import(module_name, module_path)
            default_metadata = {
                'help': module.__doc__,
                'name': module_path.name.split('.')[0],
            }
            metadata = getattr(module, 'metadata', default_metadata)
            if 'help' not in metadata:
                metadata['help'] = module.__doc__
            if 'name' not in metadata:
                metadata['name'] = module_path.name.split('.')[0]
            plugins_registry[module_name] = {
                'path': str(module_path),
                'metadata': metadata,
            }


@app.callback()
def callback(
    json: bool = typer.Option(False, '--json', help='Format the output as JSON.'),
    toml: bool = typer.Option(False, '--toml', help='Format the output as TOML.'),
    csv: bool = typer.Option(False, '--csv', help='Format the output as CSV.'),
    yaml: bool = typer.Option(False, '--yaml', '--yml', help='Format the output as YAML.')
) -> None:
    global state
    state['json'] = json
    state['toml'] = toml
    state['csv'] = csv
    state['yaml'] = yaml
    return


app.add_typer(env.app, name='env', help=env.__doc__)
app.add_typer(cfg.app, name='env', help=cfg.__doc__)

typer_click_object = typer.main.get_command(app)


def main():
    typer_click_object()


if __name__ == '__main__':
    main()
