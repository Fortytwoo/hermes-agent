# A-Phase Functional Testing Results (In Progress)

## Baseline regression status

All baseline layers were rerun against the isolated A-phase `HERMES_HOME` and passed:

- State layer
  - Command: `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/agent/test_scope.py tests/test_hermes_state.py`
  - Result: `172 passed`
- Orchestration layer
  - Command: `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway/test_session.py tests/gateway/test_background_process_notifications.py tests/gateway/test_async_memory_flush.py`
  - Result: `109 passed`
- Agent runtime layer
  - Command: `HERMES_HOME=tmp/hermes-functional-a bash tmp/run_tests_lf.sh tests/gateway/test_agent_cache.py tests/run_agent/test_compression_persistence.py`
  - Result: `44 passed, 8 warnings`

No deterministic baseline failures were observed in these three layers.

## Real MCP chain evidence

Isolated config:

- `tmp/hermes-functional-a/config.yaml`
- `tmp/mcp_probe_server.py`

Observed result under isolated `HERMES_HOME`:

- Registered tools:
  - `mcp_a_phase_probe_add_numbers`
  - `mcp_a_phase_probe_get_probe_value`
  - `mcp_a_phase_probe_get_prompt`
  - `mcp_a_phase_probe_list_prompts`
  - `mcp_a_phase_probe_list_resources`
  - `mcp_a_phase_probe_read_resource`
- Direct registry dispatch:
  - tool: `mcp_a_phase_probe_get_probe_value`
  - result: `{"result": "A_PHASE_PROBE_OK", "structuredContent": {"result": "A_PHASE_PROBE_OK"}}`

Conclusion: the isolated A-phase profile can complete a real stdio MCP registration and a real MCP tool call without mocks.

## Real gateway failure-path evidence

The webhook gateway was started from the isolated profile and exercised through the real HTTP entrypoint.

Observed runtime facts:

- Gateway start: `gateway_started=True`
- Health probe: `GET /health -> 200`
- Webhook entry:
  - `POST /webhooks/a-phase -> 202`
  - response body: `{"status": "accepted", "route": "a-phase", "event": "functional_test", "delivery_id": "..."}`
- Session persistence after the accepted webhook:
  - `state.db` exists
  - `sessions` row count: `1`
  - `messages` row count: `3`
  - assistant message persisted:
    - `⚠️ Provider authentication failed: No Codex credentials stored. Run `hermes auth` to authenticate. ...`

Conclusion: the real webhook -> `GatewayRunner` -> session persistence -> assistant failure response path is reproducible in the isolated profile. The success path remains blocked by missing isolated provider credentials.

## Environment blocker

Observed provider resolution behavior:

- Isolated A-phase profile:
  - `AuthError: No Codex credentials stored. Run \`hermes auth\` to authenticate.`
- Default user environment:
  - provider: `openai-codex`
  - credential present: yes
  - source: `device_code`

This means the machine currently has a usable default provider account, but the isolated A-phase profile does not yet have its own provider credential material.

## Temporary provider reuse validation

After explicit user approval, the default Hermes auth store was copied into the isolated A-phase profile only for this test round:

- source: default `~/.hermes/auth.json`
- target: isolated `tmp/hermes-functional-a/auth.json`

Isolated runtime resolution then succeeded:

- provider: `openai-codex`
- source: `device_code`
- api key present: yes
- base URL present: yes

## Provider and MCP component isolation

To separate gateway problems from provider/MCP problems, the same isolated profile was exercised directly through `AIAgent`.

### Provider-only

Prompt:

- `Reply with exactly PROVIDER_OK`

Observed result:

- completed successfully
- elapsed: about `3.54s`
- final response: `PROVIDER_OK`

### Provider + MCP direct

Prompt:

- `Use the MCP probe tool exactly once to retrieve the fixed token, then reply with exactly that token and nothing else.`

Observed result:

- completed successfully
- elapsed: about `6.11s`
- tool call emitted:
  - `mcp_a_phase_probe_get_probe_value`
- tool result persisted in memory:
  - `{"result": "A_PHASE_PROBE_OK", ...}`
- final response:
  - `A_PHASE_PROBE_OK`

Conclusion: provider credentials, provider inference, MCP registration, and MCP tool calling all work in the isolated A-phase profile. The remaining success-path failure is inside the gateway layer.

## Fix implementation and regression status

Two product defects were fixed and regression coverage was added before re-running the A-phase chain.

### Added regression tests

- `tests/gateway/test_session.py`
  - `TestSessionStoreSQLiteScopePersistence.test_new_session_passes_scope_and_address_to_sqlite`
- `tests/gateway/test_fast_command.py`
  - `test_run_agent_passes_session_boundaries_to_fresh_agent`

### RED verification

Before the fix:

- `test_new_session_passes_scope_and_address_to_sqlite`
  - failed with missing `enterprise_scope` in `SessionDB.create_session(...)` kwargs
- `test_run_agent_passes_session_boundaries_to_fresh_agent`
  - failed with `NameError: name 'session_entry' is not defined`

### GREEN verification

After the fix, both new regression tests passed.

### Broader regression rerun

Command group rerun:

- `tests/agent/test_scope.py`
- `tests/test_hermes_state.py`
- `tests/gateway/test_session.py`
- `tests/gateway/test_background_process_notifications.py`
- `tests/gateway/test_async_memory_flush.py`
- `tests/gateway/test_agent_cache.py`
- `tests/run_agent/test_compression_persistence.py`
- `tests/gateway/test_fast_command.py`
- `tests/gateway/test_run_progress_topics.py`
- `tests/gateway/test_session_boundary_hooks.py`

Observed result:

- `359 passed, 8 warnings`

Warnings were the same websockets deprecation warnings already seen in the earlier baseline.

## Confirmed defect from the reproduced failure path

### F1. SessionDB row loses typed scope/address metadata on early gateway-created sessions

Evidence:

- Reproduced webhook run persisted a `sessions` row with all of these fields `NULL`:
  - `tenant_id`
  - `workspace_id`
  - `agent_id`
  - `chat_id`
  - `thread_id`
  - `chat_type`
  - `model`
  - `model_config`
- Code path in `gateway/session.py` creates the SQLite session row using only:
  - `session_id`
  - `source`
  - `user_id`
- `SessionDB.create_session()` uses `INSERT OR IGNORE`, so a later agent-side create cannot backfill the missing typed metadata into the existing row.

Primary evidence lines:

- `gateway/session.py:868-883`
- `hermes_state.py:406-444`
- `run_agent.py:1382-1397`

Impact:

- The new PR1 typed boundary data is not reliably persisted in SQLite for gateway-created sessions when the row is pre-created before agent initialization.
- This is confirmed on the provider-failure path and the code path strongly suggests the same loss can affect first-turn success paths unless a later explicit update/backfill exists.

Regression backlog candidate:

- Add a gateway integration test that forces early provider failure after session creation and asserts the resulting `state.db.sessions` row still contains scoped metadata and session address fields.
 
Status:

- fixed for gateway pre-created rows in `SessionStore.get_or_create_session()`
- fixed for gateway reset-created rows in `SessionStore.reset_session()`

### F2. First gateway provider-backed turn crashes before agent creation because `_run_agent()` references `session_entry` out of scope

Reproduction:

1. start `GatewayRunner` with webhook enabled,
2. use an isolated profile with valid provider credentials and working MCP config,
3. submit a first-turn gateway event,
4. gateway returns a user-facing error:
   - `Sorry, I encountered an error (NameError).`
   - `name 'session_entry' is not defined`

Primary code evidence:

- `gateway/run.py:9157-9208`
- `gateway/run.py:9702-9729`

Observed root cause:

- `_run_agent(...)` does not define or receive `session_entry`,
- but the fresh-agent construction path dereferences:
  - `session_entry.enterprise_scope`
  - `session_entry.session_address`

Impact:

- The first successful provider-backed gateway turn cannot start.
- This blocks:
  - webhook success-path testing,
  - real gateway provider+MCP end-to-end completion,
  - any first-turn route that needs to create a fresh `AIAgent`.

Why the earlier provider-failure path still produced an assistant error:

- provider-auth failure returns early before the fresh-agent construction branch,
- so the NameError stays hidden until valid credentials are present.

Regression backlog candidate:

- Add a gateway test that exercises `_run_agent()` with a valid provider path on a fresh session and asserts no `NameError` occurs on first-turn agent construction.
- Add a webhook integration test that posts one real event, waits for completion, and asserts:
  - the transcript contains user + tool + assistant messages,
  - the tool name `mcp_a_phase_probe_get_probe_value` appears,
  - the final assistant response is `A_PHASE_PROBE_OK`.

Status:

- fixed by threading `session_entry` through `_run_agent(...)` and falling back to session-store lookup when it is not passed explicitly

## Real gateway success-path verification after fixes

After applying F1/F2 fixes, the full isolated A-phase success chain was rerun through the real webhook gateway:

- gateway start: `gateway_started=True`
- health: `GET /health -> 200`
- webhook entry: `POST /webhooks/a-phase -> 202`
- terminal result: `probe_token_seen`

Persisted SQLite session snapshot:

- source: `webhook`
- user_id: `webhook:a-phase`
- agent_id: `main`
- chat_id: `webhook:a-phase:a-phase-success-...`
- chat_type: `webhook`
- model: `gpt-5.4`

Persisted messages for the successful turn:

1. `user`
2. `assistant` with `finish_reason="tool_calls"`
3. `tool` containing `A_PHASE_PROBE_OK`
4. `assistant` final response `A_PHASE_PROBE_OK`

Conclusion: the isolated A-phase real chain now completes end-to-end:

1. real webhook gateway entry,
2. real provider-backed turn,
3. real MCP tool call,
4. persisted SQLite session/messages,
5. typed session address fields preserved on the created session row.

## Remaining work for A phase

The original A-phase target is now satisfied for:

- baseline regression layers,
- real MCP registration/call,
- real webhook/provider/MCP success path,
- confirmed failure-path reproduction,
- regression additions for the fixed defects.

If we continue, the next logical step is B phase: expand from PR1 chain validation to broader hermes-agent functional surface coverage.
