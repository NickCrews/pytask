"""This module contains helper functions for the configuration."""
from __future__ import annotations

from enum import Enum
from typing import Callable, Any

import attrs


def parse_click_choice(
    name: str, enum_: type[Enum]
) -> Callable[[Enum | str | None], Enum | None]:
    """Validate the passed options for a :class:`click.Choice` option."""
    value_to_name = {enum_[name].value: name for name in enum_.__members__}

    def _parse(x: Enum | str | None) -> Enum | None:
        if x in [None, "None", "none"]:
            out = None
        elif isinstance(x, str) and x in value_to_name:
            out = enum_[value_to_name[x]]
        else:
            raise ValueError(f"'{name}' can only be one of {list(value_to_name)}.")
        return out

    return _parse


class ShowCapture(Enum):
    NO = "no"
    STDOUT = "stdout"
    STDERR = "stderr"
    ALL = "all"


def merge_settings(
    paths: tuple[str, ...], main_settings: Any, command_settings: Any, command: str
) -> Any:
    """Merge main settings and command-specific settings."""
    main_dict = attrs.asdict(main_settings)
    command_dict = attrs.asdict(command_settings)

    duplicates = set(main_dict) & set(command_dict)
    if duplicates:
        raise ValueError(f"There are duplicated settings: {duplicates}")

    settings_dict = {"paths": paths, "command": command, **main_dict, **command_dict}
    settings = {k: settings_dict[k] for k in sorted(settings_dict)}
    settings = {k: None if v == "None" else v for k, v in settings.items()}

    return settings
