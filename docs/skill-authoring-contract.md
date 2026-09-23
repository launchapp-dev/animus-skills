# Skill Authoring Contract

This repository publishes one portable Agent Skills bundle to several agent
harnesses. The shared source must remain useful without relying on one
harness's private frontmatter extensions.

## Portable `SKILL.md`

Every `skills/<name>/SKILL.md` uses the common subset accepted by the Agent
Skills specification and Codex:

```yaml
---
name: animus-example
description: Explain what the skill does. Use when the request has a specific trigger; name the neighboring skill for the nearest exclusion.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---
```

Rules:

- `name` matches the directory and uses lowercase letters, digits, and single
  hyphens.
- `description` states both capability and activation boundary. Differentiate
  the skill from its closest neighbors instead of adding a keyword dump.
- `metadata` values are strings. Do not restore the historical top-level
  `user_invocable`, `auto_invoke`, or `animus_version` keys.
- Do not add harness-specific fields such as `disable-model-invocation`,
  `user-invocable`, `paths`, `context`, or UI colors to the shared frontmatter.
  Some clients ignore them, while others reject them.
- Skill invocation supplies instructions, not authorization. Mutating,
  destructive, privileged, external, or expensive actions still require the
  authority implied by the user's request and the active harness.

## Harness extensions

- Codex reads `agents/openai.yaml`. Keep its display name, short description,
  default prompt, and implicit-invocation policy consistent with `SKILL.md`.
- Claude Code, Cursor, OpenCode, and Kiro can consume the portable skill
  directly. Their extra invocation or path-scoping features belong in
  host-local settings or a future generated host overlay—not the shared file.
- `animus-setup` and `animus-bootstrap` are intentionally explicit-only in
  Codex. Their portable descriptions also say they require an explicit user
  request so other harnesses receive the same safety intent.

The compatibility baseline is the [Agent Skills specification](https://agentskills.io/specification).
Before changing host behavior, verify it against the current official docs for
[Claude Code](https://code.claude.com/docs/en/slash-commands),
[Cursor](https://prod.cursor.com/docs/skills),
[OpenCode](https://opencode.ai/docs/skills), and
[Kiro](https://kiro.dev/docs/skills/). Shared portability does not imply that
every host implements the same optional extension fields or invocation UI.

## Progressive disclosure

The entrypoint contains the decision-changing workflow, boundaries, and links
needed for routing. Put command catalogs, complete schemas, large templates,
and symptom matrices in focused `references/` files. Link a reference from the
entrypoint and say when to read it. Avoid chains where one reference is needed
only to discover another.

Keep `SKILL.md` below 400 lines in this bundle. This is a repository quality
limit, not an Agent Skills protocol limit.

## Routing boundaries

Use the description to separate the common overlaps:

- setup vs bootstrap vs getting started;
- task lifecycle vs subject backend/kind vs queue state;
- daemon lifecycle vs observability vs troubleshooting;
- workflow syntax vs workflow patterns vs hosted Portal mutation;
- host-to-Animus MCP setup vs MCP servers inside agent runs vs exact tool
  lookup;
- plugin operation vs flavor bundles vs supply-chain policy; and
- agent run control vs human interactions vs chat conversations.

## Validation

Run:

```bash
python3 scripts/validate-skills.py
```

The validator checks the portable frontmatter subset, version metadata,
descriptions, Codex sidecars, entrypoint size, and relative Markdown links.
When Codex's bundled validator is available, also run `quick_validate.py` over
every skill directory before publishing.
