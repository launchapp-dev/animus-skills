# Agents And Phases

Use this reference only when you need field-level details for `agents:` or `phases:`.

## Agents

Agent profiles define the model, CLI tool, prompt, and MCP access.

```yaml
models:
  primary:
    model: claude-opus-4-8
    tool: claude
  secondary:
    model: gpt-5.5
    tool: codex
  cheap:
    model: claude-haiku-4-5
    tool: claude

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

The top-level `models:` registry lets agents reference named model entries instead of repeating full model/tool pairs. The first named model becomes the primary model and the rest become fallbacks. A `models:` list is authoritative: it clears inherited fallbacks and overrides a profile `tool`. Names not found in the registry are treated as literal model ids. When `tool` is omitted on a registry entry, it is auto-derived from the model id prefix.

### Agent fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name used in prompts/UI |
| `description` | string | Agent description |
| `system_prompt` | string | Instructions for the agent |
| `system_prompt_file` | string | Load the system prompt from a UTF-8 file at compile time; mutually exclusive with `system_prompt`. Relative paths resolve from the YAML file's parent directory |
| `role` | string | Agent role identifier |
| `persona` | object | Personality/style config (`style`, `traits`, `instructions`, `customizations`) |
| `memory` | object | Project-scoped memory (`enabled`, `scope`, `max_context_chars`, `max_entries`, `write_policy`) |
| `communication` | object | Channel access (`enabled`, `channels`, `can_message`, `max_context_chars`); pairs with top-level `agent_channels:` |
| `models` | list | Named entries from the top-level `models:` registry |
| `model` | string | LLM model ID |
| `tool` | string | Provider tool (`claude`, `codex`, `gemini`, `opencode`, `oai`, `oai-agent`) |
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
| `retry_on` / `no_retry_on` | list | (v0.6.x, protocol v0.1.26) Failure-class tokens gating the agent-call retry loop. `no_retry_on` always wins; an empty `retry_on` means retry all transient classes |
| `reasoning_effort` | string | Provider reasoning effort: `low`/`medium`/`high`; validated at compile time |
| `permission_mode` | string | Provider permission/approval mode (claude: `default`/`acceptEdits`/`bypassPermissions`/`plan`; codex: `untrusted`/`on-failure`/`on-request`/`never`; gemini: `default`/`auto_edit`/`yolo`). Unknown values warn but pass through. The value is mapped by each provider plugin (transports differ since v0.6.9 — claude native, codex over MCP, gemini/opencode over ACP) |
| `tool_policy` | object | Allow and deny glob patterns |
| `approval_policy` | object | Routing for `animus.agent.request_approval` calls — see below |
| `hooks` | object | Harness-hook policy: `policy_rules[]` (`events`, `tools` globs, `input_matchers`, `decision: deny/ask/allow/defer` — deny always wins, rules only add restriction) and `observers[]` (`events`, `action: record`). Claude-only; kill-switch `ANIMUS_DISABLE_HARNESS_HOOKS` |
| `skills` | list | Skill identifiers to activate |
| `capabilities` | object | Boolean capability flags |
| `project_overrides` | object | Per-project overrides |
| `codex_config_overrides` | object | Codex-specific overrides |

The merge with base profiles is presence-aware per field: a field written in
YAML always wins (even when set to its default — `mcp_servers: []` or
`skills: []` explicitly disable what a pack enabled); an omitted field
inherits the base profile's value.

### Human-in-the-loop: `approval_policy`

Agents can call the blocking `animus.agent.ask` / `animus.agent.request_approval`
MCP tools mid-run. In workflow phases these use suspend/resume: the tool
returns immediately, the workflow pauses, and answering via
`animus agent interactions answer` resumes the provider session with the
decision as feedback. `approval_policy` routes approval requests per agent:

```yaml
agents:
  implementer:
    approval_policy:
      auto_allow: ["cargo *", "git.commit"]
      auto_deny: ["git.push*"]
      default: ask        # ask (escalate to a human) | allow | deny | llm
```

`auto_allow` / `auto_deny` are `*`-glob lists matched against the request's
`tool_name` (or its `action` when absent); `auto_deny` wins on overlap
(fail closed).

`default: llm` (v0.6.0+) routes anything the glob lists don't decide to an
LLM judge instead of a human:

```yaml
agents:
  triager:
    approval_policy:
      default: llm
      evaluator_model: claude-haiku-4-5   # defaults to the agent's own model
      evaluator_instructions: |
        Allow read-only and test commands. Deny anything that pushes,
        publishes, or deletes.
```

The judge runs one-shot with no MCP access; it also auto-answers
`animus.agent.ask` questions. Evaluator failure falls back to `ask` — it
never silently allows. Decisions are recorded with `source: "llm"` in the
interaction log.

### Model routing notes

- `tool_profile` is a Claude-only account routing hook resolved from global Animus config.
- `fallback_models` and `fallback_tools` can be set directly on the agent or in phase `runtime:`.
- If an agent uses `models:`, Animus compiles that list into a primary model plus fallbacks.

### Tool options

- `claude` (native)
- `codex` (driven over MCP since v0.6.9 — `animus-provider-codex-mcp`)
- `gemini` (driven over ACP since v0.6.9)
- `opencode` (driven over ACP since v0.6.9)
- `oai` (one-shot direct API)
- `oai-agent` (agentic multi-step; the legacy `oai-runner` id still parses
  but canonicalizes to `oai-agent` — write `oai-agent` in new YAML)

All providers are plugins, not kernel built-ins; `provider_tool` ids and
model→tool routing are unchanged by the transport differences.

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
        - gpt-5.5
      fallback_tools:
        - codex
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
| `runtime` | object | agent | Overrides: `tool`, `tool_profile`, `model`, `fallback_models`, `fallback_tools`, `reasoning_effort`, `permission_mode`, `web_search`, `network_access`, `timeout_secs`, `max_attempts`, `retry_on`, `no_retry_on`, `extra_args`, `codex_config_overrides`, `max_continuations` |
| `capabilities` | object | agent | Boolean capability flags |
| `output_contract` | object | agent | Expected output fields and types |
| `output_json_schema` | object | agent | JSON schema for phase output |
| `decision_contract` | object | agent | Required evidence / confidence / risk thresholds |
| `retry` | object | any | Max attempts and backoff |
| `default_tool` | string | agent | Preferred tool override |
| `idempotency` | string | any | Whether the phase is safe to re-run |
| `worktree` | object/string | any | Worktree mode (`auto`/`required`/`skip`), `cleanup`, `base_ref`; shorthand `worktree: skip` is accepted |
| `evals` | object | any | Quality gate: `checks` (`kind: command` or `kind: llm_judge`), `pass_threshold`, `on_fail` (`rework`/`block`), `max_reworks`. Parsed and validated, but NOT yet executed by the workflow runner — phases advance regardless, and declaring `evals:` emits a declared-but-unenforced warning in `workflow config validate`/`compile` |
| `command` | object | command | Program spec (required for command mode) |
| `manual` | object | manual | Human instructions (required for manual mode) |

`runtime.reasoning_effort` and `runtime.permission_mode` cascade
**phase runtime → agent profile** (a non-empty phase value wins), mirroring
`model` and `tool`. `permission_mode` is handed to the provider plugin, which
maps it onto its own transport (claude `--permission-mode` natively; codex and
gemini/opencode map it inside their MCP/ACP drivers since v0.6.9); the
`--permission-mode` flag on `animus agent run` / `animus chat send` overrides
both. The ad-hoc surfaces honour `permission_mode` today; workflow phase
execution enforces it once the out-of-tree workflow-runner plugin pin
consumes the field.

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

Phase skills actually reach workflow phase agents as of v0.5.14 (requires
workflow-runner >= v0.4.2 — `animus daemon preflight` warns, non-fatally,
when the installed runner is below that floor). How it works:

- The phase's effective skill set is the **union** of the phase-level
  `skills:` list and the executing agent profile's `skills:` (phase entries
  first, deduplicated). A workflow-YAML `agents.<id>.skills` declaration —
  even an explicit empty list — replaces the base profile's list; omit it to
  inherit.
- The daemon resolves skill names at workflow dispatch time against the same
  scoped sources and trust rules as the ad-hoc `--skill` path
  (project > user > installed > agent-host prompt-only), and ships the
  resolved definitions to the workflow runner via the
  `ANIMUS_PHASE_SKILLS_JSON` spawn environment.
- Activation gating (`activation.tools` / `activation.models`) is evaluated
  at phase execution against the tool/model the runner actually selects.
  Applied skills inject prompt fragments (system/prefix/suffix/directives),
  tool policy, MCP server attachments (resolved by name against
  `mcp_servers:`; unknown names warn and are skipped), launch args/env, and
  capability overrides.
- A skill name that does not resolve is a loud dispatch-log warning plus a
  `missing` record in the phase execution metadata — never a hard failure.
  Explicit `skills:` declarations are also checked at compile/validate time:
  unresolvable names WARN in `animus workflow config validate` / `compile`.
- Verify after the fact: `animus output phase-outputs --workflow-id <id>`
  shows per-phase requested/applied/missing skills;
  `animus workflow prompt render` previews the skill-injected prompt.

Put role-defining skills on the agent and phase-specific lenses on the phase.

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

**Always set `cwd_mode` explicitly.** A YAML-omitted `cwd_mode` resolves to
`project_root` in the YAML parser while the struct-level serde default is
`task_root` — relying on the default gets you different behavior depending on
which layer materialized the phase.

**Where commands run (v0.7):** when the workflow resolves to an execution
environment (see top-level-and-routing.md "Execution environments"), command
phases execute **inside the run's shared broker node** — the same ephemeral
environment as the agent phases, with state persisting across phases of the
run. Without an environment, they run locally per `cwd_mode` in the
worktree/project root as before.

Advanced command fields also include:

- `env`
- `success_exit_codes` (default `[0]`, must be non-empty)
- `parse_json_output`
- `expected_result_kind`
- `expected_schema`
- `failure_pattern` (regex over output)
- `on_success_verdict` / `on_failure_verdict` — free-form verdict strings;
  this is how a command phase mints **custom verdicts** that the workflow's
  per-phase `on_verdict` map routes (e.g. `on_failure_verdict: needs-rebase`
  routed to a `rebase-on-main` phase)
- `confidence`
- `failure_risk`

#### Structured phase decisions from scripts

With `parse_json_output: true`, the command's stdout is parsed for a single
JSON `phase_decision` object:

```json
{"kind": "phase_decision", "verdict": "advance", "reason": "...",
 "confidence": 0.9, "risk": "low", "target_phase": null, "outputs": {}}
```

`verdict` may be `advance` / `rework` / `skip` / `fail` or any custom string
routed by `on_verdict`. The runner injects context for the script:
`ANIMUS_SUBJECT_ID` (kind-qualified), `ANIMUS_SUBJECT_NATIVE_ID`,
`ANIMUS_SUBJECT_KIND`, `ANIMUS_SUBJECT_TITLE`, `ANIMUS_SUBJECT_STATUS`,
`ANIMUS_WORKFLOW_REF`, `ANIMUS_WORKFLOW_ID` (run id), `ANIMUS_PHASE_ID`,
`ANIMUS_PROJECT_ROOT`, `ANIMUS_EXECUTION_CWD`, `ANIMUS_DISPATCH_INPUT`, and
`ANIMUS_CONTEXT_FILE` — a JSON file with the full subject (including its
`data`/custom bag), workflow ref/run/phase ids, prior completed phases with
their verdicts and outputs, and the dispatch input.

On portal deployments, the `phase_context_schema` MCP tool returns this whole
contract as one JSON document, and the `script_*` MCP tools maintain a durable
script registry (scripts materialized under `/data/animus-state/scripts/`) so
command phases can reference team-editable scripts instead of inline args —
see the animus-workflow-patterns skill for the pattern.

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
