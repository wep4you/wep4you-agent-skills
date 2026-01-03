# wep4you-agent-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blueviolet)](https://claude.ai/code)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-1.0-green)](https://agentskills.io)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI%20Codex-Compatible-blue)](https://openai.com)
[![Security](https://img.shields.io/badge/Security-Scanned-brightgreen)](https://github.com/wep4you/wep4you-agent-skills/actions)

A Claude Code skills marketplace following the open [Agent Skills](https://agentskills.io) specification. Cross-platform compatible with Claude Code, OpenAI Codex, and GitHub Copilot.

## Available Skills

### Obsidian Plugin (v0.60.0)

Complete PKM (Personal Knowledge Management) toolkit for Obsidian vaults.

| Skill | Description | Version |
|-------|-------------|---------|
| [init](skills/init/) | Initialize vault with methodology wizard (PARA, LYT-ACE, Zettelkasten, Minimal) | 0.31.0 |
| [config](skills/config/) | Configuration loader and settings management with backup | 0.5.0 |
| [validate](skills/validate/) | Validate and auto-fix frontmatter with JSONL audit logging | 1.6.0 |
| [note-types](skills/note-types/) | Manage note type definitions (folders, properties, templates) | 0.53.0 |
| [frontmatter](skills/frontmatter/) | Manage frontmatter properties for note types | 1.0.0 |
| [templates](skills/templates/) | Create, view, and manage note templates | 1.0.0 |

### Slash Commands

After installing the plugin, these commands are available:

**Vault Initialization**
| Command | Description |
|---------|-------------|
| `/obsidian:init` | Initialize vault with interactive wizard |

**Configuration Management**
| Command | Description |
|---------|-------------|
| `/obsidian:config-show` | Show vault settings from `.claude/settings.yaml` |
| `/obsidian:config-validate` | Validate settings.yaml structure |
| `/obsidian:config set KEY VALUE` | Set a config value (with backup) |
| `/obsidian:config diff` | Show differences from defaults |
| `/obsidian:config reset METHODOLOGY` | Reset to a methodology |

**Validation**
| Command | Description |
|---------|-------------|
| `/obsidian:validate` | Validate vault frontmatter (auto-fix available) |

**Note Types**
| Command | Description |
|---------|-------------|
| `/obsidian:note-types list` | List all note types |
| `/obsidian:note-types add NAME` | Add new note type with folder + template |
| `/obsidian:note-types edit NAME` | Edit note type (renames folders, updates frontmatter) |
| `/obsidian:note-types remove NAME` | Remove a note type |

**Frontmatter**
| Command | Description |
|---------|-------------|
| `/frontmatter list` | List all core properties |
| `/frontmatter list --type NAME` | Show properties for a note type |
| `/frontmatter add --property NAME --type TYPE` | Add property to note type |
| `/frontmatter remove --property NAME --type TYPE` | Remove property from note type |

**Templates**
| Command | Description |
|---------|-------------|
| `/templates list` | List all templates |
| `/templates show NAME` | Show template content |
| `/templates create --name NAME --type TYPE` | Create new template |
| `/templates delete --name NAME` | Delete template |

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
