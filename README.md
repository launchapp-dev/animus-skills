# Animus Skills

> The fastest way to turn Claude Code (or Codex, OpenCode, Cursor) into an autonomous engineering team that ships PRs while you sleep.

[Animus](https://github.com/launchapp-dev/animus-cli) is a Rust agent orchestrator. A daemon dispatches workflows from a queue, uses provider and subject plugins to run agents in isolated worktrees, runs your tests, opens PRs, and reviews them — on cron, on demand, or in response to events. **animus-skills** is the skill bundle that teaches your agent how to drive it.

You point a fresh agent at this README. It installs the CLI, links the skills, wires up MCP, and you start running workflows in about a minute.

**Who this is for:**
- **Solo builders** who want 5–15 parallel sprints running across their repos
- **Small teams** who need a self-hosted, auditable orchestrator (no cloud lock-in)
- **Agent power users** who already use Claude Code / Codex / Cursor and want a real backend

## Quick start

1. Install (30 seconds — see below)
2. `cd` into any repo and run `/animus-setup` — scaffolds `.animus/`, writes a first workflow, starts the daemon
3. `/animus-getting-started` — creates your first task and runs it end-to-end
4. `animus daemon stream` — watch the agent work in real time
5. Stop here. If you can run a workflow on a real task, you'll know if Animus is for you.

## Install — 30 seconds

**Requirements:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (or Codex / OpenCode / Cursor), [Git](https://git-scm.com/), `bash`, `curl`. Animus itself is a single Rust binary — no Node, no Python, no Docker.

### One paste, any agent

Open a fresh Claude Code session and paste this. The agent does the rest — clones the repo, installs the `animus` CLI, links every skill into your host's skill directory, and writes `.mcp.json` if you're inside a project:

> Install Animus + Animus Skills: run **`git clone --single-branch --depth 1 https://github.com/launchapp-dev/animus-skills.git ~/.claude/skills/animus-skills && cd ~/.claude/skills/animus-skills && ./setup`**, then add an "Animus" section to CLAUDE.md (or AGENTS.md for Codex) listing the available slash commands: `/animus-setup`, `/animus-bootstrap`, `/animus-getting-started`, `/animus-mcp-setup`, `/animus-workflow-authoring`, `/animus-pack-authoring`, `/animus-skill-authoring`, `/animus-troubleshooting`. Restart the agent so the new MCP server (`animus`) is picked up.

For Codex CLI, swap the clone path to `~/.codex/skills/animus-skills` and AGENTS.md instead of CLAUDE.md.

### Power user — explicit script

```bash
git clone https://github.com/launchapp-dev/animus-skills.git ~/animus-skills
cd ~/animus-skills && ./setup            # auto-detects installed hosts
```

```bash
./setup --host claude        # only Claude Code
./setup --host codex         # only Codex
./setup --host all           # every supported host (claude, codex, opencode, cursor, slate, kiro)
./setup --no-cli             # skip the animus CLI install (use existing binary)
./setup --no-mcp             # skip writing .mcp.json into the current project
```

The script:
1. Installs the `animus` CLI to `~/.local/bin/animus` if it's not already on `PATH`.
2. Symlinks each skill into the host's skill directory (e.g. `~/.claude/skills/<skill-name>`, `~/.codex/skills/<skill-name>`). Hosts discover skills flat as `<host-skills-dir>/<name>/SKILL.md`, so the script links one level down rather than the whole repo.
3. Writes a project-local `.mcp.json` exposing the `animus` MCP server (skipped if one already exists or you pass `--no-mcp`).

### Claude Code marketplace (alternative)

```bash
/plugin marketplace add launchapp-dev/animus-skills
```

This skips the CLI install and MCP wiring — pair it with a manual `curl -fsSL https://raw.githubusercontent.com/launchapp-dev/animus-cli/main/scripts/install.sh | bash` if you don't already have `animus`.

## See it work

```
You:    /animus-setup
Claude: [scaffolds .animus/, writes config.json, generates a first workflow YAML,
         starts the daemon, verifies MCP is reachable]

You:    Create a task to add rate limiting to the /api/upload endpoint.
Claude: [calls animus.subject.create with kind=task, then enqueues TASK-001]

You:    Run it.
Claude: [calls animus.workflow.run — daemon picks up TASK-001, spawns a
         Claude session in an isolated worktree, runs the standard pipeline:
         research → plan → implement → test → review → PR]

You:    animus daemon stream
        [live JSONL — phase transitions, model calls, test runs, git ops]

You:    Now schedule a nightly retro across all my repos.
Claude: [edits .animus/workflows/retro.yaml, adds a cron schedule, restarts daemon]
```

Every step is replayable from the queue — pause, resume, drop, reorder, hold. Failed phases are sticky (the daemon won't silently retry and burn API credits). Outputs land in `~/.animus/<repo-scope>/runs/` so you can audit exactly what each model did.

## Slash commands

| Command | What it does |
|---------|--------------|
| `/animus-setup` | Bootstraps Animus in the current project — `.animus/` config, MCP wiring, first workflow, daemon start |
| `/animus-bootstrap` | Full project bootstrap — interviews you, writes VISION.md + AGENT_PRINCIPLES.md + agents/phases/workflows/schedules YAML + scripts + a runnable first task |
| `/animus-getting-started` | First task, first workflow run, core concepts |
| `/animus-mcp-setup` | Write or repair `.mcp.json` so any MCP-aware agent can drive Animus |
| `/animus-workflow-authoring` | Write or edit workflow YAML — agents, phases, model registries, schedules |
| `/animus-pack-authoring` | Build installable workflow packs — `pack.toml`, runtime overlays, MCP descriptors |
| `/animus-skill-authoring` | Author Animus skills — prompts, tool policies, capabilities, adapters |
| `/animus-troubleshooting` | Daemon crashes, workflow failures, queue problems, merge conflicts |

## Auto-invoked reference skills

These load automatically when the conversation needs them — you don't type a slash command:

| Skill | Loaded when... |
|-------|----------------|
| `animus-configuration` | …you ask about `.animus/`, daemon config, agent runtime, env vars, state layout |
| `animus-task-management` | …creating, listing, updating, blocking, or bulk-editing tasks |
| `animus-subject-operations` | …working with subject backends, task/requirement replacement surfaces, Linear/SQLite/Markdown/custom subject kinds |
| `animus-daemon-operations` | …starting, stopping, monitoring, or debugging the daemon |
| `animus-observability` | …checking status, logs, daemon stream, run output, artifacts, runner health, web UI, or triggers |
| `animus-queue-management` | …enqueueing, holding, releasing, dropping, or reordering work |
| `animus-mcp-tools` | …the agent needs an exact `animus.*` MCP tool name or parameter shape |
| `animus-plugin-operations` | …installing, updating, signing, locking, inspecting, or troubleshooting Animus plugins |
| `animus-model-operations` | …checking model availability, provider API-key status, rosters, validation, or model evals |
| `animus-agent-operations` | …running direct agent executions, controlling runs, or using agent memory/message channels |
| `animus-project-history-git` | …managing project registry entries, execution history, Git repos, worktrees, or confirmation records |
| `animus-workflow-patterns` | …authoring pipelines — QA gates, command phases, conflict resolution, CI checks |
| `animus-agent-personas` | …configuring product-lifecycle agents (PO, architect, auditor, docs-writer, devops) |
| `animus-mcp-servers-for-agents` | …connecting agents to Context7, package-version, sequential-thinking, memory, or GitHub MCP |
| `animus-environment-operations` | …pinning workflows to execution environments/coder nodes, `workspaces:`, broker leases, node teardown (v0.7) |
| `animus-portal-operations` | …driving a hosted portal deployment — portal MCP tools, Connections, MCP-server catalog, script registry |

## Multi-host

`./setup` auto-detects which agents are installed. Force one with `--host`:

| Agent | Flag | Skills install to |
|-------|------|-------------------|
| Claude Code | `--host claude` | `~/.claude/skills/animus-*/` |
| OpenAI Codex CLI | `--host codex` | `~/.codex/skills/animus-*/` |
| OpenCode | `--host opencode` | `~/.config/opencode/skills/animus-*/` |
| Cursor | `--host cursor` | `~/.cursor/skills/animus-*/` |
| Slate | `--host slate` | `~/.slate/skills/animus-*/` |
| Kiro | `--host kiro` | `~/.kiro/skills/animus-*/` |
| All of the above | `--host all` | every directory above |

## What you actually get

After setup you have:

- **`animus` CLI** at `~/.local/bin/animus` — command groups for `subject`, `workflow`, `queue`, `daemon`, `agent`, `chat`, `install`, `add`, `remove`, `git`, `skill`, `pack`, `plugin`, `flavor`, `cost`, `history`, `logs`, `events`, `trigger`, `mcp`, `web`, `init`, `doctor`, `secret`, `auth`, `state`, `approval`, `status`, `output`, `update`, …
- **A daemon** that runs in the background, dispatches workflows from a queue, and manages agent processes in isolated worktrees
- **A plugin-based runtime** — projects declare plugins and packs in a committed `animus.toml` manifest and install them with `animus install` (lockfile-driven; `animus install --locked` in CI/Docker reproduces `.animus/plugins.lock` exactly). On a machine without a manifest, `animus plugin install-defaults` installs the required set; subject and transport/UI defaults are added with `--include-subjects` and `--include-transports`
- **An MCP server** (`animus mcp serve`) that exposes typed tools — your agent calls them directly instead of shelling out
- **Project-local config** in `.animus/` (workflow YAML, skills, pack overrides) — checked in, sharable with teammates
- **Scoped runtime state** in `~/.animus/<repo-scope>/` — runs, artifacts, compiled config — never pollutes your repo
- **A web UI** (`animus web`) backed by installed transport/UI plugins for queue inspection, run replay, and live event streaming

Workflows are battle-tested across 150+ autonomous PRs (see `animus-workflow-patterns`). Current projects either author workflows in `.animus/workflows*.yaml`, initialize from a template, or install/pin workflow packs such as `animus.task`, `animus.review`, and `animus.requirement`.

## Troubleshooting

**Skill not showing up?** `cd ~/.claude/skills/animus-skills && ./setup`

**Stale install after upgrade?** Re-run `./setup` — it auto-cleans dangling symlinks from earlier versions.

**MCP tools missing in Claude / Codex?** Restart your agent so it picks up the new `.mcp.json`. Verify with `animus mcp serve --help` to confirm the binary is on `PATH`.

**Daemon won't start?** Run `animus doctor` and `animus daemon preflight`. In a project with a committed `animus.toml`, fix missing plugins with `animus install`; without a manifest, `animus plugin install-defaults --include-subjects`. For everything else, `/animus-troubleshooting`.

**Agent says "Cannot be launched inside another Claude Code session"?** The daemon inherits `CLAUDECODE=1` from a parent Claude Code shell. Start it from a clean terminal, or prefix with `env -u CLAUDECODE animus daemon start`.

**Want shorter command names?** All slash commands use the `animus-` prefix on purpose — to avoid colliding with other skill packs (gstack, etc.). If you don't run other packs and want to drop the prefix, edit your host's skill directory directly (the symlinks are easy to rename).

## Uninstall

```bash
# 1. Stop the daemon in any project where it's running
animus daemon stop

# 2. Remove the skill symlinks from each host
find ~/.claude/skills ~/.codex/skills ~/.cursor/skills ~/.config/opencode/skills \
  -maxdepth 1 -type l 2>/dev/null | while read -r link; do
  case "$(readlink "$link" 2>/dev/null)" in *animus-skills/skills/*) rm -f "$link" ;; esac
done

# 3. Remove the clone and the CLI
rm -rf ~/.claude/skills/animus-skills ~/animus-skills
rm -f ~/.local/bin/animus

# 4. (Optional) Remove scoped runtime state — runs, artifacts, compiled config
rm -rf ~/.animus
```

Per-project: `rm -rf .animus .mcp.json` (only if `.mcp.json` was Animus-only — check before deleting if you have other MCP servers wired).

## License

MIT. Use it, fork it, ship with it.
