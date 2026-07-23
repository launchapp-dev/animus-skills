---
name: animus-workflow-authoring
description: Write or update Animus workflow YAML in `.animus/workflows.yaml` and `.animus/workflows/*.yaml` - workflow definitions, agents, phases, model registries, MCP bindings, schedules, triggers, daemon config, and related runtime sections. Use when defining a workflow or fixing workflow config.
user_invocable: true
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
---

# Workflow Authoring

Project-authored workflow sources live in `.animus/workflows.yaml` and `.animus/workflows/*.yaml`.

Do not read every reference file up front. Start with the smallest change that solves the task, then open only the reference that matches the section you are editing:

- Read [references/agents-and-phases.md](references/agents-and-phases.md) for agent or phase fields (including command phases and custom verdicts).
- Read [references/top-level-and-routing.md](references/top-level-and-routing.md) for the real top-level authored surface, workflow composition, variables, budgets, and the v0.7 execution-environment surface (`environment:`, `workspaces:`, `environment_routing:`).
- Read [references/automation-and-integrations.md](references/automation-and-integrations.md) for `phase_mcp_bindings`, `tools`, `integrations`, `schedules`, `triggers`, `daemon`, and inter-workflow fan-in.
- Read [mcp-servers-for-agents](../animus-mcp-servers-for-agents/SKILL.md) only when wiring external MCP servers.

Prefer `workflows:` as the authored surface. Some Animus docs still mention `pipelines:`, but `animus-cli`'s current workflow YAML parser, types, and tests are centered on `workflows:`.

## Minimal skeleton

Start from the smallest valid shape and expand only where the task needs more structure:

```yaml
agents:
  default:
    model: claude-sonnet-4-6
    tool: claude

phases:
  implementation:
    mode: agent
    agent: default
    directive: Implement the task.

workflows:
  - id: standard
    name: Standard
    phases: [implementation]
```

## Authoring flow

1. Inspect the existing YAML before adding new sections.
2. Add or update only the sections the task actually touches.
3. Keep deterministic operations in command phases and judgment calls in agent phases.
4. Prefer `cwd_mode: task_root` for git, build, and test commands.
5. Add schedules, triggers, and daemon tuning only after the base workflow works manually.
6. For autonomous workflows, declare a `budget:` cap (`max_cost_usd` / `max_tokens`) — the daemon enforces it on its housekeeping sweep and pauses the workflow on breach.
7. Validate against current `animus-cli` behavior when docs and examples disagree.

## Rules

1. Use agent phases for decisions and command phases for deterministic execution.
2. Do not add rework loops to command phases.
3. Stagger cron offsets instead of starting every schedule on the same minute.
4. Since v0.6.0 the base workflow config is served by a `config_source` plugin (default `launchapp-dev/animus-config-yaml` — YAML in `.animus/workflows.yaml` + `.animus/workflows/*.yaml` remains the default authoring surface; the portal uses `animus-postgres`). The daemon keeps one resident config_source host per project root and picks up file edits on change (CacheToken short-circuits unchanged configs); `animus workflow config reload` is the manual fallback. A malformed edit keeps the prior config active.
5. Express merge/PR/commit automation as `command:` phases that run `git`/`gh` (a phase with a `command:` block). Animus no longer performs git operations as runner automation — `post_success.merge` and the daemon-level git policy keys (`integrations.git.auto_merge`, `auto_pr`, `auto_commit_before_merge`, `auto_prune_worktrees`) were removed and now fail to parse.
6. Use `default_workflow_ref` when the repo should have a stable implicit default.
7. Prefer pack refs like `animus.task/standard` over copying bundled behavior into project YAML.

## Validation

Validate and inspect the effective config:

```bash
animus workflow config validate
animus workflow config compile
animus workflow definitions list
animus workflow phases list
animus workflow prompt render --subject-id <kind:ID>   # preview a phase's effective (skill-injected) prompt
```

(`prompt render --subject-id` is v0.7-rc/portal only — not on 0.6.x local
installs; on 0.6.x use `--task-id` / `--requirement-id` / `--title` instead.)

Config can also be edited through the CLI instead of raw YAML (requires a
config_source plugin that advertises `config_write`; read-only sources refuse
up front): `animus workflow config set` (full model), `agent-set` /
`agent-remove`, `workflow-set` / `workflow-remove`, and
`phase-set --id <id> --input-json <json>` (v0.7-rc.13+/portal only — not on
0.6.x local installs, where the `workflow config` verbs are `set` /
`agent-set` / `agent-remove` / `workflow-set` / `workflow-remove` and
`workflow phases upsert` is the extant overlay path; on the rc line
`phase-set` writes `phase_definitions` on the config_source base — the layer
the validator sees, unlike the legacy `workflow phases upsert` overlay).

`validate` and `compile` emit a `warnings` array (also on stderr) for
declared-but-unenforced fields (e.g. `daemon.pool_size`, removed git policy
keys, phase `evals:`) and for explicit `skills:` names that do not resolve
against the project's skill sources. Warnings never fail the compile.

If the workflow is still unclear after that, open the specific reference file that covers the missing section instead of broad-reading the whole skill set.
