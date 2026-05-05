---
name: animus-task-management
description: Full task lifecycle — create, list, update, block/unblock, checklists, bulk ops via CLI and MCP
user_invocable: false
auto_invoke: true
---

# Task Management

## Task Lifecycle

```
backlog → todo → ready → in-progress → done
                    ↘ blocked → ready
                    ↘ on-hold → ready
backlog/todo/ready/in-progress → cancelled
```

## CLI Commands

### Create
```bash
animus task create --title "Fix login bug" --priority critical --task-type bugfix
animus task create --title "Add dark mode" --priority medium --task-type feature --description "Support system theme preference"
```

Options:
- `--priority`: critical, high, medium, low
- `--task-type`: feature, bugfix, hotfix, refactor, docs, test, chore, experiment
- `--description`: detailed description
- `--linked-requirement`: repeat to attach requirement ids
- `--linked-architecture-entity`: repeat to attach architecture entities

### List and Filter
```bash
animus task list                          # all tasks
animus task list --status ready           # ready tasks only
animus task list --status blocked         # blocked tasks
animus task list --task-type bugfix       # filter by task type
animus task prioritized                   # sorted by priority
animus task stats                         # aggregate counts by status/priority/type
```

### Get Details
```bash
animus task get --id TASK-001
```

### Update Status
```bash
animus task status --id TASK-001 --status ready
animus task status --id TASK-001 --status in-progress
animus task status --id TASK-001 --status done
animus task status --id TASK-001 --status blocked
animus task status --id TASK-001 --status on-hold
animus task status --id TASK-001 --status cancelled
```

Setting `ready` clears `paused`, `blocked_at`, `blocked_reason`, and `blocked_by`.

### Pause / Resume
```bash
animus task pause --id TASK-001
animus task resume --id TASK-001
```

### Cancel / Reopen
```bash
animus task cancel --id TASK-001 --confirm TASK-001
animus task reopen --id TASK-001 --confirm TASK-001
```

### Set Priority / Deadline
```bash
animus task set-priority --id TASK-001 --priority critical
animus task set-deadline --id TASK-001 --deadline "2026-04-01T00:00:00Z"
```

### Update Content
```bash
animus task update --id TASK-001 --title "Updated title" --description "New details"
```

### Checklists
```bash
animus task checklist-add --id TASK-001 --description "Add unit tests"
animus task checklist-update --id TASK-001 --item-id chk-1 --completed true
```

Use `animus task get --id TASK-001` first to find the checklist `item_id`.

### Dependencies
```bash
animus task dependency-add --id TASK-002 --dependency-id TASK-001 --dependency-type blocked-by
animus task dependency-remove --id TASK-002 --dependency-id TASK-001
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `animus.task.create` | Create a new task |
| `animus.task.get` | Get task details by ID |
| `animus.task.list` | List tasks, filter by status |
| `animus.task.update` | Update task title/description |
| `animus.task.delete` | Delete a task |
| `animus.task.assign` | Assign a task to an agent or human |
| `animus.task.status` | Change task status |
| `animus.task.stats` | Aggregate task metrics |
| `animus.task.prioritized` | Get tasks sorted by priority |
| `animus.task.next` | Get the next recommended task to work on |
| `animus.task.checklist-add` | Add a checklist item |
| `animus.task.checklist-update` | Mark checklist item complete/incomplete |
| `animus.task.bulk-status` | Update multiple task statuses at once |
| `animus.task.bulk-update` | Bulk update multiple tasks |
| `animus.task.pause` | Pause a task |
| `animus.task.resume` | Resume a paused task |
| `animus.task.cancel` | Cancel a task |
| `animus.task.set-priority` | Set task priority |
| `animus.task.set-deadline` | Set or clear task deadline |
| `animus.task.history` | View task dispatch history |

### MCP Examples

```json
// Create a task
{ "title": "Add rate limiting", "priority": "high", "task_type": "feature" }

// List ready tasks
{ "status": "ready" }

// Update status
{ "id": "TASK-042", "status": "done" }

// Bulk status update
{
  "updates": [
    { "id": "TASK-001", "status": "done" },
    { "id": "TASK-002", "status": "cancelled" }
  ]
}
```

## Patterns

### Promoting from Backlog
Tasks start as `backlog`. Promote to `ready` when dependencies are met:
```bash
animus task status --id TASK-005 --status ready
```

### Blocking and Unblocking
When a task can't proceed:
```bash
animus task status --id TASK-005 --status blocked
# Later, when the blocker is resolved:
animus task status --id TASK-005 --status ready
```

### Task Dependencies
Use explicit dependency edges when task ordering matters. They show up in task detail and are respected by prioritization and scheduling logic.

### Workflow Integration
Typical flow:
1. Move the task to `ready`
2. Enqueue it with `animus queue enqueue --task-id TASK-XXX`
3. Run a workflow explicitly or let the daemon pick it up
4. Inspect execution with `animus workflow list`, `animus output run`, and `animus output phase-outputs`
