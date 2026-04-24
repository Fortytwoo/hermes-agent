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
| PR3 | Scoped Memory | In code + verified | Rebased onto PR2 baseline; local implementation complete and final merged-rollout Functional Testing green |
| PR4 | Scoped Skills Visibility | In code + verified | Local implementation complete; all entrypoint visibility tests and broad Functional Testing green |
| PR5 | Tool Policy and Context Pack | In code + verified | Local implementation complete and final merged-rollout Functional Testing green |
| PR6 | Run Queue and Session Actor | In code + verified | Local implementation complete and final merged-rollout Functional Testing green |

## PR1 - Scope Foundation

**Objective**
- Introduce typed enterprise and routing boundaries without breaking legacy session keys, current gateway behavior, or prompt caching.

**Current status**
- Implemented in `codex/pr1-scope-foundation`
- Functional validation completed
- Retained as the canonical rollout tracker/baseline branch; no extra standalone PR1 artifact is required beyond this local stack

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
- [x] Resolve PR1 packaging decision by keeping this branch as the canonical tracker/baseline instead of emitting an extra standalone artifact

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
- [x] Add internal `_build_scope_filters(...)` helper to `SessionDB`
- [x] Apply scope filters to `list_sessions_rich(...)`
- [x] Apply scope filters to `search_messages(...)` full-text/fallback paths
- [x] Apply scope filters to `get_compression_tip(...)` so recent browse hints do not leak cross-scope
- [x] Pass runtime `enterprise_scope` from `run_agent.py` into session search
- [x] Extend `tools/session_search_tool.py` internals to accept `enterprise_scope`
- [x] Keep tool schema unchanged for the model
- [x] Add isolation tests for scoped vs unscoped callers and lineage-stop behavior
- [x] Verify with:
  - `scripts/run_tests.sh tests/test_hermes_state.py`
  - `scripts/run_tests.sh tests/tools/test_session_search.py`
  - `scripts/run_tests.sh tests/run_agent/test_run_agent.py -k "invoke_tool"`
- [x] Prepare PR2 commit/PR

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
- [x] Create minimal namespace-rule layer in `agent/memory_namespace.py`
- [x] Define namespace rules for shared memory vs user memory
- [x] Implement scoped backend path resolution using `get_hermes_home()`
- [x] Refactor `tools/memory_tool.py` to use scoped backend internally
- [x] Route gateway stale-guard flushes through the scoped backend in `gateway/run.py`
- [x] Keep frozen snapshot semantics unchanged
- [x] Ensure child sessions inherit the same enterprise memory namespace
- [x] Add tests for namespace separation and legacy fallback
- [x] Verify with:
  - `scripts/run_tests.sh tests/tools/test_memory_tool.py`
  - `scripts/run_tests.sh tests/tools/test_memory_tool_import_fallback.py`
  - `scripts/run_tests.sh tests/gateway/test_flush_memory_stale_guard.py`
  - `scripts/run_tests.sh tests/run_agent/test_compression_persistence.py`
  - `scripts/run_tests.sh tests/gateway/test_agent_cache.py`
- [x] Prepare PR3 commit/PR

**Done definition**
- Same memory target under different enterprise scopes maps to different files
- Legacy no-scope storage still works
- Prompt-cache safety is preserved
- Gateway stale-guard behavior reads the correct scoped memory files

**Current execution evidence**
- Local branch: `codex/pr3-scoped-memory`
- Commits:
  - `8110f226` `test: isolate mcp oauth prefetch regressions`
  - `61e5125e` `feat: scope session search to enterprise context`
  - `2afd52f9` `feat: scope memory storage by enterprise context`
- Verification:
  - focused verification: `108 passed, 8 warnings`
  - broad Functional Testing wave: `7168 passed, 27 skipped, 176 warnings`

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
- [x] Create skill visibility policy layer
- [x] Default to allow-all when no policy is configured
- [x] Apply visibility filtering in `skills_list()`
- [x] Re-check visibility in `skill_view()` to block direct bypasses
- [x] Ensure external skill directories and plugin skills follow the same policy
- [x] Remove or isolate global skill-command caching that can leak cross-scope visibility
- [x] Make tool, slash, help, autocomplete, TUI, and gateway entrypoints agree on visible skills
- [x] Add tests for hidden skill list/view behavior, entrypoint consistency, and no-scope compatibility
- [x] Verify with:
  - `scripts/run_tests.sh tests/tools/test_skills_tool.py`
  - `scripts/run_tests.sh tests/test_plugin_skills.py`
  - `scripts/run_tests.sh tests/agent/test_external_skills.py`
  - `scripts/run_tests.sh tests/agent/test_skill_commands.py`
  - `scripts/run_tests.sh tests/hermes_cli/test_commands.py`
  - `scripts/run_tests.sh tests/tui_gateway/test_protocol.py`
  - `scripts/run_tests.sh tests/gateway/test_discord_slash_commands.py`
- [x] Prepare PR4 commit/PR

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

## PR5 - Tool Policy and Context Pack

**Objective**
- Separate tool authorization from visibility and package enterprise context into a deterministic runtime context pack.

**Status**
- Implemented in `codex/pr5-tool-policy-context-pack`
- Local verification completed
- Final integrated Functional Testing after cross-PR merge completed green

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
- [x] Add tool-policy layer distinct from visibility
- [x] Build typed context pack for enterprise context
- [x] Keep runtime context injection additive in `run_agent.py`
- [x] Add targeted tests for tool definitions and runtime context behavior
- [x] Verify implementation locally
- [x] Prepare PR5 commit/PR

**Done definition**
- Tool call authorization is scope-aware
- Enterprise context injection remains cache-safe
- Context assembly is deterministic and testable

**Current execution evidence**
- Local branch: `codex/pr5-tool-policy-context-pack`
- Commits:
  - `5d9d76a7` `test: isolate mcp oauth prefetch regressions`
  - `2d5b868a` `feat: add runtime tool policy and context pack`
- Verification:
  - focused verification: `429 passed`
  - broad Functional Testing wave: `6196 passed, 34 skipped, 36 warnings`

## PR6 - Run Queue and Session Actor

**Objective**
- Introduce per-session execution actors/queues so runtime ownership is explicit while preserving current external gateway semantics.

**Status**
- Implemented in `codex/pr6-session-actor`
- Local verification completed
- Final integrated Functional Testing after cross-PR merge completed green

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
- [x] Add per-session actor abstraction
- [x] Move queue + interrupt ownership behind actor boundary
- [x] Preserve current externally visible behavior
- [x] Migrate gateway tests that currently couple to `GatewayRunner._running_agents`
- [x] Add explicit queue and interrupt coverage
- [x] Prepare PR6 commit/PR

**Done definition**
- Session execution ownership is explicit
- Same-session serialism and cross-session parallelism are preserved
- Interrupt semantics remain stable

**Current execution evidence**
- Local branch: `codex/pr6-session-actor`
- Commits:
  - `5d9d76a7` `test: isolate mcp oauth prefetch regressions`
  - `a8866cce` `refactor: add gateway session run queue`
- Verification:
  - focused verification: `94 passed, 8 warnings`
  - broad Functional Testing wave: `3543 passed, 148 warnings`

---

## Merge gate summary

### Milestone A gate (after PR4)
- [x] Scope exists as first-class runtime object
- [x] SQLite session metadata is scope-aware
- [x] Session search is scope-isolated
- [x] Memory is namespace-separated by enterprise scope
- [x] Skills visibility is scope-aware
- [x] Prompt caching behavior remains unchanged

### Milestone B gate (after PR6)
- [x] Tool authorization is scope-aware
- [x] Context pack is deterministic and additive
- [x] Session actor/queue model is stable
- [x] Gateway concurrency semantics remain unchanged externally

**Merge gate note**
- Milestone A/B technical gates are complete based on current per-PR implementation and verification evidence.
- Final cross-PR integrated full Functional Testing after merge is complete.

## Final merged-rollout Functional Testing

**Integration branch**
- `codex/final-enterprise-rollout-ft`

**Merged PR sequence**
- `06bc8fb6` `feat: scope session search to enterprise context`
- `0ee3046e` `feat: scope skill visibility across entrypoints`
- `71f34c57` `feat: scope memory storage by enterprise context`
- `eb7ee735` `feat: add runtime tool policy and context pack`
- `e0b65237` `refactor: add gateway session run queue`

**Cross-PR regression fixes discovered during merged validation**
- `tests/conftest.py`
  - Clear leaked `TERMINAL_*` env for non-integration/e2e tests
  - Reset `tools.terminal_tool` module-level sandbox state between tests
- `tests/e2e/conftest.py`
  - Prefer importing real `discord` when installed so e2e collection does not poison voice integration tests with a mock package
- `tests/hermes_cli/test_skills_config.py`
  - Updated stale `SKILLS_DIR` mocking to use real tmp-path skill trees
- `tests/tools/test_delegate.py`
  - Removed leftover merge-conflict marker
- `tests/hermes_cli/test_provider_config_validation.py`
  - Capture warnings from `hermes_cli.config` explicitly so xdist logger-level pollution cannot hide provider-config warning assertions

**Verification evidence**
- merged `tests` wave:
  - `14352 passed, 41 skipped, 183 warnings`
- merged `tests/integration + tests/e2e` wave:
  - `111 passed, 1 skipped, 18 warnings`
- focused merged regressions:
  - `12 passed` for `tests/hermes_cli/test_provider_config_validation.py`

---

## Recommended execution order / current state

1. PR1-PR6 local implementation work is complete and individually verified.
2. Final cross-PR merged Functional Testing is complete and green.
3. Local rollout execution is complete; optional follow-up work is remote PR submission/reviewer handling if requested.

## Notes

- Current rollout state: PR1/PR2/PR3/PR4/PR5/PR6 are all in code and verified locally.
- PR3, PR5, and PR6 now have explicit local branch/commit/verification evidence recorded in this checklist.
- Final rollout risk is no longer merged-test readiness; any remaining work is optional remote PR/reviewer follow-up.
- Baseline stabilization note: `29e16eb1` / `8110f226` / `5d9d76a7` reflect the MCP OAuth prefetch regression-isolation baseline carried through the local branch stacks.
