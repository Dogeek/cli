from pathlib import Path

from xdgconfig import JsonConfig


config = JsonConfig('cli', 'config.json')
env = JsonConfig('cli', 'env.json')
root_path = Path(__file__).parent.resolve()
templates_path: Path = (config.app_path / 'templates')
templates_path.mkdir(parents=True, exist_ok=True)
plugins_path: Path = (config.app_path / 'plugins')
plugins_path.mkdir(parents=True, exist_ok=True)
plugins_registry = JsonConfig('cli', 'registry.json')
state = {
    'json': False,
    'csv': False,
    'toml': False,
    'yaml': False,
}
