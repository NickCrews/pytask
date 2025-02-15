from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from _pytask.exceptions import NodeNotFoundError
from pytask import cli
from pytask import ExitCode
from pytask import main
from pytask import TaskOutcome


@pytest.mark.xfail(sys.platform == "win32", reason="See #293.")
@pytest.mark.end_to_end()
def test_python_m_pytask(tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    subprocess.run(["python", "-m", "pytask", tmp_path.as_posix()], check=True)


@pytest.mark.end_to_end()
def test_execute_w_autocollect(runner, tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    cwd = Path.cwd()
    os.chdir(tmp_path)
    result = runner.invoke(cli)
    os.chdir(cwd)
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_task_did_not_produce_node(tmp_path):
    source = """
    import pytask

    @pytask.mark.produces("out.txt")
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.FAILED
    assert len(session.execution_reports) == 1
    assert isinstance(session.execution_reports[0].exc_info[1], NodeNotFoundError)


@pytest.mark.end_to_end()
def test_task_did_not_produce_multiple_nodes_and_all_are_shown(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.produces(["1.txt", "2.txt"])
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "NodeNotFoundError" in result.output
    assert "1.txt" in result.output
    assert "2.txt" in result.output


@pytest.mark.end_to_end()
def test_node_not_found_in_task_setup(tmp_path):
    """Test for :class:`_pytask.exceptions.NodeNotFoundError` in task setup.

    Before a task is executed, pytask checks whether all dependencies can be found.
    Normally, missing dependencies are caught during resolving dependencies if they are
    root nodes or when a task does not produce a node.

    To force this error one task accidentally deletes the product of another task.

    """
    source = """
    import pytask

    @pytask.mark.produces(["out_1.txt", "deleted.txt"])
    def task_1(produces):
        for product in produces.values():
            product.touch()

    @pytask.mark.depends_on("out_1.txt")
    @pytask.mark.produces("out_2.txt")
    def task_2(depends_on, produces):
        depends_on.with_name("deleted.txt").unlink()
        produces.touch()

    @pytask.mark.depends_on(["deleted.txt", "out_2.txt"])
    def task_3(depends_on):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.FAILED
    assert sum(i.outcome == TaskOutcome.SUCCESS for i in session.execution_reports) == 2

    report = session.execution_reports[2]
    assert report.outcome == TaskOutcome.FAIL
    assert isinstance(report.exc_info[1], NodeNotFoundError)


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    "dependencies",
    [[], ["in.txt"], ["in_1.txt", "in_2.txt"]],
)
@pytest.mark.parametrize("products", [["out.txt"], ["out_1.txt", "out_2.txt"]])
def test_execution_w_varying_dependencies_products(tmp_path, dependencies, products):
    source = f"""
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on({dependencies})
    @pytask.mark.produces({products})
    def task_example(depends_on, produces):
        if isinstance(produces, dict):
            produces = produces.values()
        elif isinstance(produces, Path):
            produces = [produces]
        for product in produces:
            product.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    for dependency in dependencies:
        tmp_path.joinpath(dependency).touch()

    session = main({"paths": tmp_path})
    assert session.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
def test_depends_on_and_produces_can_be_used_in_task(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_example(depends_on, produces):
        assert isinstance(depends_on, Path) and isinstance(produces, Path)
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Here I am. Once again.")

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").read_text() == "Here I am. Once again."


@pytest.mark.end_to_end()
def test_assert_multiple_dependencies_are_merged_to_dict(tmp_path, runner):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on({3: "in_3.txt", 4: "in_4.txt"})
    @pytask.mark.depends_on(["in_1.txt", "in_2.txt"])
    @pytask.mark.depends_on("in_0.txt")
    @pytask.mark.produces("out.txt")
    def task_example(depends_on, produces):
        expected = {
            i: Path(__file__).parent.joinpath(f"in_{i}.txt").resolve()
            for i in range(5)
        }
        assert depends_on == expected
        produces.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    for name in [f"in_{i}.txt" for i in range(5)]:
        tmp_path.joinpath(name).touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
def test_assert_multiple_products_are_merged_to_dict(tmp_path, runner):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces({3: "out_3.txt", 4: "out_4.txt"})
    @pytask.mark.produces(["out_1.txt", "out_2.txt"])
    @pytask.mark.produces("out_0.txt")
    def task_example(depends_on, produces):
        expected = {
            i: Path(__file__).parent.joinpath(f"out_{i}.txt").resolve()
            for i in range(5)
        }
        assert produces == expected
        for product in produces.values():
            product.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
@pytest.mark.parametrize("input_type", ["list", "dict"])
def test_preserve_input_for_dependencies_and_products(tmp_path, input_type):
    """Input type for dependencies and products is preserved."""
    path = tmp_path.joinpath("in.txt")
    input_ = {0: path.as_posix()} if input_type == "dict" else [path.as_posix()]
    path.touch()

    path = tmp_path.joinpath("out.txt")
    output = {0: path.as_posix()} if input_type == "dict" else [path.as_posix()]

    source = f"""
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on({input_})
    @pytask.mark.produces({output})
    def task_example(depends_on, produces):
        for nodes in [depends_on, produces]:
            assert isinstance(nodes, dict)
            assert len(nodes) == 1
            assert 0 in nodes
        produces[0].touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})
    assert session.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
@pytest.mark.parametrize("n_failures", [1, 2, 3])
def test_execution_stops_after_n_failures(tmp_path, n_failures):
    source = """
    def task_1(): raise Exception
    def task_2(): raise Exception
    def task_3(): raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path, "max_failures": n_failures})

    assert len(session.tasks) == 3
    assert len(session.execution_reports) == n_failures


@pytest.mark.end_to_end()
@pytest.mark.parametrize("stop_after_first_failure", [False, True])
def test_execution_stop_after_first_failure(tmp_path, stop_after_first_failure):
    source = """
    def task_1(): raise Exception
    def task_2(): raise Exception
    def task_3(): raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main(
        {"paths": tmp_path, "stop_after_first_failure": stop_after_first_failure}
    )

    assert len(session.tasks) == 3
    assert len(session.execution_reports) == 1 if stop_after_first_failure else 3


@pytest.mark.end_to_end()
def test_scheduling_w_priorities(tmp_path):
    source = """
    import pytask

    @pytask.mark.try_first
    def task_z(): pass

    def task_x(): pass

    @pytask.mark.try_last
    def task_y(): pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    assert session.execution_reports[0].task.name.endswith("task_z")
    assert session.execution_reports[1].task.name.endswith("task_x")
    assert session.execution_reports[2].task.name.endswith("task_y")


@pytest.mark.end_to_end()
def test_scheduling_w_mixed_priorities(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.try_last
    @pytask.mark.try_first
    def task_mixed(): pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.DAG_FAILED
    assert "Failures during resolving dependencies" in result.output
    assert "'try_first' and 'try_last' cannot be applied" in result.output


@pytest.mark.end_to_end()
@pytest.mark.parametrize("show_errors_immediately", [True, False])
def test_show_errors_immediately(runner, tmp_path, show_errors_immediately):
    source = """
    def task_succeed(): pass
    def task_error(): raise ValueError
    """
    tmp_path.joinpath("task_error.py").write_text(textwrap.dedent(source))

    args = [tmp_path.as_posix()]
    if show_errors_immediately:
        args.append("--show-errors-immediately")
    result = runner.invoke(cli, args)

    assert result.exit_code == ExitCode.FAILED
    assert "::task_succeed │ ." in result.output

    matches_traceback = re.findall("Traceback", result.output)
    if show_errors_immediately:
        assert len(matches_traceback) == 2
    else:
        assert len(matches_traceback) == 1


@pytest.mark.end_to_end()
@pytest.mark.parametrize("verbose", [1, 2])
def test_traceback_of_previous_task_failed_is_not_shown(runner, tmp_path, verbose):
    source = """
    import pytask

    @pytask.mark.produces("in.txt")
    def task_first(): raise ValueError

    @pytask.mark.depends_on("in.txt")
    def task_second(): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--verbose", str(verbose)])

    assert result.exit_code == ExitCode.FAILED
    assert ("Task task_example.py::task_second failed" in result.output) is (
        verbose == 2
    )


@pytest.mark.end_to_end()
def test_that_dynamically_creates_tasks_are_captured(runner, tmp_path):
    source = """
    _DEFINITION = '''
    def task_example():
        pass
    '''

    exec(_DEFINITION)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example" in result.output
    assert "Collected 1 task" in result.output


def test_task_executed_with_force_although_unchanged(tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    session = main({"paths": tmp_path})
    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS
    session = main({"paths": tmp_path, "force": True})
    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS


@pytest.mark.end_to_end()
def test_task_executed_with_force_although_unchanged_runner(runner, tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task" in result.output
    assert "1  Succeeded" in result.output

    result = runner.invoke(cli, [tmp_path.as_posix(), "--force"])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_task_is_not_reexecuted_when_modification_changed_file_not(runner, tmp_path):
    tmp_path.joinpath("task_example.py").write_text("def task_example(): pass")
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output

    tmp_path.joinpath("task_example.py").write_text("def task_example(): pass")
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Skipped" in result.output
