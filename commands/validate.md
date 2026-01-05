---
name: obsidian:validate
description: Validate Obsidian vault frontmatter against standards
argument-hint: [--fix] [--type <type>] [--vault path]
allowed-tools: Bash(uv run:*)
---

# obsidian:validate - Vault Validation

Validate Obsidian vault frontmatter and auto-fix common issues.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault .
```

## Options

### Auto-Fix Mode
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --fix
```
Automatically fix all detected issues. Creates JSONL audit log.

### Filter by Note Type
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --type project
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --type daily --fix
```
Validate only notes of a specific type (based on folder hints).

### Filter by Path
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --path Atlas/
```
Validate only notes in a specific path.

### Save Report
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --report validation-report.md
```
Save detailed validation report to a markdown file.

### Disable Audit Logging
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --no-jsonl
```
Skip JSONL audit logging (enabled by default).

## Validation Checks

| Check | Description | Auto-Fix |
|-------|-------------|----------|
| Missing Frontmatter | Note has no frontmatter block | No |
| Empty Types | `type:` property is empty | Yes - infers from folder |
| Missing Properties | Required properties missing | Yes - adds defaults |
| Invalid Daily Links | Full-path instead of basename | Yes |
| Unquoted Wikilinks | `[[link]]` without quotes | Yes - adds quotes |
| Invalid Created | `created:` as wikilink | Yes - converts to date |
| Title Properties | Redundant `title:` | Yes - removes |
| Date Mismatches | `created:` and `daily:` differ | Yes - syncs |

## Required Properties

From settings.yaml, notes typically need these core properties:
- `type` - Note type (dot, map, source, project, etc.)
- `up` - Parent note link (quoted wikilink)
- `created` - Creation date (YYYY-MM-DD)
- `daily` - Daily note link (quoted, basename only)
- `collection` - Collection classification
- `related` - Related notes list

## Audit Logging

By default, validation results are logged to:
`.claude/logs/validate.jsonl`

Each line contains:
- Timestamp
- Vault path
- Mode (report/auto)
- Issues found by type
- Fixes applied

## Examples

Basic validation:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault .
```

Fix all issues:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --fix
```

Validate only projects:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault . --type project --fix
```

Full validation with report:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validate_command.py" --vault ~/notes --fix --report report.md
```

## Deprecated Flags

| Deprecated | Replacement |
|------------|-------------|
| `--mode auto` | `--fix` |
| `--mode report` | (default, no flag needed) |
