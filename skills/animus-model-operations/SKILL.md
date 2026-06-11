---
name: animus-model-operations
description: Inspect Animus model availability, provider API-key status, task model validation, cached model rosters, and model evaluation runs and reports.
user_invocable: false
auto_invoke: true
---

# Model Operations

Use the `animus model` tree to check whether provider CLIs and credentials can
run a model before assigning it to a workflow phase.

Daemon dispatch also needs provider plugins:

```bash
animus plugin install-defaults
animus daemon preflight
```

## Availability

Check explicit model ids:

```bash
animus model availability --model claude-sonnet-4-6
animus model availability --model gpt-5.4 --model zai-coding-plan/glm-5
```

For scripts, pass provider input as a JSON array of `model[:tool]` strings:

```bash
animus model availability --input-json '["claude-sonnet-4-6","gpt-5.4:codex"]'
```

Use availability when choosing phase routing, validating an upgrade, or
checking whether a provider plugin recognizes a model id.

## Provider and API-Key Status

```bash
animus model status --cli-tool claude --model-id claude-sonnet-4-6
animus model status --cli-tool codex --model-id gpt-5.4
animus model status --cli-tool opencode --model-id zai-coding-plan/glm-5
```

This is the fastest operator check for "is this model configured for this CLI
tool and provider plugin?"

## Validate Model Selection

Validate models directly:

```bash
animus model validate --model claude-sonnet-4-6 --model gpt-5.4
```

With no `--model` flags, validation runs against the default model set.
`--task-id` is a pass-through label echoed in the output JSON for audit
purposes — it does not look up the task or its model requirements:

```bash
animus model validate --task-id TASK-001
```

Use validation before bulk queueing or before enabling a new workflow pack in a
repo.

## Roster Cache

```bash
animus model roster refresh
animus model roster get
```

Refresh the roster after installing or updating provider plugins, changing API
keys, or adding a provider-specific model.

## Model Evaluations

```bash
animus model eval run --model claude-sonnet-4-6 --model gpt-5.4
animus model eval report
```

Use eval runs to compare candidate models for phase routing. Keep workflow
changes separate from model eval changes so regressions are easy to attribute.

## Practical Routing Pattern

1. `animus plugin list` to confirm the provider plugin is installed.
2. `animus model status --cli-tool <tool> --model-id <model>` to verify credentials and provider setup.
3. `animus model availability --model <model>` to confirm recognition.
4. `animus model validate --model <model>` before dispatch.
5. Update workflow YAML only after the model checks pass.

## Troubleshooting

- Unknown model: refresh the roster and verify the provider plugin version.
- API-key failure: start the daemon or run the command from a shell with the provider's required env vars.
- Model works in the vendor CLI but fails in Animus: inspect the provider plugin with `animus plugin info` and update it with `animus plugin update --dry-run`.
- Daemon cannot dispatch any provider work: install default provider plugins and rerun `animus daemon preflight`.
