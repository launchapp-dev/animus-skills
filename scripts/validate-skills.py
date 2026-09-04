#!/usr/bin/env python3
"""Validate the portable Animus Agent Skills bundle without third-party packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOP_LEVEL_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
STRING_META_RE = re.compile(r'^  ([A-Za-z0-9_-]+):\s*"([^"\n]*)"\s*$')
QUOTED_VALUE_RE = re.compile(r'^  ([A-Za-z0-9_-]+):\s*"([^"\n]*)"\s*$', re.M)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ALLOWED_TOP_LEVEL = {"name", "description", "license", "metadata"}
EXPLICIT_ONLY = {"animus-bootstrap", "animus-setup"}


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def frontmatter(path: Path) -> tuple[dict[str, str], list[str], int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must begin with ---")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter has no closing ---") from exc

    values: dict[str, str] = {}
    top_keys: list[str] = []
    for line in lines[1:end]:
        match = TOP_LEVEL_RE.match(line)
        if match:
            key, value = match.groups()
            top_keys.append(key)
            values[key] = unquote(value or "")
    return values, top_keys, len(lines)


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    name = path.parent.name
    try:
        values, top_keys, line_count = frontmatter(path)
    except ValueError as exc:
        return [str(exc)]

    unknown = sorted(set(top_keys) - ALLOWED_TOP_LEVEL)
    if unknown:
        errors.append(f"unsupported portable frontmatter: {', '.join(unknown)}")
    declared = values.get("name", "")
    if not NAME_RE.fullmatch(declared):
        errors.append(f"invalid name: {declared!r}")
    if declared != name:
        errors.append(f"name {declared!r} does not match directory {name!r}")

    description = values.get("description", "")
    if not 1 <= len(description) <= 1024:
        errors.append("description must contain 1-1024 characters")
    if not re.search(r"\bUse (?:when|only when|for)\b", description):
        errors.append("description must state an explicit use condition")
    if values.get("license") != "MIT":
        errors.append("license must be MIT")
    if line_count > 400:
        errors.append(f"SKILL.md has {line_count} lines; repository limit is 400")

    raw = path.read_text(encoding="utf-8").splitlines()
    end = raw.index("---", 1)
    if "metadata" not in values:
        errors.append("missing metadata map")
    else:
        in_metadata = False
        metadata: dict[str, str] = {}
        for line in raw[1:end]:
            if line == "metadata:":
                in_metadata = True
                continue
            if in_metadata and line and not line.startswith("  "):
                in_metadata = False
            if in_metadata and line.strip():
                match = STRING_META_RE.match(line)
                if not match:
                    errors.append(f"metadata value is not a quoted string: {line.strip()}")
                    continue
                metadata[match.group(1)] = match.group(2)
        if metadata.get("animus-version") != "0.7.0-rc.50":
            errors.append("metadata.animus-version must be 0.7.0-rc.50")

    sidecar = path.parent / "agents" / "openai.yaml"
    if not sidecar.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        sidecar_text = sidecar.read_text(encoding="utf-8")
        fields = dict(QUOTED_VALUE_RE.findall(sidecar_text))
        display = fields.get("display_name", "")
        short = fields.get("short_description", "")
        prompt = fields.get("default_prompt", "")
        if not 1 <= len(display) <= 64:
            errors.append("openai display_name must contain 1-64 characters")
        if not 25 <= len(short) <= 64:
            errors.append("openai short_description must contain 25-64 characters")
        if f"${name}" not in prompt:
            errors.append(f"openai default_prompt must mention ${name}")
        policy = re.search(
            r"^policy:\n  allow_implicit_invocation: (true|false)$", sidecar_text, re.M
        )
        if not policy:
            errors.append("openai sidecar needs a boolean implicit-invocation policy")
        else:
            expected = "false" if name in EXPLICIT_ONLY else "true"
            if policy.group(1) != expected:
                errors.append(
                    f"openai implicit-invocation policy must be {expected} for {name}"
                )

    return errors


def validate_links(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in skill_dir.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            file_part = target.split("#", 1)[0]
            if file_part and not (path.parent / file_part).resolve().exists():
                errors.append(f"{path.relative_to(ROOT)}: broken link {target}")
    return errors


def main() -> int:
    failures: list[str] = []
    skill_dirs = sorted(path for path in SKILLS.iterdir() if (path / "SKILL.md").is_file())
    for skill_dir in skill_dirs:
        for error in validate_skill(skill_dir / "SKILL.md"):
            failures.append(f"{skill_dir.name}: {error}")
        failures.extend(validate_links(skill_dir))

    if failures:
        for failure in failures:
            print(f"ERROR {failure}")
        print(f"\n{len(failures)} validation error(s) across {len(skill_dirs)} skills")
        return 1

    print(f"Validated {len(skill_dirs)} portable skills and Codex sidecars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
