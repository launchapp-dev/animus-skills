---
name: animus-skill-authoring
description: Build Animus skills - YAML skill definitions, prompts, tool policies, capabilities, adapters, and registries. Use when creating or updating Animus skill files under user or project skill definitions.
user_invocable: true
auto_invoke: true
---

# Skill Authoring

Skills control how Animus agents behave: prompts, tool policies, model preferences, MCP access, and capability flags.

Do not memorize the full schema before making progress. Start with a narrow edit, then open only the reference that matches the gap:

- Read [references/schema.md](references/schema.md) for field-level schema details.
- Read [references/examples.md](references/examples.md) for complete examples or workflow composition.
- Read [references/cli-and-registry.md](references/cli-and-registry.md) only for install, search, publish, or registry work.

## Minimal pattern

Start from a small skill and add only the sections the task needs:

```yaml
skills:
  code-review:
    name: code-review
    description: Review code for correctness and risk.
    prompt:
      directives:
        - Flag correctness issues first.
    tool_policy:
      allow: ["Read", "Grep", "Glob"]
      deny: ["Write", "Edit", "Bash"]
    capabilities:
      is_review: true
      writes_files: false
```

## Authoring flow

1. Decide whether the skill is primarily about prompt shaping, tool access, model selection, or capability flags.
2. Start with the smallest viable YAML shape.
3. Add `prompt.directives` before reaching for a full `prompt.system` override.
4. Keep tool policies tight and explicit.
5. Add adapters only when the behavior must differ by CLI tool.

## Rules

1. Keep one skill focused on one behavior.
2. Prefer composable `directives` over large system prompts.
3. Restrict destructive tools by default unless the skill is explicitly mutating.
4. Put project-specific skills in `.ao/skill_definitions/`.
5. Put personal preferences in `~/.ao/config/skill_definitions/`.
6. Tag skills for discoverability only when tags add real value.

If the task expands into registry operations or a complex schema question, open the matching reference file instead of reading all references preemptively.
