---
name: animus-plugin-operations
description: Install, inspect, update, lock, sign, scaffold, and troubleshoot Animus STDIO plugins — global and project-scoped installs, flavor-driven defaults, TOFU org trust auditing — covering provider, subject_backend, trigger, transport/web, workflow_runner, queue, and log-storage plugins.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
---

# Plugin Operations

Current Animus depends on STDIO plugins for provider execution, subject
storage, config sourcing, workflow running, queueing, transports, web UI,
triggers, environments, and optional log storage / journal / conversation
storage. Daemon preflight requires: `at_least_one_provider`,
`at_least_one_subject_backend`, `config_source` (required since v0.6.0 — the
kernel no longer parses workflow YAML in the runtime load path),
`workflow_runner`, and `queue`. The `environment` kind (v0.7-rc/portal
only, e.g. `animus-environment-railway`) is optional at preflight.

**Multi-kind plugins (v0.7-rc/portal only):** a manifest can declare
`plugin_kinds` (secondary kinds) + `kind_capabilities`, and every role
resolver routes by `serves_kind` — one consolidated plugin can serve many
roles (e.g. `animus-postgres` serves subject_backend + config_source +
queue + workflow_journal + conversation_store from one process). The
0.6.x in-tree plugin protocol does not implement multi-kind — on local
installs each plugin serves exactly its primary kind.

Plugin commands use typed exit codes: invalid input = 2, not found = 3,
unavailable (missing plugin / network) = 5.

## First Fix for Missing Plugins

Project with a committed `animus.toml` (v0.6.9+):

```bash
animus daemon preflight
animus install            # installs the manifest-declared set from plugins.lock
animus daemon preflight
```

No manifest (fresh machine / ad-hoc project):

```bash
animus daemon preflight
animus plugin install-defaults
animus daemon preflight
```

Bare `install-defaults` installs the default flavor's full required set —
claude provider, subject-default, subject-requirements, config-yaml,
transport-http, workflow-runner-default, queue-default — covering every
preflight role in one command (no second `--include-subjects` pass needed).
When preflight finds multiple roles missing, it prints the one composed fix.

`animus daemon start` and `animus daemon run` run preflight by default.
Use `--auto-install` to install recommended missing defaults. Use
`--skip-preflight` only for local development or intentionally degraded runs.

## The Project Manifest: `animus.toml` (v0.6.9+)

`animus.toml` declares intent (`[project]` kernel version, `[plugins]`,
`[packs]`; deps as a version string, `{ git, tag }`, or `{ path }`);
`.animus/plugins.lock` is the resolved **source of truth**, and
`plugins.yaml` registries are derived projections regenerated on every
mutating op (never hand-edit them; drift heals on the next op).

```bash
animus install                     # resolve manifest → lock, install plugins + packs
animus install --locked            # npm-ci: reproduce the committed lock exactly; fails on manifest↔lock drift
animus install --allow-org my-org  # non-TTY/server escape hatch for org TOFU (v0.7-rc only; 0.6.x `animus install` has just --locked/--force and only installs from the trusted launchapp-dev org)
animus add launchapp-dev/animus-subject-linear@v0.2.0    # manifest + install
animus add my-org/my-pack@v1.0.0 --pack
animus remove animus-subject-linear
```

## Discovery

Default discovery order (first source to yield a name wins):

1. Project-local tier: `<project>/.animus/plugins/` dir scan, then the
   project registry `<project>/.animus/plugins.yaml` (a lock-derived
   projection)
2. Global registry `~/.animus/plugins.yaml` (lock-derived); legacy
   `~/.config/animus/plugins.yaml` only when the new registry is absent
3. Optional DB-registry tier (v0.7-rc/portal only, opt-in — not on 0.6.x
   local installs): resolve the plugin set from a Postgres
   `plugin_registry` (animus-postgres BaaS deployments)
4. Global install dir: `$ANIMUS_PLUGIN_DIR` if set, otherwise `~/.animus/plugins/`
5. `$ANIMUS_PLUGIN_PATH` (colon-separated directories)
6. System `$PATH` (opt-in only)

The project-local tier wins name collisions, so a project install shadows a
same-named global install (registry-recorded or bare binary).

**Discovery hardening (v0.7-rc/portal only):** project-local
`plugins.yaml` `binary:` entries and project-local dir scans are gated by
trust and location — server-safe discovery never executes repo-shipped
binaries, even under an `all` scope. Trusted installed candidates are
always probed post-filter, so renamed plugins keep working. 0.6.x local
installs do not carry this gating.

`$PATH` scanning is opt-in:

```bash
animus plugin list --include-system-path
animus plugin info animus-provider-claude --include-system-path
```

`animus plugin list` shows each row's install scope in the `SCOPE` column
(`project`/`global`; `scope` field in JSON) and surfaces hidden global
binaries as `shadowed` entries. Stale registry entries (binary path vanished)
collapse to one summary warning line naming the prune remedy; `--verbose`
restores per-entry detail; `--json` always carries the full `warnings` array.

## Install Defaults (flavor-manifest-driven)

The flavor manifest (`flavors/<name>.toml`; binary-bundled fallback for
`default`) is the source of truth for the install plan. Unknown flavor
names error instead of silently falling back.

```bash
# Default flavor's required set (every preflight role)
animus plugin install-defaults

# Required + recommended (extra providers, more subjects, graphql, web UI)
animus plugin install-defaults --include-recommended

# Another flavor manifest
animus plugin install-defaults --flavor <name>

# Add the OAI agent provider
animus plugin install-defaults --include-oai-agent

# Legacy flags still work; they add the recommended slice of those sections
animus plugin install-defaults --include-subjects
animus plugin install-defaults --include-transports
```

Useful flags:

- `--flavor <NAME>` selects the manifest (default `default`; `$ANIMUS_FLAVORS_DIR` overrides the search dir).
- `--include-recommended` adds the manifest's `recommended` set.
- `--plugin-dir <PATH>` overrides the install directory.
- `--force` reinstalls existing plugins.
- `--yes` accepts the trust-on-first-use prompt for `launchapp-dev`.
- `--json` emits per-plugin results and a failure summary; exits non-zero on any failure.

A successful `install-defaults --flavor <name>` persists the selection to
`.animus/plugin-scope.yaml` under `active_flavor:` (selecting `default`
clears it). `animus flavor current` probes the persisted flavor and reports
a `source` field (`flag` | `persisted` | `default`); `animus plugin scope
show` adds `active_flavor` + `active_flavor_source`. `animus flavor install
<name>` delegates to `install-defaults --flavor <name>`; `animus flavor info
--name <name>` prints the manifest. Flavor drift counts a required plugin as
installed when it is in EITHER the global install dir or the project-scoped
install set.

## Install One Plugin

```bash
animus plugin install launchapp-dev/animus-provider-claude
animus plugin install launchapp-dev/animus-provider-claude@v0.2.2
animus plugin install launchapp-dev/animus-provider-claude --tag v0.2.2
animus plugin install --path ./target/release/animus-provider-custom --name custom
animus plugin install --url https://example.com/plugin --sha256 <hex>
```

Use `--force` to replace an installed plugin. `--url` requires `--sha256`.

Signature policy — v0.7-rc/portal resolution is context-aware, precedence:
per-call `--signature-policy` flag > `ANIMUS_PLUGIN_SIGNATURE_POLICY` env
(`strict`/`warn`/`skip`) > `plugins.signature_policy` global config > `warn`
default. (On 0.6.x local installs there is no env or global-config layer:
precedence is the `--signature-policy` flag > legacy
`--skip-signature`/`--require-signature` > `warn` default.) The flag's mode
words are `strict`/`warn`/`disabled`:

- `--signature-policy strict` fails closed on missing, invalid, or untrusted signatures (cosign preflight fails fast).
- `--signature-policy warn` (default) logs signature failures and installs anyway.
- `--signature-policy disabled` skips verification.
- `--require-signature`, `--allow-unsigned`, and `--skip-signature` are legacy aliases.
- `--allow-org <OWNER>` or `--yes` records trusted orgs for future installs.
  **Fail-closed TOFU (v0.7-rc/portal only):** on a non-TTY or with
  `ANIMUS_SERVER=1`, `--yes`/`--force` will NOT auto-trust an unknown org —
  `--allow-org` is the explicit escape hatch, and the release-source gate
  runs BEFORE download. On 0.6.x local installs `--yes`/`--force` auto-trust
  unconditionally (with a warning), and the org gate runs after
  download + manifest probe.
- `--trusted-signers <PATH>` points at a `trusted-signers.yaml` allowlist.

Reserved provider names (`claude`, `codex`, `gemini`, `opencode`, `oai`,
`oai-agent`, `oai-runner`) are an anti-squat guard, not native backends: a
canonical `animus-provider-<reserved>` published by the built-in trusted
publisher `launchapp-dev` installs with **no flag** (v0.6.10+). Only
untrusted orgs — and `--path` / `--url` installs (owner unknown) — need
`--allow-shadow-builtin`.

## Project-Scoped Installs

`animus plugin install --project` (also on `uninstall` and `update`) targets
the project-local triple instead of the global one:

- Binaries: `<project>/.animus/plugins/`
- Lockfile (source of truth): `<project>/.animus/plugins.lock`
- Registry (derived from the lock): `<project>/.animus/plugins.yaml`

Same sha256 / cosign / TOFU / fail-closed-lockfile pipeline as global
installs. `--project` conflicts with `--plugin-dir`. Project installs shadow
same-named global installs during discovery and flow into `plugin list`
(SCOPE column), `plugin status`, `plugin outdated` (per-row `scope`),
`plugin update --project`, and `plugin lock verify`.

Version control: `animus init` and project installs write a
`.animus/.gitignore` covering `plugins/` so binaries stay out of VCS; commit
`animus.toml` and the project lockfile (`.animus/plugins.lock`) — the lock
pins the repo's plugin set with per-target integrity (schema 2.0), so a lock
generated on macOS drives verified linux `--locked` installs.

## Org Trust (audited TOFU)

`~/.animus/trusted-orgs.yaml` records per-org audit metadata: `trusted_at`,
`decided_by` (`interactive-prompt` | `yes` | `allow-org` | `built-in`), and
`first_plugin`. Legacy bare-string entries still load.

```bash
animus plugin trust list           # current + revoked orgs (--json)
animus plugin revoke-trust <ORG>   # tombstones revoked_at; re-installs re-prompt
```

The built-in `launchapp-dev` anchor cannot be revoked. Successful
release-source installs surface an `org_trust` block (`org`, `trusted_at`,
`decided_by`) in the install JSON envelope.

## Inspect and Call

```bash
animus plugin list
animus plugin info animus-provider-claude
animus plugin ping --name animus-provider-claude
animus plugin call --name animus-provider-claude --method '$/ping'
animus plugin call --name animus-subject-linear --method 'linear/list' --params '{"limit":5}'
```

Use `plugin call` for plugin-specific methods that are not wrapped by the core
CLI or MCP subject surfaces. `info`/`ping`/`call` fail before handshake when
the plugin's manifest-declared `env_required` vars are unset.

## Diagnostics, Cache, and Scope

- `animus plugin doctor` — per-role view of installed plugins (installed_kind + native_kind) with duplicate/collision detection across all five preflight roles (`at_least_one_provider`, `at_least_one_subject_backend`, `workflow_runner`, `queue`, `config_source`).
- `animus plugin status [NAME]` — per-plugin runtime status (pid, state, last RPC, restart count, supervisor `disabled_by_supervisor` / `cooldown_until`); also reports aggregate provider health (absorbed from the removed `animus runner health`): a `providers` array plus a rolled-up `provider_plugins_healthy` boolean. Only provider runtimes report live fields; other kinds show `discovered`.
- `animus plugin prune [--yes]` — remove stale `plugins.yaml` registry entries whose binary was deleted (the prune remedy named in the `plugin list` stale-entry warning); without `--yes` it previews.
- `animus plugin rename <NAME> --to <KIND>` — change an installed plugin's `installed_kind` in the lockfile; the binary and manifest `native_kind` are untouched.
- `animus plugin cache clear|list` — inspect or wipe the manifest cache under `~/.animus/cache/manifests/`; clear after a manual binary swap. `ANIMUS_DISABLE_MANIFEST_CACHE=1` (also accepts `true`/`yes`) is the kill switch.
- `animus plugin scope show|set|reset` — per-project plugin scoping via `.animus/plugin-scope.yaml` (`mode: all`, `flavor-only`, or `allowlist`) so discovery and preflight only iterate the project's relevant plugins. The same file carries the persisted `active_flavor:`.
- Orphaned CLI process detection moved to `animus doctor` (`--fix` prunes dead tracker entries; live PIDs get a manual kill suggestion).

## Marketplace and Updates

```bash
animus plugin search linear --kind subject_backend
animus plugin browse --kind provider
animus plugin browse --available
animus plugin update --all --check
animus plugin update --name animus-provider-codex --tag v0.2.3
animus plugin update --all --restart-daemon
animus plugin outdated
animus plugin outdated --exit-code --offline
```

`plugin update` requires exactly one selector: `--all`, `--kind <KIND>`, or
`--name <NAME>` (a bare positional name still works as a legacy form).
`--check` previews the diff without writing (`--dry-run` is a legacy alias);
`--restart-daemon` restarts the daemon after a successful update;
`--project` operates on the project-local registry + install root.

`animus plugin outdated` reports drift per installed plugin: installed tag vs
the recommended pin in `default-install.json` vs the latest registry tag.
Row `status` is `current`, `outdated`, `ahead`, `unknown`, or `local`; rows
carry `scope` (`global`/`project`). Always exits 0 unless `--exit-code` is
passed (CI gate). `--offline` serves the cached registry index.

Registry fetch resilience: transient failures (connection errors, 5xx, 429 —
the 429 message names the rate limit and points at `--offline`) retry with
backoff; an expired cache falls back to the stale copy with a loud age
warning instead of hard-failing. `--no-cache` forces a fresh fetch;
mutually exclusive with `--offline`.

There is no `plugin list --check-updates`; use `plugin update --all --check`
or `plugin outdated`.

## Lockfile

```bash
animus plugin lock list
animus plugin lock verify
animus plugin lock verify --lockfile .animus/plugins.lock --plugin-dir .animus/plugins
```

`plugin lock verify` sweeps BOTH lockfile roots by default: global
`~/.animus/plugins.lock` (against the global install dir) and project
`<project>/.animus/plugins.lock` (against the project dir, with a global-dir
fallback for legacy entries). Each result carries `scope`
(`global`/`project`/`explicit`); `--lockfile <PATH>` restricts to one file.
Any mismatch or missing binary exits non-zero.

Lock schema 2.0 (v0.6.7): each entry records per-target-triple integrity —
`targets: {triple → {archive_sha256, signature_bundle_sha256,
installed_binary_sha256}}` — captured from the release's `SHA256SUMS.txt`
for EVERY published platform at install time. Schema-1.0 locks migrate with
empty targets; re-install to upgrade them. `lock verify` and `--locked`
installs verify the current platform's entry. When no triple-specific
release asset exists, install falls back to a `<name>-noarch.tar.gz` asset
(v0.7-rc only — 0.6.x local installs have no noarch fallback).

## Scaffolding

Two paths:

- `animus plugin new --kind subject|provider|trigger` clones the
  `launchapp-dev/animus-plugin-template` repo (needs network).
- `animus plugin scaffold trigger <NAME>` writes a self-contained starter
  project from built-in templates, offline. Trigger only.

```bash
animus plugin new --kind subject --name jira --org my-org
animus plugin new --kind provider --name openai-compat --out-dir ./animus-provider-openai-compat
animus plugin new --kind trigger --name webhook --template-version main
animus plugin scaffold trigger fswatch
```

## MCP Tools

Use MCP when the host already has `animus mcp serve` wired:

- `animus.plugin.list`, `info`, `ping`, `call`
- `animus.plugin.install`, `uninstall`
- `animus.plugin.search`, `browse`, `update`

Plugin lock, `install-defaults`, `outdated`, and the trust verbs are
CLI-first surfaces in the current reference.

## Troubleshooting

- Daemon preflight fails: `animus install` in a manifest project, else `animus plugin install-defaults` (covers every required role), then rerun preflight. The error message includes the exact per-role install commands.
- Plugin installed but not discovered: check the project tier (`.animus/plugins/`, `.animus/plugins.yaml`), `~/.animus/plugins.yaml`, the global install dir, `ANIMUS_PLUGIN_DIR`, and `ANIMUS_PLUGIN_PATH`; add `--include-system-path` only when needed. Also check `.animus/plugin-scope.yaml` — a `flavor-only` or `allowlist` scope can filter the plugin out of discovery.
- Project install not taking effect: confirm it shadows the global one in `animus plugin list` (`shadowed` note) and that the scope file admits it.
- Bad provider plugin: uninstall it or move its binary out of discovery. `ANIMUS_PROVIDER_DISABLE_PLUGIN` was removed and has no effect.
- Subject calls all fail: check `ANIMUS_DAEMON_DISABLE_SUBJECT_PLUGINS` and whether a subject backend claims the requested kind.
- Log tail is wrong: check `ANIMUS_DAEMON_DISABLE_LOG_STORAGE_PLUGIN`; when set, Animus forces the in-tree `events.jsonl` fallback.
- Opaque "plugin connection lost" on startup: since v0.6.33 the plugin host captures a bounded, redacted ring buffer of each plugin's stderr and appends it to handshake/ConnectionLost errors, so the error names WHY the plugin died; the subject_router and config_source spawn+handshake paths also retry transient (re)spawn failures with backoff before surfacing a hard error.
- Zombie run after a container/host reboot: since v0.6.32 runner pid files record the per-process start-time alongside the PID, so a reboot-reused PID no longer passes liveness — it can no longer shield an interrupted workflow from cancellation/resume.
- Stale flavor selection (`flavors/<name>.toml` deleted): the scope resolver logs a warning and falls back to the default flavor's plugin set — it never fail-closes discovery to empty. Re-run `animus plugin install-defaults` (default flavor) to clear the persisted key.
