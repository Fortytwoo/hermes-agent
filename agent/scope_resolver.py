"""Resolve enterprise scope and routing address from runtime inputs."""

from __future__ import annotations

import os

from agent.scope import EnterpriseScope, SessionAddress


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    return str(value)


def resolve_enterprise_scope(*, overrides: dict | None = None) -> EnterpriseScope:
    overrides = overrides or {}
    return EnterpriseScope(
        tenant_id=str(
            overrides.get("tenant_id")
            or os.getenv("HERMES_SCOPE_TENANT_ID", "")
        ),
        workspace_id=str(
            overrides.get("workspace_id")
            or os.getenv("HERMES_SCOPE_WORKSPACE_ID", "")
        ),
        agent_id=str(
            overrides.get("agent_id")
            or os.getenv("HERMES_SCOPE_AGENT_ID", "main")
        ),
    )


def resolve_session_address(source) -> SessionAddress:
    platform = _stringify(getattr(source, "platform", ""))
    source_name = _stringify(getattr(source, "source", "")) or platform
    return SessionAddress(
        source=source_name,
        platform=platform,
        chat_type=_stringify(getattr(source, "chat_type", "")),
        chat_id=_stringify(getattr(source, "chat_id", "")),
        thread_id=_stringify(getattr(source, "thread_id", "")),
        user_id=_stringify(getattr(source, "user_id", "")),
    )


def resolve_session_boundary(
    *,
    source=None,
    overrides: dict | None = None,
) -> tuple[EnterpriseScope, SessionAddress]:
    return resolve_enterprise_scope(overrides=overrides), resolve_session_address(source)
