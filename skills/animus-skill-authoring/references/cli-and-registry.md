# CLI And Registry

Use this reference only when the task involves authoring via CLI, discovering, installing, uninstalling, publishing, or updating Animus skills.

## Create a skill (two scopes)

```bash
animus skill create --name pr-reviewer --description "Reviews PRs" --prompt "You review pull requests."
animus skill create --name rust-tips --description "Rust guidance" --prompt-file tips.md --user
animus skill create --name pr-reviewer --description "v2" --prompt "..." --force
```

- `--project` (default) writes `.animus/config/skill_definitions/<name>.yaml`; `--user` writes `~/.animus/config/skill_definitions/<name>.yaml` (shared across projects). Project shadows user on a name collision. The flags are mutually exclusive.
- `--name` must be a slug: lowercase ASCII letters/digits plus `-`/`_`, no path separators.
- `--prompt` (stored as `prompt.system`) and `--prompt-file` are mutually exclusive. Optional `--category` and `--tags` (comma-separated or repeated).
- The file is round-tripped through the skill parser before landing on disk, so a malformed skill is never left behind. Without `--force` the command refuses to overwrite an existing definition at the same scope.

MCP equivalents: `animus.skill.create` / `animus.skill.update` take `scope: "project" | "user"` (default `"project"`; `update` requires an explicit `scope` only when the name exists at both scopes). Results carry the same non-fatal `warnings` array as `animus.skill.get` when the definition contains inert tool-id declarations.

## Search skills

```bash
animus skill search --query "review"
animus skill search --source user
animus skill search --registry community
```

## Install a skill

```bash
# From GitHub (v0.6.8+) — imports Anthropic "Agent Skills" SKILL.md format
animus skill install OWNER/REPO
animus skill install OWNER/REPO@ref
animus skill install https://github.com/OWNER/REPO/tree/main/skills/my-skill
animus skill install https://raw.githubusercontent.com/OWNER/REPO/main/SKILL.md

# From a registry / local path
animus skill install --name code-review --registry community
animus skill install --name code-review --version "^1.0" --allow-prerelease
animus skill install --path .animus/skills/code-review/SKILL.md
animus skill install --path .animus/skills/
```

GitHub imports auto-detect format: `animus:` frontmatter → native
passthrough; otherwise Anthropic Agent Skills semantics (`name`/`description`
map over, the markdown body → `prompt.system`, `allowed-tools` →
`tool_policy.allow`). Trees of `skills/<name>/SKILL.md` install each skill
with sibling assets; foreign names are slugified; provenance is recorded
under the `github-import` source shown by `skill list` / `skill info`.

On the portal, the flat-named `skill_install` / `skill_uninstall` /
`skill_info` / `skill_search` / `skill_update` MCP tools wrap this surface;
GitHub installs there land in a durable on-volume registry that survives
redeploys, while `--path` installs are ephemeral.

`--path` accepts a Markdown skill file, a single skill folder, or a directory of
skill folders. `--name` is optional when installing from `--path`. Installing an
agent-host `SKILL.md` (e.g. from `~/.claude/skills/`) promotes it to the
high-trust Installed tier with an integrity snapshot.

## List skills

```bash
animus skill list
animus skill list --source project    # built-in | user | project | installed
```

Definition rows carry a non-fatal `warnings` array when inert `activation.tools`
or `adapters` tool-id declarations are detected (typos or aliases that never
match a canonical tool id).

## Inspect or update a skill

```bash
animus skill info --name code-review
animus skill update --name code-review --version "^2.0"
animus skill update
```

`skill info` includes the same non-fatal `warnings` array as `skill list`.
Omitting `--name` on `update` re-resolves every installed skill.
The old `skill show` verb is gone: it became an alias for `skill info` in
v0.5.13 and the alias was removed in v0.5.14.

## Uninstall a skill

```bash
animus skill uninstall code-review --dry-run
animus skill uninstall code-review
animus skill uninstall code-review --source github
```

The skill name is positional. Removes the installed entry's materialized files
plus its registry and lock entries (`--json` works as usual). `--source` limits
removal to one source; a filter that matches nothing errors instead of
cascading into file deletion, and when another source's snapshot remains the
materialized definition is rewritten from it. `--dry-run` prints what would be
removed without modifying anything. Unlike Animus's dry-run-by-default
destructive verbs, `skill uninstall` applies immediately — `--dry-run` is the
opt-in preview. Unknown skills exit with a not-found error.

## Publish a skill

```bash
animus skill publish --name code-review --version "1.0.0" --source my-org --registry community
animus skill publish --name code-review --version "1.0.0" --source github --registry community --artifact ./dist/code-review.tgz --integrity sha256-...
```

## Registry commands

```bash
animus skill registry add --id community --url https://github.com/animus-skills/registry --priority 10
animus skill registry list
animus skill registry remove --id community
```

`--priority <N>` on `registry add` sets the registry's search priority (lower
value = higher priority).

## Registry state and pinning

Installed-skill state is per-project-scope:

- `~/.animus/<repo-scope>/state/skills-registry.v1.json` — catalog of installed skill versions (written by `skill install` / `skill publish`).
- `~/.animus/<repo-scope>/state/skills-lock.v1.json` — integrity lock for the installed set.

Known limitation: there is no per-skill `animus skill pin` verb (unlike
`animus pack pin`); the lock pins the whole resolved set on `install` /
`update`, so pinning a single skill independently is not yet supported.
