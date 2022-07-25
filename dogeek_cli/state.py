from dataclasses import dataclass

from dogeek_cli.config import config
from dogeek_cli.enums import OutputFormat


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class State(metaclass=Singleton):
    format: OutputFormat = OutputFormat.DEFAULT
    verbosity: int = config['app.default_verbosity']


state = State()
