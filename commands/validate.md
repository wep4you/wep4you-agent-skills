---
description: Validate Obsidian vault frontmatter against standards
argument-hint: [--mode auto|report] [--vault path]
allowed-tools: Bash(uv run:*)
---

# Obsidian Vault Validation

Validate an Obsidian vault against frontmatter standards and auto-fix common issues.

## Execution

Run the validator script:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/validate/scripts/validator.py" --vault . --mode report
```

For auto-fix mode, use `--mode auto` instead of `--mode report`.

## Arguments

- `--mode report` - Show issues without fixing (default)
- `--mode auto` - Auto-fix issues automatically
- `--vault <path>` - Obsidian vault path (default: current directory)
- `--config <path>` - Custom configuration file

## Validation Checks

| Check | Description | Auto-Fix |
|-------|-------------|----------|
| Empty Types | `type:` property exists but empty | Yes - infers from folder |
| Missing Properties | Required frontmatter missing | Yes - adds defaults |
| Invalid Daily Links | Full-path instead of basename | Yes |
| Unquoted Wikilinks | `[[link]]` without quotes in YAML | Yes |
| Invalid Created | `created:` as wikilink not date | Yes |
| Title Properties | Redundant `title:` in frontmatter | Yes - removes |
| Date Mismatches | `created:` and `daily:` don't match | Yes - syncs |

## Required Properties

Per vault standards, notes need these 6 properties:
- `type` - Note type (dot, map, source, project, etc.)
- `up` - Parent note link
- `created` - Creation date (YYYY-MM-DD)
- `daily` - Daily note link
- `collection` - Collection classification
- `related` - Related notes
