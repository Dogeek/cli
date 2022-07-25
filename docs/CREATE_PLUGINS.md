# Creating plugins

CLI plugins are just python files or modules placed in the `~/.config/cli/plugins` directory,
with a few caveats, namely :

* The module's `__doc__` is going to be the subcommand's help text
  * whitespace is stripped, and the string is dedented
* 