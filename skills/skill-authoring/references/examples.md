# Examples

Use this reference when you need a fuller example or workflow composition pattern.

## Use skills in agent profiles

```yaml
agents:
  my-reviewer:
    skills:
      - code-review
      - security-review
    tool: claude
    model: claude-sonnet-4-6
```

## Use skills on a phase

```yaml
phases:
  security-audit:
    mode: agent
    agent_id: my-reviewer
    directive: "Audit the codebase for security issues."
    skills:
      - security-review
```

## Complete implementation skill

```yaml
skills:
  careful-implementer:
    name: careful-implementer
    version: "1.0.0"
    description: Implementation skill that prioritizes correctness over speed.
    category: implementation

    prompt:
      system: |
        You are a careful software engineer. Before writing code:
        1. Read existing tests to understand expected behavior
        2. Check for similar patterns in the codebase
        3. Write code that follows existing conventions
        4. Run tests before committing
        5. Commit with descriptive messages
      directives:
        - Never modify test files unless the task explicitly requires it
        - Always check for existing utility functions before writing new ones
        - Use the project's existing error handling patterns

    tool_policy:
      allow:
        - "Read"
        - "Write"
        - "Edit"
        - "Glob"
        - "Grep"
        - "Bash"
        - "task.*"
        - "output.*"
      deny:
        - "task.delete"
        - "requirements.delete"

    model:
      preferred: claude-sonnet-4-6
      fallback:
        - claude-opus-4-6

    mcp_servers:
      - animus      - context7

    capabilities:
      writes_files: true
      mutates_state: true
      requires_commit: true

    adapters:
      gemini:
        model: gemini-3.1-pro-preview
        prompt_override:
          suffix: "Use your 1M context window to read broadly before making changes."

    tags: ["implementation", "careful", "quality"]
```
