# wep4you-agent-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blueviolet)](https://claude.ai/code)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-1.0-green)](https://agentskills.io)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI%20Codex-Compatible-blue)](https://openai.com)
[![Security](https://img.shields.io/badge/Security-Scanned-brightgreen)](https://github.com/wep4you/wep4you-agent-skills/actions)

**Repository**: [github.com/wep4you/wep4you-agent-skills](https://github.com/wep4you/wep4you-agent-skills)

A Claude Code skills marketplace following the open [Agent Skills](https://agentskills.io) specification. Cross-platform compatible with Claude Code, OpenAI Codex, and GitHub Copilot.

## Available Skills

### Obsidian Plugin (v1.0.0)

Complete PKM (Personal Knowledge Management) toolkit for Obsidian vaults.

| Skill | Description | Version |
|-------|-------------|---------|
| [init](skills/init/) | Initialize vault with methodology wizard (PARA, LYT-ACE, Zettelkasten, Minimal) | 1.0.0 |
| [config](skills/config/) | Configuration loader and settings management with backup | 1.0.0 |
| [validate](skills/validate/) | Validate and auto-fix frontmatter with JSONL audit logging | 1.0.0 |
| [note-types](skills/note-types/) | Manage note type definitions (folders, properties, templates) | 1.0.0 |
| [frontmatter](skills/frontmatter/) | Manage frontmatter properties for note types | 1.0.0 |
| [templates](skills/templates/) | Create, view, and manage note templates | 1.0.0 |

## Complete Slash Command Reference

All commands use the unified `obsidian:` namespace (v1.0.0+).

### Vault Initialization

| Command | Description | Example |
|---------|-------------|---------|
| `/obsidian:init` | Initialize vault with wizard | `/obsidian:init ~/my-vault` |
| `/obsidian:init --list` | List methodologies | |
| `/obsidian:init --git` | Initialize with git repo | |

### Configuration (`/obsidian:config`)

| Command | Description | Example |
|---------|-------------|---------|
| `/obsidian:config` | Show configuration | |
| `/obsidian:config show` | Show config (verbose) | `/obsidian:config show --verbose` |
| `/obsidian:config show --format json` | JSON output | |
| `/obsidian:config validate` | Validate settings.yaml | |
| `/obsidian:config create` | Create new settings | `/obsidian:config create --methodology para` |
| `/obsidian:config methodologies` | List methodologies | |
| `/obsidian:config edit` | Open in editor | |
| `/obsidian:config diff` | Compare with defaults | |

### Validation (`/obsidian:validate`)

| Command | Description | Example |
|---------|-------------|---------|
| `/obsidian:validate` | Validate frontmatter | |
| `/obsidian:validate --fix` | Auto-fix issues | |
| `/obsidian:validate --type project` | Validate note type | |
| `/obsidian:validate --path Atlas/` | Validate path | |
| `/obsidian:validate --report report.md` | Save report | |

### Note Types (`/obsidian:types`)

| Command | Description | Example |
|---------|-------------|---------|
| `/obsidian:types` | List all types | |
| `/obsidian:types list` | List all types | |
| `/obsidian:types show project` | Show type details | |
| `/obsidian:types add meeting` | Add new type | `/obsidian:types add meeting --config '{...}'` |
| `/obsidian:types edit project` | Edit type | |
| `/obsidian:types remove meeting` | Remove type | |
| `/obsidian:types wizard` | Interactive wizard | |

### Properties (`/obsidian:props`)

| Command | Description | Example |
|---------|-------------|---------|
| `/obsidian:props` | List core properties | |
| `/obsidian:props core` | List core properties | |
| `/obsidian:props core add rank` | Add core property | |
| `/obsidian:props core remove rank` | Remove core property | |
| `/obsidian:props type project` | Type properties | |
| `/obsidian:props required` | Required properties | `/obsidian:props required --type project` |
| `/obsidian:props types` | All types with props | |

### Templates (`/obsidian:templates`)

| Command | Description | Example |
|---------|-------------|---------|
| `/obsidian:templates` | List templates | |
| `/obsidian:templates list` | List templates | |
| `/obsidian:templates show map/basic` | Show content | |
| `/obsidian:templates create meeting` | Create template | |
| `/obsidian:templates edit meeting` | Edit template | |
| `/obsidian:templates delete meeting` | Delete template | |
| `/obsidian:templates apply map/basic Note.md` | Apply template | `/obsidian:templates apply map/basic Note.md --var title=MyNote` |

## Key Features

- **Single Source of Truth**: `.claude/settings.yaml` manages all configuration
- **Automatic Backups**: Config changes create timestamped backups in `.claude/backups/`
- **JSONL Audit Logging**: Validation results logged to `.claude/logs/validate.jsonl`
- **Multi-Methodology Support**: PARA, LYT-ACE, Zettelkasten, Minimal
- **Auto-Fix**: Validator can automatically fix common frontmatter issues

## Quick Start (Claude Code)

1. Open Claude Code and run `/plugin`
2. Select **"Add Marketplace"** and enter: `https://github.com/wep4you/wep4you-agent-skills`
3. Install the **"obsidian"** plugin

**Done!** Use `/obsidian:init` to set up your vault.

<details>
<summary>Alternative Installation Methods</summary>

### Development Mode

```bash
claude --plugin-dir /path/to/wep4you-agent-skills
```

### OpenAI Codex

```bash
git clone https://github.com/wep4you/wep4you-agent-skills.git
ln -s $(pwd)/wep4you-agent-skills/skills/* ~/.codex/skills/
```

</details>

## Requirements

- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Python 3.10+
- [Claude Code](https://claude.ai/code), [OpenAI Codex](https://openai.com), or compatible CLI

## Development

### Setup

```bash
git clone https://github.com/wep4you/wep4you-agent-skills.git
cd wep4you-agent-skills
uv sync --all-extras
uv run pre-commit install
```

### Commands

```bash
# Run tests with coverage
uv run pytest --cov --cov-fail-under=88

# Run linter
uv run ruff check .

# Run type checker
uv run mypy skills/ --ignore-missing-imports

# Run security scan
uv run bandit -r skills/ -ll --skip B101

# Validate all SKILL.md files
uv run python scripts/validate_skills.py --verbose
```

### Quality Gates

All skills must pass:
- **Ruff**: Linting with security rules (S, B, C90)
- **Mypy**: Static type checking
- **Bandit**: Python security analysis
- **pip-audit**: CVE vulnerability scanning
- **Tests**: pytest with 88% coverage threshold
- **SKILL.md validation**: Required frontmatter fields

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

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
