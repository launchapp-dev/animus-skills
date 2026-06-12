---
name: animus-plugin-operations
description: Install, inspect, update, lock, sign, scaffold, and troubleshoot Animus STDIO plugins, including provider, subject_backend, trigger, transport/web, and log-storage plugins.
user_invocable: false
auto_invoke: true
---

# Plugin Operations

Current Animus depends on STDIO plugins for provider execution, subject
storage, transports, web UI, triggers, and optional log storage. Provider and
subject plugins are required for normal daemon operation.

## First Fix for Missing Plugins

```bash
animus daemon preflight
animus plugin install-defaults --include-subjects
animus daemon preflight
```

Add transport and web UI plugins only when `animus web` is needed:

```bash
animus plugin install-defaults --include-transports
```

`animus daemon start` and `animus daemon run` run preflight by default.
Use `--auto-install` to install recommended missing defaults. Use
`--skip-preflight` only for local development or intentionally degraded runs.

## Discovery

Default discovery order (first source to yield a name wins):

1. Registry config `~/.animus/plugins.yaml`; legacy `~/.config/animus/plugins.yaml` only when the new registry is absent
2. Project-local `<project_root>/.animus/plugins/`
3. Global install dir: `$ANIMUS_PLUGIN_DIR` if set, otherwise `~/.animus/plugins/` — scanned unconditionally
4. `$ANIMUS_PLUGIN_PATH` (colon-separated directories)
5. System `$PATH` (opt-in only)

`$PATH` scanning is opt-in:

```bash
animus plugin list --include-system-path
animus plugin info --name animus-provider-claude --include-system-path
```

## Install Defaults

```bash
# Provider plugins: claude, codex, gemini, opencode, oai
animus plugin install-defaults

# Add OAI agent provider
animus plugin install-defaults --include-oai-agent

# Add subject backends: default, requirements, linear, sqlite, markdown
animus plugin install-defaults --include-subjects

# Add transport and web UI plugins
animus plugin install-defaults --include-transports
```

Useful flags:

- `--plugin-dir <PATH>` overrides the install directory.
- `--force` reinstalls existing plugins.
- `--yes` accepts the trust-on-first-use prompt for `launchapp-dev`.
- `--json` emits per-plugin results and a failure summary.

## Install One Plugin

```bash
animus plugin install launchapp-dev/animus-provider-claude
animus plugin install launchapp-dev/animus-provider-claude@v0.2.2
animus plugin install launchapp-dev/animus-provider-claude --tag v0.2.2
animus plugin install --path ./target/release/animus-provider-custom --name custom
animus plugin install --url https://example.com/plugin --sha256 <hex>
```

Use `--force` to replace an installed plugin. `--url` requires `--sha256`.

Signature policy:

- `--signature-policy strict` fails closed on missing, invalid, or untrusted signatures.
- `--signature-policy warn` logs signature failures and installs anyway.
- `--signature-policy disabled` skips verification.
- `--require-signature`, `--allow-unsigned`, and `--skip-signature` are legacy aliases.
- `--allow-org <OWNER>` or `--yes` records trusted orgs for future installs.
- `--trusted-signers <PATH>` points at a `trusted-signers.yaml` allowlist.

Avoid `--allow-shadow-builtin` unless deliberately replacing provider dispatch
for a built-in provider tool name such as `claude`, `codex`, `gemini`,
`opencode`, or `oai-runner`.

## Inspect and Call

```bash
animus plugin list
animus plugin info --name animus-provider-claude
animus plugin ping --name animus-provider-claude
animus plugin call --name animus-provider-claude --method '$/ping'
animus plugin call --name animus-subject-linear --method 'linear/list' --params '{"limit":5}'
```

Use `plugin call` for plugin-specific methods that are not wrapped by the core
CLI or MCP subject surfaces.

## Diagnostics, Cache, and Scope

- `animus plugin doctor` — per-role view of installed plugins (installed_kind + native_kind) with duplicate/collision detection.
- `animus plugin status [NAME]` — per-plugin runtime status (pid, state, last RPC, restart count); only provider runtimes report live fields, other kinds show `discovered`.
- `animus plugin rename <NAME> --to <KIND>` — change an installed plugin's `installed_kind` in the lockfile; the binary and manifest `native_kind` are untouched.
- `animus plugin cache clear|list` — inspect or wipe the manifest cache under `~/.animus/cache/manifests/`; clear after a manual binary swap. `ANIMUS_DISABLE_MANIFEST_CACHE=1` (also accepts `true`/`yes`) is the kill switch.
- `animus plugin scope show|set|reset` — per-project plugin scoping via `.animus/plugin-scope.yaml` (`mode: all`, `flavor-only`, or `allowlist`) so discovery and preflight only iterate the project's relevant plugins.

## Marketplace and Updates

```bash
animus plugin search linear --kind subject_backend
animus plugin browse --kind provider
animus plugin browse --available
animus plugin update --all --check
animus plugin update --name animus-provider-codex --tag v0.2.3
```

`plugin update` requires exactly one selector: `--all`, `--kind <KIND>`, or
`--name <NAME>` (a bare positional name still works as a legacy form).
`--check` previews the diff without writing; `--dry-run` is a legacy alias.

There is no `plugin list --check-updates`; use `plugin update --all --check`.

## Lockfile

```bash
animus plugin lock list
animus plugin lock verify
animus plugin lock verify --lockfile .animus/plugins.lock --plugin-dir .animus/plugins
```

Project-local installs use `.animus/plugins.lock`; otherwise Animus falls back
to `~/.animus/plugins.lock`.

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

Plugin lock and `install-defaults` are CLI-first surfaces in the current
reference.

## Troubleshooting

- Daemon preflight fails: install providers plus subject plugins, then rerun preflight.
- Plugin installed but not discovered: check `~/.animus/plugins.yaml`, install directory, `ANIMUS_PLUGIN_DIR`, and `ANIMUS_PLUGIN_PATH`; add `--include-system-path` only when needed.
- Bad provider plugin: uninstall it or move its binary out of discovery. `ANIMUS_PROVIDER_DISABLE_PLUGIN` was removed and has no effect.
- Subject calls all fail: check `ANIMUS_DAEMON_DISABLE_SUBJECT_PLUGINS` and whether a subject backend claims the requested kind.
- Log tail is wrong: check `ANIMUS_DAEMON_DISABLE_LOG_STORAGE_PLUGIN`; when set, Animus forces the in-tree `events.jsonl` fallback.
