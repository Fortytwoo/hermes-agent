# A-Phase Functional Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute bottom-up functional testing for the PR1 scope/session foundation, covering critical business flows and state transitions first, then capturing defects and required regression tests.

**Architecture:** Use four layers of validation: state, orchestration, agent runtime, and real integration. Keep the test environment isolated under a dedicated `HERMES_HOME`, prefer the canonical `scripts/run_tests.sh` logic, and when the Windows checkout blocks that script because of CRLF, run an LF-normalized repo-local copy of the same wrapper logic instead of inventing a different test harness.

**Tech Stack:** Hermes gateway, `AIAgent`, SQLite `SessionDB`, MCP stdio/http registration, WSL bash wrapper execution, isolated `HERMES_HOME`, pytest.

---

### Task 1: Prepare isolated A-phase test environment

**Files:**
- Create: `tmp/run_tests_lf.sh` (generated, repo-local temp wrapper copy)
- Create: `tmp/hermes-functional-a/` (generated isolated `HERMES_HOME`)
- Inspect: `scripts/run_tests.sh`
- Inspect: `gateway/config.py`
- Inspect: `hermes_cli/runtime_provider.py`

- [ ] **Step 1: Verify canonical wrapper status**

Run:

```bash
bash scripts/run_tests.sh tests/agent/test_scope.py
```

Expected: fail on this Windows checkout with CRLF parsing, proving we need the normalized wrapper copy.

- [ ] **Step 2: Generate repo-local LF-normalized wrapper copy**

Run:

```bash
python - <<'PY'
from pathlib import Path
src = Path("scripts/run_tests.sh")
dst = Path("tmp/run_tests_lf.sh")
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(src.read_text(encoding="utf-8").replace("\r\n", "\n"), encoding="utf-8")
PY
```

- [ ] **Step 3: Create isolated `HERMES_HOME` skeleton**

Run:

```bash
python - <<'PY'
from pathlib import Path
base = Path("tmp/hermes-functional-a")
for rel in ("", "sessions", "cron", "memories", "skills", "logs"):
    (base / rel).mkdir(parents=True, exist_ok=True)
PY
```

- [ ] **Step 4: Record real-chain blockers before execution**

Capture whether the machine already has:

- an isolated provider credential source for the A-phase profile,
- an isolated gateway target (recommended: `api_server` platform if no external bot token is provisioned yet),
- an isolated MCP server command or endpoint we can call for a true tool invocation.

If any of these are missing, stop before claiming real-chain completion and report the missing piece precisely.

### Task 2: Run baseline PR1 regression suite

**Files:**
- Test: `tests/agent/test_scope.py`
- Test: `tests/gateway/test_session.py`
- Test: `tests/gateway/test_background_process_notifications.py`
- Test: `tests/gateway/test_async_memory_flush.py`
- Test: `tests/gateway/test_agent_cache.py`
- Test: `tests/run_agent/test_compression_persistence.py`
- Test: `tests/test_hermes_state.py`

- [ ] **Step 1: Run state-layer tests**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/agent/test_scope.py tests/test_hermes_state.py
```

Expected: PASS, covering typed scope/address helpers and SQLite v7 persistence.

- [ ] **Step 2: Run orchestration-layer tests**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway/test_session.py tests/gateway/test_background_process_notifications.py tests/gateway/test_async_memory_flush.py
```

Expected: PASS, covering session lifecycle, dual-stack parse compatibility, and background fallback routing.

- [ ] **Step 3: Run agent-runtime tests**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway/test_agent_cache.py tests/run_agent/test_compression_persistence.py
```

Expected: PASS, covering startup/recovery/compression metadata propagation.

- [ ] **Step 4: Save baseline evidence**

Record:

- exact commands,
- exit codes,
- pass/fail counts,
- any flaky/failing cases,
- whether failures are deterministic.

### Task 3: Execute A-phase real integration chain

**Files:**
- Inspect/Run: `gateway/run.py`
- Inspect/Run: `acp_adapter/server.py`
- Inspect/Run: `tools/mcp_tool.py`
- Inspect/Run: `hermes_cli/runtime_provider.py`
- Test reference: `tests/acp/test_mcp_e2e.py`

- [ ] **Step 1: Prefer an isolated real gateway target**

Use the `api_server` gateway platform if no independent Telegram/Discord/Slack test bot is already provisioned. This still exercises the real gateway stack without requiring production chat credentials.

- [ ] **Step 2: Select one real provider**

Resolve exactly one provider from the isolated A-phase config and verify only the provider name / model, never secrets.

Acceptance:

- provider resolves successfully,
- a minimal real prompt completes,
- the session row persists typed metadata.

- [ ] **Step 3: Select one core MCP chain**

Use one real MCP server reachable from the isolated config:

- stdio server preferred when we can point to a deterministic local command,
- otherwise one isolated HTTP/SSE MCP endpoint.

Acceptance:

- registration succeeds,
- tool surface refreshes,
- one tool call runs,
- tool progress / completion flows back through the runtime.

- [ ] **Step 4: Execute one end-to-end stateful flow**

Required flow:

1. enter through real gateway,
2. create or resume session,
3. run one provider-backed turn,
4. run one MCP-backed tool call,
5. verify persisted session row,
6. verify routing/progress fallback still works.

- [ ] **Step 5: Execute one failure-path flow**

Pick one of:

- provider failure,
- MCP registration failure,
- process-event fallback after origin is absent.

Acceptance: failure is reproducible and the observed behavior is documented.

### Task 4: Defect inventory and regression backlog

**Files:**
- Modify if needed: relevant failing test files
- Create if needed: additional regression tests adjacent to failing coverage

- [ ] **Step 1: Classify all findings**

Buckets:

- state-boundary defect,
- lifecycle defect,
- routing-fallback defect,
- real-integration defect,
- environment blocker (not product defect).

- [ ] **Step 2: Define regression additions**

For each confirmed product defect, specify:

- minimal reproducer,
- target test file,
- whether unit/component/integration regression is required.

- [ ] **Step 3: Stop before fixing**

Do not patch product code yet. Present the defect list and regression backlog first, because this A phase is explicitly “measure first, fix after the full run”.
