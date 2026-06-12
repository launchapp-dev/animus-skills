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
<<<<<<< HEAD
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
=======
animus init --walkthrough
```

For non-interactive automation:

```bash
animus init --walkthrough --non-interactive --no-install
```

This creates or updates project-local `.animus/` files such as:

- `.animus/config.json` — repository-local Animus config
- `.animus/workflows.yaml` or `.animus/workflows/*.yaml` — authored workflow sources
- `.animus/skills/<name>/SKILL.md` — optional project-scoped skills
- `.animus/plugins/<pack-id>/` — optional project pack overrides

Daemon settings and mutable runtime state are stored outside the repo under
`~/.animus/<repo-scope>/`.

## Core Concepts

### Subjects

Subjects are units of work. Tasks and requirements are subject kinds backed by
plugins. Use `kind=task` for local task work:

```bash
animus subject create --kind task --title "Add user authentication" --priority p1 --status ready
animus subject list --kind task --status ready
animus subject status --kind task --id TASK-001 --status in_progress
>>>>>>> origin/main
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
<<<<<<< HEAD
# Create a task
animus subject create --kind task --title "Add health check endpoint" --priority high
=======
# Create a ready task subject
animus subject create --kind task --title "Add health check endpoint" --priority p1 --status ready
>>>>>>> origin/main

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

<<<<<<< HEAD
```
animus.subject.create — create tasks (kind=task)
animus.subject.list   — list tasks by status (kind=task)
animus.queue.enqueue  — add work to the dispatch queue
animus.daemon.health  — check daemon status
animus.workflow.run   — trigger a workflow manually
animus.output.tail    — read agent output
=======
```text
animus.subject.create   create task/requirement/external subjects
animus.subject.list     list subjects by kind/status
animus.queue.enqueue    add work to the dispatch queue
animus.daemon.health    check daemon status
animus.workflow.run     trigger a workflow
animus.output.tail      read recent agent output
animus.logs.tail        read active log backend entries
>>>>>>> origin/main
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
<<<<<<< HEAD
│   └── workflows/
│       └── custom.yaml
└── ~/.animus/<repo-scope>/      # Repo-scoped runtime state
    ├── core-state.json
    ├── resume-config.json
    ├── config/                  # compiled workflow + agent runtime config
    ├── daemon/                  # daemon.log + pm-config.json
    ├── runs/
    └── artifacts/
=======
│   ├── workflows/
│   │   └── custom.yaml
│   ├── skills/
│   │   └── <skill-name>/SKILL.md
│   └── plugins/
│       └── <pack-id>/
└── ~/.animus/<repo-scope>/
    ├── core-state.json
    ├── resume-config.json
    ├── cost-state.v1.json
    ├── workflow.db
    ├── config/
    │   ├── state-machines.v1.json
    │   ├── workflow-config.v2.json
    │   └── agent-runtime-config.v2.json
    ├── daemon/
    │   └── pm-config.json
    ├── docs/
    ├── logs/
    ├── mcp-oauth-cache/
    ├── runner/
    ├── runs/
    ├── state/
    └── worktrees/
>>>>>>> origin/main
```
