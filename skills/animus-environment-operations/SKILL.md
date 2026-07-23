---
name: animus-environment-operations
description: Operate Animus v0.7 execution environments — environment plugins and coder nodes, the cross-phase environment broker, workflow/phase `environment:` pinning, `environment_routing:` rules, `workspaces:` multi-repo checkout sets, lease records and the startup reaper, and animus-environment-railway. Use when pinning workflows to remote execution, debugging node acquisition or teardown, or authoring multi-repo runs.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets (runner v0.4.49, animus-environment-railway v0.4.15)
---

# Execution Environments (v0.7)

**Version gate: this entire surface requires a v0.7.0-rc install** (e.g. the
portal's rc.27 deployment). None of it — the `environment` plugin kind, the
YAML surfaces, the broker, or the `animus environment` command group —
exists on 0.6.x local installs.

v0.7 adds an `environment` plugin kind: instead of local worktrees, a
workflow run can execute inside an ephemeral remote node the environment
plugin provisions (a "coder node" — e.g. a per-run Railway container from
`animus-environment-railway`). The role is **optional at daemon preflight**
— with no environment plugin installed, everything runs locally and the
classic worktree model applies unchanged.

## The three YAML surfaces

```yaml
workspaces:                     # named multi-repo checkout sets
  platform:
    repos:
      - url: https://github.com/acme/api
        name: api               # checkout subdir; defaults to last URL segment
        git_ref: main
        primary: true           # default cwd; first entry wins if none marked
      - url: https://github.com/acme/web

environment_routing:
  default: railway              # env plugin id when nothing more specific matches
  rules:
    - match: { kind: task, harness: claude }   # ANDed; unset = wildcard; all-unset = catch-all
      environment: railway
      spec: { size: large }     # opaque map merged into the compiled EnvironmentSpec

workflows:
  - id: platform-delivery
    environment: railway        # workflow-level pin (honored by daemon rc.16+)
    workspace: platform
    phases:
      - implementation
      - heavy-test:
          environment: railway-xl   # phase-level override
```

**Resolution precedence** (first hit wins): phase `environment:` → first
matching `environment_routing.rules` entry → workflow `environment:` →
`environment_routing.default` → none (local execution).

`workspaces:` is **inert without an environment plugin** — declaring it
changes nothing for local runs. Single-repo runs without a `workspace:` can
still resolve their repo from the subject's `custom` bag
(`{{git_repo}}`, workflow-runner v0.4.34+; set via
`animus subject update --data '{"git_repo": "..."}'`).

## The cross-phase environment broker

When a run resolves to an environment, the daemon-resident
**EnvironmentBroker** owns the node lifecycle:

- **One node per workflow run.** Every phase — agent AND command phases
  (runner v0.4.33+) — executes in the same node, so state (installed deps,
  build artifacts, checkouts) persists across phases of the run.
- **Acquisition is single-flight, keyed on the subject** — parallel runs on
  the same subject share the acquire rather than racing to provision
  duplicate nodes.
- **Exec is proxied** from the runner to the node over a private local
  socket with bearer auth; the daemon sets `ANIMUS_ENVIRONMENT_BROKER_*`
  env vars on the runner (not user-configurable).
- **Durable leases** are recorded at
  `~/.animus/<repo-scope>/workflow-environments/<run_id>.json`.
- **Teardown** happens on terminal run states; a **startup reaper**
  cold-tears-down stale leases when the daemon boots (so `animus daemon
  restart` cleans up nodes leaked by a crash).
- `environment/prepare` gets its own generous RPC timeout (node cold-start
  is minutes, not seconds); the environment host is pinned across
  prepare/exec/teardown.

Gating env vars (kernel-side, default off — the broker path on portal
deployments enables what it needs): `ANIMUS_ENVIRONMENT_DELEGATE`
(worktree materialization delegated to the env plugin),
`ANIMUS_ENVIRONMENT_EXEC` (agent exec routed through resolved environment
plugins; once resolved there is no silent local fallback).

## animus-environment-railway (reference plugin)

Provisions ephemeral per-run Railway containers from a run-image, relayed
over an outbound WebSocket to an in-plugin RelayServer, deleted on teardown.
Operationally notable:

- **GitHub App token minting** (v0.3.0+): nodes push branches and open PRs
  as the GitHub App with repo-scoped, short-lived tokens — no long-lived
  PATs inside nodes.
- **Central Claude token refresh** (v0.4.0+): nodes never rotate shared
  credentials; the plugin refreshes centrally and injects fresh tokens.
- In-node claude runs use bypassPermissions (runner v0.4.35+); codex runs
  disable the bwrap sandbox inside nodes (runner v0.4.38).

## Node management: `animus environment` (rc.26+)

Direct node inspection and cleanup through the installed environment
plugin's node-management surface (`environment/list` · `/get` ·
`/teardown_node` · `/reap`):

```bash
animus environment list                     # managed nodes: state + orphan flag
animus environment get <ID>                 # one node by substrate id or name (e.g. animus-run-*)
animus environment teardown <ID>            # destroy one node (idempotent)
animus environment reap                     # reap dead (FAILED/CRASHED) nodes only
animus environment reap --dry-run           # report what WOULD be reaped
animus environment reap --older-than-secs 3600
animus environment reap --all --force       # also reap healthy nodes with no live owning run
```

`--all` requires `--force` (guards against a process with no liveness view
treating every node as an orphan). All verbs take `--environment <PLUGIN>`
to target a specific plugin; it defaults to the sole installed environment
plugin. Matching MCP tools: `animus.environment.{list,get,teardown,reap}`.

## Patterns

- **Heavy pipeline**: workflow-level `environment:` + one `install-deps`
  command phase first — deps persist for the whole run (contrast the local
  model where every run's worktree starts bare).
- **Multi-repo change**: `workspaces:` with the primary repo marked;
  phases `cd` between checkout subdirs by name.
- **Selective routing**: `environment_routing.rules` matched on subject
  `kind` — route `task` runs to nodes while `blog`/content runs stay local.

## Troubleshooting

1. **Run stalls at a phase boundary**: first grep the daemon log for a
   `runner-exit` diagnostic (rc.25+ — emitted when a dispatched runner
   process dies, with exit code, signal, duration, and a stderr tail). Then
   check the lease file exists for the run id and compare against
   `animus environment list` — a lease whose node shows dead/orphaned means
   the node died: `animus environment teardown <node>` (or `reap`), then
   cancel the run and re-dispatch. Note the orphan sweep no longer reaps
   in-flight delegated runs (rc.24), so a live remote run won't be killed
   under you mid-stall.
2. **Leaked nodes after a daemon crash**: `animus environment reap`
   (`--dry-run` first; `--all --force` for healthy orphans) reaps directly;
   `animus daemon restart` also works — the startup reaper reconciles
   `workflow-environments/` leases.
3. **Broker auth/connection errors in run output**: the daemon-set
   `ANIMUS_ENVIRONMENT_BROKER_*` wiring is stale — restart the daemon; do
   not hand-set those vars.
4. **Hung acquisition blocks several runs**: acquisition is keyed on the
   subject — one stuck provision holds every parallel run on that subject.
   Look at the environment plugin's logs (`animus logs tail --plugin
   animus-environment-railway`).
5. **`workspaces:` seems ignored**: no environment plugin resolved — check
   the precedence chain and that the plugin is installed
   (`animus plugin list`).
6. **Cost**: a non-terminal run keeps its node alive; cancel abandoned runs
   to release nodes, and use `animus environment list` / `reap
   --older-than-secs` to find and clear long-lived leftovers.

Cross-references: animus-workflow-authoring (YAML field tables),
animus-workflow-patterns (environment-pinned pipeline pattern),
animus-troubleshooting (broker failure triage), animus-configuration
(state layout + env vars).
