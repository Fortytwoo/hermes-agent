# Enterprise PR Rollout Checklist

> **For agentic workers:** This document is the execution tracker for the enterprise scope rollout. It summarizes what each PR must deliver, the current status, the detailed task checklist, and the concrete acceptance bar before a PR can be considered complete.

**Goal:** Record the PR-by-PR rollout plan for enterprise scope/session isolation so execution can proceed in discrete, reviewable PRs.

**Source plans:**
- `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation\docs\superpowers\plans\2026-04-22-enterprise-scope-rollout.md`
- `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation\docs\superpowers\plans\2026-04-22-pr1-scope-foundation-detail.md`
- `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation\docs\superpowers\plans\2026-04-23-a-phase-functional-testing-results.md`
- `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation\docs\superpowers\plans\2026-04-23-b-phase-functional-testing-results.md`

---

## Rollout status snapshot

| PR | Theme | Status | Notes |
|---|---|---|---|
| PR1 | Scope Foundation | In code + verified | Scope/address foundation landed in current worktree; A/B functional testing completed |
| PR2 | Scoped Session Search | In code + verified | Local implementation complete; targeted + broad Functional Testing green after baseline test-stability fix |
| PR3 | Scoped Memory | In progress | Rebased onto PR2 baseline; implementation underway |
| PR4 | Scoped Skills Visibility | In code + verified | Local implementation complete; all entrypoint visibility tests and broad Functional Testing green |
| PR5 | Tool Policy and Context Pack | Deferred | Depends on PR1-PR4 being stable |
| PR6 | Run Queue and Session Actor | Deferred | Depends on earlier rollout proving stable |

## PR1 - Scope Foundation

**Objective**
- Introduce typed enterprise and routing boundaries without breaking legacy session keys, current gateway behavior, or prompt caching.

**Current status**
- Implemented in `codex/pr1-scope-foundation`
- Functional validation completed
- Not yet split into a standalone final PR artifact from this worktree

**PR content to complete**
- Add `EnterpriseScope`, `SessionAddress`, `SessionIdentity`
- Add scope/address resolver layer
- Extend gateway session objects with typed metadata
- Keep live key generation on legacy `agent:main:...`
- Add dual-stack parsing for legacy and scoped keys
- Add SQLite v7 enterprise/routing metadata persistence
- Thread enterprise metadata through `AIAgent` startup, recovery, compression, and gateway-owned agent launches
- Preserve existing prompt construction behavior

**Primary files**
- `agent/scope.py`
- `agent/scope_resolver.py`
- `gateway/session.py`
- `gateway/run.py`
- `hermes_state.py`
- `run_agent.py`
- `tests/agent/test_scope.py`
- `tests/gateway/test_session.py`
- `tests/gateway/test_background_process_notifications.py`
- `tests/gateway/test_async_memory_flush.py`
- `tests/gateway/test_agent_cache.py`
- `tests/run_agent/test_compression_persistence.py`
- `tests/test_hermes_state.py`

**Detailed task checklist**
- [x] Add typed enterprise, routing, and identity models
- [x] Add resolver that returns enterprise scope plus session address
- [x] Extend `SessionEntry` and `SessionContext` with typed metadata
- [x] Keep legacy session-key builder unchanged and add scoped-key builder separately
- [x] Add dual-stack `_parse_session_key()` compatibility
- [x] Add SQLite v7 additive schema for scope/routing metadata
- [x] Extend session lifecycle writes to persist typed metadata
- [x] Thread typed metadata through `AIAgent` and gateway startup/recovery/compression
- [x] Add focused regression coverage
- [x] Complete A-phase real-chain functional validation
- [x] Complete B-phase wrapper + independent integration/e2e validation
- [ ] Split/finalize PR1 commit stack and submit as dedicated PR if still needed

**Verification record**
- PR1 baseline suite: `325 passed`
- A-phase: real gateway / provider / MCP chain validated and documented
- B-phase: wrapper sweeps green
- Independent extra validation:
  - `tests/integration`: `57 passed, 1 skipped`
  - `tests/e2e`: `54 passed`

**Done definition**
- Typed scope metadata exists in runtime + SQLite
- Legacy session behavior still works
- Prompt caching behavior remains unchanged
- Gateway fallback paths still work
- Functional validation evidence is documented

---

## PR2 - Scoped Session Search

**Objective**
- Restrict session search and recent-session browsing to the active tenant/workspace/agent scope, without exposing scope controls to the model schema.

**PR content to complete**
- Add reusable scope WHERE-clause helper in `SessionDB`
- Apply scope filtering to recent listing, search, and compression-tip lookups
- Pass enterprise scope into session search from runtime, not from model-visible args
- Keep public tool schema unchanged
- Ensure lineage exclusion remains intra-scope only

**Primary files**
- `hermes_state.py`
- `tools/session_search_tool.py`
- `run_agent.py`
- `tests/test_hermes_state.py`
- `tests/tools/test_session_search.py`

**Detailed task checklist**
- [ ] Add internal `_build_scope_filters(...)` helper to `SessionDB`
- [ ] Apply scope filters to `list_sessions_rich(...)`
- [ ] Apply scope filters to `search_messages(...)` full-text/fallback paths
- [ ] Apply scope filters to `get_compression_tip(...)` so recent browse hints do not leak cross-scope
- [ ] Pass runtime `enterprise_scope` from `run_agent.py` into session search
- [ ] Extend `tools/session_search_tool.py` internals to accept `enterprise_scope`
- [ ] Keep tool schema unchanged for the model
- [ ] Add isolation tests for scoped vs unscoped callers and lineage-stop behavior
- [ ] Verify with:
  - `scripts/run_tests.sh tests/test_hermes_state.py`
  - `scripts/run_tests.sh tests/tools/test_session_search.py`
  - `scripts/run_tests.sh tests/run_agent/test_run_agent.py -k "invoke_tool"`
- [ ] Prepare PR2 commit/PR

**Done definition**
- Scoped callers only see sessions in the same tenant/workspace/agent
- Legacy unscoped behavior is preserved for unscoped callers
- No scope is derived from parsing `session_key` at tool level
- Compression guidance and lineage traversal stay intra-scope

**Current execution evidence**
- Local branch: `codex/pr2-scoped-session-search`
- Commits:
  - `8110f226` `test: isolate mcp oauth prefetch regressions`
  - `61e5125e` `feat: scope session search to enterprise context`
- Verification:
  - targeted regression: `567 passed`
  - broad Functional Testing wave: `3894 passed, 27 skipped`

---

## PR3 - Scoped Memory

**Objective**
- Separate memory storage by enterprise namespace while preserving the existing frozen snapshot behavior and file formats.

**PR content to complete**
- Introduce explicit memory namespace rules
- Add scoped memory backend with namespace-to-path resolution
- Keep memory snapshots frozen at session start
- Resolve enterprise scope at runtime, not in tool schema
- Preserve legacy no-scope path behavior

**Primary files**
- `agent/memory_namespace.py`
- `agent/memory_backend.py`
- `tools/memory_tool.py`
- `run_agent.py`
- `gateway/run.py`
- `tests/tools/test_memory_tool.py`
- `tests/tools/test_memory_tool_import_fallback.py`
- `tests/gateway/test_flush_memory_stale_guard.py`
- `tests/run_agent/test_compression_persistence.py`
- `tests/gateway/test_agent_cache.py`

**Detailed task checklist**
- [ ] Create `MemoryNamespace` model
- [ ] Define namespace rules for shared memory vs user memory
- [ ] Implement scoped backend path resolution using `get_hermes_home()`
- [ ] Refactor `tools/memory_tool.py` to use scoped backend internally
- [ ] Route gateway stale-guard flushes through the scoped backend in `gateway/run.py`
- [ ] Keep frozen snapshot semantics unchanged
- [ ] Ensure child sessions inherit the same enterprise memory namespace
- [ ] Add tests for namespace separation and legacy fallback
- [ ] Verify with:
  - `scripts/run_tests.sh tests/tools/test_memory_tool.py`
  - `scripts/run_tests.sh tests/tools/test_memory_tool_import_fallback.py`
  - `scripts/run_tests.sh tests/gateway/test_flush_memory_stale_guard.py`
  - `scripts/run_tests.sh tests/run_agent/test_compression_persistence.py`
  - `scripts/run_tests.sh tests/gateway/test_agent_cache.py`
- [ ] Prepare PR3 commit/PR

**Done definition**
- Same memory target under different enterprise scopes maps to different files
- Legacy no-scope storage still works
- Prompt-cache safety is preserved
- Gateway stale-guard behavior reads the correct scoped memory files

---

## PR4 - Scoped Skills Visibility

**Objective**
- Filter visible skills by enterprise scope without replacing the current skills system or breaking platform/disabled-skill filtering.

**PR content to complete**
- Add enterprise visibility policy layer
- Filter `skills_list()` after existing platform/disabled checks
- Enforce the same visibility policy in `skill_view()`
- Apply policy equally to built-in, plugin, and external-dir skills
- Keep slash/help/autocomplete/TUI/gateway entrypoints consistent with tool-level visibility
- Preserve current behavior when no enterprise scope/policy is configured

**Primary files**
- `agent/skill_registry.py`
- `agent/skill_visibility.py`
- `tools/skills_tool.py`
- `agent/skill_utils.py`
- `agent/skill_commands.py`
- `gateway/run.py`
- `tui_gateway/server.py`
- `hermes_cli/commands.py`
- `tests/tools/test_skills_tool.py`
- `tests/test_plugin_skills.py`
- `tests/agent/test_external_skills.py`
- `tests/agent/test_skill_commands.py`
- `tests/hermes_cli/test_commands.py`
- `tests/tui_gateway/test_protocol.py`
- `tests/gateway/test_discord_slash_commands.py`

**Detailed task checklist**
- [ ] Create skill visibility policy layer
- [ ] Default to allow-all when no policy is configured
- [ ] Apply visibility filtering in `skills_list()`
- [ ] Re-check visibility in `skill_view()` to block direct bypasses
- [ ] Ensure external skill directories and plugin skills follow the same policy
- [ ] Remove or isolate global skill-command caching that can leak cross-scope visibility
- [ ] Make tool, slash, help, autocomplete, TUI, and gateway entrypoints agree on visible skills
- [ ] Add tests for hidden skill list/view behavior, entrypoint consistency, and no-scope compatibility
- [ ] Verify with:
  - `scripts/run_tests.sh tests/tools/test_skills_tool.py`
  - `scripts/run_tests.sh tests/test_plugin_skills.py`
  - `scripts/run_tests.sh tests/agent/test_external_skills.py`
  - `scripts/run_tests.sh tests/agent/test_skill_commands.py`
  - `scripts/run_tests.sh tests/hermes_cli/test_commands.py`
  - `scripts/run_tests.sh tests/tui_gateway/test_protocol.py`
  - `scripts/run_tests.sh tests/gateway/test_discord_slash_commands.py`
- [ ] Prepare PR4 commit/PR

**Done definition**
- Skill visibility respects enterprise scope
- Existing platform and disabled-skill filtering still works
- No scope inference is derived from `session_key`
- Every user-facing skill entrypoint returns the same visibility result for the same scope

**Current execution evidence**
- Local branch: `codex/pr4-scoped-skills-visibility`
- Commits:
  - `8110f226` `test: isolate mcp oauth prefetch regressions`
  - `0ae2556d` `feat: scope skill visibility across entrypoints`
- Verification:
  - targeted skill visibility suites: `114 passed`
  - entrypoint consistency suites: `218 passed`
  - broad Functional Testing wave: `3970 passed, 25 skipped`

---

## PR5 - Deferred Tool Policy and Context Pack

**Objective**
- Separate tool authorization from visibility and package enterprise context into a deterministic runtime context pack.

**Status**
- Deferred until PR1-PR4 are stable

**PR content to complete**
- Add tool-policy layer
- Add typed context-pack object
- Keep enterprise context injection additive to user messages
- Do not rebuild system prompts mid-session

**Primary files**
- `agent/tool_policy.py`
- `agent/context_pack.py`
- `agent/enterprise_context_engine.py`
- `agent/context_engine.py`
- `model_tools.py`
- `run_agent.py`

**Detailed task checklist**
- [ ] Add tool-policy layer distinct from visibility
- [ ] Build typed context pack for enterprise context
- [ ] Keep runtime context injection additive in `run_agent.py`
- [ ] Add targeted tests for tool definitions and runtime context behavior
- [ ] Verify after PR1-PR4 are stable
- [ ] Prepare PR5 commit/PR

**Done definition**
- Tool call authorization is scope-aware
- Enterprise context injection remains cache-safe
- Context assembly is deterministic and testable

---

## PR6 - Deferred Run Queue and Session Actor

**Objective**
- Introduce per-session execution actors/queues so runtime ownership is explicit while preserving current external gateway semantics.

**Status**
- Deferred until earlier rollout proves stable

**PR content to complete**
- Extract per-session actor abstraction
- Move `_running_agents`, interrupt handling, and queued follow-up logic behind actor boundary
- Preserve current same-session serial / cross-session parallel behavior

**Primary files**
- `gateway/run_queue.py`
- `gateway/session_actor.py`
- `gateway/run.py`
- `tests/gateway/` queue/interrupt coverage

**Detailed task checklist**
- [ ] Add per-session actor abstraction
- [ ] Move queue + interrupt ownership behind actor boundary
- [ ] Preserve current externally visible behavior
- [ ] Migrate gateway tests that currently couple to `GatewayRunner._running_agents`
- [ ] Add explicit queue and interrupt coverage
- [ ] Prepare PR6 commit/PR

**Done definition**
- Session execution ownership is explicit
- Same-session serialism and cross-session parallelism are preserved
- Interrupt semantics remain stable

---

## Merge gate summary

### Milestone A gate (after PR4)
- [ ] Scope exists as first-class runtime object
- [ ] SQLite session metadata is scope-aware
- [ ] Session search is scope-isolated
- [ ] Memory is namespace-separated by enterprise scope
- [ ] Skills visibility is scope-aware
- [ ] Prompt caching behavior remains unchanged

### Milestone B gate (after PR6)
- [ ] Tool authorization is scope-aware
- [ ] Context pack is deterministic and additive
- [ ] Session actor/queue model is stable
- [ ] Gateway concurrency semantics remain unchanged externally

---

## Recommended execution order

1. PR1 finalization and standalone PR packaging
2. PR2 scoped session search and PR4 scoped skills visibility in parallel
3. PR3 scoped memory from the same sibling baseline, then rebase/final-verify after PR2
4. PR5 deferred authorization/context work
5. PR6 deferred queue/actor refactor

## Notes

- Current branch already covers the PR1 foundation plus functional validation evidence.
- PR2 and PR4 are the first parallel delivery wave from the frozen PR1 baseline.
- PR3 should start from the same sibling baseline but must rebase before final verification because it overlaps PR2 in `run_agent.py`.
- PR5 and PR6 should not start until PR2-PR4 are stable and reviewed.
- Baseline stabilization note: `29e16eb1` isolates MCP OAuth prefetch in four regression tests so Linux/CI broad Functional Testing does not stall on real discovery traffic.
