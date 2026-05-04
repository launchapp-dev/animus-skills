# Animus Skills

A skill bundle for using [Animus](https://github.com/launchapp-dev/animus-cli) — an autonomous agent orchestrator for software development workflows. Works with Claude Code, OpenAI Codex CLI, OpenCode, Cursor, and other agent hosts.

## Install — 30 seconds

### One paste, any agent

Paste this into a fresh Claude Code (or Codex / OpenCode / Cursor) session. The agent does the rest — clones the repo, installs the `animus` CLI, links the skills into the host's skill directory, and writes `.mcp.json` if you're inside a project:

> Install Animus + Animus Skills: run **`git clone --single-branch --depth 1 https://github.com/samishukri/animus-skills.git ~/.claude/skills/animus-skills && cd ~/.claude/skills/animus-skills && ./setup`**, then add an "Animus" section to CLAUDE.md (or AGENTS.md for Codex) listing the available skills: `/setup-animus`, `/getting-started`, `/mcp-setup`, `/workflow-authoring`, `/pack-authoring`, `/skill-authoring`, `/troubleshooting`. Restart the agent so the new MCP server (`animus`) is picked up.

For Codex CLI, swap the clone path to `~/.codex/skills/animus-skills` and AGENTS.md instead of CLAUDE.md.

### Power user — explicit script

```bash
git clone https://github.com/samishukri/animus-skills.git ~/animus-skills
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
2. Symlinks this repo into the host's skill directory (e.g. `~/.claude/skills/animus-skills`, `~/.codex/skills/animus-skills`).
3. Writes a project-local `.mcp.json` exposing the `animus` MCP server (skipped if one already exists or you pass `--no-mcp`).

### Claude Code marketplace (alternative)

```bash
/plugin marketplace add samishukri/animus-skills
```

This skips the CLI install and MCP wiring — pair it with a manual `curl -fsSL https://raw.githubusercontent.com/launchapp-dev/ao/main/install.sh | bash` if you don't already have `animus`.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/setup-animus` | Set up Animus in the current project — init, MCP, first workflow |
| `/getting-started` | Install Animus, core concepts, first task and workflow |
| `/mcp-setup` | Create `.mcp.json` and connect AI tools to Animus |
| `/workflow-authoring` | Write custom workflow YAML — agents, phases, crons |
| `/pack-authoring` | Build workflow packs — manifest, agents, phases, marketplace |
| `/skill-authoring` | Build Animus skills — prompts, tool policies, capabilities |
| `/troubleshooting` | Common Animus issues and fixes |

## Auto-Invoked Reference Skills

These skills are automatically loaded by Claude when contextually relevant:

| Skill | Description |
|-------|-------------|
| configuration | Project config, daemon config, agent runtime, state layout |
| task-management | Full task lifecycle — create, list, update, block/unblock |
| daemon-operations | Start, monitor, and troubleshoot the daemon |
| queue-management | Dispatch queue operations |
| mcp-tools | Complete `animus.*` MCP tool reference |
| workflow-patterns | Battle-tested pipeline patterns from 150+ autonomous PRs |
| agent-personas | Product lifecycle agents — PO, architect, auditor, docs-writer |
| mcp-servers-for-agents | Connect agents to Context7, package-version, memory, GitHub |
| pack-authoring | Build workflow packs with pack.toml, agent overlays, MCP descriptors |
| skill-authoring | Build Animus skills with YAML definitions, tool policies, adapters |

## Usage

Once installed, Claude can help you:

- **Set up Animus**: `/setup-animus` walks through project init, MCP config, and first workflow
- **Write workflows**: Ask Claude to create or update `.ao/workflows.yaml` and `.ao/workflows/*.yaml`
- **Manage tasks**: Claude can create, prioritize, and enqueue tasks via MCP tools
- **Debug issues**: `/troubleshooting` covers daemon crashes, workflow failures, queue problems, and the new live log streaming flow via `animus daemon stream`
- **Configure agents**: Claude knows how to set up persona agents for the full product lifecycle
- **Build packs**: `/pack-authoring` guides you through creating installable workflow packs
- **Build skills**: `/skill-authoring` covers creating reusable agent behavior definitions
