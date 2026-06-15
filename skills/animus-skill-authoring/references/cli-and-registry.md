# CLI And Registry

Use this reference only when the task involves discovering, installing, publishing, or updating Animus skills.

## Search skills

```bash
animus skill search --query "review"
animus skill search --source user
animus skill search --registry community
```

## Install a skill

```bash
animus skill install --name code-review --registry community
animus skill install --name code-review --version "^1.0" --allow-prerelease
animus skill install --path .animus/skills/code-review/SKILL.md
animus skill install --path .animus/skills/
```

`--path` accepts a Markdown skill file, a single skill folder, or a directory of
skill folders. `--name` is optional when installing from `--path`.

## List skills

```bash
animus skill list
animus skill list --source project
```

## Inspect, update, or uninstall a skill

```bash
animus skill info --name code-review
animus skill update --name code-review --version "^2.0"
animus skill uninstall --name code-review --dry-run
animus skill uninstall --name code-review
```

`info` is the canonical detail verb (`show` remains as an alias). `uninstall` removes an installed skill's materialized files plus its registry/lock entries; it supports `--source` and `--dry-run`.

## Publish a skill

```bash
animus skill publish --name code-review --version "1.0.0" --source my-org --registry community
animus skill publish --name code-review --version "1.0.0" --source github --registry community --artifact ./dist/code-review.tgz --integrity sha256-...
```

## Registry commands

```bash
animus skill registry add --id community --url https://github.com/animus-skills/registry
animus skill registry list
animus skill registry remove --id community
```
