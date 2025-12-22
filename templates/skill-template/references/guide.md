# Skill Development Guide

This document provides guidance for developing this skill.

## Structure

```
your-skill-name/
├── SKILL.md              # Skill definition (required)
├── scripts/              # Python/Bash scripts
│   └── main.py           # Main entry point
├── config/               # Configuration templates
│   └── default.yaml      # Default configuration
└── references/           # Documentation
    └── guide.md          # This file
```

## Development Workflow

1. Copy this template to `skills/your-skill-name/`
2. Update `SKILL.md` with your skill's details
3. Implement your logic in `scripts/main.py`
4. Test with your Obsidian vault
5. Submit a Pull Request

## Testing Locally

```bash
# Run the script directly
uv run scripts/main.py ~/path/to/your/vault

# With verbose output
uv run scripts/main.py -v ~/path/to/your/vault

# With custom config
uv run scripts/main.py -c config/default.yaml ~/path/to/your/vault
```

## Best Practices

1. **Use PEP 723 inline dependencies** - Keep dependencies in the script header
2. **Handle errors gracefully** - Provide clear error messages
3. **Support configuration** - Allow customization via YAML config
4. **Document thoroughly** - Include usage examples in SKILL.md
5. **Follow naming conventions** - Use kebab-case for skill names
