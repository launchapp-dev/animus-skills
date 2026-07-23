# Skill Schema

Use this reference when you need field-level details for an Animus skill definition.

## Skill definition format

Skills are defined in YAML files with schema `animus.skills.v1`.

```yaml
skills:
  code-review:
    name: code-review
    version: "1.0.0"
    description: Professional code review with security and performance focus.
    category: review

    activation:
      tools: [claude]
      models: []

    prompt:
      system: |
        You are an expert code reviewer.
      prefix: "Review the following changes carefully."
      suffix: "Provide actionable feedback with line references."
      directives:
        - Never approve code with hardcoded secrets

    tool_policy:
      allow:
        - "Read"
        - "Grep"
        - "Glob"
        - "subject.*"
      deny:
        - "Write"
        - "Edit"
        - "Bash"

    model:                 # discouraged — see the `model` field note below
      preferred: claude-sonnet-4-6
      fallback: claude-opus-4-8

    mcp_servers:
      - animus
      - sequential-thinking

    timeout_secs: 300

    capabilities:
      is_review: true
      writes_files: false
      mutates_state: false

    extra_args: []
    env: {}
    tags: ["review", "security", "quality"]
```

## Field reference

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `name` | string | Yes | Unique skill identifier |
| `version` | string | No | Semver version |
| `description` | string | Yes | What this skill does |
| `category` | string | No | One of `implementation`, `testing`, `review`, `research`, `documentation`, `operations`, `planning` |
| `activation` | object | No | Which tools or models trigger this skill |
| `prompt` | object | No | System prompt, prefix, suffix, directives |
| `tool_policy` | object | No | Allow and deny glob patterns |
| `model` | object | No | `preferred` and `fallback` model IDs — each is a single string, not a list. **Discouraged:** a skill-pinned model SILENTLY OVERRIDES the activating agent's model — and, when the pinned model implies a different provider, its tool. Skills should be model-agnostic; put model choice on the agent profile / phase runtime instead. v0.6.33+ surfaces a `warn_skill_pins_model` warning ("skills should be model-agnostic — move the model to the agent profile") on `animus skill info` / `skill list` and the skill MCP tools |
| `mcp_servers` | list | No | MCP servers to activate |
| `timeout_secs` | int | No | Agent timeout override |
| `capabilities` | object | No | Boolean capability flags |
| `extra_args` | list | No | Extra CLI arguments |
| `env` | object | No | Environment variables |
| `codex_config_overrides` | list | No | Codex-specific overrides |
| `adapters` | object | No | Per-tool behavior overrides |
| `tags` | list | No | Searchable tags |

## Prompt structure

```yaml
prompt:
  system: |
    Full system prompt override.
  prefix: |
    Prepended before the phase directive.
  suffix: |
    Appended after the phase directive.
  directives:
    - Individual rules merged into the prompt.
```

Use `directives` for composable rules. Use `system` for a full override.

## Tool policies

```yaml
tool_policy:
  allow:
    - "subject.*"
    - "Read"
    - "output.*"
  deny:
    - "queue.drop"
    - "Bash"
    - "git.*"
```

`deny` takes precedence over `allow`.
Use `subject.*` for task and requirement operations; the old `task.*` and
`requirements.*` MCP families were removed from Animus.

## Capabilities

```yaml
capabilities:
  writes_files: true
  mutates_state: true
  requires_commit: true
  enforce_product_changes: true
  is_research: true
  is_ui_ux: true
  is_review: true
  is_testing: true
  is_requirements: true
```

Aliases are supported: `write_files`, `file_write`, and `can_write` all map to `writes_files`.
This is a representative subset, not exhaustive — the source accepts more, including
`file_writes` (→`writes_files`), `state_mutation` / `managed_state_mutation`
(→`mutates_state`), `require_commit` (→`requires_commit`), `product_changes`
(→`enforce_product_changes`), and the role flags `research`, `review`, `testing`,
`requirements`, and `ui_ux` / `ui-ux`.

Treat capabilities as **feature flags**, not permissions the skill requests and
the host grants: on workflow phases the flags merge deterministically into the
phase's capability set at load time — there is no negotiation or escalation
prompt. An unknown capability key fails validation (a config error, not a
denied request). Capabilities do not apply on ad-hoc runs (`agent run` /
`chat send`), which have no phase capability set to override.

## Adapters

```yaml
adapters:
  claude:
    model: claude-opus-4-8
    extra_args: ["--no-stream"]
    mcp_servers: ["animus", "sequential-thinking"]
    prompt_override:
      suffix: "Use extended thinking for complex reviews."

  codex:
    model: gpt-5.5
    tool_policy:
      allow: ["*"]
    extra_args: ["--full-auto"]
```

`adapters.<tool>.model` pins carry the same caveat as top-level `model:`:
they silently override the activating agent's model (and tool, when the model
implies a different provider), and trigger the same `warn_skill_pins_model`
warning (v0.6.33+). Prefer model-agnostic skills.

## Activation filters

```yaml
activation:
  tools: [claude, codex]
  models: []
```

Leave both empty for universal activation. Gating is evaluated where the skill
executes: on workflow phases the runner checks `activation` against the
actually selected tool/model.

`activation.tools` and `adapters.<tool>` keys match the runtime tool id with a
literal case-insensitive comparison. Workflow phases use canonical ids only
(`claude`, `codex`, `gemini`, `opencode`, `oai`, `oai-agent` — the legacy
`oai-runner` id canonicalizes to `oai-agent`), so a typo (`claud`),
whitespace padding, or an alias (`open-code`) silently never matches there.
Such inert declarations surface as a non-fatal `warnings` array on
`animus skill info`, `animus skill list`, and the `animus.skill.get` /
`animus.skill.create` / `animus.skill.update` MCP tools — they warn, never
error.

## Markdown skills and the `animus:` namespace

A directory skill (`SKILL.md`) parses `name`, `description`, and `version`
from frontmatter; the markdown body becomes `prompt.system`. To declare
structural fields without breaking portability to other agent hosts, nest
them under an `animus:` key:

```yaml
---
name: my-skill
description: Custom skill for X
animus:
  tool_policy:
    allow: ["subject.*"]
  mcp_servers: ["context7"]
  model:
    preferred: claude-sonnet-4-6
  timeout_secs: 300
---
```

Top-level placement of structural fields in frontmatter is intentionally not
parsed. The `animus:` namespace is honored only by high-trust sources
(project / user / installed); agent-host sources still get the structural
fields stripped.

## Skill sources and priority

Five trust tiers, lowest to highest. When two sources define the same skill name, the higher tier wins.

| Priority | Source | Location |
|:--------:|--------|----------|
| 1 (lowest) | Agent-host global | `~/.claude/skills/`, `~/.codex/skills/`, etc. (`SKILL.md`) |
| 2 | Agent-host project | `.claude/skills/`, `.codex/skills/`, etc. within the project |
| 3 | Installed | Pack `[skills]` manifests + `animus skill install` snapshots in `~/.animus/<repo-scope>/state/skills-registry.v1.json` |
| 4 | User | `~/.animus/config/skill_definitions/*.yaml` + `~/.animus/skills/` (`SKILL.md`) |
| 5 (highest) | Project | `.animus/config/skill_definitions/*.yaml` + `.animus/skills/` (`SKILL.md`) |

There is no builtin tier embedded in the binary — bundled skills were extracted to packs (e.g. `animus.core-skills`) and load through the Installed tier.

Agent-host skills (tiers 1–2) are **prompt-text-only**: the loader strips `tool_policy`, `extra_args`, `env`, `mcp_servers`, `adapters`, `codex_config_overrides`, `capabilities`, `model`, and `timeout_secs` at parse time, regardless of what the frontmatter declares. To use those structural fields, promote the skill with `animus skill install --path <dir>`, which converts it to the Installed tier with an integrity snapshot.

Within a single scope: files load in lexicographic path order, manifest (`skills:` map) entries apply first, standalone `<name>.yaml` files shadow manifest entries of the same name, and YAML definitions shadow markdown `SKILL.md` skills of the same name.

## Runtime application

Every structural field is enforced on both execution paths (v0.5.14+):

- **Workflow phases** — the daemon resolves the union of `phases.<id>.skills` and the executing agent profile's `skills:` at dispatch time and ships the definitions to the workflow runner via the `ANIMUS_PHASE_SKILLS_JSON` spawn-env payload (`animus.phase-skills.v1`; needs `animus-workflow-runner-default` >= v0.4.2 — `animus daemon preflight` warns on older runners). Skill-declared `mcp_servers` join the phase contract by name (resolved against workflow-YAML `mcp_servers:` or project config; unknown names warn and are skipped). Missing skill names warn loudly and record `missing` metadata — never a hard failure.
- **Ad-hoc runs** (`animus agent run --skill`, `animus chat send --skill`) — `prompt.prefix`/`directives`/`suffix` wrap the outgoing prompt and `prompt.system` rides the session system prompt; `extra_args` and `codex_config_overrides` graft onto the runtime contract's `cli.launch` block; `env` rides the session request env (still gated by the provider plugin's `env_required` manifest); `model` and `timeout_secs` apply when no explicit `--model` / `--timeout-secs` is given. `capabilities` are workflow-phase-only.

Precedence for every field: explicit CLI flags / context-json > skill > defaults. A caller-supplied `--runtime-contract-json` (or `runtime_contract` in `--context-json`) disables skill application entirely. On `animus chat send`, a skill with launch-affecting fields (`extra_args` / `codex_config_overrides` / `env`) forces full-history replay instead of native session resume so launch flags reach every turn's provider process.

Verify application after a workflow run with `animus output phase-outputs --workflow-id <id>`: the per-phase Skills block lists requested vs applied (source scope + contribution kinds: `prompt`, `tool_policy`, `mcp_servers`, `args`, `env`, `codex_config`, `model`, `timeout`, `capabilities`) vs missing skills. Typo'd explicit `skills:` declarations in workflow YAML additionally warn (never error) in `animus workflow config validate` / `compile`.
