---
name: animus-setup
description: Set up Animus in the current project - initialize config, connect MCP, install required plugins, create a first workflow, and start the daemon. Use when bootstrapping Animus in a repo or fixing an incomplete Animus setup.
user_invocable: true
auto_invoke: false
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

<<<<<<< HEAD
1. Run `animus init --walkthrough` in the project root to initialize `.animus/`, detect AI CLIs, and install default plugins. Add `--install-packs` to also install the recommended workflow packs and reach a runnable state immediately. (`animus setup` was removed in v0.4.4 — use `animus init`.)
2. Create `.mcp.json` pointing to the `animus` binary.
3. Create a minimal workflow file (or keep the bundled hello-world template the walkthrough copies into `.animus/workflows/`).
4. Start the daemon with conservative defaults.
5. Create one small test task and verify end-to-end execution.
=======
1. Run `animus init --walkthrough` in the project root to initialize `.animus/`.
2. Install required plugins with `animus plugin install-defaults --include-subjects`.
3. Run `animus daemon preflight` and resolve missing providers or subject backends.
4. Create or verify `.mcp.json` pointing to the `animus` binary.
5. Create or validate a minimal workflow file.
6. Start the daemon with conservative defaults.
7. Create one small task subject, enqueue it, and verify end-to-end execution.

Use `animus init --walkthrough --non-interactive --no-install` when automation
should avoid prompts and plugin installs are already handled elsewhere.
>>>>>>> origin/main

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
animus daemon start --autonomous --auto-run-ready true --pool-size 5 --interval-secs 10
animus daemon health
```

If preflight reports missing defaults on a dev machine:

```bash
animus daemon start --autonomous --auto-install
```

Use `--skip-preflight` only when intentionally debugging without required
plugins.

## Verification

- Run `animus daemon status` or the MCP equivalent.
<<<<<<< HEAD
- Create a small task with `animus subject create --kind task --title "..."`.
- Enqueue it with `animus queue enqueue`.
=======
- Create a small task subject with `animus subject create --kind task --title "Verify setup"`.
- Enqueue it with `animus queue enqueue --task-id <id>`.
>>>>>>> origin/main
- Confirm the daemon picks it up before adding more workflows or schedules.

If something fails, read only the skill that matches the blocker instead of
sweeping the whole repo.
