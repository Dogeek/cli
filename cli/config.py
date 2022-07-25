from pathlib import Path

from xdgconfig import JsonConfig


class DefaultConfig:
    _DEFAULTS = {
        'app.theme': 'monokai',
        'app.logger.level': 'info',
        'app.editor.prefer_visual': False,
        'app.editor.name': 'vi',
        'app.editor.flags': [],
        'app.pager.name': 'less',
        'app.pager.flags': [],
    }


class Config(DefaultConfig, JsonConfig):
    ...


config = Config('cli', 'config.json')
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
RESERVED_COMMANDS = ['config', 'env', 'plugins']
logs_path: Path = (config.app_path / 'logs')
logs_path.mkdir(parents=True, exist_ok=True)
