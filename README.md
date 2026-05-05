# Animus Skills

A skill bundle for using [Animus](https://github.com/launchapp-dev/animus-cli) — an autonomous agent orchestrator for software development workflows. Works with Claude Code, OpenAI Codex CLI, OpenCode, Cursor, and other agent hosts.

## Install — 30 seconds

### One paste, any agent

Paste this into a fresh Claude Code (or Codex / OpenCode / Cursor) session. The agent does the rest — clones the repo, installs the `animus` CLI, links the skills into the host's skill directory, and writes `.mcp.json` if you're inside a project:

> Install Animus + Animus Skills: run **`git clone --single-branch --depth 1 https://github.com/launchapp-dev/animus-skills.git ~/.claude/skills/animus-skills && cd ~/.claude/skills/animus-skills && ./setup`**, then add an "Animus" section to CLAUDE.md (or AGENTS.md for Codex) listing the available skills: `/animus-setup`, `/animus-getting-started`, `/animus-mcp-setup`, `/animus-workflow-authoring`, `/animus-pack-authoring`, `/animus-skill-authoring`, `/animus-troubleshooting`. Restart the agent so the new MCP server (`animus`) is picked up.

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

This skips the CLI install and MCP wiring — pair it with a manual `curl -fsSL https://raw.githubusercontent.com/launchapp-dev/ao/main/install.sh | bash` if you don't already have `animus`.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/animus-setup` | Set up Animus in the current project — init, MCP, first workflow |
| `/animus-getting-started` | Install Animus, core concepts, first task and workflow |
| `/animus-mcp-setup` | Create `.mcp.json` and connect AI tools to Animus |
| `/animus-workflow-authoring` | Write custom workflow YAML — agents, phases, crons |
| `/animus-pack-authoring` | Build workflow packs — manifest, agents, phases, marketplace |
| `/animus-skill-authoring` | Build Animus skills — prompts, tool policies, capabilities |
| `/animus-troubleshooting` | Common Animus issues and fixes |

## Auto-Invoked Reference Skills

These skills are automatically loaded by Claude when contextually relevant:

| Skill | Description |
|-------|-------------|
| animus-configuration | Project config, daemon config, agent runtime, state layout |
| animus-task-management | Full task lifecycle — create, list, update, block/unblock |
| animus-daemon-operations | Start, monitor, and troubleshoot the daemon |
| animus-queue-management | Dispatch queue operations |
| animus-mcp-tools | Complete `animus.*` MCP tool reference |
| animus-workflow-patterns | Battle-tested pipeline patterns from 150+ autonomous PRs |
| animus-agent-personas | Product lifecycle agents — PO, architect, auditor, docs-writer |
| animus-mcp-servers-for-agents | Connect agents to Context7, package-version, memory, GitHub |
| animus-pack-authoring | Build workflow packs with pack.toml, agent overlays, MCP descriptors |
| animus-skill-authoring | Build Animus skills with YAML definitions, tool policies, adapters |

## Usage

Once installed, Claude can help you:

- **Set up Animus**: `/animus-setup` walks through project init, MCP config, and first workflow
- **Write workflows**: Ask Claude to create or update `.ao/workflows.yaml` and `.ao/workflows/*.yaml`
- **Manage tasks**: Claude can create, prioritize, and enqueue tasks via MCP tools
- **Debug issues**: `/animus-troubleshooting` covers daemon crashes, workflow failures, queue problems, and the new live log streaming flow via `animus daemon stream`
- **Configure agents**: Claude knows how to set up persona agents for the full product lifecycle
- **Build packs**: `/animus-pack-authoring` guides you through creating installable workflow packs
- **Build skills**: `/animus-skill-authoring` covers creating reusable agent behavior definitions
