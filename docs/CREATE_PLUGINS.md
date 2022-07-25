# Creating plugins

CLI plugins are just python files or modules placed in the `~/.config/cli/plugins` directory,
with a few caveats, namely :

* The module's `__doc__` is going to be the subcommand's help text
  * whitespace is stripped, and the string is dedented
* Plugins require the use of [typer](https://typer.tiangolo.com)


## CLI package documentation

### Logger

You can import the `Logger` class from the `cli` module. It is a subclass of the `logging.Logger` class
which will store logs in the appropriate directory (`~/.config/cli/logs/$logger_name/`)

This logger also interacts with the configuration of the CLI, which allows the user to specify the log level desired.

### config

You can import the `config` instance from the `cli` module.

It provides a class allowing you to get and set configuration parameters in a pretty straightforward way :
```python
from cli import config

# get 'my_plugin.config.value'
config['my_plugin.config.value']

# set 'my_plugin.config.value' to true
config['my_plugin.config.value'] = True

# get or default
config['my_plugin.config.value'] or []
```

## Sample plugin code

```python
'''
Sample plugin to demonstrate what is available in the CLI package.
'''
from cli import Logger, config, env, tmp_dir, templates, state
import typer

name = __file__.split('/').pop().split('.')[0]

logger = Logger(name)
app = typer.Typer()
```
