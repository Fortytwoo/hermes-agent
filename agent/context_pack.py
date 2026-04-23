"""Typed runtime context payloads for enterprise-aware sessions."""

from __future__ import annotations

from dataclasses import dataclass

from agent.scope import EnterpriseScope, SessionAddress


@dataclass(frozen=True)
class RuntimeContextMetadata:
    enterprise_scope: EnterpriseScope
    session_address: SessionAddress
    user_id: str = ""
    platform: str = ""
    session_id: str = ""


@dataclass(frozen=True)
class ContextPack:
    runtime: RuntimeContextMetadata

    def render(self) -> str:
        """Render a deterministic, fenced runtime context block."""
        scope = self.runtime.enterprise_scope
        address = self.runtime.session_address
        lines: list[str] = []

        if scope.tenant_id:
            lines.append(f"tenant_id: {scope.tenant_id}")
        if scope.workspace_id:
            lines.append(f"workspace_id: {scope.workspace_id}")
        if scope.agent_id:
            lines.append(f"agent_id: {scope.agent_id}")

        platform = self.runtime.platform or address.platform
        if platform:
            lines.append(f"platform: {platform}")
        if address.chat_type:
            lines.append(f"chat_type: {address.chat_type}")
        if address.chat_id:
            lines.append(f"chat_id: {address.chat_id}")
        if address.thread_id:
            lines.append(f"thread_id: {address.thread_id}")

        user_id = self.runtime.user_id or address.user_id
        if user_id:
            lines.append(f"user_id: {user_id}")
        if self.runtime.session_id:
            lines.append(f"session_id: {self.runtime.session_id}")

        if not lines:
            return ""
        return "```runtime_context\n" + "\n".join(lines) + "\n```"
