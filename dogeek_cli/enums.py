from enum import Enum


class OutputFormat(str, Enum):
    DEFAULT = 'default'
    JSON = 'json'
    TOML = 'toml'
    CSV = 'csv'
    YAML = 'yaml'
    YML = 'yaml'
    TABLE = 'table'


class PurgeWhat(str, Enum):
    LOGS = 'logs'
    TMP = 'tmp'
