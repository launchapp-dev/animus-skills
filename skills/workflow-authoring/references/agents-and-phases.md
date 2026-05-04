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
