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
- The required plugins installed before daemon startup (one command:
  `animus plugin install-defaults`)

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

The daemon's preflight requires a provider, task + requirement subject
backends, a workflow runner, and a queue plugin. One command installs the
default flavor's full required set (provider-claude, subject-default,
subject-requirements, transport-http, workflow-runner-default,
queue-default):

```bash
animus plugin install-defaults
animus daemon preflight
```

Add `--include-recommended` for the recommended extras (more providers, the
web UI, GraphQL transport — needed for `animus web serve` / `animus web open`).
`--flavor <name>` installs a different flavor manifest. API keys belong in the
OS keychain: `animus secret set <KEY>` (preferred over env vars; `${VAR}`
interpolation in workflow YAML also checks the keychain).

For team repos, `animus plugin install --project` installs into
`<project>/.animus/plugins/` with a committable `.animus/plugins.lock` that
pins the repo's plugin set (binaries stay gitignored).

## Initialize a Project

```bash
cd /path/to/your/project
animus init --walkthrough
```

`animus init` now reaches a runnable state: the walkthrough detects installed
CLIs, installs default plugins, offers to install the recommended workflow
packs (`animus.core-skills`, `animus.task`, `animus.requirement`,
`animus.review`; default yes), suggests migrating API keys found in env vars
to the keychain (`animus secret set <KEY>`; never stored silently), and prints
the first runnable workflow command. When more than the bundled `default`
flavor is discoverable, the walkthrough offers an interactive flavor picker
(TTY-only; non-interactive runs keep `default`).

For non-interactive automation:

```bash
animus init --walkthrough --non-interactive --no-install --install-packs
```

Use `--no-packs` to skip the pack install entirely (takes precedence over
`--install-packs`).

This creates or updates project-local `.animus/` files such as:

- `.animus/config.json` — self-update config only (daemon runtime settings
  live in the scoped `daemon/pm-config.json`, managed via `animus daemon config`)
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
animus subject status --kind task --id TASK-001 --status in-progress
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

The daemon dispatches queued subjects and supervises workflow runs. Dispatch
is event-driven: subject and queue writes wake the daemon immediately, so
there is no tick interval to wait for.

```bash
animus daemon start --auto-run-ready true --pool-size 3
animus daemon health
animus daemon stream --pretty
animus daemon restart
animus daemon stop
```

`animus daemon start` always detaches: it backgrounds the daemon, prints the
pid and log path, and is idempotent if a daemon is already running. Use
`animus daemon run` for a foreground dev/debug daemon (Ctrl-C to stop). The
old `--autonomous` flag is a deprecated no-op.

Startup runs plugin preflight by default. Use `--auto-install` for one-shot dev
setup or `--skip-preflight` only for intentional local debugging.

Agents can ask questions or request approvals mid-run (human-in-the-loop);
pending items land in the `animus agent interactions` inbox
(`list` / `show` / `answer`).

### Queue

Queue entries tell the daemon what subject to dispatch next. An enqueue
nudges the daemon, so dispatch is effectively immediate. Explicit enqueues
drain even when `auto_run_ready` is false — that flag only gates auto-dispatch
of Ready tasks.

```bash
animus queue enqueue --task-id TASK-001
animus queue list
animus queue stats
```

## First Workflow

```bash
# Create a ready task subject
animus subject create --kind task --title "Add health check endpoint" --priority p1 --status ready

# Enqueue it
animus queue enqueue --task-id TASK-001

# Start the daemon (detaches; prints pid + log path)
animus daemon start --auto-run-ready true --pool-size 2

# Watch it work
animus daemon health
animus queue list
animus daemon stream --pretty
```

## MCP Integration

Animus exposes operations as MCP tools:

```text
animus.subject.create   create task/requirement/external subjects
animus.subject.list     list subjects by kind/status
animus.queue.enqueue    add work to the dispatch queue
animus.daemon.health    check daemon status
animus.workflow.run     trigger a workflow
animus.output.tail      read recent agent output
animus.logs.tail        read active log backend entries
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
│   ├── workflows/
│   │   └── custom.yaml
│   ├── skills/
│   │   └── <skill-name>/SKILL.md
│   ├── plugins/                  # pack overrides + project-scoped plugin binaries (gitignored)
│   ├── plugins.lock              # committable pin of project-scoped plugins
│   └── plugin-scope.yaml         # optional plugin scope + active_flavor
└── ~/.animus/<repo-scope>/
    ├── core-state.json
    ├── resume-config.json
    ├── cost-state.v1.json
    ├── workflow.db
    ├── artifacts/
    ├── cache/
    ├── config/
    │   ├── state-machines.v1.json
    │   └── agent-runtime-config.v2.json
    ├── daemon/
    │   └── pm-config.json
    ├── docs/
    ├── interactions/
    ├── logs/
    ├── mcp-oauth-cache/
    ├── runs/
    ├── state/
    └── worktrees/
```

Compiled workflow config is in-memory only — the only on-disk compile artifact
is the hash-keyed cache under `cache/`. A `config/workflow-config.v2.json`
file is a hard load error directing you back to workflow YAML.
