---
name: animus-configuration
description: Animus project config, daemon config, agent runtime, environment variables, and state layout
user_invocable: false
auto_invoke: true
---

# Animus Configuration

Animus has three main configuration layers: project-local `.ao/`, repo-scoped runtime state under `~/.ao/<repo-scope>/`, and global machine config.

## Project-Local `.ao/`

Created by `animus setup`. This is the project-authored configuration surface.

Common files:
- `.ao/config.json`
- `.ao/pm-config.json`
- `.ao/workflows.yaml`
- `.ao/workflows/*.yaml`

## Daemon Config

Managed via CLI and MCP. Do not hand-edit generated JSON.

### Read Config
```bash
animus daemon config
```
MCP: `animus.daemon.config`

### Update Config
```bash
animus daemon config --auto-merge true
animus daemon config --auto-pr true
animus daemon config --auto-commit-before-merge true
animus daemon config --pool-size 3 --auto-run-ready true
```
MCP: `animus.daemon.config-set`

## Workflow Config

Hand-edited YAML. Defines agents, phases, workflows, and cron schedules. See the [workflow-authoring](../animus-workflow-authoring/SKILL.md) skill for full details.

Source locations:
- `.ao/workflows.yaml`
- `.ao/workflows/*.yaml`

Useful commands:
```bash
animus workflow config get
animus workflow config validate
animus workflow config compile
```

## Agent Runtime Config

Controls which AI model/tool each agent profile uses.

Inspect and update through workflow config commands rather than direct file edits where possible.

### Model Options
- `claude-sonnet-4-6` — Claude Sonnet (default for implementation)
- `claude-opus-4-6` — Claude Opus (higher quality, slower)
- `gemini-3.1-pro-preview` — Google Gemini (good for research phases)

### Tool Options
- `claude` — Claude Code CLI
- `codex` — OpenAI Codex CLI
- `gemini` — Google Gemini CLI
- `oai-runner` — OpenAI-compatible model runner

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `AO_CONFIG_DIR` | Override global config directory |
| `AO_ALLOW_NON_EDITING_PHASE_TOOL` | Allow non-write-capable tools (e.g., gemini) for all phases |

## State Layout

```
.ao/
├── config.json
├── pm-config.json
├── workflows.yaml
└── workflows/

~/.ao/<repo-scope>/
├── core-state.json
├── resume-config.json
├── docs/
├── requirements/
├── tasks/
├── index/
├── state/
├── runs/
├── artifacts/
├── daemon/
└── worktrees/
```

## Repo Scope

`<repo-scope>` is derived from the canonical project path: `<sanitized-repo-name>-<12 hex sha256 prefix>`.

This ensures multiple projects don't collide in runtime state.

## Precedence

For model/tool selection:
1. Phase-level `runtime.model` override (in workflow YAML)
2. Agent profile `model`/`tool` (in agent-runtime-config)
3. Compiled defaults in the Animus binary

For workflow resolution:
1. `.ao/workflows.yaml`
2. `.ao/workflows/*.yaml`
3. Built-in and installed definitions
