from unittest.mock import MagicMock


def test_registry_views_share_single_actor_state():
    from gateway.session_actor import SessionActorRegistry

    registry = SessionActorRegistry()
    agent = MagicMock()

    registry.running_agents["session-1"] = agent
    registry.running_started_at["session-1"] = 12.5
    registry.busy_ack_ts["session-1"] = 99.0
    registry.pending_approvals["session-1"] = {"command": "rm -rf /tmp/x"}
    registry.update_prompt_pending["session-1"] = True
    registry.pending_messages["session-1"] = "follow-up"
    registry.run_generations["session-1"] = 7

    actor = registry.ensure("session-1")
    assert actor.running_agent is agent
    assert actor.running_started_at == 12.5
    assert actor.busy_ack_ts == 99.0
    assert actor.pending_approval == {"command": "rm -rf /tmp/x"}
    assert actor.update_prompt_pending is True
    assert actor.pending_message == "follow-up"
    assert actor.run_generation == 7


def test_clear_running_state_only_clears_runtime_fields():
    from gateway.session_actor import SessionActorRegistry

    registry = SessionActorRegistry()
    registry.running_agents["session-1"] = MagicMock()
    registry.running_started_at["session-1"] = 12.5
    registry.busy_ack_ts["session-1"] = 99.0
    registry.pending_approvals["session-1"] = {"command": "ls"}
    registry.update_prompt_pending["session-1"] = True
    registry.pending_messages["session-1"] = "follow-up"
    registry.run_generations["session-1"] = 7

    registry.clear_running_state("session-1")

    assert "session-1" not in registry.running_agents
    assert "session-1" not in registry.running_started_at
    assert "session-1" not in registry.busy_ack_ts
    assert registry.pending_approvals["session-1"] == {"command": "ls"}
    assert registry.update_prompt_pending["session-1"] is True
    assert registry.pending_messages["session-1"] == "follow-up"
    assert registry.run_generations["session-1"] == 7
