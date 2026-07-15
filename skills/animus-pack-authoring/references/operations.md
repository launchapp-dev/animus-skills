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

Animus no longer ships bundled packs in the binary. Pinning a pack to the `bundled` source fails; install from an external repository and pin as `installed` or `project_override`.

## CLI commands

### Install a pack

Projects with a committed `animus.toml` (v0.6.9+) declare packs in `[packs]`
and install them with the manifest flow — this is the canonical team path:

```bash
animus add my-org/my-pack@v1.2.0 --pack   # add to animus.toml + install
animus install                            # install everything the manifest declares
animus install --locked                   # CI/Docker: reproduce .animus/plugins.lock exactly
animus remove my-pack --pack              # drop from manifest + uninstall
```

`animus pack install` remains the direct/ad-hoc path:

```bash
animus pack install --path ./my-pack
animus pack install --name my-pack --registry my-registry
animus pack install --path ./my-pack --force --activate
animus pack install --path ./my-pack --dry-run          # print dependency closure + plugin requirements, install nothing
animus pack install --path ./my-pack --no-deps          # skip declared pack dependencies
animus pack install --path ./my-pack --install-plugins  # install missing [[requires_plugins]] without prompting
```

As of v0.5.14, `install` also resolves the pack's non-optional
`[[dependencies]]` after the parent (semver-aware skip of already-installed,
depth cap 5 with cycle detection; a failing dependency never aborts the parent
and prints the manual command), and checks `[[requires_plugins]]` against the
installed-plugin registry (interactive prompt default-yes; non-interactive runs
print exact `animus plugin install <repo>@<tag>` commands unless
`--install-plugins` is passed).

### List and inspect packs

```bash
animus pack list
animus pack list --active-only
animus pack list --source installed
animus pack info --pack-id my-org.my-pack
animus pack info --path ./my-pack
```

`pack info` reports pack dependencies and required plugins with
installed/missing status. The `pack inspect` alias was retired in v0.5.14.

### Uninstall a pack

```bash
animus pack uninstall my-org.my-pack --dry-run
animus pack uninstall my-org.my-pack            # all versions + project selection entry
animus pack uninstall my-org.my-pack --version 0.1.0
animus pack uninstall my-org.my-pack --force    # even when project workflow YAML still references it
```

Uninstall applies immediately (no `--yes`); use `--dry-run` to preview. It
refuses while project workflow YAML references the pack unless `--force`.

### Pin or disable a pack

```bash
animus pack pin --pack-id my-org.my-pack --version "=0.2.0"
animus pack pin --pack-id animus.task --source installed
animus pack pin --pack-id my-org.my-pack --disable
```

Pack selections are stored in `~/.animus/<repo-scope>/state/pack-selection.v1.json`
(pack content installs machine-wide; activation is per-project).

### Marketplace

```bash
animus pack registry add --id community --url https://github.com/animus-packs/registry
animus pack registry sync --id community
animus pack search --query "review" --registry community
animus pack registry list
animus pack registry remove --id community
```

### Publish a pack

```bash
animus pack publish --path ./my-pack --registry community \
  --url https://github.com/my-org/my-pack --category devops
```

`publish` validates the manifest, registers the pack in the locally cached
registry clone, and prints git commit/push instructions — it does not push
automatically. `--path` defaults to the current directory; the registry must
already exist via `animus pack registry add`.

## First-party packs

These are not bundled in the binary. `animus init` installs and activates them
from their pinned GitHub release tags in `default-install.json` (interactive
walkthrough offers it default-yes; pass `--install-packs` for non-interactive
runs, `--no-packs` to skip the prompt entirely). Per-pack failures never abort
init — each pack reports `installed` / `already_installed` / `failed` with a
manual recovery command. `ANIMUS_INIT_PACK_SOURCE_DIR` overrides the GitHub
clone with a local `<dir>/<pack-id>` source for offline installs. You can also
install them individually with `animus pack install`.

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
