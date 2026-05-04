---
name: pack-authoring
description: Build Animus workflow packs - `pack.toml`, workflow exports, runtime overlays, MCP server descriptors, schedules, and marketplace operations. Use when creating or updating installable Animus packs.
user_invocable: true
auto_invoke: true
---

# Pack Authoring

Workflow packs bundle reusable Animus workflows, runtime overlays, and optional MCP integrations.

Do not read the full pack manual before starting. Open only the reference that matches the file you are editing:

- Read [references/manifest.md](references/manifest.md) for `pack.toml` structure and field definitions.
- Read [references/runtime-and-workflows.md](references/runtime-and-workflows.md) for workflow exports, overlays, decision contracts, or MCP server descriptors.
- Read [references/operations.md](references/operations.md) only for install, pin, registry, bundled pack, or schedule questions.

## Minimal pack shape

Start with the smallest viable pack:

```text
my-pack/
├── pack.toml
├── workflows/
│   └── workflows.yaml
└── runtime/
    └── agent-runtime.overlay.yaml
```

## Authoring flow

1. Pick the pack kind: `domain-pack`, `connector-pack`, or `capability-pack`.
2. Write a minimal `pack.toml`.
3. Export one working workflow before adding more variants.
4. Add runtime overlays only for the agents and phases the pack actually needs.
5. Declare permissions and secrets early so activation failures are explicit.

## Rules

1. Pack-qualify workflow IDs to avoid collisions.
2. Keep agents narrow and role-specific.
3. Use workflow references to compose with bundled packs instead of duplicating logic.
4. Use decision contracts on review-style phases that should gate progress.
5. Test with `animus pack inspect` before installing or publishing.

If the task shifts from manifest work to runtime overlays or registry operations, open the corresponding reference file instead of broad-reading every pack detail.
