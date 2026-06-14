---
name: animus-agent-interactions
description: Deep reference for Animus human-in-the-loop (HITL) agent interactions — agent questions and approval requests, the pending-interaction inbox, paused workflows waiting for an answer, permission prompts, approval_policy routing, and suspend/resume mechanics. Use when an agent is parked on a pending interaction, a workflow is paused awaiting a human decision, an approval or permission prompt needs answering, or when configuring approvals for agents.
user_invocable: false
auto_invoke: true
animus_version: "0.5.15"   # animus CLI surface this skill targets
---

# Agent Interactions (Human-in-the-Loop)

Animus agents escalate to humans through two blocking MCP tools on the
kernel's `animus mcp serve` server:

- `animus.agent.ask` — a clarifying **question** (`agent_id`, `question`,
  `options[]`, `timeout_secs`, `workflow_id`, `task_id`, `wait`).
- `animus.agent.request_approval` — an **approval** for a sensitive action
  (`agent_id`, `action` — derived as `use tool <tool_name>` when omitted —
  `tool_name`, `input`/`arguments`, `tool_use_id`, `suggestions`,
  `timeout_secs`, `workflow_id`, `task_id`, `wait`).

Each call writes a pending record under
`~/.animus/<repo-scope>/interactions/` until a human answers it. Timeouts:
default 600s, max 3600s.

## Wait modes: block vs suspend

| Mode | Default for | Behavior | Timeout |
|---|---|---|---|
| `block` | ad-hoc `animus agent run` / `animus chat` | tool call parks until answered | approval ⇒ **deny (fail closed)**; question ⇒ structured error telling the agent to proceed on best judgment |
| `suspend` | workflow phases (server pinned via `animus mcp serve --workflow-id <ID>` or `ANIMUS_MCP_WORKFLOW_ID`) | tool returns `{ status: "pending", interaction_id, instruction }` immediately, the workflow pauses, the interaction id is stamped into the phase session checkpoint | no auto-expiry; workflow stays paused until answered |

Answering a suspend-created record resumes the workflow via the detached-runner
resume path with the decision threaded in as session feedback. Only
suspend-created records trigger a resume — a block-mode payload `workflow_id`
is observability metadata only. Agents may downgrade suspend→block; a
block→suspend request on an unpinned server is ignored with a warning.
Prefer suspend for daemon-driven phases: no process parks waiting, and a
crash mid-wait is recoverable from the checkpoint.

## Approval policy (workflow YAML)

Per-agent routing for `animus.agent.request_approval` calls, consulted before
escalating:

```yaml
agents:
  swe:
    permission_mode: acceptEdits    # transport-level guard (provider's own flag)
    approval_policy:                # kernel inbox layer
      auto_allow: ["cargo *", "git.commit"]
      auto_deny: ["git.push*"]
      default: ask                  # ask | allow | deny
```

- `auto_allow` / `auto_deny` are `*`-glob lists matched against the request's
  `tool_name` when present, otherwise its `action`. `auto_deny` wins on
  overlap (fail closed). `default: ask` escalates to a pending interaction.
- Declaring an `approval_policy` implies `--approvals` on `animus agent run`
  (sets `extras.approvals` so transports route permission decisions through
  the kernel tool).
- `permission_mode` **composes** with `approval_policy` — neither overrides
  the other. `permission_mode` is the transport-level guard (forwarded
  verbatim: claude `--permission-mode`, codex `-c approval_policy`, gemini
  approval mode) deciding whether the provider escalates at all;
  `approval_policy` decides what happens to escalations that reach the
  kernel. Caveat: ad-hoc surfaces honour `permission_mode` today; workflow
  phase execution enforces it once the out-of-tree workflow-runner plugin
  pin consumes the field. Phase `runtime.permission_mode` wins over the
  agent profile's value.

## Native enforcement (claude) — SDK conformance

With approvals enabled, the claude transport wires
`animus.agent.request_approval` as the claude CLI's
`--permission-prompt-tool`, so every native permission decision routes
through the kernel — enforced, not voluntary. The wire contract:

- Input: `{ tool_name, input, tool_use_id }`. No `agent_id` — identity comes
  from the server pin.
- Response (first text content block, SDK permission-result schema):
  `{ "behavior": "allow", "updatedInput": <original or modified input>, "updatedPermissions"? }`
  or `{ "behavior": "deny", "message": <string> }` — with the legacy
  `{ tool, result: { decision, source, … } }` envelope alongside.
- Native `AskUserQuestion` calls become structured **Question** records
  (`questions[]` parsed from the input) in the same inbox, bypassing the
  approval policy; the allow answer carries
  `updatedInput { questions, answers, response? }`.
- A `suggestions` array (SDK `PermissionUpdate[]`) is stored on the record;
  answering `--allow --remember` echoes the localSettings-destination subset
  back as `updatedPermissions` (pure echo — no kernel permission-rule engine).
- Suspend mode on a native prompt-tool call answers `behavior: "deny"` with
  an end-your-turn instruction, pauses the workflow, and the session later
  resumes with the answer as feedback (voluntary agent calls keep the
  `pending` payload).

codex / gemini / opencode have no exec-mode approval hook: they get
`permission_mode` mapping plus a system-prompt instruction block directing
the agent to call the two kernel tools — voluntary compliance.

## Operator inbox: `animus agent interactions`

```bash
animus agent interactions list                # pending only
animus agent interactions list --all          # include answered + expired
animus agent interactions list --agent swe    # filter by requesting agent
animus agent interactions show <ID>           # renders structured questions readably
animus agent interactions answer <ID> --text "use the copy table"   # question
animus agent interactions answer <ID> --allow                       # approval
animus agent interactions answer <ID> --deny --message "too risky"
animus agent interactions answer <ID> --allow --remember            # echo localSettings suggestions
animus agent interactions answer <ID> --allow --updated-input '{"command":"rm -rf build/sandbox"}'
animus agent interactions answer <ID> \
  --select "Format=Summary" --select "2=Introduction,Conclusion" \
  --text "keep it short"                      # structured (AskUserQuestion)
```

Answer flags: `--text` (question answer; on structured records it maps to the
single question's answer, or the freeform `response` on multi-question records
or when `--select` is given), `--allow`/`--deny` (exactly one, approvals),
`--message`, repeatable `--select "<question text|header|1-based index>=<label[,label...]>"`
(comma-separate labels or repeat for multi-select), `--remember` and
`--updated-input <JSON>` (require `--allow`), `--by <NAME>` (defaults to
`human`). All subcommands support `--json` (`animus.cli.v1` envelope).

If a suspended workflow's resume spawn fails, the answer still succeeds and
the output carries a `workflow_resume.guidance` field with the exact
`animus workflow resume --id <id>` command. Two racing answers: first commit
wins, the second errors with a "not pending" message (e.g.
`interaction '<id>' is not pending (status: answered)`).

## Management-gated MCP tools and identity pins

`animus mcp serve --management` registers two non-blocking inbox tools over
the same store (the default agent-injected server omits them so an agent can
never list or answer its own approvals — the gate stays human-only):

- `animus.interactions.list` — `all`, `agent_id`, `limit`, `project_root`.
- `animus.interactions.answer` — `id`, `text`, `decision` (`allow`/`deny`),
  `message`, `answers` (keyed by exact question text; string or label array),
  `response`, `updated_input`, `updated_permissions`, `remember`,
  `answered_by`, `project_root`. Triggers the same suspended-workflow resume.

There is no `animus.interactions.get` tool; use `list` (or the CLI `show`).

Identity pins on the serving process:

- `animus mcp serve --agent-id <ID>` (or `ANIMUS_MCP_AGENT_ID`) makes the
  payload `agent_id` ignored, so an agent cannot claim a sibling profile with
  a looser `approval_policy`. The ad-hoc `animus agent run --agent` /
  `animus chat send --agent` injection path appends it automatically.
- `animus mcp serve --workflow-id <ID>` (or `ANIMUS_MCP_WORKFLOW_ID`) binds
  escalations to that workflow and flips the default wait mode to suspend.
- The two blocking tools accept no `project_root` override — they always
  operate on the server's own project scope.

## Events, notifications, state

- Lifecycle events land in the daemon event log: `interaction_created`,
  `interaction_answered`, `interaction_expired` — surfaced by
  `animus daemon events` (each with a summary and a ready-to-run
  `answer_command`), so no store polling is needed.
- Installed notifier plugins (Slack / Telegram / HTTP) are pushed fresh
  escalations best-effort via the daemon's notifier dispatcher.
- Store: one JSON record per interaction under
  `~/.animus/<repo-scope>/interactions/` (flock'd read-modify-write, atomic
  writes; survives daemon restarts).

## Diagnosing a paused workflow

A workflow silently "stuck"? Check whether it is parked on an interaction:

```bash
animus agent interactions list          # pending question/approval?
animus workflow list                    # suspended workflows show paused
animus subject get --kind task --id task:TASK-XXX   # blocked_reason: "paused by workflow wf-..."
animus daemon events                    # interaction_created records
```

Answering the interaction auto-resumes the workflow when the daemon is up;
with no daemon the answer prints the `animus workflow resume --id <id>` command to
run. If the agent process died while blocked, the record stays pending and
answering warns it is a no-op.

## Not the same as `animus approval`

`animus approval {request, respond, outcome}` is a separate surface gating
operator-initiated destructive **git** operations (e.g. `animus git worktree
prune` requires an approved `prune_worktrees` record passed back via
`--confirmation-id`). Its records live in the project-local git-confirmations
store and never appear in the agent interactions inbox; agent escalations are
answered with `animus agent interactions answer`, not `animus approval respond`.

## Related skills

- animus-agent-operations — running ad-hoc agents (`--approvals`, `--permission-mode` flags).
- animus-workflow-authoring — full agent-profile YAML, phase `runtime:` blocks.
- animus-mcp-tools — the rest of the `animus.*` MCP tool surface.

## Differences on installed v0.5.14

This skill documents the **v0.5.15** surface (see `animus_version`). On an installed **v0.5.14**, the following differ:

- `animus agent interactions answer --select` / `--remember` / `--updated-input` are v0.5.15+; on v0.5.14 the CLI `answer` takes only `--text`/`--allow`/`--deny`/`--message`/`--by`, and structured-question / remember / updated-input answering is MCP-only (`animus.interactions.answer`).
