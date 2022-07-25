# cli


[![PyPI](https://img.shields.io/pypi/v/cli.svg)](https://pypi.python.org/pypi/cli)
[![Documentation Status](https://readthedocs.org/projects/cli/badge/?version=latest)](https://readthedocs.org/projects/cli/badge/?version=latest)


Interactive CLI to store scripts into


* Free software: MIT license
* Documentation: https://cli.readthedocs.io.

## Installation / Setup

Install this project from PyPI => `pip3 install -U dogeek-cli`

Once complete, the project should be installed, and the `cli` command should be available.
You should run `cli config reset` at least once to initialize the global configuration file with the defaults.

Commands :

- `cli plugins install $plugin_name` => install a plugin from the public registry
- `cli plugins upgrade` => Upgrades all plugins to the latest version
- `cli config set $config_key $config_value` => sets a configuration key/value pair

Plugins are installed in `$XDG_CONFIG_HOME/cli/plugins`.
On Windows, they are installed in `C:\Users\$USER\AppData\Roaming\cli\plugins`.

Plugins can be as simple as plain python files, which export a `typer.Typer` instance. They can also be more complex and be whole python modules, in that case, the module's `__init__.py` file should export the `typer.Typer` instance.

## Features

* Extensible plugins system
* Built-in configuration options
* Included templating system (Mako)
* Automatic setup for logging and state management
* Public registry and publishing using asymmetric encryption for login in.
* Easily implement plugins for the CLI, supporting features such as
  * .cliignore => .gitignore/.dockerignore like file which prevents files from being packaged when publishing
  * requirements.txt support

## Planned features

* Update checking for cli app
* Handle plugins dependancy management cleanly
  * install in virtualenv ?
  * config file for plugins ? Or variable in plugins => on update read requirements
  * syntax : `import mylib  # v1.2.3` would be good I think
  * how to handle dir plugins ? => manifest file in directory ?
