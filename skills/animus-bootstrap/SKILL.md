---
name: animus-bootstrap
description: Turn a project idea into a complete Animus operating model by interviewing the user and creating vision, principles, registry, agents, phases, workflows, schedules, scripts, and a first task. Use only when the user explicitly asks for full project bootstrap; use animus-setup for a minimal existing-repository setup and animus-getting-started for a guided first run.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---

# Animus Bootstrap

Build a coherent project operating model, not a pile of sample configuration.
This flow can create many project files and start runtime services; invocation
does not itself authorize changes the user did not request.

Read [the full bootstrap playbook](references/bootstrap-playbook.md) before
executing this flow. Read the narrower domain skill when the interview reveals
work that needs exact workflow, MCP, plugin, model, or Portal behavior.

## Required outcome

A complete bootstrap normally produces:

- a user-approved `VISION.md` with scope, users, outcomes, exclusions, and a
  measurable near-term success definition;
- `AGENT_PRINCIPLES.md` and a surface registry that state ownership,
  boundaries, quality gates, and external-effect rules;
- valid agents, globally unique phase IDs, bounded workflows, schedules,
  scripts, and MCP assignments appropriate to the installed runtime;
- a minimal harness-facing `CLAUDE.md` or `AGENTS.md` section that points to
  Animus without copying the skills into always-on context; and
- one real task that proves the installed configuration end to end.

## Operating sequence

1. Inspect the repository, existing Animus state, available providers, project
   instructions, and the user's stated constraints before asking questions.
2. Interview only for decisions that cannot be inferred safely. Resolve the
   product goal and boundaries before designing agent roles or schedules.
3. Draft the vision and operating principles first. Ask for decisions when a
   product, risk, external-effect, or approval choice would materially change
   the system.
4. Design the smallest team and workflow set that covers the accepted scope.
   Keep deterministic work in command phases, judgment in agent phases, and
   real authority in manual/approval gates.
5. Write or merge artifacts without overwriting unrelated project-owned
   content. Respect the installed kernel/plugin/runner versions and the actual
   config authority.
6. Validate the effective configuration, start or reload the daemon only when
   authorized, and run one bounded canary task. Inspect decisions and terminal
   evidence rather than treating process exit alone as success.
7. Hand off what was created, what remains intentionally manual, operational
   commands, known limitations, and the first recommended iteration.

## Hard boundaries

- Do not invent product requirements merely to finish the scaffold.
- Do not enable schedules, triggers, publication, or external side effects
  before the same path succeeds manually and its idempotency is understood.
- Do not create overlapping generic phase IDs; phase definitions are global.
- Do not assume a parse-valid field is enforced by the deployed runner.
- Do not mark the bootstrap complete until the user can identify the source of
  truth, observe a run, and recover or stop the automation.
