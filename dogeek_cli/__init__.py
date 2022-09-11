'''
Interactive CLI to store scripts into
'''
__version__ = '1.4.0'

from dogeek_cli.logging import Logger  # noqa
from dogeek_cli.config import config, env, tmp_dir, templates, templates_path  # noqa
from dogeek_cli.state import state  # noqa
from dogeek_cli.utils import open_editor, open_pager  # noqa
from dogeek_cli.plugin import Plugin  # noqa
