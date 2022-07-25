'''Subcommand that handles system cleanups and such.'''
import shutil

import typer

from dogeek_cli.enums import PurgeWhat
from dogeek_cli.config import logs_path, tmp_dir
from dogeek_cli.state import State

app = typer.Typer()


@app.command()
def purge(what: PurgeWhat):
    '''Purges the cli directory of files.'''
    state = State()
    if state.verbosity > 0:
        print('Deleting %s ' % what.value)
    match what:
        case PurgeWhat.LOGS:
            shutil.rmtree(logs_path)
            logs_path.mkdir(exist_ok=True, parents=True)
        case PurgeWhat.TMP:
            shutil.rmtree(tmp_dir)
            tmp_dir.mkdir(exist_ok=True, parents=True)
