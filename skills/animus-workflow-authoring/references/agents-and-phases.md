# Agents and Phases

## Agent profiles

Agent profiles select a provider tool/model and optional policy, skills, and
MCP servers. Resolve values from the deployment's provider/capacity registry;
model names and authentication change independently of workflow YAML.

Common authored fields include `tool`, `provider`, `model`, fallback targets,
reasoning effort, `permission_mode`, skills, MCP servers, runtime limits, and
tool policy. Portal-managed agents currently round-trip the legacy
`tool`/`provider`/`capacityAccount`/`model` fields more reliably than the
newer structured `runtimePolicy`; see the portal operations skill before
editing them.

Provider fallback, invocation attempts, and session continuations are
different from workflow rework:

- provider target/fallback: choose a runnable backend
- invocation attempt: retry a classified transient provider failure
- continuation: continue the same agent session when supported
- semantic rework: run a workflow phase again because its verdict requested it

`runtime.retry_on` and `runtime.no_retry_on` currently parse but do not drive
the runner's hard-coded transient-error classification. Do not use them as a
load-bearing reliability policy.

## Phase modes

### Agent

Use for generation, investigation, synthesis, or judgment. Provide one
specific directive, the minimum tools/skills, an output contract for
machine-consumed results, and explicit capabilities.

```yaml
phases:
  orders-implement:
    mode: agent
    agent: implementer
    directive: Implement the scoped change and run the named verification.
    capabilities:
      writes_files: true
      requires_commit: true
    output_contract:
      allow_missing_decision: false
```

### Command

Use for deterministic checks and transforms. The program is spawned directly,
not through a shell: pipes, redirects, globbing, variable expansion, and
compound commands do not work unless the explicitly allowlisted program is a
shell or a durable script invoked by its interpreter.

```yaml
phases:
  orders-test:
    mode: command
    command:
      program: npm
      args: ["test", "--", "orders"]
      cwd_mode: task_root
      timeout_secs: 300
```

Always set `cwd_mode` for repo-sensitive commands. Use `task_root` for the
managed task checkout, `project_root` only for intentional main-repo work, or
`path` with a confined `cwd_path`. The executable basename must be in the
daemon's command tool allowlist.

A nonzero command exit is normally converted to a semantic failure/rework
outcome rather than a runner crash. For routing, set `parse_json_output: true`
and print exactly one decision object:

```json
{"kind":"phase_decision","verdict":"advance","reason":"checks passed","outputs":{"suite":"orders"}}
```

Supported fields include `verdict`, `reason`, `confidence`, `risk`,
`target_phase`, and `outputs`. Without JSON parsing, stdout is evidence/log
text and cannot drive `on_verdict`. A deterministic failure should usually
fail cleanly; route it to a remediation phase only when the route is
intentional, safe, and bounded.

### Manual

Use when a human must authorize, choose, or supply data. A manual phase pauses
the workflow until answered. Do not hold a run open for ordinary business
waiting that may last hours or days; finish a bounded proposal workflow and
launch a continuation when the external approval event arrives.

## Capabilities are execution authority

| Capability | Meaning |
|---|---|
| `writes_files: true` | Agent may create or edit repository files and receives write-capable provider posture where supported. |
| `mutates_state: true` | Agent may mutate approved managed/external state but is explicitly told not to edit repo files unless `writes_files` is also true. |
| `requires_commit: true` | A commit is part of successful completion; pair with `writes_files`. |
| `enforce_product_changes: true` | Require meaningful product changes rather than only metadata/report output. |

Name-based defaults exist for a small set of legacy phase IDs such as exact
`implementation`. They are compatibility sugar, not policy. Custom phase IDs
must declare their capabilities explicitly.

When the active runner/provider combination transports it, `permission_mode`
changes provider approval posture; the current portal path supports it, while
older/local combinations must be verified. It is never an authorization
boundary. Enforce sensitive authority with server-side scopes, actor/resource
checks, narrowly assigned MCP servers, tool allowlists, capabilities, and
human approval where required.

## Skills and MCP context

Effective phase skills are the phase list followed by the agent list, with
deduplication. The daemon resolves them at dispatch and stages definitions in
a per-run directory exposed as `ANIMUS_PHASE_SKILLS_DIR`. The former
`ANIMUS_PHASE_SKILLS_JSON` payload was removed because large environment
values can prevent process spawn. Missing skills are recorded/warned and may
not fail autonomous dispatch; validate prerequisites before publication.

Treat skill content as guidance, not authority. MCP tool availability is
controlled separately. Assign an agent only the servers it needs and enforce
permissions on the server. Actor-bound workflow MCP intentionally exposes a
smaller surface than a management MCP server.

## Decisions, outputs, and routing

Prefer `advance`, `rework`, and `fail`. Custom verdict strings can route via
`on_verdict`; agent-selected `target_phase` is honored only when explicitly
enabled and allowlisted.

Require machine-critical decisions with `allow_missing_decision: false` and
validate their output shape. Current lifecycle code does not fully enforce all
declared `min_confidence`, `max_risk`, or named-evidence requirements; add a
deterministic later gate when these are safety-critical.

Prior phase payload variables expose top-level scalar values. Nested
objects/arrays are not a dependable variable handoff, duplicate keys can be
overwritten by later phases, and reserved workflow variables win. Use a small
explicit scalar contract or a durable artifact/record for complex handoffs.

## Rework and retries

The lifecycle resolves the rework target first, checks that target phase's
retry config, and increments that target's durable rework counter. Here
`max_attempts` means permitted re-entries, not total executions: `1` permits
one remediation and therefore at most two executions of the target.

```yaml
phases:
  orders-implement:
    mode: agent
    agent: implementer
    capabilities:
      writes_files: true
    retry:
      max_attempts: 1

  orders-review:
    mode: agent
    agent: reviewer

workflows:
  - id: orders-delivery
    phases:
      - orders-implement
      - orders-review:
          on_verdict:
            rework:
              target: orders-implement
```

Rich workflow-step `max_rework_attempts` is accepted and validated but is not
the counter used by the rc.50 lifecycle. Transition `guard` is also not
evaluated. Every cycle must therefore have a deterministic escape and rely on
`phases.<target>.retry.max_attempts`.

## Evaluations

`evals` can run command checks and `llm_judge` checks after an advancing phase
decision on current runners. Checks run sequentially; the pass rate is
compared with `pass_threshold`. `on_fail: rework` repeats up to `max_reworks`,
then blocks; `on_fail: block` blocks immediately. An inoperable check fails
closed.

This is runner-version dependent. The older runner pinned by the rc.50 CLI
default-install manifest does not execute evals; portal runner 0.4.71 does.
Additionally, current eval rework counters are in-memory and reset across a
runner restart/resume. Keep an independently bounded lifecycle retry and do
not use eval counts as durable business-state authority.
