from typing import Any, Dict, Union, List, Optional

from typer.models import CommandInfo, TyperInfo, DefaultPlaceholder
from typer.main import get_click_param
from typer.utils import get_params_from_function
from typer.core import TyperArgument, TyperOption


def format_params(params: List[Union[TyperOption, TyperArgument]]) -> Dict[str, List[Dict[str, Any]]]:
    for param in params:
        yield param.to_info_dict()


def make_cmd(command: CommandInfo):
    name = (command.name or command.callback.__name__).lower().replace('_', '-')
    help = command.help or command.callback.__doc__
    params = get_params_from_function(command.callback)
    click_params = [get_click_param(p)[0] for p in params.values()]

    return {
        'name': name,
        'help': help,
        'params': list(format_params(click_params)),
    }


def make_callback(callback: Optional[TyperInfo]):
    if callback is None:
        return

    name, help = callback.name, callback.help
    if isinstance(name, DefaultPlaceholder):
        name = name.value
    if isinstance(help, DefaultPlaceholder):
        help = help.value
    params = get_params_from_function(callback.callback)
    click_params = [get_click_param(p)[0] for p in params.values()]

    return {
        'name': name,
        'help': help,
        'params': list(format_params(click_params))
    }
