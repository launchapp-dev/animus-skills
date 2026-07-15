---
name: animus-model-operations
description: Choose models and verify provider readiness in Animus — provider plugin health, API-key and CLI-tool diagnostics, model/tool routing in workflow YAML, and per-model cost attribution. Use when selecting a model for a phase or agent, or when diagnosing why a provider or model fails to dispatch.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.18"   # animus CLI surface this skill targets
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
    model: claude-opus-4-8
    fallback_models:
      - gpt-5.5
      - gemini-2.5-pro
```

Provider transports (v0.6.9+): all providers are plugins — `claude` and
`oai` drive natively, `codex` over MCP (`animus-provider-codex-mcp`),
`gemini` and `opencode` over ACP (`animus-provider-{gemini,opencode}` v0.3.0
on the shared ACP client). `tool` ids and model→tool routing are unchanged
by the transports; they matter only when diagnosing dispatch failures (see
Backing-CLI Config Errors below).

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
animus workflow run --subject-id task:TASK-001 --model claude-sonnet-4-6
```

Tool inference (`tool_for_model_id()`, now in the `animus-protocol` repo's
model-routing module): `claude-*` → `claude`, `gpt-*` → `codex`, `gemini-*`
→ `gemini`, `zai-*`/`glm-*`/`minimax-*`/`openrouter/*` → `oai-runner`
(which canonicalizes to `oai-agent` — the agentic OAI provider; write
`oai-agent` in new YAML), `deepseek-*`/`qwen-*` → `opencode`. Model ids are
normalized through `canonical_model_id()` (aliases like `opus` resolve to
the current canonical id), and fallback models map to tools automatically.
Cost-rate matching strips OpenRouter-style `<provider>/` prefixes
(`openai/gpt-5.5` matches the `gpt-5.5` rate).

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

## Backing-CLI Config Errors

A provider CLI can be installed and runnable yet still fail **at dispatch**
because its *own* config file is invalid — a failure mode that `plugin status`,
`daemon preflight`, and `doctor --check cli_tools|api_keys` all miss, because the
plugin is healthy and the binary launches; it's the vendor's config parse that
rejects the run. Symptom: a phase exits code 1 almost immediately with a parse
error naming the vendor config, e.g.:

```
phase code-review exited with code Some(1); diagnostics:
Error loading config.toml: unknown variant `priority`, expected `fast` or `flex` | in `service_tier`
```

Diagnose and fix:

1. Read the raw phase diagnostics — they name the failing file and field:
   `animus workflow get --id <RUN_ID>` (look at the failed phase's
   `error_message`). The vendor checks here come back clean, so trust the phase
   diagnostic over the health surfaces.
2. Validate the vendor config directly. The file lives outside Animus's
   control surface:
   - codex → `~/.codex/config.toml`. Valid `service_tier` is **`fast`** or
     **`flex`** only. `priority` is the model-catalog tier id (display name
     "Fast") that the **Codex desktop app may write** when you pick that tier —
     it is NOT a valid config value for the headless codex the provider
     plugin drives (since v0.6.9 over MCP — the vendor config is still read
     by the codex process the plugin manages). Remove the line to use the
     default, or set `fast`/`flex`.
   - claude → backing config under the claude CLI's home; gemini → its CLI config.
3. Re-run. Note the interactive vendor app can tolerate the bad value while
   headless invocations fail, and claude-backed phases are unaffected — so a
   pipeline can pass `builder` (claude) and die on the first codex phase.

Keywords: `unknown variant`, `Error loading config.toml`, `service_tier`,
present-but-unparseable, exit code 1, headless vendor CLI.

## Troubleshooting

- No provider can dispatch: `animus daemon preflight`, then `animus install`
  (manifest project) / `animus plugin install-defaults` (or
  `animus daemon start --auto-install`).
- Plugin stuck or flapping: `animus plugin status <NAME>` — check
  `disabled_by_supervisor` / `cooldown_until`; fix the underlying error, then
  restart the daemon.
- Phase exits code 1 immediately with a vendor config-parse error (e.g.
  `unknown variant ... in service_tier`): the provider CLI's own config is
  invalid — see **Backing-CLI Config Errors** above. Health/preflight checks
  will look clean.
- Model works in the vendor CLI but not in Animus: `animus plugin info
  <NAME>` and `animus plugin update`.
- Credential failures: `animus doctor --check api_keys`; prefer
  `animus secret set <KEY>` over daemon-process env vars.
