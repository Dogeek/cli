# cli


[![PyPI](https://img.shields.io/pypi/v/cli.svg)](https://pypi.python.org/pypi/cli)
[![Documentation Status](https://readthedocs.org/projects/cli/badge/?version=latest)](https://readthedocs.org/projects/cli/badge/?version=latest)


Interactive CLI to store scripts into


* Free software: MIT license
* Documentation: https://cli.readthedocs.io.


## Features

* Extensible plugins system
* Built-in configuration options
* Included templating system (Mako)
* Automatic setup for logging and state management

## Planned features

* Public registry for plugins
  * cli plugins publish
  * cli plugins install
  * cli plugins uninstall
  * cli plugins upgrade
* Update checking for cli app
* Handle plugins dependancy management cleanly
  * install in virtualenv ?
  * config file for plugins ? Or variable in plugins => on update read requirements
  * syntax : `import mylib  # v1.2.3` would be good I think
  * how to handle dir plugins ? => manifest file in directory ?
