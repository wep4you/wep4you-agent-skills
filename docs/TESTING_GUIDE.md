# Testing Guide

This guide explains how to test skills locally before submitting them.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- An Obsidian vault for testing
- [Claude Code](https://claude.ai/code) CLI (optional, for integration testing)

## Test Structure

The test suite is organized into three main directories:

```
tests/
├── unit/              # Unit tests - fast, isolated tests
│   └── core/          # Core module tests
│       ├── generation/    # Content generation tests
│       ├── models/        # Data model tests
│       ├── prompts/       # Prompt handling tests
│       ├── settings/      # Settings loader tests
│       ├── utils/         # Utility function tests
│       └── vault/         # Vault detection tests
├── integration/       # Integration tests - test module interactions
│   └── scripts/       # Script integration tests
├── e2e/               # End-to-end tests - full workflow tests
└── fixtures/          # Test fixtures and helpers
    ├── valid/         # Valid test files
    └── invalid/       # Invalid test files for error testing
```

### Unit Tests (`tests/unit/`)

Unit tests verify individual functions and classes in isolation. These tests:
- Run fast (no I/O, no network)
- Test single units of code
- Use mocks for external dependencies
- Should be the majority of your tests

Example structure:
```
tests/unit/core/
├── conftest.py           # Shared fixtures for unit tests
├── generation/
│   ├── test_content.py   # Content generation tests
│   ├── test_frontmatter.py
│   ├── test_moc.py
│   └── test_templates.py
├── models/
│   ├── test_note_type.py
│   └── test_wizard.py
├── prompts/
│   └── test_init_prompts.py
├── settings/
│   └── test_loader.py
├── utils/
│   ├── test_paths.py
│   └── test_ranking.py
└── vault/
    ├── test_detection.py
    ├── test_git.py
    └── test_structure.py
```

### Integration Tests (`tests/integration/`)

Integration tests verify that modules work together correctly:
- Test script execution with real file I/O
- Test module interactions
- May use temporary directories
- Run slower than unit tests

```
tests/integration/
└── scripts/
    ├── test_create_skill.py
    ├── test_extract_dependencies.py
    ├── test_init_validate_integration.py
    ├── test_install_skills.py
    ├── test_settings_loader.py
    ├── test_validate_skills.py
    └── test_verify_dependencies.py
```

### End-to-End Tests (`tests/e2e/`)

E2E tests verify complete workflows from user perspective:
- Test full command execution
- Test CLI interfaces
- May create real vaults
- Slowest tests, run sparingly

### Test Fixtures (`tests/fixtures/`)

Shared test data and helpers:

```
tests/fixtures/
├── valid/
│   ├── minimal-valid.md    # Minimal valid frontmatter
│   └── valid-note.md       # Complete valid note
└── invalid/
    ├── date-mismatch.md    # Date validation error
    ├── has-title.md        # Redundant title property
    ├── missing-type.md     # Missing required type
    └── unquoted-wikilink.md # Unquoted wikilink error
```

## Running Tests

### Run All Tests

```bash
# From the repository root
uv run pytest

# With verbose output
uv run pytest -v

# With coverage
uv run pytest --cov --cov-fail-under=88
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Specific module tests
uv run pytest tests/unit/core/generation/

# Single test file
uv run pytest tests/unit/core/models/test_note_type.py

# Single test function
uv run pytest tests/unit/core/models/test_note_type.py::test_note_type_creation
```

### Run with Markers

```bash
# Skip slow tests
uv run pytest -m "not slow"

# Only integration tests
uv run pytest -m integration
```

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

## Writing Tests

### TDD Workflow (MANDATORY)

Follow the Red-Green-Refactor cycle:

1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Clean up while keeping tests green

```python
# Example TDD cycle

# 1. RED - Write failing test
def test_note_type_has_description():
    note_type = NoteType(name="project")
    assert note_type.description == "Project notes"

# 2. GREEN - Implement minimal code
@dataclass
class NoteType:
    name: str
    description: str = "Project notes"

# 3. REFACTOR - Improve if needed
@dataclass
class NoteType:
    name: str
    description: str = field(default_factory=lambda: f"{name.title()} notes")
```

### Test Both Modes

Always test both terminal and non-interactive modes:

```python
def test_wizard_terminal_mode(mock_tty):
    """Test interactive mode in terminal."""
    result = run_wizard(interactive=True)
    assert result.status == "completed"

def test_wizard_non_interactive_mode():
    """Test JSON output in Claude Code."""
    result = run_wizard(interactive=False)
    assert "interactive_required" in result
    assert result["action"] == "add"
```

## Validation Checklist

Before submitting a skill, verify:

- [ ] `SKILL.md` exists with `name` and `description` in frontmatter
- [ ] Scripts run successfully with `uv run`
- [ ] No hardcoded paths (use relative paths or CLI arguments)
- [ ] Works with a fresh Obsidian vault
- [ ] Error messages are clear and actionable
- [ ] Configuration options are documented
- [ ] Unit tests cover core functionality
- [ ] Integration tests cover script execution
- [ ] Both terminal and non-interactive modes tested

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

### Tests failing in CI but passing locally

- Check Python version compatibility (3.10, 3.11, 3.12)
- Ensure all dependencies are in `pyproject.toml`
- Check for path separator issues (Windows vs Unix)

## Coverage Requirements

- **Minimum coverage**: 88%
- **Unit tests**: Should cover all public functions
- **Integration tests**: Should cover main workflows
- **Edge cases**: Test error handling and boundary conditions
