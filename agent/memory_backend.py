"""Filesystem path resolution and safe encoding for scoped memory."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from agent.memory_namespace import namespace_for_target
from agent.scope import EnterpriseScope


class MemoryBackend:
    """Resolve durable memory paths under a profile-scoped root directory."""

    def __init__(self, root: Path | str):
        self.root = Path(root)

    @staticmethod
    def encode_component(value: str) -> str:
        """Encode a dynamic namespace value into a Windows-safe path segment."""
        raw = str(value or "").encode("utf-8")
        if not raw:
            return "v-_"
        token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        return f"v-{token}"

    def path_for(
        self,
        target: str,
        *,
        scope: Optional[EnterpriseScope],
        user_id: str,
    ) -> Path:
        """Resolve the on-disk path for a memory target."""
        namespace = namespace_for_target(target, scope=scope, user_id=user_id)
        filename = "USER.md" if target == "user" else "MEMORY.md"
        if namespace is None:
            return self.root / filename

        path = self.root / "scoped"
        path = path / "tenants" / self.encode_component(namespace[2])
        path = path / "workspaces" / self.encode_component(namespace[4])
        path = path / "agents" / self.encode_component(namespace[6])
        if target == "user":
            path = path / "users" / self.encode_component(namespace[8])
        return path / filename
