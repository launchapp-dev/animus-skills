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
        - "task.*"
      deny:
        - "Write"
        - "Edit"
        - "Bash"

    model:
      preferred: claude-sonnet-4-6
      fallback:
        - claude-opus-4-6

    mcp_servers:
      - animus      - sequential-thinking

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
| `model` | object | No | Preferred and fallback model IDs |
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
    - "task.*"
    - "Read"
    - "requirements.*"
  deny:
    - "task.delete"
    - "Bash"
    - "git.*"
```

`deny` takes precedence over `allow`.

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

## Adapters

```yaml
adapters:
  claude:
    model: claude-opus-4-6
    extra_args: ["--no-stream"]
    mcp_servers: ["animus", "sequential-thinking"]
    prompt_override:
      suffix: "Use extended thinking for complex reviews."

  codex:
    model: o3
    tool_policy:
      allow: ["*"]
    extra_args: ["--full-auto"]
```

## Activation filters

```yaml
activation:
  tools: [claude, codex]
  models: []
```

Leave both empty for universal activation.

## Skill sources and priority

| Priority | Source | Location |
|:--------:|--------|----------|
| 1 | Builtin | Embedded in Animus binary |
| 2 | Installed | `~/.ao/state/skills-registry.v1.json` |
| 3 | User | `~/.ao/config/skill_definitions/*.yaml` |
| 4 | Project | `.ao/skill_definitions/*.yaml` |
