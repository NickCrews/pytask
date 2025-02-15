from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest
from _pytask.collect_command import _find_common_ancestor_of_all_nodes
from _pytask.collect_command import _print_collected_tasks
from attrs import define
from pytask import cli
from pytask import ExitCode
from pytask import MetaNode
from pytask import Task


@pytest.mark.end_to_end()
def test_collect_task(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example>" in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example>" in captured
    assert "<Dependency" in captured
    assert "in.txt>" in captured
    assert "<Product" in captured
    assert "out.txt>" in captured


@pytest.mark.end_to_end()
def test_collect_task_in_root_dir(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    cwd = Path.cwd()
    os.chdir(tmp_path)
    result = runner.invoke(cli, ["collect"])
    os.chdir(cwd)

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example>" in captured


@pytest.mark.end_to_end()
def test_collect_parametrized_tasks(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.parametrize("arg, produces", [(0, "out_0.txt"), (1, "out_1.txt")])
    def task_example(arg):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "").replace("\u2502", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "[0-out_0.txt]>" in captured
    assert "[1-out_1.txt]>" in captured


@pytest.mark.end_to_end()
def test_collect_task_with_expressions(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_example_1():
        pass

    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()
    tmp_path.joinpath("in_2.txt").touch()

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-k", "_1"])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-k", "_1", "--nodes"])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


@pytest.mark.end_to_end()
def test_collect_task_with_marker(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.wip
    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_example_1():
        pass

    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()

    config = """
    [tool.pytask.ini_options]
    markers = {'wip' = 'A work-in-progress marker.'}
    """
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(config))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-m", "wip"])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "-m", "wip", "--nodes"]
    )

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


@pytest.mark.end_to_end()
def test_collect_task_with_ignore_from_config(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_example_1():
        pass
    """
    tmp_path.joinpath("task_example_1.py").write_text(textwrap.dedent(source))

    source = """
    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_example_2.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()

    config = """
    [tool.pytask.ini_options]
    ignore = ["task_example_2.py"]
    """
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(config))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


@pytest.mark.end_to_end()
def test_collect_task_with_ignore_from_cli(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_example_1():
        pass
    """
    tmp_path.joinpath("task_example_1.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()

    source = """
    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_example_2.py").write_text(textwrap.dedent(source))

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "--ignore", "task_example_2.py"]
    )

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(
        cli,
        ["collect", tmp_path.as_posix(), "--ignore", "task_example_2.py", "--nodes"],
    )

    assert result.exit_code == ExitCode.OK
    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


@define
class MetaNode(MetaNode):
    path: Path

    def state(self):
        ...


def function():
    ...


@pytest.mark.unit()
def test_print_collected_tasks_without_nodes(capsys):
    dictionary = {
        "task_path.py": [
            Task(
                base_name="function",
                path=Path("task_path.py"),
                function=function,
                depends_on={0: MetaNode("in.txt")},
                produces={0: MetaNode("out.txt")},
            )
        ]
    }

    _print_collected_tasks(dictionary, False, "file", Path())

    captured = capsys.readouterr().out
    assert "<Module task_path.py>" in captured
    assert "<Function task_path.py::function>" in captured
    assert "<Dependency in.txt>" not in captured
    assert "<Product out.txt>" not in captured


@pytest.mark.unit()
def test_print_collected_tasks_with_nodes(capsys):
    dictionary = {
        "task_path.py": [
            Task(
                base_name="function",
                path=Path("task_path.py"),
                function=function,
                depends_on={0: MetaNode("in.txt")},
                produces={0: MetaNode("out.txt")},
            )
        ]
    }

    _print_collected_tasks(dictionary, True, "file", Path())

    captured = capsys.readouterr().out

    assert "<Module task_path.py>" in captured
    assert "<Function task_path.py::function>" in captured
    assert "<Dependency in.txt>" in captured
    assert "<Product out.txt>" in captured


@pytest.mark.unit()
@pytest.mark.parametrize(("show_nodes", "expected_add"), [(False, "src"), (True, "..")])
def test_find_common_ancestor_of_all_nodes(show_nodes, expected_add):
    tasks = [
        Task(
            base_name="function",
            path=Path.cwd() / "src" / "task_path.py",
            function=function,
            depends_on={0: MetaNode(Path.cwd() / "src" / "in.txt")},
            produces={
                0: MetaNode(Path.cwd().joinpath("..", "bld", "out.txt").resolve())
            },
        )
    ]

    result = _find_common_ancestor_of_all_nodes(tasks, [Path.cwd() / "src"], show_nodes)
    assert result == Path.cwd().joinpath(expected_add).resolve()


@pytest.mark.end_to_end()
def test_task_name_is_shortened(runner, tmp_path):
    tmp_path.joinpath("a", "b").mkdir(parents=True)
    tmp_path.joinpath("a", "b", "task_example.py").write_text("def task_example(): ...")

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example.py::task_example" in result.output
    assert "a/b/task_example.py::task_example" not in result.output
