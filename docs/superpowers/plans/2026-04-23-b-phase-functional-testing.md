# B-Phase Functional Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute repo-wide functional testing for hermes-agent main user-facing surfaces after A-phase stabilizes the PR1 scope/session foundation.

**Architecture:** Reuse the isolated A-phase test environment and the LF-normalized wrapper so all B-phase suite runs stay reproducible on this Windows/WSL checkout. Run by functional surface in waves: CLI/config, agent/runtime, gateway, then tools/integration adapters; record defects and add regressions only after the failing behavior is confirmed.

**Tech Stack:** pytest, WSL bash wrapper, isolated `HERMES_HOME`, Hermes gateway, CLI, ACP, TUI gateway, MCP/tooling, cron/integration tests.

---

### Task 1: Lock B-phase execution baseline

**Files:**
- Inspect: `docs/superpowers/plans/2026-04-23-a-phase-functional-testing-results.md`
- Inspect: `tmp/run_tests_lf.sh`
- Create: `docs/superpowers/plans/2026-04-23-b-phase-functional-testing-results.md`

- [ ] **Step 1: Confirm the A-phase fix baseline before broadening scope**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway/test_session.py tests/gateway/test_fast_command.py
```

Expected: PASS. This is the minimal guardrail for the two fresh A-phase regressions before broad B-phase sweeps.

- [ ] **Step 2: Create the B-phase result log document**

Create:

- `docs/superpowers/plans/2026-04-23-b-phase-functional-testing-results.md`

Seed sections:

- execution environment
- wave results
- failures / blockers
- regression additions

### Task 2: Wave 1 - CLI and config-driven functional surfaces

**Files:**
- Test: `tests/cli/`
- Test: `tests/hermes_cli/`

- [ ] **Step 1: Run CLI functional suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/cli
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 2: Run hermes_cli configuration/model/auth surface suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/hermes_cli
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 3: Record counts and any failing files in the B-phase results doc**

Record:

- command
- pass/fail count
- failure file names
- whether failures are deterministic or environment-only

### Task 3: Wave 2 - agent core and run_agent runtime

**Files:**
- Test: `tests/agent/`
- Test: `tests/run_agent/`

- [ ] **Step 1: Run agent core suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/agent
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 2: Run run_agent runtime suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/run_agent
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 3: Record wave result**

Record the same evidence fields as Wave 1.

### Task 4: Wave 3 - gateway full functional surface

**Files:**
- Test: `tests/gateway/`

- [ ] **Step 1: Run full gateway suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 2: If failures appear, classify them before fixing**

Buckets:

- session/state boundary
- platform adapter behavior
- progress/streaming
- restart/recovery
- auth/provider routing
- environment-only

- [ ] **Step 3: Record wave result**

Record counts and failing files.

### Task 5: Wave 4 - tooling and external integration surfaces

**Files:**
- Test: `tests/tools/`
- Test: `tests/acp/`
- Test: `tests/tui_gateway/`
- Test: `tests/cron/`
- Test: `tests/integration/`
- Test: `tests/skills/`
- Test: `tests/e2e/`

- [ ] **Step 1: Run tooling suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/tools
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 2: Run ACP and TUI gateway suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/acp tests/tui_gateway
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 3: Run cron/integration/skills/e2e suite**

Run:

```bash
HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/cron tests/integration tests/skills tests/e2e
```

Expected: PASS or actionable deterministic failures only.

- [ ] **Step 4: Record wave result**

Record counts and failing files.

### Task 6: Defect inventory and regression backlog

**Files:**
- Modify: `docs/superpowers/plans/2026-04-23-b-phase-functional-testing-results.md`
- Modify if needed: failing test files adjacent to the reproduced defect

- [ ] **Step 1: Consolidate confirmed failures**

For each confirmed failure capture:

- reproducer command
- failing test name
- root-cause layer
- whether it is product defect or environment blocker

- [ ] **Step 2: Define regression additions for real product defects**

For each confirmed product defect, record:

- target test file
- minimal regression shape
- whether the fix belongs in A follow-up scope or B broad-surface scope

- [ ] **Step 3: Stop before broad refactors**

Only fix defects that directly block continuing B-phase execution or invalidate the test surface. Do not broaden into unrelated cleanup.
