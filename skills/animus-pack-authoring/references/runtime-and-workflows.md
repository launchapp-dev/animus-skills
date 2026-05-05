# Runtime And Workflows

Use this reference when authoring workflow exports, runtime overlays, MCP descriptors, or decision contracts inside a pack.

## Workflow definitions

```yaml
phase_catalog:
  my-analysis:
    label: Analysis
    description: Analyze the codebase for issues.
    category: review
    tags: ["analysis", "review"]

workflows:
  - id: my-org.my-pack/standard
    name: My Standard Workflow
    description: Full analysis and fix pipeline.
    phases:
      - my-analysis
      - implementation
      - workflow_ref: ao.review/cycle

  - id: my-org.my-pack/quick-fix
    name: Quick Fix
    description: Implement and test only.
    phases:
      - implementation
      - testing
```

## Rework loops

Only use rework on agent phases.

```yaml
phases:
  - implementation
  - code-review:
      on_verdict:
        rework:
          target: implementation
      max_rework_attempts: 3
```

## Agent runtime overlay

```yaml
tools_allowlist:
  - animus  - gh
  - pnpm

agents:
  my-analyzer:
    description: Analyzes the codebase for issues.
    system_prompt: |
      You are a code analyzer. Inspect the codebase and report issues.
    role: reviewer
    mcp_servers: ["animus"]
    tool_policy:
      allow:
        - task.*
        - output.*
      deny:
        - task.delete
        - project.remove
    skills:
      - code-review
    capabilities:
      is_review: true
      implementation: false
    tool: claude
    model: claude-sonnet-4-6

phases:
  my-analysis:
    mode: agent
    agent_id: my-analyzer
    directive: Analyze the codebase and report findings via Animus MCP.
    capabilities:
      mutates_state: true
    runtime:
      tool: claude
      model: claude-sonnet-4-6
    decision_contract:
      required_evidence: []
      min_confidence: 0.7
      max_risk: medium
      allow_missing_decision: false
```

## Agent profile fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | What this agent does |
| `system_prompt` | string | Instructions for the agent |
| `role` | string | Semantic role |
| `mcp_servers` | list | MCP servers this agent can access |
| `tool_policy` | object | Allow and deny glob patterns |
| `skills` | list | Skill identifiers to activate |
| `capabilities` | object | Boolean capability flags |
| `tool` | string | CLI tool |
| `model` | string | LLM model ID |
| `fallback_models` | list | Fallback models |
| `timeout_secs` | int | Agent timeout |
| `max_attempts` | int | Retry attempts |
| `max_continuations` | int | Max continuations per phase |
| `extra_args` | list | Extra CLI arguments |

## Phase definition fields

| Field | Type | Description |
|-------|------|-------------|
| `mode` | string | `agent`, `command`, or `manual` |
| `agent_id` | string | Agent profile to use |
| `directive` | string | Instructions for the phase |
| `capabilities` | object | `mutates_state`, `writes_files`, `requires_commit`, and similar flags |
| `runtime` | object | Override tool, model, timeout, and related settings |
| `decision_contract` | object | Required evidence, confidence, and risk thresholds |
| `output_contract` | object | Expected output structure |
| `skills` | list | Additional skills to activate |
| `command` | object | Command definition for `mode: command` |
| `manual` | object | Manual approval config for `mode: manual` |

## Decision contract

```yaml
decision_contract:
  required_evidence:
    - code_review_clean
  min_confidence: 0.7
  max_risk: medium
  allow_missing_decision: false
```

Evidence kinds include `tests-passed`, `tests-failed`, `code-review-clean`, `code-review-issues`, `files-modified`, `requirements-met`, `research-complete`, `manual-verification`, and `custom`.

## MCP server descriptors

```toml
[[server]]
id = "jira"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-jira"]
required_env = ["JIRA_BASE_URL", "JIRA_API_TOKEN"]
tool_namespace = "jira"
startup = "phase-local"
```

Pack manifests reference these files through:

```toml
[mcp]
servers = "mcp/servers.toml"
tools = "mcp/tools.toml"
```

Use the `mcp` block in `pack.toml`; do not rely on implicit `mcp/servers.toml` discovery.
