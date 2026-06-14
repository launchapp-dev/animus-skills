---
name: animus-setup
description: Set up Animus in the current project - initialize config, connect MCP, install required plugins, create a first workflow, and start the daemon. Use when bootstrapping Animus in a repo or fixing an incomplete Animus setup.
user_invocable: true
auto_invoke: false
animus_version: "0.5.15"   # animus CLI surface this skill targets
---

You are setting up Animus in the current project.

Do not preload the entire `~/animus-skills/skills/` directory. Start with
targeted reads:

- Read [getting-started](../animus-getting-started/SKILL.md) first for the core Animus mental model.
- Read [mcp-setup](../animus-mcp-setup/SKILL.md) only when creating or fixing `.mcp.json`.
- Read [workflow-authoring](../animus-workflow-authoring/SKILL.md) only when editing `.animus/workflows.yaml` or `.animus/workflows/*.yaml`.
- Read [daemon-operations](../animus-daemon-operations/SKILL.md) only when starting, checking, or debugging the daemon.
- Read [troubleshooting](../animus-troubleshooting/SKILL.md) only if setup fails.
- Use [configuration](../animus-configuration/SKILL.md), [task-management](../animus-task-management/SKILL.md), [queue-management](../animus-queue-management/SKILL.md), and [mcp-tools](../animus-mcp-tools/SKILL.md) as lookup references, not mandatory preload.

## Setup flow

1. Run `animus init --walkthrough` in the project root to initialize `.animus/`.
   The interactive walkthrough also installs the recommended workflow packs
   (default yes), offers a flavor picker when multiple flavors are
   discoverable, and suggests migrating env-var API keys to the keychain
   (`animus secret set <KEY>` — preferred over env vars).
2. Install required plugins with `animus plugin install-defaults` (bare — it
   installs the flavor's full required set: provider, task + requirement
   subject backends, transport-http, workflow-runner, queue; every
   daemon-preflight role in one command). `--include-recommended` adds extras.
3. Run `animus daemon preflight` and resolve any missing role. Preflight also
   requires the `workflow_runner` and `queue` roles; when multiple roles are
   missing it prints the composed fix
   (`animus plugin install-defaults --flavor default --yes`).
4. Create or verify `.mcp.json` pointing to the `animus` binary.
5. Create or validate a minimal workflow file.
6. Start the daemon with conservative defaults.
7. Create one small task subject, enqueue it, and verify end-to-end execution.
   Dispatch is event-driven — the enqueue wakes the daemon immediately.

Use `animus init --walkthrough --non-interactive --no-install` when automation
should avoid prompts and plugin installs are already handled elsewhere; add
`--install-packs` to install the recommended packs non-interactively, or
`--no-packs` to skip them.

For team repos, prefer project-scoped plugin installs
(`animus plugin install --project`): binaries land in
`<project>/.animus/plugins/` (gitignored) and the committable
`.animus/plugins.lock` pins the repo's plugin set for everyone.

## Minimal workflow

Start with a small workflow instead of a full production pipeline:

```yaml
agents:
  default:
    model: claude-sonnet-4-6
    tool: claude

phases:
  implementation:
    mode: agent
    agent: default
    idempotency: idempotent
    directive: Implement the task and report what changed.

workflows:
  - id: standard
    name: Standard
    phases: [implementation]
```

Expand it only after the daemon, MCP, and subject dispatch loop work.

## Daemon startup

Start with:

```bash
animus daemon preflight
animus daemon start --auto-run-ready true --pool-size 5
animus daemon health
```

`animus daemon start` always detaches (prints pid + log path; idempotent if
already running). Use `animus daemon run` for a foreground dev/debug daemon
and `animus daemon restart` to bounce it. The legacy `--autonomous` flag is a
deprecated no-op. `--interval-secs` is only a fallback heartbeat now —
dispatch itself is event-driven.

If preflight reports missing defaults on a dev machine:

```bash
animus daemon start --auto-install
```

Use `--skip-preflight` only when intentionally debugging without required
plugins.

## Verification

- Run `animus daemon status` or the MCP equivalent.
- Create a small task subject with `animus subject create --kind task --title "Verify setup"`.
- Enqueue it with `animus queue enqueue --task-id <id>`. The enqueue nudges
  the daemon, so pickup is immediate — no tick interval to wait for. Explicit
  enqueues drain even when `auto_run_ready` is false.
- Confirm the daemon picks it up before adding more workflows or schedules.
- If a run stalls, check `animus agent interactions list` — agents can park
  mid-run on a pending question or approval; answer with
  `animus agent interactions answer <ID>`.

If something fails, read only the skill that matches the blocker instead of
sweeping the whole repo.
