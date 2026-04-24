from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass
from typing import Any


@dataclass
class SessionActor:
    session_key: str
    running_agent: Any = None
    running_started_at: float | None = None
    busy_ack_ts: float | None = None
    pending_message: str | None = None
    pending_approval: dict[str, Any] | None = None
    update_prompt_pending: bool = False
    run_generation: int = 0

    def is_empty(self) -> bool:
        return (
            self.running_agent is None
            and self.running_started_at is None
            and self.busy_ack_ts is None
            and self.pending_message is None
            and self.pending_approval is None
            and not self.update_prompt_pending
            and self.run_generation == 0
        )


class _ActorAttributeMapping(MutableMapping[str, Any]):
    def __init__(
        self,
        registry: "SessionActorRegistry",
        *,
        attr_name: str,
        default_value: Any,
        is_present,
    ) -> None:
        self._registry = registry
        self._attr_name = attr_name
        self._default_value = default_value
        self._is_present = is_present

    def __getitem__(self, session_key: str) -> Any:
        actor = self._registry.get(session_key)
        if actor is None:
            raise KeyError(session_key)
        value = getattr(actor, self._attr_name)
        if not self._is_present(value):
            raise KeyError(session_key)
        return value

    def __setitem__(self, session_key: str, value: Any) -> None:
        actor = self._registry.ensure(session_key)
        setattr(actor, self._attr_name, value)
        self._registry.prune(session_key)

    def __delitem__(self, session_key: str) -> None:
        actor = self._registry.get(session_key)
        if actor is None:
            raise KeyError(session_key)
        setattr(actor, self._attr_name, self._default_value)
        self._registry.prune(session_key)

    def __iter__(self) -> Iterator[str]:
        for session_key, actor in self._registry._actors.items():
            value = getattr(actor, self._attr_name)
            if self._is_present(value):
                yield session_key

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def clear(self) -> None:
        for session_key in list(self):
            actor = self._registry.get(session_key)
            if actor is None:
                continue
            setattr(actor, self._attr_name, self._default_value)
            self._registry.prune(session_key)


class SessionActorRegistry:
    def __init__(self) -> None:
        self._actors: dict[str, SessionActor] = {}
        self.running_agents = _ActorAttributeMapping(
            self,
            attr_name="running_agent",
            default_value=None,
            is_present=lambda value: value is not None,
        )
        self.running_started_at = _ActorAttributeMapping(
            self,
            attr_name="running_started_at",
            default_value=None,
            is_present=lambda value: value is not None,
        )
        self.busy_ack_ts = _ActorAttributeMapping(
            self,
            attr_name="busy_ack_ts",
            default_value=None,
            is_present=lambda value: value is not None,
        )
        self.pending_messages = _ActorAttributeMapping(
            self,
            attr_name="pending_message",
            default_value=None,
            is_present=lambda value: value is not None,
        )
        self.pending_approvals = _ActorAttributeMapping(
            self,
            attr_name="pending_approval",
            default_value=None,
            is_present=lambda value: value is not None,
        )
        self.update_prompt_pending = _ActorAttributeMapping(
            self,
            attr_name="update_prompt_pending",
            default_value=False,
            is_present=bool,
        )
        self.run_generations = _ActorAttributeMapping(
            self,
            attr_name="run_generation",
            default_value=0,
            is_present=lambda value: int(value or 0) != 0,
        )

    def get(self, session_key: str) -> SessionActor | None:
        return self._actors.get(session_key)

    def ensure(self, session_key: str) -> SessionActor:
        actor = self._actors.get(session_key)
        if actor is None:
            actor = SessionActor(session_key=session_key)
            self._actors[session_key] = actor
        return actor

    def prune(self, session_key: str) -> None:
        actor = self._actors.get(session_key)
        if actor is not None and actor.is_empty():
            self._actors.pop(session_key, None)

    def clear_running_state(self, session_key: str) -> None:
        actor = self._actors.get(session_key)
        if actor is None:
            return
        actor.running_agent = None
        actor.running_started_at = None
        actor.busy_ack_ts = None
        self.prune(session_key)

    def snapshot_running_agents(self, pending_sentinel: Any) -> dict[str, Any]:
        return {
            session_key: actor.running_agent
            for session_key, actor in self._actors.items()
            if actor.running_agent is not None and actor.running_agent is not pending_sentinel
        }

    def running_count(self) -> int:
        return len(self.running_agents)
