# Enterprise Scope Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce enterprise-grade tenant/workspace/agent isolation into Hermes without breaking prompt caching, legacy gateway routing, or the current SQLite-backed session model.

**Architecture:** Replace the earlier oversized `AgentScope` draft with three typed boundaries: `EnterpriseScope` for tenant/workspace/agent isolation, `SessionAddress` for platform/chat/thread/user routing, and `SessionIdentity` for session bookkeeping. PR1 now ships those typed models, dual-stack session-key parsing, additive SQLite persistence, and runtime threading through gateway plus `AIAgent`, while deliberately keeping live session-key generation on legacy `agent:main:...` during rollout. Keep dynamic enterprise context additive to the current user message, tighten isolation one subsystem at a time, and defer scoped search/memory/skills policy changes to later PRs.

**Tech Stack:** Python, dataclasses, gateway session routing, SQLite migrations in `hermes_state.py`, existing tool dispatch in `run_agent.py`, current `scripts/run_tests.sh` test wrapper.

---

## Constraints and non-goals

- Preserve prompt caching. Do not rebuild the system prompt mid-session.
- Keep legacy session-key parsing working while scoped keys are introduced.
- Do not replace SQLite in the first milestone.
- Do not rewrite `AIAgent` in the first milestone.
- Keep enterprise dynamic context on the existing user-message injection path in `run_agent.py`.
- All persistent paths must remain profile-safe and use `get_hermes_home()`.
- Preferred verification path is `scripts/run_tests.sh`; the current Windows environment still has a CRLF issue in that wrapper, so CI-parity hermetic `pytest` commands are an acceptable temporary fallback for this rollout record.

## Current PR1 status

- Status: PR1 scope foundation is implemented in `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation` on branch `codex/pr1-scope-foundation`.
- Shipped in code: `EnterpriseScope` / `SessionAddress` / `SessionIdentity`, typed metadata on `SessionEntry` and `SessionContext`, dual-stack `_parse_session_key()` compatibility, SQLite v7 scope metadata, and `AIAgent` startup/recovery/compression propagation.
- Deliberately not switched: live session-key generation still emits legacy `agent:main:...`; scoped keys are parser/test/future-cutover groundwork only.
- Verification record: the consolidated PR1 suite passed as a wrapper-equivalent hermetic `pytest` run on Windows because `scripts/run_tests.sh` currently fails in this environment due to CRLF handling.
- Verification result: `325 passed`.

## Boundary review summary

The first draft was directionally correct but one boundary was still too blurry: it overloaded one `AgentScope` object with both enterprise-isolation data and gateway-routing data. That coupling would make `memory`, `session_search`, and `skills` accidentally depend on platform/chat routing details, while gateway code would keep absorbing tenant/workspace concerns.

Milestone one should separate the model into three concepts:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class EnterpriseScope:
    tenant_id: str = ""
    workspace_id: str = ""
    agent_id: str = "main"


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
```

Propagation path:

1. Gateway or CLI message source -> `SessionAddress`
2. Enterprise metadata/config/adapter overrides -> `EnterpriseScope`
3. Session store combines `EnterpriseScope` + `SessionAddress` into `SessionIdentity`
4. `SessionEntry` and `SessionContext` carry both `EnterpriseScope` and `SessionAddress`
5. `SessionDB.sessions` persists both, but isolation queries are driven by `EnterpriseScope`
6. `AIAgent.enterprise_scope` flows into tool dispatch (`session_search`, `memory`, `skills`)

## Session-key migration rule

Legacy keys remain valid:

```text
agent:main:{platform}:{chat_type}:{chat_id}[:{extra}...]
```

Recommended new tagged format:

```text
agent:scope:v1:tenant:{tenant}:workspace:{workspace}:agent:{agent}:platform:{platform}:chat_type:{chat_type}:chat:{chat_id}[:thread:{thread_id}][:user:{user_id}]
```

Migration rule:

- Parser must support both formats.
- Builder remains legacy by default until the scoped path is proven in tests.
- New format should be built from `EnterpriseScope` plus `SessionAddress`, not from one overstuffed scope object.
- Session keys are a transport/session-identity artifact. They must not remain the authority for enterprise isolation after PR1 lands.

## Authority rules

- `EnterpriseScope` is the authority for tenant/workspace/agent isolation.
- `SessionAddress` is the authority for routing, notifications, reply targeting, and platform context.
- `SessionIdentity` is the authority for active session lookup in memory and session-store bookkeeping.
- `gateway/run.py::_parse_session_key()` becomes legacy fallback only. After PR1, persisted `SessionEntry`/SQLite metadata is the primary source of truth.
- Tool layers (`session_search`, `memory`, `skills`) receive `EnterpriseScope` from runtime injection and must not derive it from session-key strings.

## Inheritance rules

- Delegation child sessions, compression continuations, and resumed sessions must inherit the root session's `EnterpriseScope` unchanged.
- `parent_session_id` chains must never cross `EnterpriseScope` boundaries.
- `SessionAddress` for internal child sessions may be copied from the parent when needed for display or routing fallback, but child-session creation must not invent a different tenant/workspace/agent.
- `current_session_id` lineage exclusion in `session_search` must only walk within the same `EnterpriseScope`.

## Repository map for this rollout

- `agent/scope.py` - `EnterpriseScope`, `SessionAddress`, `SessionIdentity`, and serialization helpers
- `agent/scope_resolver.py` - runtime and gateway source -> resolved enterprise scope plus session address
- `gateway/session.py` - session keys, `SessionEntry`, `SessionContext`, store integration
- `gateway/run.py` - key parsing, background notifications, fallback route reconstruction
- `hermes_state.py` - SQLite schema and scoped queries
- `run_agent.py` - runtime enterprise-scope plumbing and tool dispatch injection
- `tools/session_search_tool.py` - scoped history retrieval
- `tools/memory_tool.py` - namespace-aware file backend while preserving frozen snapshots
- `tools/skills_tool.py` - scope-based skill visibility on top of current platform/disabled filtering

---

### Task 1: PR1 Scope Foundation

**Files:**
- Create: `agent/scope.py`
- Create: `agent/scope_resolver.py`
- Modify: `gateway/session.py:143-190,333-425,491-547,626-632,1241-1271`
- Modify: `gateway/run.py:544-552,1690-1697,8293-8301`
- Modify: `hermes_state.py:41-69,298-306,356-379`
- Modify: `run_agent.py`
- Test: `tests/agent/test_scope.py`
- Test: `tests/gateway/test_session.py`
- Test: `tests/gateway/test_background_process_notifications.py`
- Test: `tests/gateway/test_async_memory_flush.py`
- Test: `tests/gateway/test_agent_cache.py`
- Test: `tests/run_agent/test_compression_persistence.py`
- Test: `tests/test_hermes_state.py`

Detailed execution companion: `docs/superpowers/plans/2026-04-22-pr1-scope-foundation-detail.md`

- [x] **Step 1: Add separate enterprise, routing, and identity models**

Create `agent/scope.py` with small frozen dataclasses plus helpers for normalization and emptiness checks.

```python
from dataclasses import dataclass


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
```

- [x] **Step 2: Add one resolver that returns both isolation and routing data**

Create `agent/scope_resolver.py` and make it the only place that converts runtime or gateway metadata into `EnterpriseScope` and `SessionAddress`.

```python
from agent.scope import EnterpriseScope, SessionAddress


def resolve_session_boundary(*, source=None, overrides=None) -> tuple[EnterpriseScope, SessionAddress]:
    overrides = overrides or {}
    enterprise_scope = EnterpriseScope(
        tenant_id=str(overrides.get("tenant_id") or os.getenv("HERMES_SCOPE_TENANT_ID", "")),
        workspace_id=str(overrides.get("workspace_id") or os.getenv("HERMES_SCOPE_WORKSPACE_ID", "")),
        agent_id=str(overrides.get("agent_id") or os.getenv("HERMES_SCOPE_AGENT_ID", "main")),
    )
    address = SessionAddress(
        source=str(getattr(source, "source", "") or getattr(source, "platform", "") or ""),
        platform=str(getattr(source, "platform", "") or ""),
        chat_type=str(getattr(source, "chat_type", "") or ""),
        chat_id=str(getattr(source, "chat_id", "") or ""),
        thread_id=str(getattr(source, "thread_id", "") or ""),
        user_id=str(getattr(source, "user_id", "") or ""),
    )
    return enterprise_scope, address
```

- [x] **Step 3: Thread enterprise scope and session address through gateway session objects**

Extend `gateway/session.py` so `SessionEntry` and `SessionContext` carry both `enterprise_scope` and `session_address`, and add a dedicated scoped-key builder instead of overloading the current positional format.

```python
def build_scoped_session_key(scope: EnterpriseScope, address: SessionAddress) -> str:
    parts = [
        "agent", "scope", "v1",
        "tenant", scope.tenant_id or "_",
        "workspace", scope.workspace_id or "_",
        "agent", scope.agent_id or "main",
        "platform", address.platform or "_",
        "chat_type", address.chat_type or "_",
        "chat", address.chat_id or "_",
    ]
    if address.thread_id:
        parts.extend(["thread", address.thread_id])
    if address.user_id:
        parts.extend(["user", address.user_id])
    return ":".join(parts)
```

- [x] **Step 4: Make session-key parsing dual-stack**

Update `gateway/run.py` so `_parse_session_key()` supports both the old `agent:main:...` format and the new tagged scoped format.

```python
def _parse_session_key(session_key: str) -> dict | None:
    if session_key.startswith("agent:main:"):
        return _parse_legacy_session_key(session_key)
    if session_key.startswith("agent:scope:v1:"):
        return _parse_scoped_session_key(session_key)
    return None
```

- [x] **Step 5: Add nullable enterprise and routing columns to SQLite**

Extend the `sessions` table in `hermes_state.py` with nullable enterprise-scope and routing columns and add indexes for scoped lookups.

```sql
ALTER TABLE sessions ADD COLUMN tenant_id TEXT;
ALTER TABLE sessions ADD COLUMN workspace_id TEXT;
ALTER TABLE sessions ADD COLUMN agent_id TEXT;
ALTER TABLE sessions ADD COLUMN chat_id TEXT;
ALTER TABLE sessions ADD COLUMN thread_id TEXT;
ALTER TABLE sessions ADD COLUMN chat_type TEXT;
CREATE INDEX IF NOT EXISTS idx_sessions_scope
    ON sessions(tenant_id, workspace_id, agent_id, started_at DESC);
```

- [x] **Step 6: Store enterprise scope and address on session creation without changing prompt behavior**

Update `SessionDB.create_session(...)` to accept optional enterprise-scope and session-address fields and persist them, but do not change system-prompt construction or message injection yet.

```python
def create_session(
    self,
    session_id: str,
    source: str,
    model: str = None,
    model_config: dict | None = None,
    system_prompt: str = None,
    user_id: str = None,
    parent_session_id: str = None,
    *,
    enterprise_scope: EnterpriseScope | None = None,
    session_address: SessionAddress | None = None,
) -> str:
    ...
```

- [x] **Step 7: Add focused regression tests**

Cover:

- enterprise scope and session address normalization
- legacy key builder unchanged by default
- new scoped key round-trip parser
- background notification fallback parsing for both key formats
- SQLite migration leaves legacy rows readable
- child-session inheritance keeps enterprise scope unchanged
- cached-agent construction and compression continuation preserve typed metadata

- [x] **Step 8: Verify PR1 in a CI-parity environment**

Primary target:

```bash
scripts/run_tests.sh tests/gateway/test_session.py
scripts/run_tests.sh tests/gateway/test_background_process_notifications.py
scripts/run_tests.sh tests/gateway/test_async_memory_flush.py
scripts/run_tests.sh tests/gateway/test_agent_cache.py
scripts/run_tests.sh tests/run_agent/test_compression_persistence.py
scripts/run_tests.sh tests/test_hermes_state.py
```

Current Windows rollout note: `scripts/run_tests.sh` hits a CRLF issue in this environment, so verification was completed with a hermetic `pytest` command that mirrors the wrapper's env hardening and test selection.

Result: PASS (`325 passed`), with legacy `agent:main:` fixtures still valid and new typed metadata paths covered.

- [ ] **Step 9: Commit PR1**

```bash
git add agent/scope.py agent/scope_resolver.py gateway/session.py gateway/run.py hermes_state.py run_agent.py tests/agent/test_scope.py tests/gateway/test_session.py tests/gateway/test_background_process_notifications.py tests/gateway/test_async_memory_flush.py tests/test_hermes_state.py
git commit -m "feat: add scope foundation for enterprise sessions"
```

---

### Task 2: PR2 Scoped Session Search

**Files:**
- Modify: `hermes_state.py:764-804,1130-1238,1300-1314,1322-1331,1356-1366,1404-1424`
- Modify: `tools/session_search_tool.py:266-315,318-364`
- Modify: `run_agent.py:7694-7704,8201-8212`
- Test: `tests/test_hermes_state.py`
- Test: `tests/tools/test_session_search_tool.py`

- [ ] **Step 1: Add a reusable enterprise-scope filter helper to SessionDB**

Implement one internal helper so all list and search paths share the same WHERE clause shape.

```python
def _build_scope_filters(self, enterprise_scope: EnterpriseScope | None) -> tuple[list[str], list[object]]:
    if not enterprise_scope or not enterprise_scope.is_scoped():
        return [], []
    return (
        [
            "COALESCE(s.tenant_id, '') = ?",
            "COALESCE(s.workspace_id, '') = ?",
            "COALESCE(s.agent_id, '') = ?",
        ],
        [enterprise_scope.tenant_id, enterprise_scope.workspace_id, enterprise_scope.agent_id],
    )
```

- [ ] **Step 2: Extend recent-session listing to respect enterprise scope**

Update `list_sessions_rich(...)` so enterprise-scoped callers do not see legacy unscoped rows by default.

```python
def list_sessions_rich(..., enterprise_scope: EnterpriseScope | None = None) -> list[dict[str, object]]:
    scope_where, scope_params = self._build_scope_filters(enterprise_scope)
    where_clauses.extend(scope_where)
    params.extend(scope_params)
```

- [ ] **Step 3: Extend full-text search and fallback LIKE search**

Update `search_full_text(...)` to apply the same scope filter in both the FTS query and the fallback LIKE query.

- [ ] **Step 4: Keep scope hidden from the model**

Do not add scope fields to the `session_search` schema. Instead, pass current enterprise scope from `run_agent.py`.

```python
return _session_search(
    query=function_args.get("query", ""),
    role_filter=function_args.get("role_filter"),
    limit=function_args.get("limit", 3),
    db=self._session_db,
    current_session_id=self.session_id,
    enterprise_scope=self.enterprise_scope,
)
```

- [ ] **Step 5: Update the tool implementation to require runtime-provided enterprise scope**

Add an optional `enterprise_scope` parameter to `tools/session_search_tool.py`, apply it to both recent browsing and keyword search, and leave the public schema unchanged. Do not let the tool derive scope from `session_key`.

- [ ] **Step 6: Add tests for isolation behavior**

Cover:

- same query, same DB, different scope -> different result sets
- scoped caller does not see null-scope legacy sessions
- unscoped caller preserves current behavior
- recent browse and keyword search use the same scope rules
- lineage exclusion does not walk into a different enterprise scope

- [ ] **Step 7: Verify PR2 with the wrapper**

Run:

```bash
scripts/run_tests.sh tests/test_hermes_state.py
scripts/run_tests.sh tests/tools/test_session_search_tool.py
```

Expected: PASS, with scoped queries only returning sessions from the active tenant/workspace/agent.

- [ ] **Step 8: Commit PR2**

```bash
git add hermes_state.py tools/session_search_tool.py run_agent.py tests/test_hermes_state.py tests/tools/test_session_search_tool.py
git commit -m "feat: scope session search by tenant workspace and agent"
```

---

### Task 3: PR3 Scoped Memory

**Files:**
- Create: `agent/memory_namespace.py`
- Create: `agent/memory_backend.py`
- Modify: `tools/memory_tool.py:49-55,110-140,181-184,359-369`
- Modify: `run_agent.py`
- Test: `tests/tools/test_memory_tool.py`
- Test: `tests/gateway/test_flush_memory_stale_guard.py`

- [ ] **Step 1: Define namespace rules before changing storage**

Create a small namespace helper that maps scope into file-backed memory locations.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryNamespace:
    kind: str
    tenant_id: str = ""
    workspace_id: str = ""
    owner_id: str = ""
```

Rules:

- `memory` target -> `(tenant, workspace, agent)`
- `user` target -> `(tenant, workspace, user)`
- missing scope -> legacy `memories/MEMORY.md` and `memories/USER.md`
- first milestone uses single-namespace reads, not cross-namespace merge

- [ ] **Step 2: Implement a backend that only changes path resolution**

Create `agent/memory_backend.py` with methods that resolve namespace-specific file paths but keep the current file format intact.

```python
class ScopedMemoryBackend:
    def path_for(self, namespace: MemoryNamespace) -> Path:
        ...
```

- [ ] **Step 3: Keep the frozen snapshot model unchanged**

Refactor `tools/memory_tool.py` so snapshot capture still happens once at session start, but the source files come from the scoped backend when `AIAgent.scope` is present.

- [ ] **Step 4: Pass enterprise scope into memory initialization, not into model-visible tool args**

The model should still call the same `memory` tool shape. Enterprise scope must be resolved by the agent runtime and consumed internally. `SessionAddress` must not influence memory namespace selection.

- [ ] **Step 5: Add tests for namespace separation**

Cover:

- same target, different scope -> different files
- legacy no-scope path still reads and writes the old files
- frozen snapshot remains stable after mid-session writes
- profile-safe path resolution still goes through `get_hermes_home()`
- child sessions inherit the same enterprise-scope memory namespace

- [ ] **Step 6: Verify PR3 with the wrapper**

Run:

```bash
scripts/run_tests.sh tests/tools/test_memory_tool.py
scripts/run_tests.sh tests/gateway/test_flush_memory_stale_guard.py
```

Expected: PASS, with namespace separation in place and no prompt-cache regression.

- [ ] **Step 7: Commit PR3**

```bash
git add agent/memory_namespace.py agent/memory_backend.py tools/memory_tool.py run_agent.py tests/tools/test_memory_tool.py tests/gateway/test_flush_memory_stale_guard.py
git commit -m "feat: add scoped memory backend with frozen snapshots"
```

---

### Task 4: PR4 Scoped Skills Visibility

**Files:**
- Create: `agent/skill_registry.py`
- Create: `agent/skill_visibility.py`
- Modify: `tools/skills_tool.py:546-588,666-725,823-1028`
- Modify: `agent/skill_utils.py`
- Test: `tests/tools/test_skills_tool.py`
- Test: `tests/test_plugin_skills.py`
- Test: `tests/agent/test_external_skills.py`

- [ ] **Step 1: Add a visibility layer, not a new skill system**

Create a small policy module that answers `can_list(scope, skill)` and `can_view(scope, skill)` using allowlists or rollout rules.

```python
def skill_visible_to_scope(enterprise_scope: EnterpriseScope | None, skill_meta: dict[str, object]) -> bool:
    return True
```

The first version can default to allow-all when no enterprise policy is configured.

- [ ] **Step 2: Filter `skills_list()` results after current platform/disabled checks**

Do not remove or replace the existing platform and disabled-skill logic in `tools/skills_tool.py`. Apply enterprise-scope visibility after those checks. `SessionAddress` should only matter where existing platform filtering already uses it.

- [ ] **Step 3: Re-check visibility inside `skill_view()`**

Prevent direct lookups from bypassing `skills_list()` filtering.

```python
if not skill_visible_to_scope(enterprise_scope, resolved_meta):
    return json.dumps({"success": False, "error": "Skill is not visible in this scope."})
```

- [ ] **Step 4: Keep external skill directories compatible**

Make sure visibility rules apply equally to local skills, plugin skills, and entries loaded from `skills.external_dirs`.

- [ ] **Step 5: Add tests for visibility boundaries**

Cover:

- hidden skill absent from `skills_list()`
- hidden skill rejected by `skill_view()`
- plugin and external-dir skills follow the same policy
- no-scope callers preserve current behavior
- visibility decisions do not depend on parsing `session_key`

- [ ] **Step 6: Verify PR4 with the wrapper**

Run:

```bash
scripts/run_tests.sh tests/tools/test_skills_tool.py
scripts/run_tests.sh tests/test_plugin_skills.py
scripts/run_tests.sh tests/agent/test_external_skills.py
```

Expected: PASS, with scope-aware visibility layered on top of current platform and disabled-skill filtering.

- [ ] **Step 7: Commit PR4**

```bash
git add agent/skill_registry.py agent/skill_visibility.py agent/skill_utils.py tools/skills_tool.py tests/tools/test_skills_tool.py tests/test_plugin_skills.py tests/agent/test_external_skills.py
git commit -m "feat: add scoped skill visibility"
```

---

### Task 5: Deferred PR5 Tool Policy and Context Pack

**Files:**
- Create: `agent/tool_policy.py`
- Create: `agent/context_pack.py`
- Create: `agent/enterprise_context_engine.py`
- Modify: `agent/context_engine.py:1-33`
- Modify: `model_tools.py:196-270`
- Modify: `run_agent.py:8982-8991,9115-9129`

- [ ] **Step 1: Separate visibility from authorization**

Add a tool-policy layer that decides what a scope may call, independent of what it can see in prompts or menus.

- [ ] **Step 2: Build a typed context pack**

Aggregate enterprise context into one runtime object so downstream injection is deterministic and testable.

- [ ] **Step 3: Keep additive context injection**

When enterprise context is injected, keep doing it by appending a fenced block to the current user message in `run_agent.py`. Do not rebuild the system prompt.

- [ ] **Step 4: Verify only after PR1-PR4 are stable**

Run targeted tests for `run_agent.py`, tool definitions, and any new context-engine tests once the earlier isolation layers have landed.

---

### Task 6: Deferred PR6 Run Queue and Session Actor

**Files:**
- Create: `gateway/run_queue.py`
- Create: `gateway/session_actor.py`
- Modify: `gateway/run.py:656-660,1507-1523,1536-1597,10429-10580`
- Test: `tests/gateway/` queue and interrupt coverage

- [ ] **Step 1: Extract a per-session actor abstraction**

Move `_running_agents`, interrupt handling, and queued follow-up logic behind a session-owned actor boundary.

- [ ] **Step 2: Keep external behavior stable**

The actor refactor must preserve current semantics:

- same session serial
- cross-session parallel
- explicit interrupt support
- queued follow-up after completion

- [ ] **Step 3: Migrate existing tests, then add new queue tests**

Update current gateway tests that assume direct access to `GatewayRunner._running_agents` only after the actor wrapper exists.

---

## Acceptance criteria by milestone

### Milestone A (merge after PR4)

- Scope exists as a first-class runtime object.
- Session metadata is scope-aware in SQLite.
- Session search is isolated by tenant/workspace/agent.
- Memory no longer leaks across enterprise namespaces.
- Skills can be filtered by scope.
- Prompt caching behavior is unchanged.
- This milestone delivers data and visibility isolation only. Tool execution authorization is still deferred to PR5.

### Milestone B (after PR6)

- Tool authorization is scope-aware.
- Enterprise context packs are injected without cache busting.
- Gateway concurrency is represented by explicit session actors instead of scattered maps and queue helpers.

## Recommended execution order

1. PR1 Scope Foundation
2. PR2 Scoped Session Search
3. PR3 Scoped Memory
4. PR4 Scoped Skills Visibility
5. PR5 Tool Policy and Context Pack
6. PR6 Run Queue and Session Actor

Do not start PR2, PR3, or PR4 until PR1 lands. PR5 and PR6 stay deferred until the isolation primitives are stable.

## Self-review

- Spec coverage: session identity, SQLite scope fields, search isolation, memory namespace isolation, skill visibility, and deferred later-stage policy/queue work are all covered.
- Placeholder scan: no `TODO`, `TBD`, or "implement later" steps inside milestone tasks. Deferred tasks are explicitly labeled as deferred follow-up, not hidden placeholders inside PR1-PR4.
- Type consistency: `EnterpriseScope`, `SessionAddress`, and `SessionIdentity` have distinct responsibilities, and downstream tasks now reference the correct one instead of reusing one oversized scope object.
