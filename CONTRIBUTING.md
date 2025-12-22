# Contributing to Obsidian Skills Marketplace

Thank you for your interest in contributing! This document provides guidelines for contributing skills and improvements.

## Ways to Contribute

1. **Submit a new skill** - Create a skill for Obsidian workflows
2. **Improve existing skills** - Bug fixes, features, documentation
3. **Report issues** - Bug reports and feature requests
4. **Improve documentation** - Clarifications, examples, translations

## Skill Submission Guidelines

### Requirements

- [ ] Skill follows the [Agent Skills specification](https://agentskills.io)
- [ ] SKILL.md has required frontmatter (`name`, `description`)
- [ ] Skill name uses kebab-case (e.g., `my-awesome-skill`)
- [ ] Works with standard Obsidian vaults
- [ ] Includes documentation for configuration options
- [ ] Python scripts use uv inline dependencies (PEP 723)

### Skill Structure

```
skills/your-skill-name/
├── SKILL.md              # Required: Skill definition
├── scripts/              # Optional: Python/Bash scripts
│   └── main.py
├── config/               # Optional: Configuration templates
│   └── default.yaml
└── references/           # Optional: Documentation
    └── guide.md
```

### SKILL.md Template

```markdown
---
name: your-skill-name
description: Clear description of what this skill does and when to use it. Include trigger keywords.
---

# Your Skill Name

Brief overview of the skill.

## Usage

How to use the skill.

## Configuration

Configuration options if applicable.
```

## Development Workflow

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/obsidian-skills.git
cd obsidian-skills
```

### 2. Create a Branch

```bash
git checkout -b feature/my-new-skill
```

### 3. Develop Your Skill

- Create your skill in `skills/your-skill-name/`
- Test locally with your Obsidian vault
- Ensure all scripts work with `uv run`

### 4. Test

```bash
# Run tests (if applicable)
uv run pytest

# Validate skill structure
/plugin validate skills/your-skill-name
```

### 5. Submit Pull Request

- Write a clear PR description
- Reference any related issues
- Ensure CI passes

## Code Style

### Python
- Use type hints
- Follow PEP 8
- Use uv inline script dependencies (PEP 723)

### Markdown
- Use clear headings
- Include code examples
- Keep lines under 100 characters

### YAML
- Use 2-space indentation
- Quote strings with special characters

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Skill folder | kebab-case | `validate` |
| Python files | snake_case | `validator.py` |
| Config files | kebab-case | `default-config.yaml` |
| Functions | snake_case | `validate_frontmatter()` |
| Classes | PascalCase | `VaultValidator` |

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open an issue or start a discussion. We're here to help!
