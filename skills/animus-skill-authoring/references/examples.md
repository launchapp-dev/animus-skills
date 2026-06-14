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

The phase's effective skill set is the union of the phase-level list and the
executing agent profile's `skills:` (phase entries first). Resolution happens
daemon-side at dispatch and rides to the runner via `ANIMUS_PHASE_SKILLS_JSON`
(needs workflow-runner v0.4.2+). A name that does not resolve warns — at
compile time in `animus workflow config validate` and at dispatch in the
daemon log — but never fails the run. Verify with:

```bash
animus output phase-outputs --workflow-id <id>   # Skills: requested / applied / missing
```

## Use a skill on ad-hoc runs

```bash
animus agent run --skill code-review --prompt "Review the diff on this branch."
animus chat send --skill careful-implementer "Refactor the retry loop."
```

The full skill applies (prompt fragments, launch args/env, model, timeout);
an unknown `--skill` name is an error on these paths. Explicit flags such as
`--model` or `--timeout-secs` win over the skill.

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
        - "subject.*"
        - "output.*"
      deny:
        - "queue.drop"
        - "plugin.uninstall"

    model:
      preferred: claude-sonnet-4-6
      fallback: claude-opus-4-8

    mcp_servers:
      - animus
      - context7

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
