---
name: animus-flavor-operations
description: Operate Animus flavors — curated plugin bundle manifests (`flavors/<name>.toml`), the `animus flavor` command group, manifest-driven `plugin install-defaults --flavor`, active-flavor persistence in `.animus/plugin-scope.yaml`, drift reports, required vs recommended plugin sets, and writing custom flavor manifests.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
---

# Flavor Operations

Animus is a kernel + flavors. A **flavor** is a named, curated bundle of
plugins (providers, subject backends, config source, transports, workflow
runner, queue, triggers, UI, packs, defaults) declared in a TOML manifest at
`flavors/<name>.toml`. One flavor ships — `default` — whose manifest is also
bundled into the `animus` binary, so a cargo-installed CLI resolves
`default` even with no `flavors/` directory on disk.

**Where flavors sit vs the project manifest (v0.6.9+):** flavors curate the
*no-manifest* experience — a fresh machine or ad-hoc project gets a working
plugin set from `install-defaults --flavor`. A project with a committed
`animus.toml` pins its own set via `animus install` + `.animus/plugins.lock`
(the source of truth); the flavor then only matters for `flavor-only` scope
filtering and drift reporting. Prefer the manifest for anything a team
shares.

Manifest discovery probes, first hit wins:

1. `$ANIMUS_FLAVORS_DIR/<name>.toml` if the env var is set
2. `<project-root>/flavors/<name>.toml`
3. Each ancestor directory's `flavors/<name>.toml`, walking up to `/`

Only `default` has the binary-bundled fallback; any other name with no
on-disk manifest is an error.

## The `animus flavor` Command Group

Verbs: `list`, `current`, `info`, `install`. The `flavor describe` alias was
retired in v0.5.14 — use `flavor info`. JSON output uses the
`animus.flavor.cli.v1` envelope.

```bash
animus flavor list                          # every manifest the loader discovers
animus flavor info --name default           # parsed manifest (TOML; --json for JSON)
animus flavor current                       # active flavor + drift report
animus flavor current --name enterprise     # probe a specific flavor regardless
animus flavor install                       # install `default`'s required set
animus flavor install myflavor --include-recommended --yes
```

`flavor current` with no `--name` probes the project's persisted active
flavor (falling back to `default`) and reports a `source` field: `flag`
(`--name` passed), `persisted` (read from `.animus/plugin-scope.yaml`
`active_flavor:`), or `default`. The drift report lists each required plugin
as installed or missing, counting a plugin as satisfied when it is in EITHER
the global install dir OR the project-scoped install set
(`<project>/.animus/plugins/` + `.animus/plugins.yaml`) — so
`animus plugin install --project` installs report satisfied.

`flavor install [name]` (flags: `--force`, `--yes`, `--include-recommended`)
delegates to `animus plugin install-defaults --flavor <name>`. Drift and the
install plan share one required-set function
(`FlavorManifest::required_plugins`), so they cannot disagree.

## Manifest-Driven Install

```bash
animus plugin install-defaults                        # default flavor, required set
animus plugin install-defaults --include-recommended  # + recommended set
animus plugin install-defaults --flavor <name> --yes  # another manifest
```

The manifest named by `--flavor` (default `default`) is the source of truth.
Everything marked `required` installs — for the default flavor that covers
every daemon-preflight role (`at_least_one_provider`,
`at_least_one_subject_backend`, `config_source` — required since v0.6.0 —
`workflow_runner`, `queue`; the subject role is satisfied by any
`subject_backend` plugin rather than hard-coded `task`/`requirement`
kinds),
so `animus flavor install` followed by `animus daemon start` needs no second
command. Unknown flavor names error instead of silently falling back.
Legacy `--include-subjects` / `--include-transports` still work: they add
just the recommended slice of those sections. Release tags come from the
kernel's curated default-install pins; manifest slugs without a pin warn
and are skipped. (Projects that need exact, reproducible versions should
pin them in `animus.toml` and install with `animus install --locked` —
the lockfile, not the flavor pins, is the source of truth there.)

## Active-Flavor Persistence

A successful `install-defaults --flavor <name>` / `flavor install <name>`
records the selection in `.animus/plugin-scope.yaml` under `active_flavor:`.
The daemon's flavor-only scope resolver, `animus plugin list`, and
`animus plugin scope show` (which adds `active_flavor` +
`active_flavor_source`) read it back, so a non-default flavor's plugins are
admitted by scoped discovery instead of being filtered against
`flavors/default.toml`. Rules:

- Selecting `default` clears the key (and downgrades a leftover
  `flavor-only` mode to `all` when no on-disk `flavors/default.toml` exists).
- A stale persisted name (its `flavors/<name>.toml` was deleted/renamed)
  logs a warning and falls back to the `default` flavor's plugin set —
  never fail-closed to an empty admit set.
- The selection merges into an existing scope file, preserving the
  operator's `mode` / `allow` / `extras`.

`animus daemon health --json` also carries a `flavor` field naming the
resolved manifest id.

## The Default Flavor's Required Set

`flavors/default.toml` (`schema = "animus.flavor.v1"`, id `default`) marks
required: `animus-provider-claude`, `animus-subject-default`,
`animus-subject-requirements`, `animus-config-yaml` (config_source —
required since v0.6.0), `animus-transport-http`,
`animus-workflow-runner-default`, `animus-queue-default` (all under
`launchapp-dev/`). Recommended adds providers (`animus-provider-codex-mcp`
— the MCP-driven codex driver that replaced `animus-provider-codex` in the
defaults — and `animus-provider-ollama`), linear/sqlite/
markdown/github subjects, graphql transport, web UI, cron/webhook triggers,
durable-store, memory-store, and the engineering-backlog pack. Check
`animus flavor info --name default` for the authoritative current roster
rather than trusting a doc snapshot.

## Writing a Custom Flavor

Manifest sections are `providers`, `subjects`, `transports`, `ui`,
`triggers`, `workflow_runner`, `queue`, `config_source`, `durable_store`,
`memory_store`, `packs` — each with optional `required` / `recommended`
slug arrays — plus a
free-form `[defaults]` block (`model_routing`, `cost_ceiling_daily_usd`,
`execution`, `cloud`; hints only, not load-bearing for install in v0.5).
Required slugs must cover every preflight role (provider, subject backend,
config_source, workflow_runner, queue) or `daemon start` will refuse after
install. Minimal `flavors/myflavor.toml`:

```toml
schema = "animus.flavor.v1"
id = "myflavor"
version = "0.1.0"
title = "My Flavor"
description = "Curated bundle for my team."

[providers]
required = ["launchapp-dev/animus-provider-claude"]
recommended = ["launchapp-dev/animus-provider-codex"]

[subjects]
required = ["launchapp-dev/animus-subject-default", "launchapp-dev/animus-subject-requirements"]

[transports]
required = ["launchapp-dev/animus-transport-http"]

[workflow_runner]
required = ["launchapp-dev/animus-workflow-runner-default"]

[queue]
required = ["launchapp-dev/animus-queue-default"]

[config_source]
required = ["launchapp-dev/animus-config-yaml"]
```

Then: `animus flavor install myflavor --yes`, verify with
`animus flavor current` and `animus daemon preflight`.

## `animus init --walkthrough` Flavor Picker

When more than the bundled `default` is discoverable (`flavors/*.toml`
anchored at the init target root), the walkthrough prompts
`Flavor [default]:` and threads the choice into its
`plugin install-defaults --flavor <name>` step so `active_flavor` persists.
TTY-guarded: non-interactive and `--json` runs keep `default`. The bundled
`default` is always offered alongside on-disk custom flavors (a sole custom
flavor still triggers the picker). Plan/apply envelopes report the selected
`flavor`.

## Troubleshooting

- **Broken `flavors/default.toml`** (parse error, unknown schema) with the
  scope in `flavor-only` mode fails closed loudly: discovery and
  `animus plugin list` warn naming the manifest + error; `animus daemon
  preflight` exits 2 with `flavor_manifest_error` set and a fix message
  leading with "fix (or delete) the manifest"; `animus daemon start` /
  `daemon run` refuse with the same message. An explicit scope `mode:` of
  `all` or `allowlist` overrides the gate (warning still surfaces). Note
  `plugin install-defaults` itself falls back to the hardcoded registry
  tables in this one broken-default case, with an error log.
- **Stale `active_flavor`**: warning + fallback to the default flavor's
  plugin set. Clear it by re-running `animus plugin install-defaults`
  (default flavor) or fix/restore the named manifest.
- **Required plugin shows missing despite being installed**: check it is in
  the global dir or the project triple; older builds' drift report scanned
  only the global install dir — current builds union both.

Cross-references: `animus-plugin-operations` for install pipeline, signing,
scope, and lockfiles; `animus-setup` for first-time project bootstrap.
