"""Namespace rules for scoped built-in memory files."""

from __future__ import annotations

from typing import Optional, Tuple

from agent.scope import EnterpriseScope


def normalize_scope(scope: Optional[EnterpriseScope]) -> EnterpriseScope:
    """Return a concrete scope object for namespace decisions."""
    return scope if isinstance(scope, EnterpriseScope) else EnterpriseScope()


def is_scoped(scope: Optional[EnterpriseScope]) -> bool:
    """True when memory should live under a scoped namespace."""
    return normalize_scope(scope).is_scoped()


def namespace_for_target(
    target: str,
    *,
    scope: Optional[EnterpriseScope],
    user_id: str,
) -> Optional[Tuple[str, ...]]:
    """Return namespace path segments for a memory target or None for legacy."""
    normalized_scope = normalize_scope(scope)
    normalized_user = str(user_id or "").strip()

    if not is_scoped(normalized_scope):
        return None

    base = (
        "scoped",
        "tenants",
        normalized_scope.tenant_id or "",
        "workspaces",
        normalized_scope.workspace_id or "",
        "agents",
        normalized_scope.agent_id or "main",
    )
    if target == "memory":
        return base
    if target == "user":
        if not normalized_user:
            return None
        return base + ("users", normalized_user)
    raise ValueError(f"Unknown memory target: {target}")
