---
name: animus-agent-operations
description: Run and inspect Animus agent executions, direct provider runs, agent control, status, project-scoped agent memory, agent message channels, and human-in-the-loop interactions.
user_invocable: false
auto_invoke: true
animus_version: "0.5.15"   # animus CLI surface this skill targets
---

# Agent Operations

Use `animus agent` for direct agent execution and inspection outside the full
workflow pipeline, or for project-scoped memory, message channels, and the
human-in-the-loop interactions inbox.

Provider execution requires provider plugins:

```bash
animus plugin install-defaults
animus daemon preflight
```

## Profiles

```bash
animus agent list
animus agent get --id architect
```

Profiles come from resolved workflow config and packs. Use
`animus workflow config get` when a profile is missing.

## Direct Agent Runs

```bash
animus agent run --tool claude --model claude-sonnet-4-6 --prompt "Review the auth module" --cwd .
animus agent run --tool codex --model gpt-5.5 --prompt "Implement TASK-001" --timeout-secs 1800
animus agent run --run-id run-auth-review --tool claude --prompt "Audit auth" --detach
```

Useful flags:

- `--run-id <ID>` sets a stable run id; otherwise Animus generates one.
- `--tool <TOOL>` selects provider CLI such as `claude`, `codex`, or `gemini`.
- `--model <MODEL>` overrides the configured model for that tool.
- `--prompt <TEXT>` sends direct prompt text.
- `--reasoning-effort low|medium|high` overrides provider reasoning effort (also settable as `reasoning_effort` on agent profiles and phase `runtime`).
- `--permission-mode <MODE>` forwards a provider permission/approval mode verbatim (claude `default|acceptEdits|bypassPermissions|plan`, codex `untrusted|on-failure|on-request|never`, gemini `default|auto_edit|yolo`). Precedence: flag > `permission_mode` in `--context-json` > the `--agent` profile's `permission_mode` field. Unknown values warn but pass through.
- `--approvals` enables kernel-mediated approvals: transports route permission decisions through the `animus.agent.request_approval` MCP tool (claude wires it as `--permission-prompt-tool`; other providers get a prompt instruction block). Implied when the `--agent` profile declares an `approval_policy`.
- `--cwd <PATH>` must resolve inside the project root.
- `--timeout-secs <N>` caps the run.
- `--context-json <JSON>` passes agent context.
- `--runtime-contract-json <JSON>` overrides runtime contract fields.
- `--detach` returns immediately.
- `--stream true|false` controls stdout event streaming.
- `--save-jsonl true|false` controls persisted run logs.
- `--jsonl-dir <PATH>` overrides persisted run log location.
- `--start-runner true|false` controls automatic runner startup.

MCP wiring for a run (the resolved server set reaches the provider itself as
`extras.mcp_servers` on all four providers, for both `agent run` and `chat`;
secret-bearing/OAuth servers are rewritten to `animus-mcp-proxy` stdio
entries so tokens never reach CLI configs or argv):

- `--agent <AGENT_ID>` gives the run that profile's declared MCP servers (skipped when a caller-supplied runtime contract is present — it is never clobbered).
- `--skill <SKILL>` adds a skill's declared MCP servers (unioned with the profile's). An unknown skill name is an error.
- `--mcp-server <NAME>` wires an extra MCP server by name (repeatable; `animus` selects the built-in stdio surface).
- `--no-animus-mcp` drops the built-in `animus` MCP server from the resolved set.

### Skills apply fully on ad-hoc runs (v0.5.14)

`--skill` on `animus agent run` / `animus chat send` applies the skill's FULL
definition, not just MCP servers + tool policy: prompt `prefix`/`directives`/
`suffix` wrap the outgoing prompt, `prompt.system` rides the session
`system_prompt`, `extra_args`/`codex_config_overrides` graft onto the runtime
contract's `cli.launch` block, skill `env` rides the request env, and the
skill's `model`/`timeout_secs` apply when not explicitly given. Precedence per
field: explicit CLI flags / context-json > skill > defaults. A caller-supplied
`--runtime-contract-json` (or `runtime_contract` in `--context-json`) disables
skill application entirely. On `animus chat send`, a launch-affecting skill
forces full-history replay instead of native session resume so launch flags
reach every turn's provider process.

## Control and Status

```bash
animus agent status --run-id <run-id>
animus agent control --run-id <run-id> --action pause
animus agent control --run-id <run-id> --action resume
animus agent control --run-id <run-id> --action terminate
```

For detailed payloads, pair status with:

```bash
animus output monitor --run-id <run-id>
animus output jsonl --run-id <run-id> --entries
```

## Agent Memory

```bash
animus agent memory get --agent architect
animus agent memory append --agent architect --text "Prefer existing billing abstractions." --source operator-note
animus agent memory clear --agent architect
```

The top-level MCP memory tools are more granular:

- `animus.memory.get`
- `animus.memory.list`
- `animus.memory.append`
- `animus.memory.clear`

Two gates on the agent profile (workflow YAML `agents:` block):

- `capabilities: { memory: true }` injects the memory MCP server into a
  spawned phase agent's runtime contract (exposes `animus.memory.*` only).
- `memory: { enabled: true }` loads recent entries into the phase prompt and
  appends a short "Coordination tools" coaching paragraph.

Memory has a FIFO retention cap: `memory.max_entries` per profile (default
200; oldest entries trim on append; `0` is rejected). Appends/clears emit
`agent-memory-updated` daemon events; message sends emit `agent-message-sent`
(reads emit nothing).

## Agent Messages

```bash
animus agent message send --channel design-review --from architect --to auditor --text "Please check TASK-001" --workflow-id wf-123 --phase-id review
animus agent message list --channel design-review --limit 25
animus agent message list --agent architect
```

Use message channels for coordination between configured profiles. Keep durable
facts in memory; keep run-specific coordination in messages. Memory prompt
injection is per-agent (an agent sees only its own entries); cross-agent reads
go through `animus.memory.get` with the other agent's id.

## Interactions (human-in-the-loop)

Agents escalate to humans with the blocking MCP tools `animus.agent.ask`
(question; block-mode timeout returns a structured error telling the agent to
proceed on best judgment) and `animus.agent.request_approval` (approval;
block-mode timeout denies, fail closed). Default timeout 600s, max 3600s.
Pending requests park under `~/.animus/<repo-scope>/interactions/` until
answered:

```bash
animus agent interactions list              # pending; --all includes answered/expired
animus agent interactions show <id>
animus agent interactions answer <id> --text "Use option B"     # question
animus agent interactions answer <id> --allow                   # approval (or --deny, optionally --message)
animus agent interactions answer <id> --allow --remember        # echo localSettings suggestions as updatedPermissions
animus agent interactions answer <id> --allow --updated-input '{"command":"rm -rf build/sandbox"}'
animus agent interactions answer <id> \
  --select "Format=Summary" --select "2=Introduction,Conclusion" \
  --text "keep it short"                    # structured AskUserQuestion record
```

Answer flags: `--text`, `--allow`/`--deny`, `--message`, repeatable
`--select "<question|header|1-based index>=<label[,label...]>"` for structured
questions, `--remember` and `--updated-input <JSON>` (with `--allow`), and
`--by <NAME>` (defaults to `human`).

Key mechanics:

- **Approval policy**: a profile's `approval_policy` (`auto_allow`/`auto_deny`
  glob lists + `default: ask|allow|deny`) is consulted before escalating;
  `auto_deny` wins on overlap (fail closed). Declaring one implies
  `--approvals`. It composes with `permission_mode` (transport-level guard) —
  neither overrides the other.
- **Block vs suspend**: ad-hoc runs default to `wait: "block"` (the tool call
  parks). When the MCP server is pinned to a workflow (`animus mcp serve
  --workflow-id <ID>` or `ANIMUS_MCP_WORKFLOW_ID`) the default is suspend: the
  tool returns `{ status: "pending", interaction_id, instruction }`, the
  workflow pauses, and answering resumes it with the decision as session
  feedback. If the resume spawn fails, the answer still succeeds and carries a
  `workflow_resume.guidance` command.
- **SDK conformance**: `animus.agent.request_approval` doubles as the claude
  CLI's `--permission-prompt-tool` (invoked with `{tool_name, input,
  tool_use_id}`, answered with the SDK `{behavior: allow|deny, ...}` payload).
  Native `AskUserQuestion` calls become structured Question records
  (`questions[]`) in the same inbox, answered with `--select`/`--text`.
- **Identity pins**: `animus mcp serve --agent-id <ID>` pins the identity used
  by the blocking tools (env fallback `ANIMUS_MCP_AGENT_ID`) so a payload
  `agent_id` cannot select a looser sibling policy; `--management` exposes the
  `animus.interactions.*` inbox tools (off by default so agent-injected
  servers cannot answer their own approvals).
- **Observability**: `interaction_created` / `interaction_answered` /
  `interaction_expired` records land in `animus daemon events` (one-shot by
  default; `--follow` streams), each with a one-line summary and a
  ready-to-run `answer_command`; installed notifier plugins are pushed fresh
  escalations best-effort.

Note: `animus approval` is a different store — it gates destructive git
operations (e.g. `git worktree prune`), not agent escalations.

## MCP Tools

Direct agent tools:

- `animus.agent.list`, `get`, `run`, `control`, `status`
- `animus.agent.memory.get`, `append`, `clear`
- `animus.agent.message.send`, `list`
- `animus.agent.ask`, `request_approval` — blocking human escalation (support `wait: block|suspend`)
- `animus.interactions.list`, `answer` — inspect and answer pending escalations; only registered on `animus mcp serve --management`

Top-level memory tools (also the only family a memory-capable workflow agent
receives via the injected sidecar):

- `animus.memory.get`, `list`, `append`, `clear`

## Troubleshooting

- Provider tool is missing: `SessionBackendResolver` hard-errors with the exact install command — run it, or `animus plugin install-defaults`, then `animus daemon preflight`.
- Provider health: `animus plugin status` (per-provider install state + aggregate `provider_plugins_healthy`); `animus daemon health` carries the same `provider_plugins_healthy` flag.
- Run appears stuck: inspect `animus daemon observe` (front-door), `animus daemon stream --run <run-id>`, and `animus output monitor --run-id <run-id>`. Check `animus agent interactions list` — it may be parked on a pending question or approval.
- Orphaned provider CLI processes: `animus doctor` detects them; `--fix` prunes dead tracker entries (live PIDs get a manual suggestion).
- Memory tools unavailable inside a workflow phase: the profile needs `capabilities: { memory: true }`; prompt injection additionally needs `memory: { enabled: true }`.

## Differences on installed v0.5.14

This skill documents the **v0.5.15** surface (see `animus_version`). On an installed **v0.5.14**, the following differ:

- `animus agent interactions answer --select` / `--remember` / `--updated-input` are v0.5.15+; on v0.5.14 the CLI `answer` takes only `--text`/`--allow`/`--deny`/`--message`/`--by` (structured/remember/updated-input answering is MCP-only there).
