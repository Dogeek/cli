import csv
import io
import json

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
import toml
import yaml

from dogeek_cli.config import config
from dogeek_cli.enums import OutputFormat
from dogeek_cli.state import state


class Formatter:
    def __init__(self):
        self.console = Console()

    def __call__(self, data: dict | list):
        match state.format:
            case OutputFormat.JSON:
                self.print_json(data)
            case OutputFormat.YAML:
                self.print_yaml(data)
            case OutputFormat.YML:
                self.print_yaml(data)
            case OutputFormat.TOML:
                self.print_toml(data)
            case OutputFormat.CSV:
                self.print_csv(data)
            case OutputFormat.TABLE:
                self.print_table(data)
            case _:
                self.print_default(data)

    def print_syntax(self, data: str, lexer: str):
        lexer = Syntax(data, lexer, theme=config['app.theme'])
        self.console.print(lexer)

    def print_json(self, data: dict | list):
        self.print_syntax(json.dumps(data, indent=2), 'json')

    def print_yaml(self, data: dict | list):
        stream = io.StringIO()
        yaml.dump(data, stream, indent=2)
        stream.seek(0)
        self.print_syntax(stream.read(), 'yaml')

    def print_toml(self, data: dict | list):
        self.print_syntax(toml.dumps(data), 'toml')

    def print_csv(self, data: dict | list):
        if isinstance(data, dict):
            data = [data]
        fieldnames = tuple({k for d in data for k in d.keys()})
        stream = io.StringIO()
        writer = csv.DictWriter(
            stream, fieldnames, 'N/A',
            delimiter=',', quotechar='"',
            escapechar='"', lineterminator='\n',
        )
        writer.writerows(data)
        stream.seek(0)
        self.print_syntax(stream.read(), 'csv')

    def print_table(self, data: dict | list):
        if isinstance(data, dict):
            data = [data]
        fieldnames = tuple({k for d in data for k in d.keys()})
        table = Table(fieldnames)
        for row in data:
            table.add_row(row.values())
        self.console.print(table)

    def print_default(self, data: dict | list, indent: int = 0):
        if indent == 0 and not isinstance(data, dict):
            raise Exception()

        for key, val in data.items():
            if isinstance(val, dict):
                self.print_default(val, indent=indent + 2)
            elif isinstance(val, list):
                for obj in val:
                    if isinstance(obj, dict):
                        self.print_default(obj, indent=indent + 2)
                    elif isinstance(obj, list):
                        raise Exception()
                    else:
                        self.console.print(f'{" " * indent}🔷 {key} : {obj}')
            else:
                self.console.print(f'{" " * indent}🔷 {key} : {val}')


formatter = Formatter()
