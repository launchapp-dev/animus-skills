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

1. Project overrides in `.ao/plugins/<pack-id>/`
2. Installed packs in `~/.ao/packs/<pack-id>/<version>/`
3. Bundled packs in the Animus binary

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
animus pack inspect --pack-id my-org.my-pack
animus pack inspect --path ./my-pack
```

### Pin or disable a pack

```bash
animus pack pin --pack-id my-org.my-pack --version "=0.2.0"
animus pack pin --pack-id animus.task --source installed
animus pack pin --pack-id my-org.my-pack --disable
```

Pack selections are stored in `.ao/state/pack-selection.v1.json`.

### Marketplace

```bash
animus pack registry add --id community --url https://github.com/animus-packs/registry
animus pack registry sync --id community
animus pack search --query "review" --registry community
animus pack registry list
animus pack registry remove --id community
```

## Bundled packs

| Pack | Exports | Purpose |
|------|---------|---------|
| `animus.task` | standard, ui-ux, quick-fix, gated, triage, refine | Task workflow pipelines |
| `animus.review` | cycle | Reusable code-review and testing loop |
| `animus.requirement` | draft, refine, plan, execute | Requirement planning and execution |

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
ao_core = ">=0.1.0"
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
