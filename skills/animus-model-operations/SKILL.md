---
name: animus-model-operations
description: Choose models and verify provider readiness in Animus — provider plugin health, API-key and CLI-tool diagnostics, model/tool routing in workflow YAML, and per-model cost attribution. Use when selecting a model for a phase or agent, or when diagnosing why a provider or model fails to dispatch.
user_invocable: false
auto_invoke: true
animus_version: "0.5.15"   # animus CLI surface this skill targets
---

# Model Selection and Provider Health

The `animus model` command group (availability, status, validate, roster,
eval) was **removed in v0.5.13** with no aliases. Its jobs were absorbed by
other surfaces:

- Provider health → `animus plugin status` (aggregate
  `provider_plugins_healthy` + per-provider install state)
- Orphaned-CLI-process detection → `animus doctor` (`--fix` prunes dead
  tracker entries)
- Model selection → workflow YAML and per-invocation `--model` / `--tool`
  flags
- Model comparison/spend → `animus cost ... --by model`

There is no roster cache or model-eval surface anymore.

## Provider Health

```bash
animus plugin status                 # all plugins: pid, state, last RPC, restart count
animus plugin status <NAME> --json   # one plugin
animus daemon health                 # leads with healthy: true|false; one row per plugin
animus daemon preflight              # required-role report incl. at_least_one_provider
animus plugin ping --name <NAME>     # spawn + handshake + ping one plugin
```

`animus plugin status` carries a `providers` array (one entry per discovered
provider binary; `installed` is true only when the binary is executable) plus
a rolled-up `provider_plugins_healthy` boolean. Per-plugin rows include
supervisor state: `disabled_by_supervisor` and `cooldown_until` (default
budget: 3 restarts in 60s, then a 5-minute cooldown).

A missing provider plugin is a hard error at dispatch time — there is no
in-tree fallback. The error names the exact install command; or run:

```bash
animus plugin install-defaults
```

## Environment Diagnostics

```bash
animus doctor --check cli_tools   # provider CLI binaries present and runnable
animus doctor --check api_keys    # provider credential checks
animus doctor --fix               # safe remediations; prunes dead CLI-tracker entries
```

Store provider API keys in the OS keychain rather than shell env:

```bash
animus secret set ANTHROPIC_API_KEY
```

## Model Selection and Routing

The editable source of truth is workflow YAML, with this cascade (first match
wins): workflow/pack phase runtime override in `.animus/workflows.yaml` or
`.animus/workflows/*.yaml` → resolved agent-runtime config
(`animus workflow agent-runtime get`) → built-in planner fallback.

```yaml
agents:
  swe:
    tool: claude
    model: claude-sonnet-4-6
    fallback_models:
      - gpt-5.5
      - gemini-2.5-pro
```

The `daemon:` block supports per-phase overrides applied at spawn time:

```yaml
daemon:
  phase_routing:
    implementation:
      tool: claude
      model: claude-sonnet-4-6
```

Inspect or replace the resolved runtime layer:

```bash
animus workflow agent-runtime get
animus workflow agent-runtime validate
animus workflow agent-runtime set --input-json '{"agents":{"default":{"model":"claude-sonnet-4-6","tool":"claude"}}}'
```

Per-invocation overrides:

```bash
animus agent run --tool claude --model claude-sonnet-4-6 --prompt "..."
animus chat send --tool codex --model gpt-5.5 "..."
animus workflow run --task-id TASK-001 --model claude-sonnet-4-6
```

Tool inference (`tool_for_model_id()` in
`crates/protocol/src/model_routing.rs`): `claude-*` → `claude`, `gpt-*` →
`codex`, `gemini-*` → `gemini`, `zai-*`/`glm-*`/`minimax-*`/`openrouter/*` →
`oai-runner`, `deepseek-*`/`qwen-*` → `opencode`. Model ids are normalized
through `canonical_model_id()` (aliases like `opus` resolve to the current
canonical id), and fallback models map to tools automatically.

Routing reference: `docs/guides/model-routing.md` in the animus-cli repo.

## Model Spend Attribution

```bash
animus cost summary --by model            # in-window spend grouped by model
animus cost summary --by provider
animus cost workflow <RUN_ID> --by model  # one run regrouped (live runs only)
animus cost top --by model                # cross-run model leaderboard
animus cost top --by provider
```

Grouped views fold unattributed phases into an `unknown` bucket and warn when
it exceeds 20% of grouped cost. Archived history rows lack per-phase detail:
`cost workflow --by` is rejected for archived runs.

## Practical Routing Pattern

1. `animus plugin status` — provider plugin installed and healthy?
2. `animus doctor --check cli_tools` / `--check api_keys` — environment OK?
3. Set `tool`/`model` in workflow YAML (agent profile or phase runtime).
4. `animus workflow agent-runtime validate` then dispatch.
5. After runs, compare candidates with `animus cost top --by model`.

## Troubleshooting

- No provider can dispatch: `animus daemon preflight`, then
  `animus plugin install-defaults` (or `animus daemon start --auto-install`).
- Plugin stuck or flapping: `animus plugin status <NAME>` — check
  `disabled_by_supervisor` / `cooldown_until`; fix the underlying error, then
  restart the daemon.
- Model works in the vendor CLI but not in Animus: `animus plugin info
  --name <NAME>` and `animus plugin update`.
- Credential failures: `animus doctor --check api_keys`; prefer
  `animus secret set <KEY>` over daemon-process env vars.
