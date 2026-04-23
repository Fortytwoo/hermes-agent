"""Tests for typed enterprise and session boundary helpers."""

import importlib

from gateway.config import Platform
from gateway.session import SessionSource


class TestEnterpriseScope:
    def test_defaults_are_unscoped(self):
        scope_mod = importlib.import_module("agent.scope")

        scope = scope_mod.EnterpriseScope()

        assert scope.tenant_id == ""
        assert scope.workspace_id == ""
        assert scope.agent_id == "main"
        assert not scope.is_scoped()

    def test_non_default_agent_id_marks_scope(self):
        scope_mod = importlib.import_module("agent.scope")

        scope = scope_mod.EnterpriseScope(agent_id="planner")

        assert scope.is_scoped()


class TestScopedSessionKeyParsing:
    def test_parse_scoped_session_key_round_trips_tagged_format(self):
        scope_mod = importlib.import_module("agent.scope")

        parsed = scope_mod.parse_scoped_session_key(
            "agent:scope:v1:tenant:acme:workspace:ops:agent:planner:"
            "platform:telegram:chat_type:group:chat:-100:thread:42:user:alice"
        )

        assert parsed == (
            scope_mod.EnterpriseScope(
                tenant_id="acme",
                workspace_id="ops",
                agent_id="planner",
            ),
            scope_mod.SessionAddress(
                platform="telegram",
                chat_type="group",
                chat_id="-100",
                thread_id="42",
                user_id="alice",
            ),
        )

    def test_parse_scoped_session_key_returns_none_for_malformed_input(self):
        scope_mod = importlib.import_module("agent.scope")

        assert scope_mod.parse_scoped_session_key(
            "agent:scope:v1:tenant:acme:workspace:ops"
        ) is None


class TestScopeResolver:
    def test_explicit_overrides_beat_env(self, monkeypatch):
        scope_mod = importlib.import_module("agent.scope")
        resolver_mod = importlib.import_module("agent.scope_resolver")

        monkeypatch.setenv("HERMES_SCOPE_TENANT_ID", "env-tenant")
        monkeypatch.setenv("HERMES_SCOPE_WORKSPACE_ID", "env-workspace")
        monkeypatch.setenv("HERMES_SCOPE_AGENT_ID", "env-agent")

        scope = resolver_mod.resolve_enterprise_scope(
            overrides={
                "tenant_id": "override-tenant",
                "workspace_id": "override-workspace",
                "agent_id": "override-agent",
            }
        )

        assert scope == scope_mod.EnterpriseScope(
            tenant_id="override-tenant",
            workspace_id="override-workspace",
            agent_id="override-agent",
        )

    def test_env_beats_empty_default(self, monkeypatch):
        scope_mod = importlib.import_module("agent.scope")
        resolver_mod = importlib.import_module("agent.scope_resolver")

        monkeypatch.setenv("HERMES_SCOPE_TENANT_ID", "env-tenant")
        monkeypatch.setenv("HERMES_SCOPE_WORKSPACE_ID", "env-workspace")
        monkeypatch.setenv("HERMES_SCOPE_AGENT_ID", "env-agent")

        scope = resolver_mod.resolve_enterprise_scope()

        assert scope == scope_mod.EnterpriseScope(
            tenant_id="env-tenant",
            workspace_id="env-workspace",
            agent_id="env-agent",
        )

    def test_resolve_session_address_maps_session_source_losslessly(self):
        scope_mod = importlib.import_module("agent.scope")
        resolver_mod = importlib.import_module("agent.scope_resolver")
        source = SessionSource(
            platform=Platform.TELEGRAM,
            chat_id="-1002285219667",
            chat_type="group",
            user_id="alice",
            thread_id="17585",
        )

        address = resolver_mod.resolve_session_address(source)

        assert address == scope_mod.SessionAddress(
            source="telegram",
            platform="telegram",
            chat_type="group",
            chat_id="-1002285219667",
            thread_id="17585",
            user_id="alice",
        )
