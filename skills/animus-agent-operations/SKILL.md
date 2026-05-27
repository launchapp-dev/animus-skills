---
name: animus-agent-operations
description: Run and inspect Animus agent executions, direct provider runs, agent control, status, project-scoped agent memory, and agent message channels.
user_invocable: false
auto_invoke: true
---

# Agent Operations

Use `animus agent` for direct agent execution and inspection outside the full
workflow pipeline, or for project-scoped memory and message channels.

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
animus agent run --tool claude --model claude-sonnet-4-5 --prompt "Review the auth module" --cwd .
animus agent run --tool codex --model gpt-5.4 --prompt "Implement TASK-001" --timeout-secs 1800
animus agent run --run-id run-auth-review --tool claude --prompt "Audit auth" --detach
```

Useful flags:

- `--run-id <ID>` sets a stable run id; otherwise Animus generates one.
- `--tool <TOOL>` selects provider CLI such as `claude`, `codex`, or `gemini`.
- `--model <MODEL>` overrides the configured model for that tool.
- `--prompt <TEXT>` sends direct prompt text.
- `--cwd <PATH>` must resolve inside the project root.
- `--timeout-secs <N>` caps the run.
- `--context-json <JSON>` passes agent context.
- `--runtime-contract-json <JSON>` overrides runtime contract fields.
- `--detach` returns immediately.
- `--stream true|false` controls stdout event streaming.
- `--save-jsonl true|false` controls persisted run logs.
- `--jsonl-dir <PATH>` overrides persisted run log location.
- `--start-runner true|false` controls automatic runner startup.
- `--runner-scope project|global` selects runner config scope.

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

Spawned workflow agents only receive memory tools when their profile has
`capabilities.memory: true`.

## Agent Messages

```bash
animus agent message send --channel design-review --from architect --to auditor --text "Please check TASK-001" --workflow-id wf-123 --phase-id review
animus agent message list --channel design-review --limit 25
animus agent message list --agent architect
```

Use message channels for coordination between configured profiles. Keep durable
facts in memory; keep run-specific coordination in messages.

## MCP Tools

Direct agent tools:

- `animus.agent.list`, `get`, `run`, `control`, `status`
- `animus.agent.memory.get`, `append`, `clear`
- `animus.agent.message.send`, `list`

Top-level memory tools:

- `animus.memory.get`, `list`, `append`, `clear`

## Troubleshooting

- Direct run fails before model startup: check `animus model status --cli-tool <tool> --model-id <model>`.
- Provider tool is missing: install provider plugins and rerun daemon preflight.
- Run appears stuck: inspect `animus runner health`, `animus daemon stream --run <run-id>`, and `animus output monitor --run-id <run-id>`.
- Memory unavailable inside a workflow phase: check the agent profile's `capabilities.memory` setting.
