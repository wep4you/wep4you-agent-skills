# wep4you-agent-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blueviolet)](https://claude.ai/code)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-1.0-green)](https://agentskills.io)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI%20Codex-Compatible-blue)](https://openai.com)
[![Security](https://img.shields.io/badge/Security-Scanned-brightgreen)](https://github.com/wep4you/wep4you-agent-skills/actions)

A Claude Code skills marketplace following the open [Agent Skills](https://agentskills.io) specification. Cross-platform compatible with Claude Code, OpenAI Codex, and GitHub Copilot.

## Available Skills

### Obsidian

| Skill | Description | Version |
|-------|-------------|---------|
| [validate](skills/validate/) | Validate and auto-fix frontmatter against standards (ACE/LYT/PARA) | 1.2.0 |

## Quick Start

### Claude Code

#### Option 1: Marketplace via `/plugin` (Recommended)

1. Open Claude Code and run `/plugin`
2. Select **"Add Marketplace"**
3. Enter the repository URL:
   ```
   https://github.com/wep4you/wep4you-agent-skills
   ```
4. Press Enter to add the marketplace

Once added, you can:
- Browse available plugins in the **"Marketplaces"** tab
- Select a plugin to see details (version, description, author)
- Choose installation scope:
  - **User scope**: Available in all your projects
  - **Project scope**: Available for all collaborators
  - **Local scope**: Only in this repository
- Update plugins when new versions are available

#### Option 2: Manual Installation

```bash
# Clone and install using the install script
git clone https://github.com/wep4you/wep4you-agent-skills.git
cd wep4you-agent-skills
uv run scripts/install_skills.py --platform claude-code

# Or install specific skill
uv run scripts/install_skills.py --skill validate
```

### OpenAI Codex

```bash
# Clone repository
git clone https://github.com/wep4you/wep4you-agent-skills.git
cd wep4you-agent-skills

# Manually symlink
ln -s $(pwd)/skills/obsidian/* ~/.codex/skills/
```

### GitHub Copilot (Enterprise)

Skills are auto-discovered from `.claude/skills/` in repositories. Symlink or copy skills to your project.

## Requirements

- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Python 3.10+
- [Claude Code](https://claude.ai/code), [OpenAI Codex](https://openai.com), or compatible CLI

## Development

### Setup

```bash
# Clone and install
git clone https://github.com/wep4you/wep4you-agent-skills.git
cd wep4you-agent-skills
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Commands

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run security scan
uv run bandit -r skills/ -ll
uv run pip-audit

# Validate all SKILL.md files
uv run python scripts/validate_skills.py --verbose
```

### Quality Gates

All skills must pass:
- **Ruff**: Linting with security rules (S, B, C90)
- **Bandit**: Python security analysis
- **pip-audit**: CVE vulnerability scanning
- **Tests**: pytest with 90% coverage threshold
- **SKILL.md validation**: Required frontmatter fields

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Creating a New Skill

```bash
# Use the automated setup script
uv run scripts/create_skill.py obsidian my-skill-name --author "Your Name"

# Or manually copy the template
cp -r templates/skill-template skills/obsidian/<skill-name>
```

Then:
1. Edit `SKILL.md` with your skill description
2. Implement your logic in `scripts/main.py`
3. Add tests in `tests/`
4. Run validation: `uv run python scripts/validate_skills.py --verbose`

## Security

This marketplace implements comprehensive security measures:

- **CVE Scanning**: pip-audit checks all dependencies
- **Security Linting**: bandit analyzes code for vulnerabilities
- **Supply Chain Protection**: Dependency hash verification
- **Pre-commit Hooks**: Automated security checks before commits

## Cross-Platform Compatibility

| Platform | Support | Skill Location |
|----------|---------|----------------|
| Claude Code | Native | `~/.claude/skills/` or `.claude/skills/` |
| OpenAI Codex | Native | `~/.codex/skills/` |
| GitHub Copilot | Enterprise | `.claude/skills/` (repo) |
| Cursor | Via MCP | MCP server integration |

## License

MIT License - see [LICENSE](LICENSE) for details.
