# Agents And Phases

Use this reference only when you need field-level details for `agents:` or `phases:`.

## Agents

Agent profiles define the model, CLI tool, prompt, and MCP access.

```yaml
models:
  primary:
    model: claude-sonnet-4-20250514
    tool: claude
  secondary:
    model: gpt-4o
    tool: oai-runner

agents:
  default:
    model: claude-sonnet-4-6
    tool: claude
    tool_profile: main

  implementer:
    system_prompt: |
      You implement code changes. Write clean, type-safe code.
    models:
      - primary
      - secondary
    mcp_servers: ["animus", "context7"]
```

The top-level `models:` registry lets agents reference named model entries instead of repeating full model/tool pairs. The first named model becomes the primary model and the rest become fallbacks.

### Agent fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Agent description |
| `system_prompt` | string | Instructions for the agent |
| `role` | string | Agent role identifier |
| `models` | list | Named entries from the top-level `models:` registry |
| `model` | string | LLM model ID |
| `tool` | string | CLI tool (`claude`, `codex`, `gemini`, `oai-runner`) |
| `tool_profile` | string | Named global Claude profile; only valid with Claude |
| `mcp_servers` | list | MCP server names this agent can access |
| `fallback_tools` | list | Explicit tools for fallback models |
| `web_search` | bool | Enable web search |
| `network_access` | bool | Enable network access |
| `extra_args` | list | Extra CLI arguments |
| `fallback_models` | list | Fallback models |
| `max_attempts` | int | Retry attempts |
| `max_continuations` | int | Max continuations per phase |
| `timeout_secs` | int | Agent timeout |
| `reasoning_effort` | string | Extended thinking level |
| `tool_policy` | object | Allow and deny glob patterns |
| `skills` | list | Skill identifiers to activate |
| `capabilities` | object | Boolean capability flags |
| `project_overrides` | object | Per-project overrides |
| `codex_config_overrides` | object | Codex-specific overrides |

### Model routing notes

- `tool_profile` is a Claude-only account routing hook resolved from global Animus config.
- `fallback_models` and `fallback_tools` can be set directly on the agent or in phase `runtime:`.
- If an agent uses `models:`, Animus compiles that list into a primary model plus fallbacks.

### Tool options

- `claude`
- `codex`
- `gemini`
- `oai-runner`
- `opencode`

## Phases

### Agent phase

```yaml
phases:
  implementation:
    mode: agent
    agent: implementer
    directive: "Implement the task requirements. Write code and commit."
    runtime:
      tool_profile: overflow
      fallback_models:
        - gpt-4o
        - o4-mini
      fallback_tools:
        - oai-runner
    capabilities:
      mutates_state: true
```

### Phase fields

| Field | Type | Mode | Description |
|-------|------|------|-------------|
| `mode` | string | required | `agent`, `command`, or `manual` |
| `agent` (alias `agent_id`) | string | agent | Agent profile to spawn |
| `directive` | string | agent | Task prompt for the phase |
| `system_prompt` | string | agent | Phase-level system context override |
| `skills` | list | agent | Skill names to activate for this phase only |
| `runtime` | object | agent | Overrides: `tool`, `tool_profile`, `model`, `fallback_models`, `fallback_tools`, `reasoning_effort`, `permission_mode`, `web_search`, `network_access`, `timeout_secs`, `max_attempts` |
| `capabilities` | object | agent | Boolean capability flags |
| `output_contract` | object | agent | Expected output fields and types |
| `output_json_schema` | object | agent | JSON schema for phase output |
| `decision_contract` | object | agent | Required evidence / confidence / risk thresholds |
| `retry` | object | any | Max attempts and backoff |
| `default_tool` | string | agent | Preferred tool override |
| `idempotency` | string | any | Whether the phase is safe to re-run |
| `worktree` | object/string | any | Worktree mode (`auto`/`required`/`skip`), `cleanup`, `base_ref`; shorthand `worktree: skip` is accepted |
| `evals` | object | any | Pass checks, `pass_threshold`, `on_fail`, `max_reworks` |
| `command` | object | command | Program spec (required for command mode) |
| `manual` | object | manual | Human instructions (required for manual mode) |

### Skills on agents vs phases

Skills attach at two points, both as plain lists of skill names:

```yaml
agents:
  reviewer:
    model: claude-sonnet-4-6
    tool: claude
    skills: [code-review]      # active in every phase this agent runs

phases:
  review:
    mode: agent
    agent: reviewer
    directive: Review the diff.
    skills: [security-lens]    # active in this phase only
```

Setting `skills:` on an agent in project YAML replaces the base profile's list (omit it to inherit). At spawn time each skill is resolved by source precedence, filtered by its `activation` rules for the selected tool/model (non-matching skills are skipped silently), then merged: prompt fragments, directives, env, and MCP servers accumulate across skills, while `tool_policy`, `model`, and `timeout_secs` are last-wins — list order matters for those three. Put role-defining skills on the agent, phase-specific lenses on the phase, and restrictive tool-policy skills last.

### Command phase

Use command phases for deterministic operations.

```yaml
  push-branch:
    mode: command
    directive: "Push the current branch to origin"
    command:
      program: git
      args: ["push", "-u", "origin", "HEAD"]
      cwd_mode: task_root
      timeout_secs: 60
      success_exit_codes: [0]
      parse_json_output: false
```

#### `cwd_mode`

- `task_root` for worktree-local git, build, and test commands.
- `project_root` for repo-level commands.
- `path` for a custom relative directory with `cwd_path`.

Advanced command fields also include:

- `env`
- `success_exit_codes`
- `parse_json_output`
- `expected_result_kind`
- `expected_schema`
- `failure_pattern`
- `on_success_verdict`
- `on_failure_verdict`
- `confidence`
- `failure_risk`

### Manual phase

```yaml
  review-gate:
    mode: manual
    directive: "Code review must pass before merge"
    manual:
      instructions: "Review the code changes and approve or reject"
      approval_note_required: false
      timeout_secs: 86400
```

Manual phases require a `manual:` block. Command phases require a `command:` block.
