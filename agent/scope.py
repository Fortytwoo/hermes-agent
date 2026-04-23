"""Typed enterprise and routing boundaries for gateway sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


_SCOPED_KEY_PREFIX = ("agent", "scope", "v1")
_REQUIRED_SCOPED_KEYS = (
    "tenant",
    "workspace",
    "agent",
    "platform",
    "chat_type",
    "chat",
)


def _decode_component(value: str) -> str:
    return "" if value == "_" else value


@dataclass(frozen=True)
class EnterpriseScope:
    tenant_id: str = ""
    workspace_id: str = ""
    agent_id: str = "main"

    def is_scoped(self) -> bool:
        return bool(self.tenant_id or self.workspace_id or self.agent_id != "main")


@dataclass(frozen=True)
class SessionAddress:
    source: str = ""
    platform: str = ""
    chat_type: str = ""
    chat_id: str = ""
    thread_id: str = ""
    user_id: str = ""


@dataclass(frozen=True)
class SessionIdentity:
    session_key: str = ""
    session_id: str = ""


def scope_to_dict(scope: EnterpriseScope) -> dict[str, str]:
    return {
        "tenant_id": scope.tenant_id,
        "workspace_id": scope.workspace_id,
        "agent_id": scope.agent_id,
    }


def scope_from_dict(data: Optional[dict[str, str]]) -> EnterpriseScope:
    data = data or {}
    return EnterpriseScope(
        tenant_id=str(data.get("tenant_id") or ""),
        workspace_id=str(data.get("workspace_id") or ""),
        agent_id=str(data.get("agent_id") or "main"),
    )


def address_to_dict(address: SessionAddress) -> dict[str, str]:
    return {
        "source": address.source,
        "platform": address.platform,
        "chat_type": address.chat_type,
        "chat_id": address.chat_id,
        "thread_id": address.thread_id,
        "user_id": address.user_id,
    }


def address_from_dict(data: Optional[dict[str, str]]) -> SessionAddress:
    data = data or {}
    return SessionAddress(
        source=str(data.get("source") or ""),
        platform=str(data.get("platform") or ""),
        chat_type=str(data.get("chat_type") or ""),
        chat_id=str(data.get("chat_id") or ""),
        thread_id=str(data.get("thread_id") or ""),
        user_id=str(data.get("user_id") or ""),
    )


def identity_to_dict(identity: SessionIdentity) -> dict[str, str]:
    return {
        "session_key": identity.session_key,
        "session_id": identity.session_id,
    }


def identity_from_dict(data: Optional[dict[str, str]]) -> SessionIdentity:
    data = data or {}
    return SessionIdentity(
        session_key=str(data.get("session_key") or ""),
        session_id=str(data.get("session_id") or ""),
    )


def parse_scoped_session_key(
    session_key: str,
) -> tuple[EnterpriseScope, SessionAddress] | None:
    parts = session_key.split(":")
    if len(parts) < len(_SCOPED_KEY_PREFIX) + (len(_REQUIRED_SCOPED_KEYS) * 2):
        return None
    if tuple(parts[:3]) != _SCOPED_KEY_PREFIX:
        return None

    remainder = parts[3:]
    if len(remainder) % 2 != 0:
        return None

    tagged: dict[str, str] = {}
    for idx in range(0, len(remainder), 2):
        key = remainder[idx]
        value = remainder[idx + 1]
        tagged[key] = value

    if any(key not in tagged for key in _REQUIRED_SCOPED_KEYS):
        return None

    unknown_keys = set(tagged) - (set(_REQUIRED_SCOPED_KEYS) | {"thread", "user"})
    if unknown_keys:
        return None

    enterprise_scope = EnterpriseScope(
        tenant_id=_decode_component(tagged["tenant"]),
        workspace_id=_decode_component(tagged["workspace"]),
        agent_id=_decode_component(tagged["agent"]) or "main",
    )
    session_address = SessionAddress(
        platform=_decode_component(tagged["platform"]),
        chat_type=_decode_component(tagged["chat_type"]),
        chat_id=_decode_component(tagged["chat"]),
        thread_id=_decode_component(tagged.get("thread", "")),
        user_id=_decode_component(tagged.get("user", "")),
    )
    return enterprise_scope, session_address
