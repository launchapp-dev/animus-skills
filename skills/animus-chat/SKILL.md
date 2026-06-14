---
name: animus-chat
description: Hold and manage multi-turn Animus chat conversations — interactive provider sessions, conversation history, resume semantics, transcript search and export, and per-conversation cost.
user_invocable: false
auto_invoke: true
animus_version: "0.5.15"   # animus CLI surface this skill targets
---

# Animus Chat

Use `animus chat` (v0.5.10+) for multi-turn conversations with a provider tool
(claude / codex / gemini / opencode / any installed `provider_backend`
plugin). It is the conversational sibling of `animus agent run`: same
`SessionBackendResolver`, same provider plugins, but with a durable,
queryable conversation store and turn-by-turn continuity.

## Command Surface

```bash
animus chat new [--id <id>] [--title <title>]      # start an empty conversation, prints its id
animus chat send "your message" [flags]            # send a turn, stream the reply
animus chat get <id>                               # print the full transcript
animus chat list                                   # conversations, most-recently-updated first
animus chat rename <id> --title <title>            # set a title (empty string clears it)
animus chat delete <id>                            # permanent; idempotent if already gone
animus chat export <id> [--format markdown|json] [--output <path>]
animus chat search <query> [--limit 20] [--case-sensitive]
```

## Sending Turns

```bash
animus chat send "Explain the queue dispatch loop" --stream
animus chat send "Now compare it to the scheduler" --conversation conv-abc123 --stream
animus chat send "Summarize open tasks" --tool codex --model gpt-5.5
animus chat send "Audit auth flows" --agent auditor --reasoning-effort high
```

Key flags on `chat send`:

- positional `MESSAGE` — the user message for this turn.
- `--conversation <ID>` — target conversation; omit to create a fresh one
  (its id is reported on the terminal frame).
- `--tool <TOOL>` (default `claude`) and `--model <MODEL>` — provider and
  model selection, same values as `animus agent run`.
- `--title <TITLE>` — names a fresh conversation or renames the target;
  empty string clears the title.
- `--cwd <PATH>` — provider working directory; defaults to the project root
  and must stay inside it.
- `--reasoning-effort low|medium|high` — provider thinking budget
  (codex `model_reasoning_effort`, claude `--effort`).
- `--permission-mode <MODE>` — forwarded verbatim (claude
  `default|acceptEdits|bypassPermissions|plan`, codex
  `untrusted|on-failure|on-request|never`, gemini `default|auto_edit|yolo`);
  overrides any agent-profile value. Unknown values warn but pass through.
- `--approvals` — kernel-mediated approvals via the
  `animus.agent.request_approval` MCP tool; implied when the `--agent`
  profile declares an `approval_policy`.
- `--agent` / `--skill` / `--mcp-server` / `--no-animus-mcp` — see below.

Output modes: `--json` (global flag) emits one JSON event per line
(`turn_started`, `text_delta`, `thinking`, `tool_call`, `tool_result`,
`metadata`, `warning`, `turn_completed`) — `turn_started` carries
`resumed: true|false`, `turn_completed` carries the captured `session_id`.
`--stream` without `--json` prints plain text deltas; neither prints the
final assistant turn once complete.

## Continuity: resume XOR replay

Providers own continuity. With a live `session_id` from a prior turn on the
same tool, Animus sends only the new message and resumes the provider's
native session. With no live session (new conversation, missing/stale
session id, or a mid-conversation tool change), Animus replays its stored
transcript into the prompt — never both, so context is never double-counted.
A stale-session error triggers exactly one full-history replay retry.

## MCP servers, agent profiles, and skills

```bash
animus chat send "Check ticket backlog" --agent support --mcp-server linear
animus chat send "Draft release notes" --skill release-notes --no-animus-mcp
```

- `--agent <AGENT_ID>` — the chat agent receives that profile's declared
  `mcp_servers`, resolved by name against the project's `mcp_servers` map.
- `--skill <SKILL>` — adds the skill's declared MCP servers (unioned with
  the profile's). Unknown skill names are an error.
- `--mcp-server <NAME>` — wire an extra server by name (repeatable;
  `animus` selects the built-in stdio surface).
- `--no-animus-mcp` — drop the built-in `animus` server. Without any
  profile/skill servers, the baseline set is just `animus`, so the model
  can call `animus.*` tools mid-conversation.

The resolved set reaches the provider itself as `extras.mcp_servers` on all
four providers. OAuth/secret-bearing servers are rewritten to
`animus-mcp-proxy` stdio entries — tokens never reach CLI configs or argv.

### Full skill application (v0.5.14)

`--skill` applies the skill's FULL definition per send invocation, not just
MCP servers + tool policy: prompt `prefix`/`directives`/`suffix` wrap the
outgoing message, `prompt.system` rides the session `system_prompt`,
`extra_args`/`codex_config_overrides` graft onto the runtime contract's
`cli.launch` block, skill `env` rides the request env, and the skill's
`model`/`timeout_secs` apply when not explicitly set. Precedence per field:
explicit flags > skill > defaults.

A launch-affecting skill (`extra_args`/`codex_config_overrides`/`env`)
forces full-history replay instead of native session resume, so launch
flags reach every turn's provider process. Practical implication: slower
turns and more tokens (history re-sent each turn), but launch behavior
stays correct on every turn.

## Inspecting, searching, exporting

Conversations live under `~/.animus/<repo-scope>/chat/<conversation-id>/`:
`meta.json` (continuity pointer: `session_id` + `tool` + `model`) and
`messages.jsonl` (append-only message log with ordered assistant `blocks[]`
timelines). Treat as tool-managed — use the `animus chat` surface, not
hand-edits.

```bash
animus chat list
animus chat search "merge conflict" --limit 10
animus chat export conv-abc123 --format json --output transcript.json
```

Search is case-insensitive by default (`--case-sensitive` to invert);
export defaults to Markdown, with `--format json` emitting the full
`{ meta, messages }` shape (same as `chat get`); both `list` and `search`
skip stray non-conversation directories (v0.5.13).

## Cost

```bash
animus cost conversation conv-abc123    # token + USD spend for one conversation
```

Per-turn `usage`/`cost_usd` from the provider's metadata frames fold into a
per-conversation total. See animus-cost-operations for the wider `animus
cost` surface (`summary`, `workflow`, `top`, `trends`, `decisions`).

## Reliability notes (v0.5.13)

- Chat sends are cross-process locked per conversation — concurrent sends
  to the same conversation cannot interleave turns.
- A chat stream ending without a terminal event is an error, not a
  silently-successful empty turn.
- OAuth `invalid_grant` on an authed MCP server evicts the cached refresh
  chain and retries the env seed in the same call — chat agents using
  OAuth-protected servers self-recover.

## Human-in-the-loop

The blocking `animus.agent.ask` / `animus.agent.request_approval` MCP tools
work on ad-hoc chat: in block mode (the default), the tool call parks until
a human answers via `animus agent interactions answer`, and on timeout a
question returns a best-judgment error while an approval denies fail-closed.
See animus-agent-interactions for the inbox workflow.

## Related

- animus-agent-operations — single-shot `animus agent run`, control/status, memory, messages.
- animus-agent-interactions — answering pending questions and approvals.
- animus-cost-operations — spend rollups beyond per-conversation totals.
