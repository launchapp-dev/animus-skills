# Changelog

## 3.0.0 — 2026-05-14

Aligned with Animus v0.4.0 hard rename: every `ao.*` reference (MCP tool names, env vars, config paths, pack ids, JSON envelope) is renamed to `animus.*`. No deprecation aliases — Animus v0.4.0 dropped `ao.*` entirely. Major version bump because every skill, README, and the setup script changed; any project still pinned to upstream `ao.*` identifiers will break on upgrade.

### Breaking
- All MCP tool references in skill bodies updated from `ao.*` → `animus.*`.
- All env var references updated from `AO_*` → `ANIMUS_*` (`AO_CONFIG_DIR`, `AO_ALLOW_NON_EDITING_PHASE_TOOL`, `AO_WEBHOOK_SECRET`).
- All config dir references updated from `.ao/` → `.animus/` (project-local) and `~/.ao/` → `~/.animus/` (scoped runtime state).
- Pack id references updated: `ao.task` → `animus.task`, `ao.review` → `animus.review`, `ao.requirement` → `animus.requirement`.
- `pack.toml` compatibility key renamed: `ao_core` → `animus_core`.

### Migration
Re-run `./setup` from your animus-skills clone to refresh symlinks. Update any project YAML or scripts that hardcoded `.ao/` paths or `AO_*` env vars (see Animus core migration guide). The `.gitignore` now covers both `.animus/` and the legacy `.ao/` while you migrate existing checkouts.

## 2.2.0 — 2026-05-06

### Added
- `/animus-bootstrap` — new user-invocable skill that walks a project from idea to running autonomous engineering team. Interviews the user (project shape, work character, cadence, risk tolerance, mission, kill criterion, model routing), then writes VISION.md, registry.yaml, AGENT_PRINCIPLES.md, agents/phases/workflows/schedules/mcp-servers YAML, scripts (`repo-health.sh`, `sweep-dispatch.sh`), reports/ directory scaffolding, CLAUDE.md/AGENTS.md project section, and verifies end-to-end with a real smoke-test task watched live via `animus daemon stream`. 13-phase flow, atomic commits between phases. Distinct from `/animus-setup` (minimal) — use bootstrap when committing a project to autonomous operation.
- Substantially expanded `animus daemon stream` coverage in `animus-daemon-operations`: full filter matrix, category cheat sheet (`llm`/`phase`/`schedule`/`queue`/`runner`/`daemon`/`agent`/`task`), five production stream patterns including jq pipelines, stream-vs-events-vs-logs decision table.
- New "Watching the Conductor Work" section in `animus-workflow-patterns` connecting the stream to autonomous-loop debugging — sweep diagnostics, dual-brain cost watch, real-time rework detection.
- 258 new lines of conductor patterns in `animus-workflow-patterns`: AGENT_PRINCIPLES.md as stable prompt anchor, kill criteria + ship score discipline (the three-sweep rule), reports directory convention, worktree + `<surface>:<action>` task title conventions, per-model implementation routing (implement/implement-codex/implement-opus/implement-haiku), scan-type read-only producers, Shape A vs Shape B review-then-rework, chained creative pipelines, multi-surface deploy with fail-fast healthcheck, and 8 production anti-patterns.

## 2.1.0 — 2026-05-04

Defensive namespace pass: every skill now starts with `animus-`. Continuation of the v2.0.0 rebrand — separate version because the slash command surface changed again.

### Breaking
- Every skill renamed with an `animus-` prefix to prevent collisions with skills from other plugins (gstack, etc.). Slash commands change accordingly:
  - `/setup-animus` → `/animus-setup` (also dropped the redundant suffix)
  - `/getting-started` → `/animus-getting-started`
  - `/mcp-setup` → `/animus-mcp-setup`
  - `/workflow-authoring` → `/animus-workflow-authoring`
  - `/pack-authoring` → `/animus-pack-authoring`
  - `/skill-authoring` → `/animus-skill-authoring`
  - `/troubleshooting` → `/animus-troubleshooting`
- Auto-invoked skills change identically: `configuration` → `animus-configuration`, `task-management` → `animus-task-management`, etc.

### Migration
Re-run `./setup` from your animus-skills clone — it auto-removes the dangling un-prefixed symlinks left over from v2.0.0 and creates the new `animus-*` ones in their place.

### Internal
- Cross-references between skill files updated (`../mcp-tools/SKILL.md` → `../animus-mcp-tools/SKILL.md`, etc.).
- Setup script `host_skills_dir` host paths verified against `~/.codex/skills/`, `~/.config/opencode/skills/`, `~/.cursor/skills/` on a real machine — all three confirmed correct.

## 2.0.0 — 2026-05-04

Breaking rebrand from AO to Animus, plus the conductor pattern docs and a multi-host install script.

### Breaking
- CLI binary renamed from `ao` to `animus`. Update any scripts that call `ao …` directly.
- MCP tool prefix renamed from `ao.*` to `animus.*` (e.g. `ao.task.create` → `animus.task.create`).
- MCP server name in `.mcp.json` changed from `"ao"` to `"animus"`. Claude Code permission ids likewise: `mcp__ao__ao_*` → `mcp__animus__animus_*`.
- Slash command `/setup-ao` renamed to `/animus-setup`. Skill directory `setup-ao/` renamed to `setup-animus/`.
- Plugin name changed from `ao-skills` to `animus-skills`. GitHub repo renamed to `launchapp-dev/animus-skills` (HTTPS redirects from the old URL still work).

### Unchanged on purpose
- `.ao/` config directory and `AO_*` env vars are kept — upstream `animus-cli` still uses them.
- Bundled pack IDs (`ao.task`, `ao.review`, `ao.requirement`) and the `ao_core` field in `pack.toml` are kept — those remain the Rust-side identifiers in upstream.

### Added
- `setup` shell script — one-command install for Claude Code, OpenAI Codex CLI, OpenCode, Cursor, Slate, Kiro. Auto-detects installed hosts, installs the `animus` CLI, creates per-skill symlinks, and writes a project-local `.mcp.json`. Supports `--host`, `--no-cli`, `--no-mcp`.
- One-paste install prompt in README — paste into a fresh Claude/Codex session and the agent does the clone + setup itself.
- Conductor / sweep pattern documentation in `workflow-patterns/SKILL.md`: single-daemon SDLC, dual-brain product owner cross-check, `qa-changes` rework gate, scheduled specialists (memory-curator, competitive-scan, e2e-periodic), sweep scripts (`repo-health.sh`, `sweep-dispatch.sh`).
- Conductor system-prompt skeleton in `agent-personas/SKILL.md` — six-section structure (READ FIRST, Mission, Sweep Priorities, Self-Check, Project Root, Managed Repos, Output) plus specialist prompts for updater, scanner, syncer, and implementer-codex.

### Changed
- `mcp-setup/SKILL.md` switched from dev paths (`target/debug/animus`) to production install (`~/.local/bin/animus`, `which animus`).
- README rewritten around the 30-second one-paste install with explicit power-user fallback.

### Fixed
- `setup` script now creates per-skill symlinks (`<host>/skills/<name>`) instead of a whole-repo symlink (`<host>/skills/animus-skills`). Hosts discover skills flat — the previous layout buried every `SKILL.md` one level too deep and the host loader silently skipped them all. Idempotent re-runs detect existing symlinks (including from a parallel clone) and clean up legacy whole-repo symlinks automatically.

### Internal
- Untracked `.claude/settings.local.json` (per-machine, contained user-specific paths). Added to `.gitignore`.
