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

## Show or update a skill

```bash
animus skill show --name code-review
animus skill update --name code-review --version "^2.0"
```

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
