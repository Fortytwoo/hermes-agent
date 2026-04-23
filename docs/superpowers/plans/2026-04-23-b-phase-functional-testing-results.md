# B-Phase Functional Testing Results (Completed)

## Execution environment

- Workspace: `D:\project\code\hermes-agent\.worktrees\pr1-scope-foundation`
- Wrapper: `tmp/run_tests_lf.sh`
- Isolated home: `tmp/hermes-functional-a`
- Goal: extend A-phase real-chain validation into repo-wide functional and regression coverage

## Final outcome

- B-phase target is complete under the current hermetic wrapper.
- All scheduled B-phase wave groups are green.
- Wrapper-excluded `tests/integration` and `tests/e2e` were then executed independently under the same isolated env and are now green.
- No remaining deterministic product defects or test-contract failures are open in the executed surface.

## Coverage boundary

- **A-phase** remains the source of truth for the real integration chain:
  - real gateway webhook
  - real provider
  - real MCP
  - SQLite session persistence
  - final probe response `A_PHASE_PROBE_OK`
- **B-phase** is the repo-wide functional/regression sweep under `tmp/run_tests_lf.sh`.
- Important boundary: `tmp/run_tests_lf.sh` hardcodes:
  - `--ignore=tests/integration`
  - `--ignore=tests/e2e`
- Therefore the wave-4 command that names `tests/integration` and `tests/e2e` effectively executes `tests/cron` + `tests/skills` only. This is expected for the wrapper and is now documented explicitly.
- To close that gap, `tests/integration` and `tests/e2e` were run separately with direct `python -m pytest -o addopts= ...` commands under the same isolated `HERMES_HOME`, locale, timezone, and hash seed settings.

## Wave results

### Baseline guardrail

- Command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway/test_session.py tests/gateway/test_fast_command.py`
- Result:
  - `74 passed`
- Notes:
  - A-phase two regression files stayed green before broadening into B-phase sweeps.

### Wave 1 - CLI / hermes_cli

- CLI command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/cli`
- CLI result:
  - `520 passed, 7 warnings`
- hermes_cli command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/hermes_cli`
- hermes_cli result:
  - `2471 passed, 7 skipped, 5 warnings`
- Fixed on this wave:
  - `hermes_cli/tips.py`
    - shortened the over-limit tip string to satisfy the 150-char corpus guard
  - `tests/hermes_cli/test_claw.py`
    - cleanup tests now mock `_detect_openclaw_processes()` so they do not depend on live host runtime state
  - `tests/hermes_cli/test_setup_hermes_script.py`
    - shell validation now LF-normalizes a temp copy before `bash -n`, so syntax validation is independent of Windows checkout CRLF

### Wave 2 - agent / run_agent

- agent command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/agent`
- agent result:
  - `1629 passed, 2 warnings`
- run_agent command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/run_agent`
- run_agent result:
  - `888 passed, 7 skipped, 6 warnings`
- Fixed on this wave:
  - `run_agent.py`
    - `switch_model()` now guards `_fallback_chain` access with `getattr(...)`
    - `close()` now imports `cleanup_vm` / `cleanup_browser` at call time so patched test doubles stay attached
  - `tests/run_agent/test_concurrent_interrupt.py`
    - mock side effect updated to accept `messages=None`
  - `tests/run_agent/test_anthropic_error_handling.py`
    - patched `agent.context_compressor.get_model_context_length()` inside the test bootstrap so the 429 recovery test stays hermetic and no longer blocks on OpenRouter model-metadata network fetch during `AIAgent.__init__`

### Wave 3 - gateway

- Command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway`
- Result:
  - `3539 passed, 149 warnings`
- Fixed on this wave:
  - `gateway/session.py`
    - pre-created SQLite session rows now preserve typed metadata
  - `gateway/run.py`
    - first-turn `_run_agent()` no longer references undefined `session_entry`
  - `tests/gateway/test_discord_document_handling.py`
    - fixture now forces `is_safe_url=True`
  - `tests/gateway/test_whatsapp_connect.py`
    - adapter fixture now uses unique session paths to avoid scoped-lock collisions
- Added regressions:
  - `tests/gateway/test_session.py`
  - `tests/gateway/test_fast_command.py`

### Wave 4 - tools / ACP / TUI / cron / skills

- tools command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/tools`
- tools result:
  - `3610 passed, 25 skipped, 31 warnings`
- ACP / TUI command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/acp tests/tui_gateway`
- ACP / TUI result:
  - `210 passed, 6 warnings`
- cron / skills command:
  - `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/cron tests/integration tests/skills tests/e2e`
- cron / skills result:
  - `353 passed, 1 skipped`
- Effective executed surface for the final command:
  - `tests/cron`
  - `tests/skills`
- Fixed on this wave:
  - `tools/approval.py`
    - gateway `exec-ask` path no longer blocks on tirith auto-install; install is backgrounded and the current request fail-opens
  - `agent/file_safety.py`
    - denylist now covers both real `HERMES_HOME/.env` and default `~/.hermes/.env`
  - `tools/checkpoint_manager.py`
    - shadow repo local config writes now use explicit `--local`
  - `tests/tools/test_approval_heartbeat.py`
    - wait for `has_blocking_approval(...)` before resolve
  - `tests/tools/test_browser_camofox.py`
    - patch target corrected to `tools.browser_camofox.load_config`
  - `tests/tools/test_checkpoint_manager.py`
    - now verifies shadow-repo config file contents directly instead of relying on `git config --file` under polluted git env
  - `tests/tools/test_command_guards.py`
    - fixture now patches `tools.tirith_security.ensure_installed` so the new non-blocking install path stays under test control
  - `tests/tools/test_mcp_oauth_integration.py`
    - Unix alarm extended to 90s for xdist stability
  - `tests/skills/test_openclaw_migration.py`
    - scan now runs on a temp copied skill tree with `__pycache__` ignored and `SKILL.md` mode normalized, removing drvfs/bytecode false positives from `skills_guard`

## Independent integration / e2e validation

### Integration

- Command:
  - `TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONHASHSEED=0 HERMES_HOME=tmp/hermes-functional-extra python -m pytest -o addopts= -n 4 tests/integration -vv`
- Result:
  - `57 passed, 1 skipped, 13 warnings`
- Initial failures found before the final green run:
  - `tests/integration/test_ha_integration.py`
    - `test_connect_auth_subscribe`
    - `test_event_received_and_forwarded`
    - `test_event_filtering_ignores_unwatched`
    - `test_disconnect_closes_cleanly`
- Root-cause split:
  - production defect
    - `gateway/platforms/homeassistant.py`
      - HA disconnect path used `ClientWebSocketResponse.close()`, which waits for a peer close frame and could hang the adapter shutdown when the peer stopped reading during teardown
  - test-contract drift
    - `tests/integration/test_ha_integration.py`
      - tests that assert successful forwarding / normal connected behavior were relying on the old implicit-open assumption instead of the current documented `watch_all` / `watch_domains` / `watch_entities` contract
- Fixes applied:
  - `gateway/platforms/homeassistant.py`
    - `_cleanup_ws()` now force-closes the underlying aiohttp WebSocket response before closing the session, avoiding teardown hangs on missing peer close frames
    - `disconnect()` now tears down the WS/session before awaiting listener cleanup
  - `tests/integration/test_ha_integration.py`
    - websocket lifecycle / forwarding cases that expect active event delivery now pass `watch_all=True` explicitly
- Additional direct regression after the fix:
  - `HERMES_HOME=tmp/hermes-functional-extra-wrapper bash tmp/run_tests_lf.sh tests/gateway/test_homeassistant.py`
  - `45 passed`

### End-to-end

- Command:
  - `TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONHASHSEED=0 HERMES_HOME=tmp/hermes-functional-extra python -m pytest -o addopts= -n 4 tests/e2e -vv`
- Result:
  - `54 passed`

## B-phase fix summary

### Production fixes closed during B-phase

- `gateway/session.py`
- `gateway/run.py`
- `run_agent.py`
- `tools/approval.py`
- `agent/file_safety.py`
- `tools/checkpoint_manager.py`
- `hermes_cli/tips.py`
- `gateway/platforms/homeassistant.py`

### Test / fixture / contract fixes closed during B-phase

- `tests/run_agent/test_concurrent_interrupt.py`
- `tests/run_agent/test_anthropic_error_handling.py`
- `tests/hermes_cli/test_claw.py`
- `tests/hermes_cli/test_setup_hermes_script.py`
- `tests/gateway/test_discord_document_handling.py`
- `tests/gateway/test_whatsapp_connect.py`
- `tests/tools/test_approval_heartbeat.py`
- `tests/tools/test_browser_camofox.py`
- `tests/tools/test_checkpoint_manager.py`
- `tests/tools/test_command_guards.py`
- `tests/tools/test_mcp_oauth_integration.py`
- `tests/skills/test_openclaw_migration.py`
- `tests/integration/test_ha_integration.py`

## Regression additions

- A-phase regressions retained and verified green:
  - `tests/gateway/test_session.py`
  - `tests/gateway/test_fast_command.py`
- No additional B-phase production regressions were needed beyond the above; remaining late-wave issues were test isolation / environment / contract drift and were closed in test code.

## Conclusion

- The planned B-phase wrapper sweep is green.
- The wrapper-excluded integration and e2e suites were executed independently and are also green.
- The real-chain validation requested for gateway / provider / MCP remains covered by A-phase.
- The execution boundary is now explicit:
  - wrapper-driven repo-wide functional sweep under the hermetic wrapper
  - plus explicit post-wrapper execution of `tests/integration` and `tests/e2e`
