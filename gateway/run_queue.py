from __future__ import annotations

import asyncio
from typing import Any, Callable

from gateway.session_actor import SessionActorRegistry


class GatewayRunQueue:
    def __init__(self, *, actors: SessionActorRegistry | None = None) -> None:
        self.actors = actors or SessionActorRegistry()
        self.running_agents = self.actors.running_agents
        self.running_agents_ts = self.actors.running_started_at
        self.pending_messages = self.actors.pending_messages
        self.busy_ack_ts = self.actors.busy_ack_ts
        self.pending_approvals = self.actors.pending_approvals
        self.update_prompt_pending = self.actors.update_prompt_pending
        self.run_generations = self.actors.run_generations

    def running_count(self) -> int:
        return self.actors.running_count()

    def snapshot_running_agents(self, pending_sentinel: Any) -> dict[str, Any]:
        return self.actors.snapshot_running_agents(pending_sentinel)

    async def drain_active(
        self,
        *,
        timeout: float,
        update_status: Callable[[], None],
        pending_sentinel: Any,
    ) -> tuple[dict[str, Any], bool]:
        snapshot = self.snapshot_running_agents(pending_sentinel)
        last_active_count = self.running_count()
        last_status_at = 0.0

        def maybe_update_status(*, force: bool = False) -> None:
            nonlocal last_active_count, last_status_at
            now = asyncio.get_running_loop().time()
            active_count = self.running_count()
            if force or active_count != last_active_count or (now - last_status_at) >= 1.0:
                update_status()
                last_active_count = active_count
                last_status_at = now

        if not self.running_agents:
            maybe_update_status(force=True)
            return snapshot, False

        maybe_update_status(force=True)
        if timeout <= 0:
            return snapshot, True

        deadline = asyncio.get_running_loop().time() + timeout
        while self.running_agents and asyncio.get_running_loop().time() < deadline:
            maybe_update_status()
            await asyncio.sleep(0.1)

        timed_out = bool(self.running_agents)
        maybe_update_status(force=True)
        return snapshot, timed_out

    def interrupt_running_agents(self, reason: str, *, pending_sentinel: Any) -> None:
        for _, agent in list(self.running_agents.items()):
            if agent is pending_sentinel:
                continue
            try:
                agent.interrupt(reason)
            except Exception:
                pass

    def release_running_state(self, session_key: str) -> None:
        self.actors.clear_running_state(session_key)

    def begin_run_generation(self, session_key: str) -> int:
        actor = self.actors.ensure(session_key)
        actor.run_generation = int(actor.run_generation) + 1
        return actor.run_generation

    def is_run_generation_current(self, session_key: str, generation: int) -> bool:
        actor = self.actors.get(session_key)
        current = actor.run_generation if actor is not None else 0
        return int(current) == int(generation)

    def clear_all_runtime_state(self) -> None:
        self.running_agents.clear()
        self.running_agents_ts.clear()
        self.pending_messages.clear()
        self.busy_ack_ts.clear()
        self.pending_approvals.clear()
        self.update_prompt_pending.clear()
        self.run_generations.clear()
