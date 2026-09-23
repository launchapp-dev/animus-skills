---
name: animus-configuration
description: Locate and reason about Animus configuration sources, precedence, environment variables, secrets, daemon settings, plugin scope, and runtime state paths. Use when determining where a setting comes from or where state is stored; use animus-workflow-authoring for workflow design and animus-portal-operations for hosted Team mutations.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---

# Animus Configuration

Determine the effective authority before proposing an edit. Animus combines a
kernel with independently versioned plugins, so accepted syntax, persisted
state, and runtime enforcement can come from different components.

Use [the configuration reference](references/configuration-reference.md) only
for the section needed by the request:

- project sources and precedence: `animus.toml`, `.animus/config.json`,
  workflow YAML/overlays, skill definitions, plugin scope, and lockfiles;
- repo-scoped runtime state, worktrees, output, caches, and cleanup boundaries;
- daemon configuration, scheduler wake behavior, notifications, and telemetry;
- machine-wide principals, RBAC, packs, plugins, flavors, and update state;
- environment variables, provider/runtime kill switches, and secrets; or
- cost and budget configuration.

## Authority map

- In a normal local project, authored workflow YAML is served by the active
  `config_source` plugin and runtime state belongs under the resolved repo
  scope—not necessarily the current directory.
- In animus-launchapp, Postgres Team config is canonical after first boot;
  image YAML is only seed/release material. Use `animus-portal-operations`
  before mutating it.
- `animus.toml` and the plugin lock describe reproducible installed components;
  ad-hoc runtime plugin changes are not automatically permanent deployment
  configuration.
- Environment variables and compatibility aliases can override or supplement
  files. Inspect the process environment without printing secrets.
- A successful config parse proves shape, not that the deployed plugin or
  workflow runner enforces every field.

## Safe configuration workflow

1. Read project instructions and identify local versus Portal authority.
2. Inspect the installed kernel, relevant plugin, and runner versions.
3. Read the smallest source that can answer the precedence question; do not
   dump credentials or entire state stores.
4. Before writing, identify who owns the file/row, whether another source will
   overwrite it, and what reload/cache mechanism makes it effective.
5. Make the narrowest lossless change, validate, reload when required, and
   re-read the effective value.
6. For secrets, store only references in configuration and use the supported
   secret facility for the value.

Route workflow shape to `animus-workflow-authoring`, plugin installation to
`animus-plugin-operations`, models/providers to `animus-model-operations`, and
runtime evidence to `animus-observability`.
