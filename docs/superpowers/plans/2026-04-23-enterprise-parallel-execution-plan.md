# Enterprise Parallel Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) together with controlled parallel worktrees. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the enterprise rollout end-to-end with a parallel execution strategy, mandatory per-PR Functional Testing, regression additions for every confirmed defect, and one final full Functional Testing sweep after all PRs land.

**Architecture:** Treat the existing PR1 scope foundation as the integration base, then execute the remaining rollout in mergeable PR units with isolated sibling worktrees. PR2, PR3, and PR4 all branch from the same frozen PR1 baseline rather than chaining on each other; safe parallelism is achieved by separating worktrees and keeping each PR vertically scoped. Because PR2 and PR3 both touch `run_agent.py`, PR3 must rebase on the latest merged baseline before final verification even though its branch starts as a sibling. PR4 is executed with the stronger boundary of full entrypoint consistency rather than tool-only filtering, so list/view/help/autocomplete surfaces cannot diverge by scope. Every PR closes with focused Functional Testing for the changed surface plus adjacent regression coverage; after the last PR, rerun the repo-wide Functional Testing matrix including wrapper-excluded `tests/integration` and `tests/e2e`.

**Tech Stack:** git worktrees, Hermes gateway/session runtime, SQLite `SessionDB`, `run_agent.py`, pytest, `tmp/run_tests_lf.sh`, WSL bash, isolated `HERMES_HOME`.

---

## Execution rules

- All parallel implementation happens in isolated worktrees under `D:\project\code\hermes-agent\.worktrees\`.
- Current `.worktrees/` directory is already gitignored by `D:\project\code\hermes-agent\.gitignore`.
- Functional Testing is mandatory after **every** PR.
- Every confirmed product defect found during a PR must add or tighten regression coverage before the PR is considered done.
- `scripts/run_tests.sh` is the canonical test wrapper, but in this Windows/WSL checkout the executable path is blocked by CRLF. Use the LF-normalized wrapper `tmp/run_tests_lf.sh` for actual execution until that environment issue is removed.
- Final success is not “all code merged”; final success is “all PRs completed + final full Functional Testing green”.

## Baseline assumptions

- Base integration branch/worktree: `codex/pr1-scope-foundation`
- Existing PR1 functional evidence already available in:
  - `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation\docs\superpowers\plans\2026-04-23-a-phase-functional-testing-results.md`
  - `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation\docs\superpowers\plans\2026-04-23-b-phase-functional-testing-results.md`
- Existing PR checklist:
  - `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation\docs\superpowers\plans\2026-04-23-enterprise-pr-rollout-checklist.md`

---

## Worktree and branch layout

### Active worktrees

- Base:
  - Worktree: `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation`
  - Branch: `codex/pr1-scope-foundation`
- Parallel execution worktrees to create:
  - `D:\project\code\hermes-agent\.worktrees\pr2-scoped-session-search`
  - `D:\project\code\hermes-agent\.worktrees\pr3-scoped-memory`
  - `D:\project\code\hermes-agent\.worktrees\pr4-scoped-skills-visibility`
  - `D:\project\code\hermes-agent\.worktrees\pr5-tool-policy-context-pack`
  - `D:\project\code\hermes-agent\.worktrees\pr6-session-actor`

### Branch names

- `codex/pr2-scoped-session-search`
- `codex/pr3-scoped-memory`
- `codex/pr4-scoped-skills-visibility`
- `codex/pr5-tool-policy-context-pack`
- `codex/pr6-session-actor`

### Parallelism policy

- Safe sibling branching:
  - PR2, PR3, and PR4 all branch from the same frozen PR1 baseline
- Safe parallel coding wave:
  - PR2 and PR4 can proceed in parallel
- Controlled overlap:
  - PR3 can begin in its own worktree, but its final implementation/test pass must happen after rebasing on the latest merged baseline because PR2 and PR3 both touch runtime plumbing around `run_agent.py`
- Serial follow-up:
  - PR5 starts only after PR2/PR3/PR4 are merged and stable
  - PR6 starts only after PR5 is stable

---

## Phase 0 - Freeze the current baseline and prepare execution lanes

### Task 1: Freeze PR1 foundation into an explicit execution base

**Why this comes first**
- Current worktree `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation` is a dirty tree.
- PR2/PR3/PR4 must not be forked directly from an ambiguous dirty state.
- Parallel worktrees should branch from one explicit PR1 baseline commit or local integration checkpoint.

**Files:**
- Inspect: `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation`
- Verify: current PR1 guardrail suites
- Create: one explicit baseline commit or local checkpoint branch before sibling worktrees are created

- [ ] **Step 1: Reconfirm PR1 guardrail on the current foundation tree**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-plan-base bash tmp/run_tests_lf.sh tests/gateway/test_session.py tests/gateway/test_fast_command.py
```

Expected: PASS.

- [ ] **Step 2: Freeze current PR1 worktree into one explicit execution base**

Acceptable outcomes:
- one local checkpoint commit on `codex/pr1-scope-foundation`, or
- one dedicated local base branch created from the current validated state

Requirement:
- PR2/PR3/PR4 sibling worktrees must all branch from the same frozen PR1 base, not from a dirty working tree.

### Task 2: Create isolated worktrees

**Files:**
- Create worktree: `D:\project\code\hermes-agent\.worktrees\pr2-scoped-session-search`
- Create worktree: `D:\project\code\hermes-agent\.worktrees\pr3-scoped-memory`
- Create worktree: `D:\project\code\hermes-agent\.worktrees\pr4-scoped-skills-visibility`
- Create worktree: `D:\project\code\hermes-agent\.worktrees\pr5-tool-policy-context-pack`
- Create worktree: `D:\project\code\hermes-agent\.worktrees\pr6-session-actor`

- [ ] **Step 1: Create PR2 worktree**

Run:

```bash
git -C /mnt/d/project/code/hermes-agent worktree add /mnt/d/project/code/hermes-agent/.worktrees/pr2-scoped-session-search -b codex/pr2-scoped-session-search codex/pr1-scope-foundation
```

- [ ] **Step 2: Create PR3 worktree**

Run:

```bash
git -C /mnt/d/project/code/hermes-agent worktree add /mnt/d/project/code/hermes-agent/.worktrees/pr3-scoped-memory -b codex/pr3-scoped-memory codex/pr1-scope-foundation
```

- [ ] **Step 3: Create PR4 worktree**

Run:

```bash
git -C /mnt/d/project/code/hermes-agent worktree add /mnt/d/project/code/hermes-agent/.worktrees/pr4-scoped-skills-visibility -b codex/pr4-scoped-skills-visibility codex/pr1-scope-foundation
```

- [ ] **Step 4: Create PR5 worktree**

Run:

```bash
git -C /mnt/d/project/code/hermes-agent worktree add /mnt/d/project/code/hermes-agent/.worktrees/pr5-tool-policy-context-pack -b codex/pr5-tool-policy-context-pack codex/pr1-scope-foundation
```

- [ ] **Step 5: Create PR6 worktree**

Run:

```bash
git -C /mnt/d/project/code/hermes-agent worktree add /mnt/d/project/code/hermes-agent/.worktrees/pr6-session-actor -b codex/pr6-session-actor codex/pr1-scope-foundation
```

- [ ] **Step 6: Verify worktrees**

Run:

```bash
git -C /mnt/d/project/code/hermes-agent worktree list --porcelain
```

Expected: all six worktrees are listed and each PR branch is attached exactly once.

### Task 3: Normalize test wrapper and isolated home roots

**Files:**
- Create/update: `tmp/run_tests_lf.sh`
- Create/update: `tmp/hermes-functional-pr2/`
- Create/update: `tmp/hermes-functional-pr3/`
- Create/update: `tmp/hermes-functional-pr4/`
- Create/update: `tmp/hermes-functional-pr5/`
- Create/update: `tmp/hermes-functional-pr6/`
- Create/update: `tmp/hermes-functional-final/`

- [ ] **Step 1: Ensure LF wrapper exists**

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

- [ ] **Step 2: Create per-PR isolated homes**

Run:

```bash
python - <<'PY'
from pathlib import Path
for name in [
    "tmp/hermes-functional-pr2",
    "tmp/hermes-functional-pr3",
    "tmp/hermes-functional-pr4",
    "tmp/hermes-functional-pr5",
    "tmp/hermes-functional-pr6",
    "tmp/hermes-functional-final",
]:
    base = Path(name)
    for rel in ("", "sessions", "cron", "memories", "skills", "logs"):
        (base / rel).mkdir(parents=True, exist_ok=True)
PY
```

---

## Phase 1 - PR1 finalization gate

### Task 4: Treat PR1 as merged baseline candidate

**Files:**
- Inspect/update if needed: `docs/superpowers/plans/2026-04-23-a-phase-functional-testing-results.md`
- Inspect/update if needed: `docs/superpowers/plans/2026-04-23-b-phase-functional-testing-results.md`
- Inspect/update if needed: `docs/superpowers/plans/2026-04-23-enterprise-pr-rollout-checklist.md`

- [ ] **Step 1: Reconfirm PR1 focused regression baseline**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr2 bash tmp/run_tests_lf.sh tests/agent/test_scope.py tests/test_hermes_state.py tests/gateway/test_session.py tests/gateway/test_background_process_notifications.py tests/gateway/test_async_memory_flush.py tests/gateway/test_agent_cache.py tests/run_agent/test_compression_persistence.py
```

Expected: PASS.

- [ ] **Step 2: If PR1 code changed during packaging, rerun independent extra validation**

Run:

```bash
bash -lc 'cd /mnt/d/project/code/hermes-agent/.worktrees/pr1-scope-foundation && export TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONHASHSEED=0 HERMES_HOME=tmp/hermes-functional-pr2 && source /home/fortytwo/.hermes/hermes-agent/venv/bin/activate && python -m pytest -o addopts= -n 4 tests/integration tests/e2e -vv'
```

Expected: PASS.

---

## Phase 2 - Parallel Wave A

### Task 5: PR2 Scoped Session Search (parallel lane A)

**Worktree**
- `D:\project\code\hermes-agent\.worktrees\pr2-scoped-session-search`

**Files:**
- Modify: `hermes_state.py`
- Modify: `tools/session_search_tool.py`
- Modify: `run_agent.py`
- Test: `tests/test_hermes_state.py`
- Test: `tests/tools/test_session_search.py`
- Test: `tests/run_agent/test_run_agent.py`
- Regression: adjacent gateway/agent persistence tests if search behavior regresses

- [ ] **Step 1: Implement PR2 in its worktree**
- [ ] **Step 2: Add/tighten regression tests for scope leakage, lineage filtering, and `SessionDB.get_compression_tip()` staying intra-scope**
- [ ] **Step 3: Run PR2 unit/component verification**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr2 bash tmp/run_tests_lf.sh tests/test_hermes_state.py tests/tools/test_session_search.py tests/run_agent/test_run_agent.py -k "invoke_tool" tests/gateway/test_session.py tests/run_agent/test_compression_persistence.py
```

Expected: PASS.

- [ ] **Step 4: Run PR2 Functional Testing wave**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr2 bash tmp/run_tests_lf.sh tests/agent/test_scope.py tests/test_hermes_state.py tests/tools/test_session_search.py tests/run_agent/test_run_agent.py -k "invoke_tool" tests/gateway/test_session.py tests/gateway/test_background_process_notifications.py tests/run_agent/test_compression_persistence.py tests/tools
```

Expected: PASS.

- [ ] **Step 5: If defects are found, add regression coverage before marking PR2 done**
- [ ] **Step 6: Mark PR2 ready to merge**

### Task 6: PR4 Scoped Skills Visibility (parallel lane B)

**Worktree**
- `D:\project\code\hermes-agent\.worktrees\pr4-scoped-skills-visibility`

**Files:**
- Create: `agent/skill_registry.py`
- Create: `agent/skill_visibility.py`
- Modify: `agent/skill_utils.py`
- Modify: `tools/skills_tool.py`
- Modify: `agent/skill_commands.py`
- Modify: `gateway/run.py`
- Modify: `tui_gateway/server.py`
- Modify: `hermes_cli/commands.py`
- Test: `tests/tools/test_skills_tool.py`
- Test: `tests/test_plugin_skills.py`
- Test: `tests/agent/test_external_skills.py`
- Test: `tests/agent/test_skill_commands.py`
- Test: `tests/hermes_cli/test_commands.py`
- Test: `tests/tui_gateway/test_protocol.py`
- Test: `tests/gateway/test_discord_slash_commands.py`

- [ ] **Step 1: Implement PR4 with full entrypoint consistency, not only tool-level filtering**
- [ ] **Step 2: Add/tighten regression tests for hidden-skill list/view bypasses and global cache leakage**
- [ ] **Step 3: Run PR4 unit/component verification**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr4 bash tmp/run_tests_lf.sh tests/tools/test_skills_tool.py tests/test_plugin_skills.py tests/agent/test_external_skills.py
```

Expected: PASS.

- [ ] **Step 4: Run PR4 Functional Testing wave**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr4 bash tmp/run_tests_lf.sh tests/tools/test_skills_tool.py tests/test_plugin_skills.py tests/agent/test_external_skills.py tests/tools tests/skills
```

Expected: PASS.

- [ ] **Step 5: Run entrypoint consistency tests for slash/help/autocomplete/gateway surfaces**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr4 bash tmp/run_tests_lf.sh tests/agent/test_skill_commands.py tests/hermes_cli/test_commands.py tests/tui_gateway/test_protocol.py tests/gateway/test_discord_slash_commands.py
```

Expected: PASS.

- [ ] **Step 6: If defects are found, add regression coverage before marking PR4 done**
- [ ] **Step 7: Mark PR4 ready to merge**

---

## Phase 3 - PR3 after PR2 rebase

### Task 7: PR3 Scoped Memory

**Dependency**
- Rebase `codex/pr3-scoped-memory` onto merged PR2 before final verification

**Worktree**
- `D:\project\code\hermes-agent\.worktrees\pr3-scoped-memory`

**Files:**
- Create: `agent/memory_namespace.py`
- Create: `agent/memory_backend.py`
- Modify: `tools/memory_tool.py`
- Modify: `run_agent.py`
- Modify: `gateway/run.py`
- Test: `tests/tools/test_memory_tool.py`
- Test: `tests/tools/test_memory_tool_import_fallback.py`
- Test: `tests/gateway/test_flush_memory_stale_guard.py`

- [ ] **Step 1: Rebase PR3 worktree onto merged PR2 baseline**
- [ ] **Step 2: Implement PR3 in its worktree**
- [ ] **Step 3: Add/tighten regression tests for namespace leakage and snapshot stability**
- [ ] **Step 4: Run PR3 unit/component verification**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr3 bash tmp/run_tests_lf.sh tests/tools/test_memory_tool.py tests/tools/test_memory_tool_import_fallback.py tests/gateway/test_flush_memory_stale_guard.py tests/gateway/test_async_memory_flush.py tests/gateway/test_agent_cache.py tests/run_agent/test_compression_persistence.py
```

Expected: PASS.

- [ ] **Step 5: Run PR3 Functional Testing wave**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr3 bash tmp/run_tests_lf.sh tests/tools/test_memory_tool.py tests/tools/test_memory_tool_import_fallback.py tests/gateway/test_flush_memory_stale_guard.py tests/gateway/test_async_memory_flush.py tests/gateway/test_agent_cache.py tests/run_agent/test_compression_persistence.py tests/gateway/test_session.py
```

Expected: PASS.

- [ ] **Step 6: If defects are found, add regression coverage before marking PR3 done**
- [ ] **Step 7: Mark PR3 ready to merge**

---

## Phase 4 - Serial closeout PRs

### Task 8: PR5 Tool Policy and Context Pack

**Start condition**
- PR2, PR3, and PR4 merged and green

**Worktree**
- `D:\project\code\hermes-agent\.worktrees\pr5-tool-policy-context-pack`

**Files:**
- Create: `agent/tool_policy.py`
- Create: `agent/context_pack.py`
- Create: `agent/enterprise_context_engine.py`
- Modify: `agent/context_engine.py`
- Modify: `model_tools.py`
- Modify: `run_agent.py`
- Test: `tests/agent/test_enterprise_context_engine.py`
- Test: `tests/run_agent/test_run_agent.py`
- Test: `tests/run_agent/test_provider_parity.py`
- Test: `tests/test_model_tools_async_bridge.py`

- [ ] **Step 1: Add explicit tests for tool policy and additive context injection**
- [ ] **Step 2: Implement PR5**
- [ ] **Step 3: Run PR5 unit/component verification**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr5 bash tmp/run_tests_lf.sh tests/agent/test_enterprise_context_engine.py tests/run_agent/test_run_agent.py tests/run_agent/test_provider_parity.py tests/test_model_tools_async_bridge.py
```

Expected: PASS.

- [ ] **Step 4: Run PR5 Functional Testing wave**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr5 bash tmp/run_tests_lf.sh tests/agent tests/run_agent tests/tools tests/gateway/test_agent_cache.py
```

Expected: PASS.

- [ ] **Step 5: Add regressions for every confirmed defect before marking PR5 done**

### Task 9: PR6 Session Actor / Run Queue

**Start condition**
- PR5 merged and green

**Worktree**
- `D:\project\code\hermes-agent\.worktrees\pr6-session-actor`

**Files:**
- Create: `gateway/run_queue.py`
- Create: `gateway/session_actor.py`
- Modify: `gateway/run.py`
- Test: `tests/gateway/test_run_queue.py`
- Test: `tests/gateway/test_session_actor.py`
- Test: `tests/gateway/test_fast_command.py`
- Test: `tests/gateway/test_background_process_notifications.py`
- Test: `tests/e2e/test_platform_commands.py`

- [ ] **Step 1: Add failing queue/actor tests first**
- [ ] **Step 2: Implement PR6**
- [ ] **Step 3: Run PR6 unit/component verification**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr6 bash tmp/run_tests_lf.sh tests/gateway/test_run_queue.py tests/gateway/test_session_actor.py tests/gateway/test_fast_command.py tests/gateway/test_background_process_notifications.py
```

Expected: PASS.

- [ ] **Step 4: Run PR6 Functional Testing wave**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-pr6 bash tmp/run_tests_lf.sh tests/gateway tests/e2e/test_platform_commands.py tests/integration
```

Expected: PASS when run in this PR worktree with LF wrapper for wrapper-covered suites and direct pytest for integration if needed.

- [ ] **Step 5: Add regressions for every confirmed defect before marking PR6 done**

---

## Phase 5 - Final full Functional Testing

### Task 10: Repo-wide final validation after all PRs land

**Files:**
- Update: `docs/superpowers/plans/2026-04-23-a-phase-functional-testing-results.md`
- Update: `docs/superpowers/plans/2026-04-23-b-phase-functional-testing-results.md`
- Update: `docs/superpowers/plans/2026-04-23-enterprise-pr-rollout-checklist.md`
- Update: `docs/superpowers/plans/2026-04-23-enterprise-parallel-execution-plan.md`
- Create/update: final execution report doc adjacent to this plan

- [ ] **Step 1: Wrapper-covered full sweep**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/cli
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/hermes_cli
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/agent
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/run_agent
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/gateway
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/tools
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/acp tests/tui_gateway
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/cron tests/skills
```

Expected: PASS.

- [ ] **Step 2: Wrapper-excluded independent integration sweep**

Run:

```bash
bash -lc 'cd /mnt/d/project/code/hermes-agent/.worktrees/pr1-scope-foundation && export TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONHASHSEED=0 HERMES_HOME=tmp/hermes-functional-final && source /home/fortytwo/.hermes/hermes-agent/venv/bin/activate && python -m pytest -o addopts= -n 4 tests/integration -vv'
```

Expected: PASS.

- [ ] **Step 3: Wrapper-excluded independent e2e sweep**

Run:

```bash
bash -lc 'cd /mnt/d/project/code/hermes-agent/.worktrees/pr1-scope-foundation && export TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONHASHSEED=0 HERMES_HOME=tmp/hermes-functional-final && source /home/fortytwo/.hermes/hermes-agent/venv/bin/activate && python -m pytest -o addopts= -n 4 tests/e2e -vv'
```

Expected: PASS.

- [ ] **Step 4: Spot-check critical real-chain regressions**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-final bash tmp/run_tests_lf.sh tests/gateway/test_session.py tests/gateway/test_fast_command.py tests/gateway/test_homeassistant.py
```

Expected: PASS.

- [ ] **Step 5: Update final execution report**

Record:
- all PRs completed
- all per-PR Functional Testing gates completed
- all final Functional Testing sweeps completed
- all newly added regressions
- any remaining environment-only constraints

---

## Continuous execution order

1. Create worktrees and test homes
2. Reconfirm PR1 baseline
3. Parallel execute PR2 and PR4
4. Rebase and execute PR3
5. Execute PR5
6. Execute PR6
7. Run final full Functional Testing
8. Close rollout only after final green evidence is documented

## Completion criteria

- [ ] PR1 baseline confirmed
- [ ] PR2 completed with Functional Testing + regressions
- [ ] PR3 completed with Functional Testing + regressions
- [ ] PR4 completed with Functional Testing + regressions
- [ ] PR5 completed with Functional Testing + regressions
- [ ] PR6 completed with Functional Testing + regressions
- [ ] Final full Functional Testing green
- [ ] Final execution report updated
