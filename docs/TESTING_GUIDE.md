# Testing Guide

This guide explains how to test skills locally before submitting them.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- An Obsidian vault for testing
- [Claude Code](https://claude.ai/code) CLI (optional, for integration testing)

## Testing Python Scripts

### Direct Execution

Skills use PEP 723 inline script dependencies, so uv handles everything:

```bash
# Navigate to the skill directory
cd skills/validate

# Run the main script
uv run scripts/validator.py ~/path/to/your/vault
```

### With Custom Configuration

```bash
# Copy default config to your vault
cp config/default.yaml ~/path/to/your/vault/.claude/config/validator.yaml

# Edit the config as needed
# Then run with the config
uv run scripts/validator.py ~/path/to/your/vault
```

## Integration Testing with Claude Code

### Install Skill Locally

Use symlink to test skills without installation:

```bash
# Create symlink in your vault's .claude/skills directory
mkdir -p ~/path/to/your/vault/.claude/skills
ln -s ~/dev/obsidian-skills/skills/validate \
      ~/path/to/your/vault/.claude/skills/validate
```

### Invoke in Claude Code

Start Claude Code in your vault and use the skill:

```
cd ~/path/to/your/vault
claude

> Validate my vault frontmatter
# Claude should pick up the skill and use it
```

## Running Tests

If the skill includes pytest tests:

```bash
# From the repository root
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/test_validator.py
```

## Validation Checklist

Before submitting a skill, verify:

- [ ] `SKILL.md` exists with `name` and `description` in frontmatter
- [ ] Scripts run successfully with `uv run`
- [ ] No hardcoded paths (use relative paths or CLI arguments)
- [ ] Works with a fresh Obsidian vault
- [ ] Error messages are clear and actionable
- [ ] Configuration options are documented

## Common Issues

### "Module not found" errors

Ensure dependencies are listed in the PEP 723 header:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
```

### Script not executable

Check the shebang line:

```python
#!/usr/bin/env -S uv run --script
```

### Configuration not loading

Verify the config path matches what's documented in SKILL.md.
