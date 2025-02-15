# Capture warnings

pytask captures warnings during the execution.

Here is an example with the most infamous warning in the world of scientific Python.

```python
import pandas as pd
import pytask


def _create_df():
    df = pd.DataFrame({"a": range(10), "b": range(10, 20)})
    df[df["a"] < 5]["b"] = 1
    return df


@pytask.mark.products("df.pkl")
def task_warning(produces):
    df = _create_df()
    df.to_pickle(produces)
```

Running pytask produces

```{include} ../_static/md/warning.md
```

## Controlling warnings

You can use the `filterwarnings` option in `pyproject.toml` to configure pytask's
behavior when it comes to warnings.

The syntax for specifying warnings filters is the same as in the
[Python standard library](https://docs.python.org/3/library/warnings.html#the-warnings-filter),
i.e., a sequence of fields separated by colons:

```
action:message:category:module:line
```

You can specify a list of such filters. When a warning matches more than one option, the
action for the last matching option is performed.

For example, the configuration below will ignore specific deprecation warnings matching
a regex, all user warnings, and transform all other warnings into errors.

```toml
[tool.pytask.ini_options]
filterwarnings = [
    "error",
    "ignore::UserWarning",
    # note the use of single quote below to denote "raw" strings in TOML
    'ignore:function ham\(\) is deprecated:DeprecationWarning',
]
```

The syntax is explained in more detail in
[this section](https://docs.python.org/3/library/warnings.html#the-warnings-filter) of
the Python documentation and there are also
[more examples](https://docs.python.org/3/library/warnings.html#describing-warning-filters).

## `@pytask.mark.filterwarnings`

You can use the `@pytask.mark.filterwarnings` to add warning filters to specific test
items, allowing you to have finer control of which warnings should be captured at test,
class or even module level:

```python
import pandas as pd
import pytask


def _create_df():
    df = pd.DataFrame({"a": range(10), "b": range(10, 20)})
    df[df["a"] < 5]["b"] = 1
    return df


@pytask.mark.filterwarnings("ignore:.*:SettingWithCopyWarning")
@pytask.mark.products("df.pkl")
def task_warning(produces):
    df = _create_df()
    df.to_pickle(produces)
```

Filters applied using a mark take precedence over filters passed on the command line or
configured by the `filterwarnings` configuration option.

## Disabling warnings summary

Although not recommended, you can use the `--disable-warnings` command-line option to
suppress the warning summary entirely from the test run output.

## Debugging warnings

Sometimes it is not clear which line of code triggered a warning. To find the location,
you can turn warnings into exceptions and then use the {option}`pytask build --pdb` flag
to enter the debugger.

You can use the configuration to convert warnings to errors by setting

```toml
[tool.pytask.ini_options]
filterwarnings = ["error:.*"]
```

and then run `pytask`.

Or, you use a temporary environment variable. Here is an example for bash

```console
$ PYTHONWARNINGS=error pytask --pdb
```

and here for Powershell

```console
$ $env:PYTHONWARNINGS = 'error'
$ pytask
$ Remove-Item env:\PYTHONWARNINGS
```
