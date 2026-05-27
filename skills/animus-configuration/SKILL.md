---
name: animus-configuration
description: Animus project config, daemon config, plugin config, agent runtime, environment variables, and state layout
user_invocable: false
auto_invoke: true
---

# Configuration

Animus resolves behavior from project-local `.animus/`, installed packs,
repo-scoped runtime state under `~/.animus/<repo-scope>/`, global machine
config, environment variables, and installed STDIO plugins.

## Project-local sources

### `.animus/config.json`

Repository-local Animus config created by `animus init`. This is authored
project config, not daemon runtime state.

Common fields include project defaults such as `default_subject_kind`.

### `.animus/workflows.yaml` and `.animus/workflows/*.yaml`

Hand-authored workflow sources. Typical uses:

- Define repo-specific workflow ids.
- Set the default workflow.
- Declare project MCP servers, agents, variables, phases, and workflows.
- Configure agent memory and communication channels.

Use:

```bash
animus workflow config get
animus workflow config validate
animus workflow config compile
```

### `.animus/skills/<name>/SKILL.md`

Project-scoped Markdown skills. These have highest priority in Animus skill
resolution. Agent-host skills from `.claude/skills` and `.codex/skills` are
lower-trust prompt-text-only probes.

### `.animus/plugins/<pack-id>/`

Project-local pack override root. Use this only when a repository needs to
override installed pack content without changing global machine state.

## Repo-scoped runtime state

Mutable project runtime state lives outside the repo:

```text
~/.animus/<repo-scope>/
├── core-state.json
├── resume-config.json
├── workflow.db
├── config/
│   └── state-machines.v1.json
├── daemon/
│   └── pm-config.json
├── state/
│   └── pack-selection.v1.json
└── worktrees/
```

Key files:

- `workflow.db` stores persisted workflows, tasks, requirements, and checkpoints.
- `daemon/pm-config.json` stores persisted daemon automation settings.
- `config/state-machines.v1.json` stores state-machine config.
- `state/pack-selection.v1.json` stores repo-scoped pack activation and pinning.

Treat these as Animus-managed state. Prefer CLI or MCP tools over direct edits.

## Daemon config

Read current settings:

```bash
animus daemon config
```

MCP: `animus.daemon.config`

Update runtime settings:

```bash
animus daemon config --auto-merge true
animus daemon config --auto-pr true
animus daemon config --auto-commit-before-merge true
animus daemon config --pool-size 3 --auto-run-ready true
```

MCP: `animus.daemon.config-set`

Daemon startup now runs plugin preflight by default:

```bash
animus daemon preflight
animus daemon start --autonomous --auto-install
```

## Machine-wide config

```text
~/.animus/
├── config.json
├── credentials.json
├── packs/
│   └── <pack-id>/<version>/
├── plugins/
│   └── <plugin-name>
├── skills/
│   └── <skill-name>/SKILL.md
└── template-registries/
```

### Packs

```bash
animus pack list
animus pack inspect --pack-id animus.task
animus pack install --path /tmp/vendor.pack --activate
animus pack pin --pack-id vendor.pack --version =1.2.3
```

### Plugins

```bash
animus plugin install-defaults --include-subjects --include-transports
animus plugin list
animus plugin lock verify
```

`animus web serve` and `animus web open` require installed transport/UI
plugins; they no longer run an in-tree web server.

## Environment variables

Core variables:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_CONFIG_DIR` | Override global config root, default `~/.animus` |
| `ANIMUS_RUNNER_CONFIG_DIR` | Override runner config directory |
| `ANIMUS_RUNNER_SCOPE` | Runner scope identifier |
| `ANIMUS_MCP_SCHEMA_DRAFT` | Select Draft-07 MCP schemas |
| `ANIMUS_MCP_ENDPOINT` | Override embedded MCP client endpoint |
| `ANIMUS_USER_ID` | Override recorded user id |
| `ANIMUS_DEBUG` | Enable verbose debug logging |
| `ANIMUS_LOG_JSON` | Emit JSON logs |
| `ANIMUS_DEBUG_MCP_STDIO` | Log raw MCP stdio frames |

Plugin and template variables:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_PLUGIN_DIR` | Override plugin install directory |
| `ANIMUS_PLUGIN_PATH` | Extra directories scanned for plugin binaries |
| `ANIMUS_TEMPLATE_REGISTRY_URL` | Override project-template registry |

Provider passthrough examples:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_CLAUDE_EXTRA_ARGS` / `_JSON` | Extra Claude CLI args |
| `ANIMUS_CODEX_EXTRA_ARGS` / `_JSON` | Extra Codex CLI args |
| `ANIMUS_CODEX_EXTRA_CONFIG_OVERRIDES` / `_JSON` | Extra Codex `--config` overrides |
| `ANIMUS_CODEX_NETWORK_ACCESS` | Toggle Codex sandbox network access |
| `ANIMUS_CODEX_WEB_SEARCH` | Toggle Codex web search |

Plugin kill-switches are operator escape hatches. Example:
`ANIMUS_DAEMON_DISABLE_TRIGGERS=1` disables trigger plugin supervision on
daemon startup. Removed built-in provider and subject adapter kill-switches are
no-ops; uninstall or quarantine the plugin instead.

## Secret handling

Do not put API tokens in workflow YAML. Plugins read secrets from the daemon's
process environment. Use YAML interpolation for non-secret config only:

```yaml
subjects:
  - id: my-linear
    backend: linear
    config:
      team_id: ${LINEAR_TEAM_ID:-default-team}
      workspace: ${LINEAR_WORKSPACE:?set LINEAR_WORKSPACE}
```

Start the daemon with required secrets in the parent shell:

```bash
LINEAR_API_TOKEN=lin_api_... OPENAI_API_KEY=sk-... animus daemon start --autonomous
```

The daemon does not auto-load `.env` files. Source them before startup if
needed.

## Precedence

Workflow resolution:

1. CLI flags and `--input-json` / `--var` overrides
2. Supported environment variables
3. Project pack overrides in `.animus/plugins/`
4. Project YAML in `.animus/workflows.yaml` and `.animus/workflows/*.yaml`
5. Installed packs in `~/.animus/packs/`

Skill resolution:

1. Project `.animus/skills/`
2. User `~/.animus/skills/`
3. Installed registry or pack skills, including `animus.core-skills`
4. Built-in fallback skills
5. Agent-host probes such as `.claude/skills` or `.codex/skills` as prompt-text-only
