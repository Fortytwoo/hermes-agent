"""Enterprise-aware runtime context helpers."""

from __future__ import annotations

from typing import Any, Dict, List

from agent.context_engine import ContextEngine
from agent.context_pack import ContextPack, RuntimeContextMetadata
from agent.scope import EnterpriseScope, SessionAddress


class EnterpriseContextEngine(ContextEngine):
    """Minimal context engine that packages enterprise runtime metadata."""

    def __init__(self) -> None:
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0
        self.threshold_tokens = 0
        self.context_length = 0
        self.compression_count = 0

    @property
    def name(self) -> str:
        return "enterprise"

    def update_from_response(self, usage: Dict[str, Any]) -> None:
        self.last_prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        self.last_completion_tokens = int(usage.get("completion_tokens", 0) or 0)
        self.last_total_tokens = int(usage.get("total_tokens", 0) or 0)

    def should_compress(self, prompt_tokens: int = None) -> bool:
        return False

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int = None,
    ) -> List[Dict[str, Any]]:
        return messages

    def build_context_pack(
        self,
        enterprise_scope: EnterpriseScope = None,
        session_address: SessionAddress = None,
        user_id: str = "",
        platform: str = "",
        session_id: str = "",
        **_: Any,
    ) -> ContextPack | None:
        scope = enterprise_scope or EnterpriseScope()
        address = session_address or SessionAddress()
        has_enterprise_runtime = scope.is_scoped() or any(
            [
                address.platform,
                address.chat_type,
                address.chat_id,
                address.thread_id,
                address.user_id,
                user_id,
            ]
        )
        if not has_enterprise_runtime:
            return None
        return ContextPack(
            runtime=RuntimeContextMetadata(
                enterprise_scope=scope,
                session_address=address,
                user_id=user_id,
                platform=platform,
                session_id=session_id,
            )
        )
