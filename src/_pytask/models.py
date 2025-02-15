"""This module contains code on models, containers and there like."""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

if TYPE_CHECKING:
    from _pytask.mark import Mark


@define
class CollectionMetadata:
    """A class for carrying metadata from functions to tasks."""

    id_: str | None = None
    """The id for a single parametrization."""
    kwargs: dict[str, Any] = field(factory=dict)
    """Contains kwargs which are necessary for the task function on execution."""
    markers: list[Mark] = field(factory=list)
    """Contains the markers of the function."""
    name: str | None = None
    """The name of the task function."""
