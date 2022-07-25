from dataclasses import dataclass

from dogeek_cli.config import config
from dogeek_cli.enums import OutputFormat
from dogeek_cli.utils import Singleton


@dataclass
class State(metaclass=Singleton):
    format: OutputFormat = OutputFormat.DEFAULT
    verbosity: int = config['app.default_verbosity']


state = State()
