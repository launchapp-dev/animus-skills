# Operations

Use this reference when installing, inspecting, pinning, or operating packs.

## Cron schedules

```yaml
schedules:
  - id: my-org.my-pack/nightly-scan
    cron: "0 2 * * *"
    workflow_ref: my-org.my-pack/standard
    enabled: true
```

## Resolution order

1. Project overrides in `.animus/plugins/<pack-id>/`
2. Installed packs in `~/.animus/packs/<pack-id>/<version>/`

Packs are no longer bundled in the Animus binary — the former bundled packs live as standalone repos (`launchapp-dev/animus-pack-{core-skills,task,requirement,review}`) and install via `animus init --install-packs` or `animus pack install`.

## CLI commands

### Install a pack

```bash
animus pack install --path ./my-pack
animus pack install --name my-pack --registry my-registry
animus pack install --path ./my-pack --force --activate
```

### List and inspect packs

```bash
animus pack list
animus pack list --active-only
animus pack list --source installed
animus pack info --pack-id my-org.my-pack
animus pack info --path ./my-pack
```

`info` is the canonical detail verb; `animus pack inspect` keeps working as an alias.

### Pin or disable a pack

```bash
animus pack pin --pack-id my-org.my-pack --version "=0.2.0"
animus pack pin --pack-id animus.task --source installed
animus pack pin --pack-id my-org.my-pack --disable
```

Pack selections are stored in `~/.animus/<repo-scope>/state/pack-selection.v1.json`.

### Uninstall a pack

```bash
animus pack uninstall --pack-id my-org.my-pack --dry-run
animus pack uninstall --pack-id my-org.my-pack
animus pack uninstall --pack-id my-org.my-pack --version 0.1.0
```

Uninstall removes the installed pack (all versions unless `--version` is given) plus its project selection entry. It refuses while project workflow YAML still references the pack unless `--force`.

### Marketplace

```bash
animus pack registry add --id community --url https://github.com/animus-packs/registry
animus pack registry sync --id community
animus pack search --query "review" --registry community
animus pack registry list
animus pack registry remove --id community
```

## Recommended packs

The recommended pack set (installed via `animus init --install-packs`):

| Pack | Exports | Purpose |
|------|---------|---------|
| `animus.task` | standard, ui-ux, quick-fix, gated, triage, refine | Task workflow pipelines |
| `animus.review` | cycle | Review-cycle sub-workflow composed by `animus.task` workflows |
| `animus.requirement` | draft, refine, plan, execute | Requirement planning and materialization |
| `animus.core-skills` | (skills only) | Default skill catalog (implementation, code-review, debugging, ...) |

## Example connector pack

```toml
schema = "animus.pack.v1"
id = "my-org.jira-sync"
version = "0.1.0"
kind = "connector-pack"
title = "Jira Sync"
description = "Sync Animus tasks with Jira issues."

[ownership]
mode = "project"

[compatibility]
animus_core = ">=0.1.0"
workflow_schema = "v2"
subject_schema = "v2"

[workflows]
root = "workflows"
exports = ["my-org.jira-sync/import", "my-org.jira-sync/export"]

[runtime]
agent_overlay = "runtime/agent-runtime.overlay.yaml"

[mcp]
servers = "mcp/servers.toml"

[permissions]
tools = ["animus"]
mcp_namespaces = ["jira"]

[secrets]
required = ["JIRA_BASE_URL", "JIRA_API_TOKEN"]

[[runtime.requirements]]
runtime = "node"
version = ">=18.0.0"
reason = "Jira MCP server requires Node 18+"
```
