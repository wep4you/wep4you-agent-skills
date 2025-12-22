---
name: your-skill-name
version: 1.0.0
author: Your Name
license: MIT
description: >-
  Brief description of what this Obsidian skill does. Include trigger keywords
  like "vault", "frontmatter", "markdown", "notes", "PKM" to help Claude identify
  when to use this skill.
---

# Your Skill Name

Brief overview of what this skill does for Obsidian vault management.

## When to Use

Claude should use this skill when:
- User wants to manage their Obsidian vault
- User mentions frontmatter, wikilinks, or markdown formatting
- User needs to validate or fix vault issues
- [Additional trigger conditions]

## Usage

### Basic Usage

```bash
uv run scripts/main.py --vault /path/to/vault
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--vault` | Path to Obsidian vault | Current directory |
| `--config` | Path to configuration file | Auto-detect |
| `--verbose` | Enable verbose output | False |

## Configuration

This skill can be configured via `.claude/config/your-skill.yaml` in the vault:

```yaml
# Obsidian-specific configuration
vault:
  daily_notes_folder: "Daily Notes"
  templates_folder: "Templates"

# Skill-specific settings
setting_name: value
```

## Examples

### Example 1: Basic Vault Operation

```markdown
User: "Help me with my Obsidian vault"
Claude: Uses this skill to [perform action]
```

## Requirements

- Python 3.10+
- uv (for script execution)
- Obsidian vault with standard structure

## See Also

- [Obsidian Documentation](https://help.obsidian.md/)
- [Frontmatter Specification](https://help.obsidian.md/Editing+and+formatting/Properties)
