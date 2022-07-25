from datetime import datetime
import logging
import logging.handlers

from dogeek_cli.config import config, logs_path


class Logger(logging.Logger):
    def __init__(self, name: str):
        level: str = config['app.logger.level'] or 'debug'
        level = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warn': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
            'fatal': logging.FATAL
        }[level.lower()]
        path = (
            logs_path / name /
            f"{datetime.now().strftime('%Y-%m-%d')}-{name}.log"
        )
        (logs_path / name).mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, 'a', 'utf8')
        formatter = logging.Formatter(
            '%(asctime)s -- %(levelname)s : %(module)s::%(funcName)s -- %(message)s'
        )
        handler.setFormatter(formatter)
        super().__init__(name, level)
        self.addHandler(handler)
        self.logger_name = name
