"""Regression tests for memory-tool import fallbacks."""

import builtins
import importlib
import sys

from agent.memory_backend import MemoryBackend
from agent.scope import EnterpriseScope
from tools.registry import registry


def test_memory_tool_imports_without_fcntl(monkeypatch, tmp_path):
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "fcntl":
            raise ImportError("simulated missing fcntl")
        return original_import(name, globals, locals, fromlist, level)

    registry.deregister("memory")
    monkeypatch.delitem(sys.modules, "tools.memory_tool", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    memory_tool = importlib.import_module("tools.memory_tool")
    backend = MemoryBackend(tmp_path)
    store = memory_tool.MemoryStore(
        memory_char_limit=200,
        user_char_limit=200,
        enterprise_scope=EnterpriseScope(
            tenant_id="acme",
            workspace_id="ops",
            agent_id="planner",
        ),
        user_id="alice",
        backend=backend,
    )
    store.load_from_disk()
    result = store.add("memory", "fact learned during import fallback test")

    assert memory_tool.fcntl is None
    assert registry.get_entry("memory") is not None
    assert result["success"] is True
    assert store._path_for("memory").exists()
    assert store._path_for("memory") != tmp_path / "MEMORY.md"
