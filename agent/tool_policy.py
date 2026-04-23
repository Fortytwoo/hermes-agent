"""Runtime tool visibility and authorization policy helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Set


@dataclass(frozen=True)
class ToolPolicy:
    """Separate what a session can see from what it may execute."""

    visible_tool_names: Optional[Set[str]] = None
    authorized_tool_names: Optional[Set[str]] = None

    def filter_visible(self, tool_names: Iterable[str]) -> Set[str]:
        names = set(tool_names)
        if self.visible_tool_names is None:
            return names
        return names & set(self.visible_tool_names)

    def filter_authorized(self, tool_names: Iterable[str]) -> Set[str]:
        names = set(tool_names)
        if self.authorized_tool_names is None:
            return names
        return names & set(self.authorized_tool_names)

    def is_authorized(self, tool_name: str) -> bool:
        if self.authorized_tool_names is None:
            return True
        return tool_name in self.authorized_tool_names
