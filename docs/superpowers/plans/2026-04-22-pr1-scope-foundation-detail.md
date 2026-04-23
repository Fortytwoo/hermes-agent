# PR1 Scope Foundation Detailed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first enterprise-isolation milestone by introducing typed enterprise and routing boundaries, persisting them in SQLite and session metadata, and keeping all live gateway behavior backward-compatible.

**Architecture:** Freeze the live session-key format at `agent:main:...` for now, add typed `EnterpriseScope` and `SessionAddress` models behind the scenes, persist them as session metadata, and make all new APIs additive and optional. Keep `SessionSource` and `_parse_session_key()` as transitional compatibility layers while moving the source of truth toward typed metadata on `SessionEntry` and `sessions` rows.

**Tech Stack:** Python dataclasses, existing gateway session store, `hermes_state.py` SQLite migrations, `run_agent.py` optional runtime fields, `scripts/run_tests.sh` as the target verification wrapper, and a temporary hermetic `pytest` fallback for the current Windows CRLF issue.

## Current rollout status (2026-04-22)

- Worktree: `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation`
- Branch: `codex/pr1-scope-foundation`
- Implementation status: Tasks 1-6 below are landed in code; commit steps remain open.
- Legacy safety guard: `build_session_key(...)` still emits `agent:main:...`; scoped-key support is additive only in PR1.
- Verification note: the current Windows environment still trips `scripts/run_tests.sh` on CRLF handling, so the completed verification steps below were satisfied with a hermetic `pytest` command that mirrors the wrapper's env hardening and test selection.
- Verification result: `325 passed`

---

## What PR1 does

- Adds typed enterprise and routing boundary models.
- Adds SQLite columns for enterprise scope and routing metadata.
- Extends `SessionEntry` and `SessionContext` to carry typed metadata.
- Extends `SessionDB.create_session()` and `SessionDB.ensure_session()` with optional typed metadata.
- Adds scoped-key parsing helpers and keeps `_parse_session_key()` dual-stack.
- Threads typed metadata through `AIAgent` startup, recovery, compression continuation, and gateway-owned agent launches.
- Keeps the runtime default on legacy `agent:main:...` session keys.

## What PR1 explicitly does not do

- Does not switch production gateway traffic to scoped session keys.
- Does not change prompt assembly or inject enterprise context into the system prompt.
- Does not scope `session_search`, `memory`, or `skills` yet.
- Does not remove `SessionSource`, `origin`, or `_parse_session_key()` fallback paths.
- Does not add user-facing config for enterprise scoping yet.

## Authority and compatibility rules

- `EnterpriseScope` is the only authority for tenant/workspace/agent isolation.
- `SessionAddress` is the authority for platform/chat/thread/user routing.
- `SessionIdentity` is the authority for in-memory active-session bookkeeping.
- `SessionSource` remains a compatibility payload for gateway delivery and prompt context.
- `_parse_session_key()` must keep returning the old routing dict shape for legacy call sites in `gateway/run.py` tests.
- `build_session_key(source, ...)` must keep its current public signature and default output.
- All new typed fields must be optional or have safe defaults so direct `SessionEntry(...)` construction in tests keeps working.

## Scope bootstrap sources for PR1

PR1 needs a minimal, deterministic way to populate `EnterpriseScope` without inventing the final enterprise control plane. Use this precedence:

1. explicit internal overrides passed by gateway/API-server/bootstrap code
2. environment variables:
   - `HERMES_SCOPE_TENANT_ID`
   - `HERMES_SCOPE_WORKSPACE_ID`
   - `HERMES_SCOPE_AGENT_ID`
3. empty legacy scope (`tenant_id=""`, `workspace_id=""`, `agent_id="main"`)

This bootstrap path is intentionally internal-only. Do not expose these fields to model-visible tool schemas.

## Boundary review outcome

The PR1 boundary split is now materially cleaner than the original draft:

- `EnterpriseScope` owns tenant/workspace/agent isolation.
- `SessionAddress` owns routing and reply targeting.
- `SessionIdentity` owns in-memory session bookkeeping.

The remaining intentional gray areas are explicit rather than accidental:

- `SessionSource`, `origin`, and `_parse_session_key()` still exist as compatibility shims.
- Live session-key generation remains legacy until PR2-PR4 prove the scoped isolation path.
- Scoped `session_search`, `memory`, and `skills` are deliberately deferred to later PRs.
- SQLite currently persists the enterprise scope plus the routing subset needed for PR1 (`chat_id`, `thread_id`, `chat_type`); origin-first delivery fallback still depends on `SessionEntry` metadata rather than treating SQL rows as the routing authority.

## File responsibilities for PR1

- `agent/scope.py`
  - define `EnterpriseScope`, `SessionAddress`, `SessionIdentity`
  - normalization helpers
  - typed parsing helpers for scoped keys
- `agent/scope_resolver.py`
  - explicit scope/address resolution from source + overrides + env
- `gateway/session.py`
  - keep legacy key builder unchanged
  - add scoped-key builder
  - extend `SessionEntry` and `SessionContext`
  - persist typed metadata into `SessionStore`
- `gateway/run.py`
  - keep `_parse_session_key()` compatibility surface
  - add typed parse helpers underneath it
  - continue fallback routing when `origin` is missing
- `hermes_state.py`
  - bump schema version
  - add new columns + indexes
  - extend session lifecycle write APIs
- `run_agent.py`
  - add optional `enterprise_scope` and `session_address` init fields
  - thread them into `SessionDB.create_session()` / `ensure_session()`

---

### Task 1: Add the typed boundary models without changing live behavior

**Files:**
- Create: `agent/scope.py`
- Test: `tests/agent/test_scope.py`

- [x] **Step 1: Define the three core dataclasses**

Create `agent/scope.py` with default-safe dataclasses so tests and constructors can adopt them incrementally.

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

- [x] **Step 2: Add normalization and dict helpers**

Keep all serialization local to this module so `SessionEntry.to_dict()` and SQLite adapters do not each invent their own field mapping.

```python
def scope_to_dict(scope: EnterpriseScope) -> dict[str, str]:
    return {
        "tenant_id": scope.tenant_id,
        "workspace_id": scope.workspace_id,
        "agent_id": scope.agent_id,
    }
```

- [x] **Step 3: Add typed scoped-key parser helpers**

Do not replace `_parse_session_key()` yet. Add helpers that can be called underneath it.

```python
def parse_scoped_session_key(session_key: str) -> tuple[EnterpriseScope, SessionAddress] | None:
    ...
```

- [x] **Step 4: Add focused tests for defaults and parsing**

Cover:

- empty `EnterpriseScope` is unscoped
- non-default `agent_id` marks scope as scoped
- `parse_scoped_session_key()` round-trips the tagged format
- malformed scoped keys return `None`

- [x] **Step 5: Run the new unit tests**

Run:

```bash
scripts/run_tests.sh tests/agent/test_scope.py
```

Expected: PASS, with no gateway or DB dependency needed for these tests.

- [ ] **Step 6: Commit Task 1**

```bash
git add agent/scope.py tests/agent/test_scope.py
git commit -m "feat: add typed enterprise and session boundary models"
```

---

### Task 2: Add resolvers for enterprise scope and routing address

**Files:**
- Create: `agent/scope_resolver.py`
- Test: `tests/agent/test_scope.py`

- [x] **Step 1: Add separate resolver functions**

Keep resolution explicit instead of returning one oversized object.

```python
from agent.scope import EnterpriseScope, SessionAddress


def resolve_enterprise_scope(*, overrides: dict | None = None) -> EnterpriseScope:
    overrides = overrides or {}
    return EnterpriseScope(
        tenant_id=str(overrides.get("tenant_id") or os.getenv("HERMES_SCOPE_TENANT_ID", "")),
        workspace_id=str(overrides.get("workspace_id") or os.getenv("HERMES_SCOPE_WORKSPACE_ID", "")),
        agent_id=str(overrides.get("agent_id") or os.getenv("HERMES_SCOPE_AGENT_ID", "main")),
    )


def resolve_session_address(source) -> SessionAddress:
    return SessionAddress(
        source=str(getattr(source, "platform", "") or ""),
        platform=str(getattr(source, "platform", "") or ""),
        chat_type=str(getattr(source, "chat_type", "") or ""),
        chat_id=str(getattr(source, "chat_id", "") or ""),
        thread_id=str(getattr(source, "thread_id", "") or ""),
        user_id=str(getattr(source, "user_id", "") or ""),
    )
```

- [x] **Step 2: Add one convenience wrapper for callers that want both**

```python
def resolve_session_boundary(*, source=None, overrides: dict | None = None) -> tuple[EnterpriseScope, SessionAddress]:
    return resolve_enterprise_scope(overrides=overrides), resolve_session_address(source)
```

- [x] **Step 3: Add tests for precedence**

Cover:

- explicit overrides beat env
- env beats empty default
- `SessionAddress` mapping from `SessionSource` is lossless for platform/chat/thread/user

- [x] **Step 4: Run the resolver tests**

Run:

```bash
scripts/run_tests.sh tests/agent/test_scope.py
```

Expected: PASS, with override/env precedence fixed.

- [ ] **Step 5: Commit Task 2**

```bash
git add agent/scope_resolver.py tests/agent/test_scope.py
git commit -m "feat: add enterprise scope and session address resolvers"
```

---

### Task 3: Extend gateway session objects while freezing the live key format

**Files:**
- Modify: `gateway/session.py`
- Test: `tests/gateway/test_session.py`
- Test: `tests/gateway/test_async_memory_flush.py`

- [x] **Step 1: Leave `build_session_key()` untouched**

Keep this exact compatibility contract:

```python
def build_session_key(
    source: SessionSource,
    group_sessions_per_user: bool = True,
    thread_sessions_per_user: bool = False,
) -> str:
    ...
```

Do not add enterprise-scope parameters here in PR1.

- [x] **Step 2: Add a separate scoped-key builder**

```python
def build_scoped_session_key(
    enterprise_scope: EnterpriseScope,
    session_address: SessionAddress,
) -> str:
    ...
```

This function exists for parser tests and future cutover work, not for live default routing in PR1.

- [x] **Step 3: Extend `SessionEntry` with typed metadata using default factories**

Add fields without breaking current direct constructors in tests.

```python
from dataclasses import field

enterprise_scope: EnterpriseScope = field(default_factory=EnterpriseScope)
session_address: SessionAddress = field(default_factory=SessionAddress)
```

Keep existing transitional fields:

- `origin`
- `display_name`
- `platform`
- `chat_type`

Do not remove them in PR1.

- [x] **Step 4: Extend `to_dict()` and `from_dict()` compatibly**

Missing keys must deserialize to default-empty typed objects.

```python
result["enterprise_scope"] = scope_to_dict(self.enterprise_scope)
result["session_address"] = address_to_dict(self.session_address)
```

- [x] **Step 5: Populate typed metadata in `get_or_create_session()`, `reset_session()`, and `switch_session()`**

Rules:

- `get_or_create_session()` resolves typed metadata from the incoming `SessionSource`
- `reset_session()` and `switch_session()` copy typed metadata from the previous entry
- child-session or resume flows must not mutate `EnterpriseScope`

- [x] **Step 6: Extend `SessionContext` but do not change prompt text**

Add:

```python
enterprise_scope: EnterpriseScope = field(default_factory=EnterpriseScope)
session_address: SessionAddress = field(default_factory=SessionAddress)
```

Then make `build_session_context(...)` populate these fields from `session_entry` when present. Do not render them into `build_session_context_prompt()` yet.

- [x] **Step 7: Add gateway session tests**

Cover:

- legacy `build_session_key()` outputs unchanged
- `build_scoped_session_key()` output
- `SessionEntry.to_dict()/from_dict()` round-trips typed metadata
- `reset_session()` and `switch_session()` preserve typed metadata
- `build_session_context()` copies typed metadata from `session_entry`

- [x] **Step 8: Run the gateway session tests**

Run:

```bash
scripts/run_tests.sh tests/gateway/test_session.py
scripts/run_tests.sh tests/gateway/test_async_memory_flush.py
```

Expected: PASS, with all old `agent:main:` assertions still green.

- [ ] **Step 9: Commit Task 3**

```bash
git add gateway/session.py tests/gateway/test_session.py tests/gateway/test_async_memory_flush.py
git commit -m "feat: store typed enterprise and routing metadata in session entries"
```

---

### Task 4: Add dual-stack parsing in gateway run fallback paths

**Files:**
- Modify: `gateway/run.py`
- Test: `tests/gateway/test_background_process_notifications.py`

- [x] **Step 1: Extract a legacy parser helper**

Keep the current return shape for old tests and call sites.

```python
def _parse_legacy_session_key(session_key: str) -> dict | None:
    ...
```

- [x] **Step 2: Add a scoped parser helper underneath the compatibility wrapper**

```python
def _parse_scoped_session_key_for_routing(session_key: str) -> dict | None:
    parsed = parse_scoped_session_key(session_key)
    if not parsed:
        return None
    enterprise_scope, session_address = parsed
    return {
        "platform": session_address.platform,
        "chat_type": session_address.chat_type,
        "chat_id": session_address.chat_id,
        **({"thread_id": session_address.thread_id} if session_address.thread_id else {}),
    }
```

- [x] **Step 3: Keep `_parse_session_key()` as the compatibility surface**

```python
def _parse_session_key(session_key: str) -> dict | None:
    if session_key.startswith("agent:main:"):
        return _parse_legacy_session_key(session_key)
    if session_key.startswith("agent:scope:v1:"):
        return _parse_scoped_session_key_for_routing(session_key)
    return None
```

- [x] **Step 4: Leave origin-first fallback logic intact**

Do not change the ordering in:

- shutdown notifications
- synthetic process-event source reconstruction

The sequence remains:

1. `SessionEntry.origin`
2. `_parse_session_key()`
3. event payload fields

- [x] **Step 5: Add parser tests**

Cover:

- all existing legacy parse cases still pass
- scoped keys return routing dicts with the same shape
- malformed scoped keys return `None`

- [x] **Step 6: Run the gateway parse tests**

Run:

```bash
scripts/run_tests.sh tests/gateway/test_background_process_notifications.py
```

Expected: PASS, with new scoped parser cases added next to existing legacy cases.

- [ ] **Step 7: Commit Task 4**

```bash
git add gateway/run.py tests/gateway/test_background_process_notifications.py
git commit -m "feat: add dual-stack session key parsing for gateway fallback routing"
```

---

### Task 5: Add SQLite schema v7 and additive session lifecycle writes

**Files:**
- Modify: `hermes_state.py`
- Test: `tests/test_hermes_state.py`

- [x] **Step 1: Bump schema version from 6 to 7**

```python
SCHEMA_VERSION = 7
```

- [x] **Step 2: Add new columns in the base schema**

Add these nullable columns to `sessions`:

- `tenant_id`
- `workspace_id`
- `agent_id`
- `chat_id`
- `thread_id`
- `chat_type`

- [x] **Step 3: Add the v7 migration**

```python
if current_version < 7:
    for name, column_type in [
        ("tenant_id", "TEXT"),
        ("workspace_id", "TEXT"),
        ("agent_id", "TEXT"),
        ("chat_id", "TEXT"),
        ("thread_id", "TEXT"),
        ("chat_type", "TEXT"),
    ]:
        ...
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_scope "
        "ON sessions(tenant_id, workspace_id, agent_id, started_at DESC)"
    )
    cursor.execute("UPDATE schema_version SET version = 7")
```

- [x] **Step 4: Extend `create_session()` using keyword-only additive parameters**

This preserves the huge existing call surface.

```python
def create_session(
    self,
    session_id: str,
    source: str,
    model: str = None,
    model_config: Dict[str, Any] = None,
    system_prompt: str = None,
    user_id: str = None,
    parent_session_id: str = None,
    *,
    enterprise_scope: EnterpriseScope | None = None,
    session_address: SessionAddress | None = None,
) -> str:
    ...
```

- [x] **Step 5: Extend `ensure_session()` the same way**

This closes the recovery path where `create_session()` can fail at startup and later writes would otherwise re-create an unscoped placeholder row.

```python
def ensure_session(
    self,
    session_id: str,
    source: str = "unknown",
    model: str = None,
    *,
    enterprise_scope: EnterpriseScope | None = None,
    session_address: SessionAddress | None = None,
) -> None:
    ...
```

- [x] **Step 6: Add hermes_state tests for the new metadata**

Cover:

- fresh DB has v7 schema
- migrated DB adds new columns
- `create_session(..., enterprise_scope=..., session_address=...)` persists all fields
- `ensure_session(...)` persists scope/address when it has to create a missing row
- old `create_session(session_id="s1", source="cli")` call sites still work unchanged

- [x] **Step 7: Run the SQLite tests**

Run:

```bash
scripts/run_tests.sh tests/test_hermes_state.py
```

Expected: PASS, including legacy callers that still pass only `session_id` and `source`.

- [ ] **Step 8: Commit Task 5**

```bash
git add hermes_state.py tests/test_hermes_state.py
git commit -m "feat: persist enterprise and routing metadata in session rows"
```

---

### Task 6: Thread optional enterprise metadata through AIAgent and gateway startup

**Files:**
- Modify: `run_agent.py`
- Modify: `gateway/run.py`
- Test: `tests/gateway/test_agent_cache.py`
- Test: `tests/run_agent/test_compression_persistence.py`

- [x] **Step 1: Add optional runtime fields to `AIAgent.__init__`**

Make them keyword-only and default-safe so the broad constructor call surface stays compatible.

```python
def __init__(
    ...,
    platform: str = None,
    user_id: str = None,
    gateway_session_key: str = None,
    enterprise_scope: EnterpriseScope | None = None,
    session_address: SessionAddress | None = None,
    ...
):
    ...
```

- [x] **Step 2: Store them on the agent instance without changing prompt behavior**

```python
self.enterprise_scope = enterprise_scope or EnterpriseScope()
self.session_address = session_address or SessionAddress()
```

- [x] **Step 3: Pass typed metadata into `SessionDB.create_session()`**

Update the existing create call in `run_agent.py`:

```python
self._session_db.create_session(
    session_id=self.session_id,
    source=self.platform or os.environ.get("HERMES_SESSION_SOURCE", "cli"),
    model=self.model,
    model_config={...},
    user_id=None,
    parent_session_id=self._parent_session_id,
    enterprise_scope=self.enterprise_scope,
    session_address=self.session_address,
)
```

- [x] **Step 4: Pass typed metadata into `ensure_session()` on recovery paths**

Any fallback path that recreates session rows must preserve the same typed metadata.

- [x] **Step 5: Only modify gateway call sites that already know the session source**

For PR1:

- gateway message handling paths that build `SessionEntry`
- API-server or adapter paths that already have `SessionSource`

Do not churn CLI, batch, cron, ACP, or test helper call sites unless they actually need typed metadata now. The new args are optional.

- [x] **Step 6: Add constructor-compatibility smoke tests**

Cover:

- `AIAgent()` still works without new args
- gateway agent construction can pass typed metadata
- cached-agent tests still behave the same with the extended signature

- [x] **Step 7: Run the runtime smoke tests**

Run:

```bash
scripts/run_tests.sh tests/gateway/test_agent_cache.py
scripts/run_tests.sh tests/run_agent/test_compression_persistence.py
```

Expected: PASS, with no constructor regressions.

- [ ] **Step 8: Commit Task 6**

```bash
git add run_agent.py gateway/run.py tests/gateway/test_agent_cache.py tests/run_agent/test_compression_persistence.py
git commit -m "feat: thread optional enterprise metadata through agent startup"
```

---

### Task 7: Final PR1 verification and rollout notes

**Files:**
- Modify: `docs/superpowers/plans/2026-04-22-enterprise-scope-rollout.md`
- Modify: `docs/superpowers/plans/2026-04-22-pr1-scope-foundation-detail.md`

- [x] **Step 1: Run the consolidated PR1 verification set**

Primary target:

```bash
scripts/run_tests.sh tests/agent/test_scope.py
scripts/run_tests.sh tests/gateway/test_session.py
scripts/run_tests.sh tests/gateway/test_background_process_notifications.py
scripts/run_tests.sh tests/gateway/test_async_memory_flush.py
scripts/run_tests.sh tests/gateway/test_agent_cache.py
scripts/run_tests.sh tests/run_agent/test_compression_persistence.py
scripts/run_tests.sh tests/test_hermes_state.py
```

Current Windows rollout note: `scripts/run_tests.sh` currently fails in this environment because of CRLF handling, so this step was completed with a hermetic `pytest` command that mirrors the wrapper's env hardening and test selection.

Result: PASS (`325 passed`). Legacy `agent:main:` behavior stayed green, and the new typed metadata paths were covered in the consolidated suite.

- [x] **Step 2: Record the rollout constraint**

Document in the main rollout plan that PR1 ships typed metadata and parsing, but production session-key generation remains legacy until PR2-PR4 prove the isolation path.

- [ ] **Step 3: Commit the final PR1 plan sync**

```bash
git add docs/superpowers/plans/2026-04-22-enterprise-scope-rollout.md docs/superpowers/plans/2026-04-22-pr1-scope-foundation-detail.md
git commit -m "docs: add detailed PR1 scope foundation plan"
```

---

## Key risks to watch during implementation

1. **Do not broaden `build_session_key()` now.** Too many gateway tests assume its exact current behavior.
2. **Do not remove `origin` or `SessionSource` now.** Gateway delivery still depends on them.
3. **Do not forget `ensure_session()`.** Otherwise recovery writes can create unscoped rows even after PR1.
4. **Do not make new constructor params positional.** `AIAgent(...)` has a wide call surface across gateway, CLI, ACP, cron, and tests.
5. **Do not let `_parse_session_key()` become the new scope authority again.** It stays routing-only and fallback-only.

## Done criteria for PR1

- Typed boundary models exist and are tested.
- Session entries and contexts carry typed metadata with backward-compatible defaults.
- SQLite stores enterprise and routing metadata in additive nullable columns.
- Agent startup can persist typed metadata when available.
- Gateway fallback parsing understands both legacy and scoped key strings.
- Live default session-key generation is still legacy.
