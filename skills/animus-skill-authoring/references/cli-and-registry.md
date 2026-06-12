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
```

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
```

## Registry commands

```bash
animus skill registry add --id community --url https://github.com/animus-skills/registry
animus skill registry list
animus skill registry remove --id community
```
