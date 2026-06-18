# Manifest

Use this reference when authoring or debugging `pack.toml`.

## Current pack layout

```text
my-pack/
├── pack.toml
├── workflows/
│   └── workflows.yaml
├── runtime/
│   ├── agent-runtime.overlay.yaml
│   └── workflow-runtime.overlay.yaml
├── mcp/
│   ├── servers.toml
│   └── tools.toml
├── schedules/
│   └── schedules.yaml
└── skills/
    └── my-skill.yaml
```

Only include the directories your manifest actually references.

## Manifest example

```toml
schema = "animus.pack.v1"
id = "my-org.my-pack"
version = "0.1.0"
kind = "domain-pack"
title = "My Pack"
description = "What this pack does."

[ownership]
mode = "project"

[compatibility]
animus_core = ">=0.5.14"   # floor required when using [[requires_plugins]]
workflow_schema = "v2"
subject_schema = "v2"

[subjects]
kinds = ["animus.task"]
default_kind = "animus.task"

[workflows]
root = "workflows"
exports = [
  "my-org.my-pack/standard",
  "my-org.my-pack/quick-fix",
]

[runtime]
agent_overlay = "runtime/agent-runtime.overlay.yaml"
workflow_overlay = "runtime/workflow-runtime.overlay.yaml"

[[runtime.requirements]]
runtime = "node"
version = ">=20"
reason = "Required by the MCP server"

[mcp]
servers = "mcp/servers.toml"
tools = "mcp/tools.toml"

[schedules]
file = "schedules/schedules.yaml"

[skills]
root = "skills"

[[dependencies]]
id = "animus.review"
version = ">=0.1.0"
reason = "Uses the review cycle for PR review."

[[requires_plugins]]
repo = "launchapp-dev/animus-subject-linear"
tag = "v0.2.0"
role = "subject_backend:linear"
optional = false
reason = "Workflows read Linear issues as subjects."

[permissions]
tools = ["animus", "gh", "pnpm"]
mcp_namespaces = ["jira"]

[secrets]
required = ["GITHUB_TOKEN"]
optional = []
```

## Manifest fields

| Section | Field | Required | Notes |
|---------|-------|:--------:|-------|
| top-level | `schema` | Yes | Must be `animus.pack.v1` |
| top-level | `id` | Yes | Unique pack ID |
| top-level | `version` | Yes | Semver version |
| top-level | `kind` | Yes | `domain-pack`, `connector-pack`, or `capability-pack` |
| top-level | `title` | Yes | Human-readable name |
| top-level | `description` | No | Free text description |
| `ownership` | `mode` | Yes | `bundled`, `installed`, or `project` |
| `compatibility` | `animus_core` | No | Semver range. `ao_core` is accepted as an alias. |
| `compatibility` | `workflow_schema` | No | Usually `v2` |
| `compatibility` | `subject_schema` | No | Usually `v2` |
| `subjects` | `kinds` | No | Required if `subjects` block exists |
| `subjects` | `default_kind` | No | Must appear in `subjects.kinds` |
| `workflows` | `root` | No | Relative path to workflow YAML; required if `workflows` block exists |
| `workflows` | `exports` | No | Must be non-empty and prefixed with `<pack-id>/` if `workflows` block exists |
| `runtime` | `agent_overlay` | No | Relative path |
| `runtime` | `workflow_overlay` | No | Relative path |
| `runtime.requirements` | `runtime` | No | One of `node`, `python`, `uv`, `npm`, `pnpm` |
| `runtime.requirements` | `binary` | No | Simple executable name only, not a path |
| `runtime.requirements` | `version` | No | Semver requirement |
| `runtime.requirements` | `optional` | No | Default false |
| `runtime.requirements` | `reason` | No | Must be non-empty if set |
| `mcp` | `servers` | No | Relative path to `servers.toml` |
| `mcp` | `tools` | No | Relative path to `tools.toml` |
| `schedules` | `file` | No | Relative path to schedules YAML |
| `skills` | `root` | No | Directory of `*.yaml` skill manifests, default `skills` |
| `skills` | `aliases` | No | Map of alias name to YAML file stem under `skills.root` |
| `dependencies` | `id` | No | Pack ID; required in each `[[dependencies]]` entry |
| `dependencies` | `version` | No | Semver requirement |
| `dependencies` | `optional` | No | Default false |
| `dependencies` | `reason` | No | Must be non-empty if set |
| `requires_plugins` | `repo` | No | Required in each `[[requires_plugins]]` entry; `OWNER/REPO` GitHub slug (e.g. `launchapp-dev/animus-subject-linear`) |
| `requires_plugins` | `tag` | No | Release tag to suggest/install (e.g. `v0.2.0`); no whitespace |
| `requires_plugins` | `role` | No | Informational role hint (e.g. `subject_backend:linear`) |
| `requires_plugins` | `optional` | No | Default false |
| `requires_plugins` | `reason` | No | Must be non-empty if set |
| `permissions` | `tools` | No | CLI or MCP-exposed tools used by the pack |
| `permissions` | `mcp_namespaces` | No | MCP namespaces the pack touches |
| `secrets` | `required` | No | Required env vars |
| `secrets` | `optional` | No | Optional env vars |
| `native_module` | `feature` | Yes | Advanced feature-gated native module; required when `[native_module]` is present |
| `native_module` | `module_id` | Yes | Native module ID; required when `[native_module]` is present |
| `native_module` | `optional` | No | Default false |

## Validation constraints that matter

- A pack must declare at least one of `workflows` or `skills`.
- `workflows.exports` cannot be empty when `workflows` is present.
- Every export must start with `<pack-id>/`.
- Relative paths must stay inside the pack root.
- `subjects.default_kind` must be listed in `subjects.kinds`.
- `mcp` must declare at least one of `mcp.servers` or `mcp.tools`.
- `runtime.requirements` rejects duplicate runtime declarations.
- `dependencies` rejects duplicates and self-references.
- `requires_plugins.repo` must be an `OWNER/REPO` slug; duplicate repos are rejected.

## Dependencies and required plugins (v0.5.14+)

Both sections are enforced at install time, not just documentation:

- `[[dependencies]]` — `animus pack install` resolves and installs declared
  non-optional pack dependencies after the parent pack: already-installed
  versions are skipped semver-aware, dependencies of dependencies recurse to
  depth 5 with cycle detection, and each dependency resolves through the same
  source path as the parent (`ANIMUS_INIT_PACK_SOURCE_DIR` offline override,
  marketplace registry, or the pinned `default-install.json` GitHub release).
  Optional dependencies print as suggestions. A failing dependency never
  aborts the parent install; the manual install command is surfaced instead.
- `[[requires_plugins]]` — checked against the installed-plugin registry at
  install. Missing required plugins prompt interactively (default yes), install
  non-interactively with `--install-plugins`, and otherwise print the exact
  `animus plugin install <repo>@<tag>` commands. `animus pack info` reports
  both pack dependencies and required plugins with installed/missing status.

Compatibility: packs WITHOUT `[[requires_plugins]]` load on older Animus
versions. Packs USING it require animus >= 0.5.14 (older versions reject the
unknown section), so pair it with `compatibility.animus_core = ">=0.5.14"`.
