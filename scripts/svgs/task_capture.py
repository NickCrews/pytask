# content of task_capture.py
from __future__ import annotations

import pytask
from click.testing import CliRunner


def task_func1() -> None:
    assert True


def task_func2() -> None:
    print("Debug statement")  # noqa: T201
    raise AssertionError


if __name__ == "__main__":
    runner = CliRunner()

    pytask.console.record = True
    runner.invoke(pytask.cli, [__file__])
    pytask.console.save_svg("capture.svg", title="pytask")
