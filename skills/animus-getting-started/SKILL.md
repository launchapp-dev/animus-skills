---
name: animus-getting-started
description: Install Animus, initialize a project, create first task subject, run first workflow — core concepts and project structure
user_invocable: true
auto_invoke: true
---

# Getting Started with Animus

Animus is a Rust-based agent orchestrator. A daemon dispatches workflows,
spawns provider plugins for tools such as Claude, Codex, Gemini, OpenCode, or
OAI, manages worktrees, records output, and coordinates queue-driven work.

## Prerequisites

- Git
- At least one AI CLI/auth path you intend to use
- Animus provider and subject plugins installed before daemon startup

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/launchapp-dev/animus-cli/main/scripts/install.sh | bash
```

```bash
# From a local source checkout
cd /path/to/animus-cli
cargo install --path crates/orchestrator-cli --bin animus --locked
```

Verify:

```bash
which animus
animus --version
```

## Install Default Plugins

Current Animus requires plugins for providers, subject backends, and optional
web transports. For a normal local setup:

```bash
animus plugin install-defaults --include-subjects
animus daemon preflight
```

Add `--include-transports` if you want `animus web serve` / `animus web open`.

## Initialize a Project

```bash
cd /path/to/your/project
animus init --walkthrough --install-packs
```

The walkthrough detects installed AI CLIs, installs the default plugins, and copies the bundled hello-world workflow. `--install-packs` also installs and activates the recommended workflow packs (`animus.core-skills`, `animus.task`, `animus.requirement`, `animus.review`), which takes the project straight to a runnable state. (`animus setup` was removed in v0.4.4 — `animus init` replaced it.)

This creates:
- `.animus/config.json` — project-level Animus config
- `.animus/workflows.yaml` and `.animus/workflows/` — workflow sources

Daemon settings persist under the repo-scoped runtime root at `~/.animus/<repo-scope>/daemon/pm-config.json`, managed via `animus daemon config`.

## Core Concepts

### Tasks
Units of work, managed through the unified subject surface (`animus subject --kind task`). Each task has an ID (TASK-001), title, status, and priority.

```bash
animus subject create --kind task --title "Add user authentication" --priority high
animus subject list --kind task --status ready
animus subject status --kind task --id task:TASK-001 --status in-progress
animus subject next --kind task
```

The removed `animus task ...` and `animus requirements ...` command trees are
replaced by `animus subject ...`.

### Workflows

Workflows are multi-phase pipelines. A typical delivery workflow:

1. Read and refine the subject.
2. Implement in a managed worktree.
3. Run checks.
4. Review and route rework if needed.
5. Push, open a PR, or merge according to project policy.

### Daemon

The daemon continuously dispatches queued subjects and supervises workflow runs.

```bash
animus daemon start --autonomous --auto-run-ready true --pool-size 3
animus daemon health
animus daemon stream --pretty
animus daemon stop
```

Startup runs plugin preflight by default. Use `--auto-install` for one-shot dev
setup or `--skip-preflight` only for intentional local debugging.

### Queue

Queue entries tell the daemon what subject to dispatch next.

```bash
animus queue enqueue --task-id TASK-001
animus queue list
animus queue stats
```

## First Workflow

```bash
# Create a task
animus subject create --kind task --title "Add health check endpoint" --priority high

# Enqueue it
animus queue enqueue --task-id TASK-001

# Start the daemon
animus daemon start --autonomous --auto-run-ready true --pool-size 2

# Watch it work
animus daemon health
animus queue list
animus daemon stream --pretty
```

## MCP Integration

Animus exposes operations as MCP tools:

```
animus.subject.create — create tasks (kind=task)
animus.subject.list   — list tasks by status (kind=task)
animus.queue.enqueue  — add work to the dispatch queue
animus.daemon.health  — check daemon status
animus.workflow.run   — trigger a workflow manually
animus.output.tail    — read agent output
```

For live CLI-side observability outside MCP:

```bash
animus daemon stream --pretty
animus logs tail --level info --since 1h
animus output monitor --run-id <run-id>
```

## Project Structure

```text
your-project/
├── .animus/
│   ├── config.json
│   ├── workflows.yaml
│   └── workflows/
│       └── custom.yaml
└── ~/.animus/<repo-scope>/      # Repo-scoped runtime state
    ├── core-state.json
    ├── resume-config.json
    ├── config/                  # compiled workflow + agent runtime config
    ├── daemon/                  # daemon.log + pm-config.json
    ├── runs/
    └── artifacts/
```
