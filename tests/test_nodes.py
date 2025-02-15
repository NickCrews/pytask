from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.shared import reduce_node_name
from pytask import FilePathNode


_ROOT = Path.cwd()


@pytest.mark.integration()
@pytest.mark.parametrize(
    ("node", "paths", "expectation", "expected"),
    [
        pytest.param(
            FilePathNode.from_path(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("alternative_src")],
            does_not_raise(),
            "pytask/src/module.py",
            id="Common path found for FilePathNode not in 'paths' and 'paths'",
        ),
        pytest.param(
            FilePathNode.from_path(_ROOT.joinpath("top/src/module.py")),
            [_ROOT.joinpath("top/src")],
            does_not_raise(),
            "src/module.py",
            id="make filepathnode relative to 'paths'.",
        ),
    ],
)
def test_reduce_node_name(node, paths, expectation, expected):
    with expectation:
        result = reduce_node_name(node, paths)
        assert result == expected
