---
name: your-skill-name
version: 1.0.0
author: Your Name
license: MIT
description: >-
  Brief description of what this skill does. Include trigger keywords that help Claude
  identify when to use this skill. Describe the main use cases.
---

# Your Skill Name

Brief overview of what this skill does and why it's useful for Obsidian vault management.

## When to Use

Claude should use this skill when:
- User wants to [specific action]
- User mentions [trigger keywords]
- [Additional trigger conditions]

## Usage

### Basic Usage

```bash
# Example command or workflow
uv run scripts/main.py --option value
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--option` | Description of option | `default` |

## Configuration

This skill can be configured via `.claude/config/your-skill.yaml` in the target vault:

```yaml
# Example configuration
setting_name: value
```

## Examples

### Example 1: [Use Case Name]

```markdown
User: "Help me with [specific task]"
Claude: Uses this skill to [perform action]
```

## Requirements

- Python 3.10+
- uv (for script execution)

## See Also

- [Link to related documentation]
- [Link to Obsidian plugin if relevant]
