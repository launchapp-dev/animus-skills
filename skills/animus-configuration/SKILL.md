---
name: animus-configuration
description: Animus project config, daemon config, plugin config, agent runtime, environment variables, and state layout
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
---

# Configuration

Animus resolves behavior from the project manifest `animus.toml`,
project-local `.animus/`, installed packs, repo-scoped runtime state under
`~/.animus/<repo-scope>/`, global machine config, environment variables, and
installed STDIO plugins.

## Project-local sources

### `animus.toml` (v0.6.9+) — the project manifest

Committed at the repo root; scaffolded by `animus init`. Declares intent:
`[project]` (kernel version), `[plugins]`, and `[packs]`, with each
dependency as a version string, `{ git, tag }`, or `{ path }`.
`animus install` resolves it into `.animus/plugins.lock` and installs the
set; `animus install --locked` (CI/Docker) reproduces the committed lock
exactly and fails on manifest↔lock drift; `animus add <spec>` /
`animus remove <name>` mutate the manifest and install/uninstall. Team
onboarding is `git clone && animus install`.

`animus init` also scaffolds `.env.example` and a merge-safe project
`.gitignore`. `animus install` syncs `.env` into the device-encrypted secret
store (idempotent; blank `KEY=` values are skipped, never stored empty;
imports audited) and warns about keys declared in `.env.example` but unset.

### `.animus/config.json`

Repository-local config created by `animus init`. It holds **only** the
optional `auto_update` block (self-update mode/interval/channel) and optional
CLI settings such as `default_subject_kind` and a project `mcp_servers` map.
It carries **no daemon runtime settings** — those live in the repo-scoped
`~/.animus/<repo-scope>/daemon/pm-config.json`, written by
`animus daemon config`.

### `.animus/workflows.yaml` and `.animus/workflows/*.yaml`

Hand-authored workflow sources. Typical uses:

- Define repo-specific workflow ids and the default workflow.
- Declare project MCP servers, agents, variables, phases, and workflows.
- Configure agent memory and communication channels.
- Declare top-level `schedules:` (cron dispatch, UTC) and `triggers:`
  (event dispatch from watchers, webhooks, or trigger plugins).
- Set `worktree:` mode (`auto` default / `required` / `skip`) per
  workflow or phase.
- Map logical secret names in `secrets:`, referenced as `${secret.<name>}`
  and resolved at consume/spawn time since v0.6 (env first, then the
  `animus secret` keychain store) — the reference passes through config
  parsing verbatim; resolved values never land in compiled artifacts.
- Declare execution-environment surfaces (v0.7-rc/portal only — not on
  0.6.x local installs): `workspaces:`, `environment_routing:`, and
  workflow/phase `environment:` / `workspace:` fields.

Use:

```bash
animus workflow config get
animus workflow config validate
animus workflow config compile
```

`validate` / `compile` also report declared-but-unenforced fields and
unresolvable explicit `skills:` names in a `warnings` array.

**Config sourcing is a plugin since v0.6.0:** the kernel no longer parses
`.animus/*.yaml` in the runtime load path — the base WorkflowConfig comes
exclusively from an installed `config_source` plugin. The default
`launchapp-dev/animus-config-yaml` serves exactly these YAML files (so YAML
remains the default authoring surface); the portal uses the consolidated
`animus-postgres` plugin instead. The daemon requires the role at preflight
and keeps ONE resident config_source host per project root (re-spawned only
on process death or binary mtime change, with a CacheToken short-circuit
when the source config is unchanged), so file edits are picked up without
per-load process churn. A malformed edit keeps the prior config active and
broadcasts `config_reload_failed` instead of crashing. Manual trigger:
`animus workflow config reload`. Daemon transport settings and
`.animus/plugins.lock` changes still require a daemon restart.

Sources that advertise `config_write` also accept CLI write-back:
`animus workflow config set / agent-set / agent-remove / workflow-set /
workflow-remove` edit the base config without touching YAML by hand
(`phase-set` is v0.7-rc only — not on 0.6.x local installs).

### `.animus/skills/<name>/SKILL.md`

Project-scoped Markdown skills (highest priority in skill resolution).
YAML skill definitions live at `.animus/config/skill_definitions/<name>.yaml`.
Agent-host skills from `.claude/skills` and `.codex/skills` are lower-trust
prompt-text-only probes.

### `.animus/plugins/`, `.animus/plugins.lock`, `.animus/plugins.yaml`

Project-scoped plugin triple, populated by `animus install` (from
`animus.toml`) or `animus plugin install --project` (same flag on
`uninstall` / `update`): binaries in `.animus/plugins/`, the **lockfile**
`.animus/plugins.lock`, and a registry `.animus/plugins.yaml`.

**The lock is the source of truth (v0.6.9+):** `plugins.yaml` is a derived
projection regenerated from the lock on every mutating op — never hand-edit
it, and don't treat it as authoritative; drift heals on the next operation.
Lock schema 2.0 (v0.6.7) records per-target-triple integrity
(`targets: {triple → {archive_sha256, signature_bundle_sha256,
installed_binary_sha256}}`) for every published platform, so a lock generated
on macOS drives a verified `--locked` install in a linux container.

Project installs run the identical integrity pipeline as global installs
(sha256, cosign policy, publisher TOFU, fail-closed lockfile) and **shadow**
same-named global installs during discovery (`animus plugin list` shows a
`SCOPE` column and a `shadowed` array). Commit `animus.toml` and
`.animus/plugins.lock` (`animus plugin lock verify` sweeps both global and
project roots); never commit binaries — `animus init` and project installs
write a `.animus/.gitignore` covering `plugins/`.
`.animus/plugins/<pack-id>/` doubles as the project-local pack override root.

### `.animus/plugin-scope.yaml`

Limits which installed plugins this project loads. `mode:` is `all`
(default), `flavor-only` (plugins declared by the active flavor), or
`allowlist` (names under `allow:`); `extras:` layers additions. Manage with
`animus plugin scope {show,set,reset}`. The file also persists the project's
**active flavor** under `active_flavor:`, written by a successful
`animus plugin install-defaults --flavor <name>` / `animus flavor install
<name>` (selecting `default` clears the key). `animus flavor current` reads
it back and reports the `source` (`flag` / `persisted` / `default`).

## Repo-scoped runtime state

Mutable project runtime state lives outside the repo:

```text
~/.animus/<repo-scope>/
├── core-state.json
├── cost-state.v1.json
├── decisions.jsonl
├── budget-enforcement.v1.json
├── resume-config.json
├── workflow.db
├── .journal-imported-v1          # marker: one-time SQLite→journal-plugin import done
├── cache/
│   ├── workflow-config.compiled.v1.json   # hash-keyed compile cache
│   └── ci-status.json                     # `animus status` CI-status cache
├── config/
│   ├── state-machines.v1.json
│   └── agent-runtime-config.v2.json
├── daemon/
│   ├── daemon.log
│   └── pm-config.json
├── interactions/
├── logs/
│   └── events.jsonl
├── mcp-oauth-cache/
│   └── <server>.json
├── runs/<run-id>/
├── artifacts/<run-id>/
├── state/
│   └── pack-selection.v1.json
├── workflow-environments/        # v0.7-rc/portal only: environment-broker lease records (<run_id>.json)
└── worktrees/
```

Key files:

- `workflow.db` stores persisted workflows, tasks, requirements, and checkpoints.
- `daemon/pm-config.json` stores persisted daemon runtime settings
  (including the `notification_config` block); `daemon/daemon.log` is the
  detached daemon's process log.
- `cost-state.v1.json` stores per-workflow/per-phase token + USD rollups;
  budget-breach decisions append to `decisions.jsonl`;
  `budget-enforcement.v1.json` records the enforcement sweep's
  `{enabled, last_sweep_at}` status surfaced by `animus daemon health`.
- `config/agent-runtime-config.v2.json` is the compiled agent runtime config
  (which AI model/tool each agent profile uses); inspect/validate/replace it
  via `animus workflow agent-runtime get|validate|set` rather than editing
  the file. The compiled *workflow* config (`animus.workflow-config.v2`) is
  **in-memory only** — an on-disk `config/workflow-config.v2.json` is a hard
  load error, not a cache.
- `workflow-environments/<run_id>.json` (v0.7-rc/portal only) are durable
  environment-broker leases for runs pinned to an execution environment;
  stale leases are cold-torn-down by the daemon's startup reaper.
- `interactions/` stores pending agent questions/approvals
  (`animus agent interactions`).
- `mcp-oauth-cache/<server>.json` caches resolved OAuth tokens for
  HTTP MCP servers (`0600` on Unix).
- `runs/<run-id>/` and `artifacts/<run-id>/` are never auto-deleted —
  reclaim disk with `animus workflow prune` / `animus workflow delete`.

Treat these as Animus-managed state. Prefer CLI or MCP tools over direct edits.

## Daemon config

Read current settings:

```bash
animus daemon config
```

MCP: `animus.daemon.config`

Update runtime settings (written to `daemon/pm-config.json`):

```bash
animus daemon config --pool-size 3
animus daemon config --max-tasks-per-tick 2 --stale-threshold-hours 12
animus daemon config --phase-timeout-secs 3600
animus daemon config --max-daily-usd 50 --silent-threshold-mins 20
```

Fleet knobs: `--max-daily-usd` is a rolling-24h fleet cost cap (pass `0` to
clear); `--silent-threshold-mins` (default 20) bounds how long a run may go
without output before it is flagged. There is no `--auto-run-ready` knob.

MCP: `animus.daemon.config-set`

The running daemon re-reads these keys once per scheduler tick, so changes
apply **without a restart** (exception: a changed `phase_timeout_secs` only
reaches the live process manager after a restart).

Removed knobs: the daemon git/merge policy (`auto_merge`, `auto_pr`,
`auto_commit_before_merge`, `auto_prune_worktrees`) and the no-op
`idle_timeout_secs` were deleted in v0.5.13 — old `pm-config.json` files
still load. Git automation (commit / push / PR / merge) is now expressed as
`command:` phases running `git` / `gh` in the workflow; the
`post_success.merge` and `integrations.git.auto_merge` keys were removed and
now fail to parse.

### Daemon lifecycle

```bash
animus daemon preflight                # standalone plugin preflight report
animus daemon start                    # always detaches (v0.5.14); prints pid + log path
animus daemon start --auto-install     # install missing required plugins first
animus daemon run                      # foreground dev/debug; --once = single tick
animus daemon restart                  # graceful stop, then detached start
```

`--autonomous` was removed — `daemon start` now errors on it as an unknown
argument; detached is the only `daemon start` behavior. Starting while
already running is idempotent.

### Scheduler wake model

The daemon main loop is event-driven, not polling. A dispatch pass runs on:
`daemon/nudge` control messages (sent fire-and-forget by
`animus subject create/update/status` and `animus queue enqueue/release`
and their MCP equivalents — pickup is typically sub-second), precise cron
deadlines from compiled `schedules:` (with a 10-minute catch-up horizon),
and workflow/phase completions. `interval_secs` (default 5) is only the
**fallback heartbeat**: it bounds pickup of out-of-band state edits and
paces the heavier housekeeping sweeps. Concurrency knobs: `pool_size` caps
steady-state concurrent runners (upper-bounded by
`ANIMUS_WORKFLOW_CONCURRENCY_MAX`, default 10); `max_tasks_per_tick`
(default 2) caps new dispatches per pass. See
`docs/reference/configuration.md#scheduler-wake-model`.

### Notifications

Notification dispatch is configured via the `notification_config` block
persisted in `daemon/pm-config.json`. Webhook URLs and headers reference
env var names through `url_env` / `headers_env` fields — commonly
`ANIMUS_NOTIFY_WEBHOOK_URL` and `ANIMUS_NOTIFY_BEARER_TOKEN` — and only
those named vars are forwarded to the notifier plugin. Notifier events
include `workflow-failed`, `task-blocked`, and `workflow-budget-breach`.

## Machine-wide config

```text
~/.animus/
├── config.json                  # global user config, telemetry consent, claude profiles
├── auto-update-state.json
├── credentials.json
├── principals.yaml
├── trusted-orgs.yaml            # plugin-install TOFU allowlist (audited; revoke-trust)
├── trusted-signers.yaml
├── plugins.lock / plugins.yaml  # global lockfile (source of truth) + derived registry
├── plugins/<plugin-name>
├── packs/<pack-id>/<version>/
├── skills/<skill-name>/SKILL.md
├── cache/manifests/             # plugin manifest cache (animus plugin cache)
└── template-registries/
```

### Principals and RBAC

`~/.animus/principals.yaml` (hand-editable) declares principals, roles,
and `policy.rbac`: `single-user` (default; checks skipped) or `enforce`
(requests must resolve to a declared principal). Inspect identity with
`animus auth whoami`; `--as <principal>` is honor-system under
`single-user` and credential-checked under `enforce`.

### Packs

```bash
animus pack list
animus pack info --pack-id animus.task
animus pack install --path /tmp/vendor.pack --activate
animus pack pin --pack-id vendor.pack --version =1.2.3
```

`pack install` also resolves declared pack dependencies (`--no-deps` skips,
`--dry-run` previews) and checks `[[requires_plugins]]` against the
installed-plugin registry (`--install-plugins` installs missing ones).
The `pack inspect` alias was retired in v0.5.14 — use `pack info`.

### Plugins and flavors

```bash
animus install                            # install the animus.toml-declared set (canonical for manifest projects)
animus install --locked                   # CI/Docker: reproduce plugins.lock exactly
animus add launchapp-dev/animus-subject-linear@v0.2.0   # add to manifest + install
animus remove animus-subject-linear      # drop from manifest + uninstall
animus plugin install-defaults            # no-manifest fallback: flavor's required set, every preflight role
animus plugin install-defaults --include-recommended
animus plugin list
animus plugin outdated                    # installed vs recommended pin vs latest
animus plugin lock verify
animus flavor current                     # active flavor + drift
```

`animus web serve` and `animus web open` require installed transport/UI
plugins (`animus plugin install-defaults --include-transports`).

### Self-update / avm

`animus update` self-updates plain installs (`~/.local/bin`,
`/usr/local/bin`, Cargo) with `--check`, `--yes`, `--channel stable|nightly`,
`--force`, `--prerelease`. When the running binary is managed by **avm** (the
Animus Version Manager — kernels under `~/.avm/versions/`, dispatched through
an `animus` shim), `animus update` defers: it prints the `avm install` /
`avm use` commands and exits instead of self-replacing (v0.6.11). Multi-project
machines should prefer avm. The former `animus self update` group was retired
— no aliases. Background checks are governed by the `auto_update` block in
`.animus/config.json` or `~/.animus/config.json`
(`mode`: `off|notify|prompt|auto`).

### Telemetry

Opt-in anonymous metrics live under `animus daemon metrics
{status,enable,disable,flush,cleanup}` (the top-level `animus metrics` group
was removed in v0.5.14). Bare `animus daemon metrics` is the live
counters/gauges display and degrades gracefully when the daemon is offline
(exits 0 with telemetry status; only `--watch` requires a live daemon).
Consent persists in the user-global `~/.animus/config.json`;
`ANIMUS_METRICS_DISABLE=1` is the hard kill switch.

## Environment variables

Core variables:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_CONFIG_DIR` | Override global config root, default `~/.animus` |
| `ANIMUS_DISABLE_CI_CACHE` / `ANIMUS_CI_CACHE_TTL_SECS` | Disable / tune the `animus status` CI-status cache |
| `ANIMUS_MCP_SCHEMA_DRAFT` | Select Draft-07 MCP schemas |
| `ANIMUS_MCP_ENDPOINT` | Override embedded MCP client endpoint |
| `ANIMUS_USER_ID` / `ANIMUS_ASSIGNEE_USER_ID` | Override recorded user / assignee ids |
| `ANIMUS_DEBUG` | Enable verbose debug logging |
| `ANIMUS_LOG_JSON` | Emit JSON logs |
| `ANIMUS_DEBUG_MCP_STDIO` | Log raw MCP stdio frames |
| `ANIMUS_AUTO_UPDATE_MODE` / `ANIMUS_AUTO_UPDATE_DISABLE` | Override / short-circuit self-update behavior |
| `ANIMUS_METRICS_DISABLE` | Hard kill switch for opt-in telemetry |

Plugin and template variables:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_PLUGIN_DIR` | Override global plugin install directory |
| `ANIMUS_PLUGIN_PATH` | Extra directories scanned for plugin binaries |
| `ANIMUS_PLUGIN_SIGNATURE_POLICY` | Signature policy override: `strict` / `warn` / `skip` (precedence: per-call flag > this env > global config `plugins.signature_policy` > `warn`). v0.7-rc/portal only — on 0.6.x local installs there is no env or global-config layer: precedence is `--signature-policy` flag > legacy `--skip-signature`/`--require-signature` > `warn` default |
| `ANIMUS_SERVER=1` | Server mode: fail-closed org TOFU — `--yes`/`--force` never auto-trust an unknown org (use `--allow-org`). v0.7-rc/portal only — on 0.6.x local installs `--yes`/`--force` DO auto-trust unconditionally |
| `ANIMUS_DISABLE_MANIFEST_CACHE` / `ANIMUS_CACHE_DIR` | Bypass / relocate the plugin manifest cache |
| `ANIMUS_RESIDENT_HOST_CACHE_MAX` | Cap the resident plugin-host registry (v0.7-rc/portal only; legacy `ANIMUS_SUBJECT_HOST_CACHE_MAX` still read — on 0.6.x local installs `ANIMUS_SUBJECT_HOST_CACHE_MAX` is the only var) |
| `ANIMUS_FLAVORS_DIR` | Override the `flavors/<name>.toml` probe directory |
| `ANIMUS_TEMPLATE_REGISTRY_URL` | Override project-template registry |

Environment / journal variables (the `ANIMUS_ENVIRONMENT_*` and OAuth-cache
rows are v0.7-rc/portal only — absent on 0.6.x local installs):

| Variable | Purpose |
|----------|---------|
| `ANIMUS_ENVIRONMENT_DELEGATE` | Gate: delegate worktree materialization to the resolved environment plugin (default off; v0.7-rc/portal only) |
| `ANIMUS_ENVIRONMENT_EXEC` | Gate: route agent exec through resolved environment plugins (default off; no silent local fallback once resolved; v0.7-rc/portal only) |
| `ANIMUS_ENVIRONMENT_BROKER_*` | Daemon-set on runners: private broker socket/bearer for exec proxying — not user-set (v0.7-rc/portal only) |
| `ANIMUS_DAEMON_DISABLE_JOURNAL_RESUME` | Kill-switch: skip the boot reconcile that RESUMES in-flight runs from a durable workflow_journal after restart (v0.6.27+, mainline) |
| `ANIMUS_MCP_OAUTH_CACHE_DIR` | Relocate the MCP OAuth token cache (containerized/durable-volume deployments). v0.7-rc/portal only — on 0.6.x local installs the path is hardwired to `~/.animus/<repo-scope>/mcp-oauth-cache/` |

Workflow-runner variables:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_WORKFLOW_RUNNER_BIN` | Override the workflow-runner binary path |
| `ANIMUS_PHASE_RUN_ATTEMPTS` / `ANIMUS_PHASE_MAX_CONTINUATIONS` | Phase retry / continuation caps |
| `ANIMUS_MCP_WORKFLOW_ID` | Pin `animus mcp serve` to a workflow (suspend-mode interactions) |

Daemon runtime quotas (read once at daemon startup; `0`/empty falls back to default):

| Variable | Default | Purpose |
|----------|---------|---------|
| `ANIMUS_TRIGGER_BACKLOG_MAX` | 1000 | Max unprocessed trigger events retained per trigger |
| `ANIMUS_SUBSCRIBER_MEMORY_MAX_MB` | 10 | Per-subscriber buffer cap for `workflow/events` |
| `ANIMUS_PLUGIN_PROCESS_MAX` | 50 | Max concurrent plugin child processes |
| `ANIMUS_WORKFLOW_CONCURRENCY_MAX` | 10 | Max parallel workflow runners; also upper-bounds `pool_size` |

Provider passthrough examples:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_CLAUDE_EXTRA_ARGS` / `_JSON` | Extra Claude CLI args |
| `ANIMUS_CLAUDE_BYPASS_PERMISSIONS` | Skip Claude permission prompts (unattended test envs only) |
| `ANIMUS_CODEX_EXTRA_ARGS` / `_JSON` | Extra Codex CLI args |
| `ANIMUS_CODEX_EXTRA_CONFIG_OVERRIDES` / `_JSON` | Extra Codex `--config` overrides |
| `ANIMUS_CODEX_NETWORK_ACCESS` / `ANIMUS_CODEX_WEB_SEARCH` | Toggle Codex sandbox network / web search |
| `ANIMUS_GEMINI_EXTRA_ARGS` / `ANIMUS_OPENCODE_EXTRA_ARGS` (+ `_JSON`) | Extra Gemini / OpenCode CLI args |

Removed in v0.5.13: `ANIMUS_RUNNER_CONFIG_DIR`, `ANIMUS_RUNNER_SCOPE`, and
the `--runner-scope` flag (dead since the agent-runner sidecar deletion).

### Plugin kill-switches

Operator escape hatches; all require a daemon restart to take effect (and
another to re-enable):

| Variable | Effect |
|----------|--------|
| `ANIMUS_DAEMON_DISABLE_TRIGGERS=1` | Skip the trigger plugin supervisor (also interrupts in-progress restart backoff) |
| `ANIMUS_DAEMON_DISABLE_SUBJECT_PLUGINS=1` | Skip subject plugin discovery entirely |
| `ANIMUS_DAEMON_DISABLE_LOG_STORAGE_PLUGIN=1` | Ignore log_storage plugins; use in-tree `logs/events.jsonl` |
| `ANIMUS_DAEMON_DISABLE_BUDGET_ENFORCEMENT=1` | Skip the budget-cap enforcement sweep (no auto-pause/fail; sweeps still record disabled status for `daemon health` / `status`) |

`ANIMUS_PROVIDER_DISABLE_PLUGIN` was removed in v0.4.12 — uninstall or
quarantine a misbehaving provider plugin instead.

## Secret handling

Do not put API tokens in workflow YAML. Preferred: store secrets in the OS
keychain with `animus secret set <KEY>` (also `get`, `list`, `rm`,
`import-env`, `export-env`). Plugins and the `${VAR}` interpolator resolve
explicit parent-process env first, then the keychain entry for the current
repo-scope. The daemon does not auto-load `.env` files — source them before
startup, or migrate with `animus secret import-env`.

Two storage backends sit behind the same `animus secret` surface, selected
per machine via the global config's `secrets.backend`
(`auto` default | `keyring` | `device` | `env`): `keyring` is the OS
keychain; `device` is a device-encrypted store — secrets AEAD-sealed
(ChaCha20-Poly1305) in `~/.animus/<repo-scope>/secrets/secrets.enc.v1`
(`0600`), master key wrapped by a `key_source`
(`device-id` / `user-key` / `passphrase`) — for hosts where the keyring is
awkward or absent (headless Linux, re-prompting macOS binaries). Move
between backends with `animus secret migrate --to device|keyring`
(verified copy; `--remove-source` clears the origin after). See
`docs/reference/secrets.md`.

Use YAML interpolation for non-secret config only:

```yaml
subjects:
  - id: my-linear
    backend: linear
    config:
      team_id: ${LINEAR_TEAM_ID:-default-team}
      workspace: ${LINEAR_WORKSPACE:?set LINEAR_WORKSPACE}
```

`${VAR}` errors with file path + line number when unset; `${VAR:-default}`
falls back; `${VAR:?message}` customizes the error; `$$` escapes a literal
`$`. `${...}` inside YAML comments is not interpolated (fixed in v0.5.13).
For credentials a phase or MCP server must receive, declare a `secrets:`
block and reference `${secret.<name>}` — since v0.6 the reference passes
through config parsing verbatim and is resolved at consume/spawn time (env
first, then keychain); resolved values are kept out of compiled artifacts,
generated overlays, and parse diagnostics.

HTTP-transport `mcp_servers` entries can attach an `oauth:` block; the daemon
resolves a bearer token and injects the `Authorization` header. Credentials
are read from env vars named via `*_env` pointers (never inline in YAML), and
tokens are cached at `~/.animus/<repo-scope>/mcp-oauth-cache/<server>.json`.
Authenticate with `animus mcp auth <server>`; check `animus mcp auth-status`.

## Cost and budget governance

Declared workflow `budget:` caps are enforced by the daemon's housekeeping
sweep once per heartbeat: a newly crossed cap triggers the declared
`on_exceed` action (`pause` / `fail` / `warn`), a breach record, and one
`workflow-budget-breach` notifier event. Inspect spend with
`animus cost {summary,workflow,top,trends,conversation,decisions}`
(`--by provider|model|task` grouping). With no daemon running, `animus cost`
records breaches but never pauses anything.

## Precedence

Workflow resolution:

1. CLI flags and `--input-json` / `--var` overrides
2. Supported environment variables
3. Project pack overrides in `.animus/plugins/`
4. Project YAML in `.animus/workflows.yaml` and `.animus/workflows/*.yaml`
5. Installed packs in `~/.animus/packs/`

Skill resolution:

1. Project `.animus/skills/` and `.animus/config/skill_definitions/`
2. User `~/.animus/skills/`
3. Installed registry or pack skills, including `animus.core-skills`
4. Agent-host probes such as `.claude/skills` or `.codex/skills` as prompt-text-only
