---
name: animus-getting-started
description: Install Animus, initialize a project, create first task subject, run first workflow — core concepts and project structure
user_invocable: true
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
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

Working across multiple projects, or want side-by-side kernel versions?
Prefer **avm**, the Animus Version Manager
(github.com/launchapp-dev/avm) — it installs kernels under
`~/.avm/versions/` and dispatches through an `animus` shim:

```bash
avm install <version> && avm use <version>
```

(`animus update` self-updates plain installs; on an avm-managed binary it
defers and prints the `avm` commands instead.)

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

## Joining an existing Animus project?

If the repo already has a committed `animus.toml`, setup is two commands —
skip the plugin sections below:

```bash
git clone <repo> && cd <repo>
animus install        # resolves animus.toml → .animus/plugins.lock, installs plugins + packs
```

`animus install --locked` (CI/Docker) reproduces the committed lock exactly.
It also syncs `.env` into the encrypted secret store and warns about keys
declared in `.env.example` but unset.

## Install Default Plugins (fresh machine, no manifest yet)

The daemon's preflight requires a provider, at least one subject backend
(the default flavor installs task + requirement), a config_source, a
workflow runner, and a queue plugin. One command
installs the default flavor's full required set (provider-claude,
subject-default, subject-requirements, config-yaml, transport-http,
workflow-runner-default, queue-default):

```bash
animus plugin install-defaults
animus daemon preflight
```

Add `--include-recommended` for the recommended extras (more providers, the
web UI, GraphQL transport — needed for `animus web serve` / `animus web open`).
`--flavor <name>` installs a different flavor manifest. API keys belong in the
OS keychain: `animus secret set <KEY>` (preferred over env vars; `${VAR}`
interpolation in workflow YAML also checks the keychain).

For team repos, declare the plugin/pack set in a committed `animus.toml`
(scaffolded by `animus init`; edited via `animus add` / `animus remove`) and
commit `.animus/plugins.lock` — teammates then just run `animus install`.
The lock is the source of truth; `.animus/plugins.yaml` is a derived
projection (never hand-edit or rely on it). Binaries stay gitignored under
`<project>/.animus/plugins/`.

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

This creates or updates the project manifest and `.animus/` files:

- `animus.toml` — the committed project manifest (`[project]` kernel version,
  `[plugins]`, `[packs]`); resolved by `animus install`
- `.env.example` and a merge-safe project `.gitignore`
- `.animus/config.json` — self-update config only (daemon runtime settings
  live in the scoped `daemon/pm-config.json`, managed via `animus daemon config`)

Since v0.6.4 `animus init` does NOT scaffold workflow YAML (the old scaffold
flag is a deprecated no-op) — a fresh project becomes functional through the
recommended pack install (`animus.task` et al. supply the default workflows).
You author `.animus/workflows.yaml` / `.animus/workflows/*.yaml` yourself when
you need project-local workflow definitions. Other author-written files that
live alongside it:

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
animus subject next --kind task
animus subject status --kind task --id TASK-001 --status in-progress
# --id also accepts the backend-qualified <kind>:<native> form:
animus subject status --kind task --id task:TASK-001 --status in-progress
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
animus daemon start --pool-size 3
animus daemon health
animus daemon stream --pretty
animus daemon restart
animus daemon stop
```

`animus daemon start` always detaches: it backgrounds the daemon, prints the
pid and log path, and is idempotent if a daemon is already running. Use
`animus daemon run` for a foreground dev/debug daemon (Ctrl-C to stop). The
old `--autonomous` flag was removed — `daemon start` now errors on it; the
daemon always starts detached.

Startup runs plugin preflight by default. Use `--auto-install` for one-shot dev
setup or `--skip-preflight` only for intentional local debugging.

Agents can ask questions or request approvals mid-run (human-in-the-loop);
pending items land in the `animus agent interactions` inbox
(`list` / `show` / `answer`).

### Queue

Queue entries tell the daemon what subject to dispatch next. An enqueue
nudges the daemon, so dispatch is effectively immediate. The daemon is
queue-only: explicit `animus queue enqueue` entries and cron `schedules:`
are the only dispatch triggers — it never scans the backend for Ready
subjects. A `ready` status makes a subject eligible to enqueue, not
something the daemon auto-runs on its own.

```bash
animus queue enqueue --subject-id task:TASK-001
animus queue list
animus queue stats
```

(`--subject-id` (v0.6.29+) is the universal dispatch selector — qualified
`kind:ID` for any subject kind, or a bare id resolved by the router. Current
0.6.x also still accepts `--task-id` / `--requirement-id`; v0.7-rc/portal
removes those kind-specific flags and requires the subject form. Prefer
`--subject-id` so commands work on both lines.)

## First Workflow

```bash
# Create a ready task subject (note the id it returns)
animus subject create --kind task --title "Add health check endpoint" --priority p1 --status ready

# Enqueue it (use the id returned by subject create)
animus queue enqueue --subject-id task:<id>

# Start the daemon (detaches; prints pid + log path)
animus daemon start --pool-size 2

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
├── animus.toml                   # committed project manifest (plugins + packs)
├── .env.example
├── .animus/
│   ├── config.json
│   ├── workflows.yaml
│   ├── workflows/
│   │   └── custom.yaml
│   ├── skills/
│   │   └── <skill-name>/SKILL.md
│   ├── plugins/                  # pack overrides + project-scoped plugin binaries (gitignored)
│   ├── plugins.lock              # committed lockfile — SOURCE OF TRUTH for the plugin set (schema 2.0, per-platform integrity)
│   ├── plugins.yaml              # derived projection of the lock (regenerated; never hand-edit)
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
