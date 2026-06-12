---
name: animus-getting-started
description: Install Animus, create first task, run first workflow — core concepts and project structure
user_invocable: true
auto_invoke: true
---

# Getting Started with Animus

Animus is a Rust-based agent orchestrator that manages autonomous software development workflows. It coordinates AI agents (Claude, Codex, Gemini) to implement tasks, run tests, create PRs, and review code.

## Prerequisites

- Git
- GitHub CLI (`gh`) authenticated
- At least one AI CLI tool: `claude` (Claude Code), `codex`, or `gemini`

## Install

```bash
# Recommended — upstream installer (puts `animus` on PATH at ~/.local/bin/animus)
curl -fsSL https://raw.githubusercontent.com/launchapp-dev/ao/main/install.sh | bash
```

```bash
# From a local source checkout
cd /path/to/animus-cli
cargo install --path crates/orchestrator-cli --bin animus
```

Verify: `which animus && animus --version`

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

### Workflows
Multi-phase pipelines that execute tasks. A typical workflow:
1. **requirements** — AI reads the task and plans implementation
2. **implementation** — AI writes code in a git worktree
3. **unit-test** — runs `cargo test` or equivalent
4. **create-pr** — pushes branch and creates GitHub PR

### Daemon
Background process that continuously dispatches workflows from a queue.

```bash
animus daemon start --autonomous --auto-run-ready true --pool-size 3
animus daemon health
animus daemon stream --pretty
animus daemon stop
```

### Queue
Tasks are enqueued for the daemon to dispatch.

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

Animus exposes all operations as MCP tools. When running inside Claude Code or any MCP-aware AI:

```
animus.subject.create — create tasks (kind=task)
animus.subject.list   — list tasks by status (kind=task)
animus.queue.enqueue  — add work to the dispatch queue
animus.daemon.health  — check daemon status
animus.workflow.run   — trigger a workflow manually
animus.output.tail    — read agent output
```

For live CLI-side observability outside MCP, use:

```bash
animus daemon stream --pretty
animus output monitor --run-id <run-id>
```

## Project Structure

```
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
