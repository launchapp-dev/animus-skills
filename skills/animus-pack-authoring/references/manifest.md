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
└── subjects/
    └── schemas.yaml
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
animus_core = ">=0.1.0"
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

[[dependencies]]
id = "animus.review"
version = ">=0.1.0"
reason = "Uses the review cycle for PR review."

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
| `compatibility` | `animus_core` | No | Semver range |
| `compatibility` | `workflow_schema` | No | Usually `v2` |
| `compatibility` | `subject_schema` | No | Usually `v2` |
| `subjects` | `kinds` | No | Required if `subjects` block exists |
| `subjects` | `default_kind` | No | Must appear in `subjects.kinds` |
| `workflows` | `root` | Yes | Relative path to workflow YAML |
| `workflows` | `exports` | Yes | Must be non-empty and prefixed with `<pack-id>/` |
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
| `dependencies` | `id` | No | Pack ID |
| `dependencies` | `version` | No | Semver requirement |
| `dependencies` | `optional` | No | Default false |
| `dependencies` | `reason` | No | Must be non-empty if set |
| `permissions` | `tools` | No | CLI or MCP-exposed tools used by the pack |
| `permissions` | `mcp_namespaces` | No | MCP namespaces the pack touches |
| `secrets` | `required` | No | Required env vars |
| `secrets` | `optional` | No | Optional env vars |
| `native_module` | `feature` | No | Advanced feature-gated native module |
| `native_module` | `module_id` | No | Native module ID |
| `native_module` | `optional` | No | Default false |

## Validation constraints that matter

- `workflows.exports` cannot be empty.
- Every export must start with `<pack-id>/`.
- Relative paths must stay inside the pack root.
- `subjects.default_kind` must be listed in `subjects.kinds`.
- `mcp` must declare at least one of `mcp.servers` or `mcp.tools`.
- `runtime.requirements` rejects duplicate runtime declarations.
- `dependencies` rejects duplicates and self-references.
