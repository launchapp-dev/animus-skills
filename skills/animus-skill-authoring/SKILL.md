---
name: animus-skill-authoring
description: Build Animus skills - YAML skill definitions, prompts, tool policies, capabilities, adapters, and registries. Use when creating or updating Animus skill files under user or project skill definitions.
user_invocable: true
auto_invoke: true
animus_version: "0.5.21"   # animus CLI surface this skill targets
---

# Skill Authoring

Skills control how Animus agents behave: prompts, tool policies, model preferences, MCP access, and capability flags.

Do not memorize the full schema before making progress. Start with a narrow edit, then open only the reference that matches the gap:

- Read [references/schema.md](references/schema.md) for field-level schema details.
- Read [references/examples.md](references/examples.md) for complete examples or workflow composition.
- Read [references/cli-and-registry.md](references/cli-and-registry.md) only for create, install, uninstall, search, publish, or registry work.

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
2. Scaffold with `animus skill create --name <slug> --description "..." --prompt "..."` (project scope by default; `--user` for cross-project), or start with the smallest viable YAML shape.
3. Add `prompt.directives` before reaching for a full `prompt.system` override.
4. Keep tool policies tight and explicit.
5. Add adapters only when the behavior must differ by CLI tool.
6. After a workflow run, verify the skill actually applied with `animus output phase-outputs --workflow-id <id>` — its Skills block shows requested vs applied (with contribution kinds) vs missing.

## Where skills apply

- **Workflow phases** — `phases.<id>.skills` and `agents.<id>.skills` resolve daemon-side at dispatch (union, phase entries first) and ride to the workflow runner as `ANIMUS_PHASE_SKILLS_JSON` (runner >= v0.4.2; `animus daemon preflight` warns on older runners). A missing skill name is a loud warning plus a `missing` metadata record — never a hard failure. Typo'd explicit `skills:` names also warn at `animus workflow config validate` / `compile` time.
- **Ad-hoc runs** — `animus agent run --skill <name>` and `animus chat send --skill <name>` apply the FULL skill: prompt prefix/suffix/directives wrap the prompt, `prompt.system` rides the session system prompt, `extra_args` / `env` / `codex_config_overrides` graft onto the launch, and the skill's `model` / `timeout_secs` apply when not explicitly given. An unknown `--skill` name is an error here. Precedence: explicit CLI flags / context-json > skill > defaults; a caller-supplied `--runtime-contract-json` disables skill application entirely.

Source precedence on both paths: project > user > installed > agent-host (prompt-text-only).

## Rules

1. Keep one skill focused on one behavior.
2. Prefer composable `directives` over large system prompts.
3. Restrict destructive tools by default unless the skill is explicitly mutating.
4. Put project-specific skills in `.animus/config/skill_definitions/` (YAML) or `.animus/skills/` (markdown `SKILL.md`).
5. Put personal preferences in `~/.animus/config/skill_definitions/` (YAML) or `~/.animus/skills/` (markdown `SKILL.md`).
6. Tag skills for discoverability only when tags add real value.

If the task expands into registry operations or a complex schema question, open the matching reference file instead of reading all references preemptively.
