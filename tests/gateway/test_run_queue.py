import asyncio
from unittest.mock import MagicMock

import pytest


@pytest.mark.asyncio
async def test_run_queue_drains_until_running_sessions_finish():
    from gateway.run_queue import GatewayRunQueue

    queue = GatewayRunQueue()
    queue.running_agents["a"] = MagicMock()
    queue.running_agents["b"] = MagicMock()

    async def finish():
        await asyncio.sleep(0.05)
        del queue.running_agents["a"]
        await asyncio.sleep(0.05)
        del queue.running_agents["b"]

    task = asyncio.create_task(finish())
    updates = []
    snapshot, timed_out = await queue.drain_active(
        timeout=1.0,
        update_status=lambda: updates.append(queue.running_count()),
        pending_sentinel=object(),
    )
    await task

    assert timed_out is False
    assert set(snapshot) == {"a", "b"}
    assert updates
    assert queue.running_count() == 0


def test_run_queue_interrupts_non_sentinel_agents():
    from gateway.run_queue import GatewayRunQueue

    queue = GatewayRunQueue()
    sentinel = object()
    live_agent = MagicMock()
    queue.running_agents["live"] = live_agent
    queue.running_agents["pending"] = sentinel

    queue.interrupt_running_agents("Gateway shutting down", pending_sentinel=sentinel)

    live_agent.interrupt.assert_called_once_with("Gateway shutting down")
