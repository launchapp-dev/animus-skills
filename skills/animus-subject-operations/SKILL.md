---
name: animus-subject-operations
description: Work with Animus subjects and subject_backend plugins, including task, requirement, Linear, SQLite, Markdown, and custom subject kinds, default_subject_kind, wire ids, and status routing.
user_invocable: false
auto_invoke: true
---

# Subject Operations

Subjects are Animus's generic work items. Tasks, requirements, Linear issues,
SQLite rows, Markdown tasks, and custom external work items all route through
the same subject surface when a `subject_backend` plugin claims the kind.

The legacy `animus task ...`, `animus requirements ...`, `animus.task.*`, and
`animus.requirements.*` surfaces are removed. Use:

```bash
animus subject <command> --kind task
animus subject <command> --kind requirement
```

## Requirements

Subject operations require an installed subject backend plugin:

```bash
animus plugin install-defaults --include-subjects
animus daemon preflight
```

The default subject set includes `subject-default`, `subject-requirements`,
`subject-linear`, `subject-sqlite`, and `subject-markdown`.

There is no in-tree subject fallback after v0.4.12. If
`ANIMUS_DAEMON_DISABLE_SUBJECT_PLUGINS=1` is set, subject calls behave as if no
backend is installed.

## Kind and IDs

`--kind` selects the backend route. When omitted, Animus falls back to
`.animus/config.json` `default_subject_kind`, which defaults to `task`.

Subject ids may be simple local ids or backend-qualified wire ids:

```text
TASK-001
requirement:REQ-004
linear:ENG-123
sqlite:01HX...
```

Prefer using the exact id returned by `subject create`, `subject list`, or the
backend integration.

## CLI Surface

```bash
animus subject list --kind task
animus subject list --kind task --status ready --limit 25
animus subject get --kind task --id TASK-001
animus subject next --kind task
```

Create:

```bash
animus subject create --kind task --title "Fix login bug" --status ready --priority p1
animus subject create --kind requirement --title "SOC2 evidence export" --body "Export audit events" --labels compliance,audit
```

Update:

```bash
animus subject update --kind task --id TASK-001 --status blocked --priority p1
animus subject update --kind task --id TASK-001 --labels backend,urgent
animus subject status --kind task --id TASK-001 --status done
```

The generic CLI update surface currently supports normalized `status`,
`priority`, and replacement `labels`. Backend-specific fields belong in the
backend plugin's own API or `animus plugin call`.

## Normalized Statuses

Common statuses:

```text
ready
in_progress
blocked
done
cancelled
```

Backends may map richer native states into these buckets. Query native fields
through the backend plugin when the normalized status is not enough.

## Queue and Workflow Use

```bash
animus queue enqueue --task-id TASK-001 --workflow-ref animus.task/standard
animus queue enqueue --requirement-id REQ-001 --workflow-ref animus.requirement/standard
animus workflow run animus.task/standard --task-id TASK-001
```

Queue and workflow command flags still use `--task-id` and `--requirement-id`
for compatibility, but the backing data comes from subjects.

## MCP Tools

Use:

- `animus.subject.list`
- `animus.subject.get`
- `animus.subject.create`
- `animus.subject.update`
- `animus.subject.next`
- `animus.subject.status`

Set `kind` to `task`, `requirement`, or the custom kind claimed by the subject
backend plugin.

## Backend Troubleshooting

- `NotFound` for every subject call: no plugin claims that kind, or subject plugins are disabled.
- Daemon refuses to start: run `animus daemon preflight`; install missing subject plugins.
- Unexpected state names: distinguish normalized Animus status from native backend status.
- Missing body/title update support in CLI: use a backend-specific plugin method if exposed.
- Requirements no longer list: use `animus subject list --kind requirement`, not `animus requirements list`.
