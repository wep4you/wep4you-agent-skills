# Agent Instructions

This file provides guidance for AI coding assistants (Claude Code, OpenAI Codex, GitHub Copilot, Cursor) when working with this repository.

## Project Overview

**wep4you-agent-skills** - A skills marketplace following the [Agent Skills specification](https://agentskills.io). Currently focused on Obsidian PKM workflows. Cross-platform compatible with Claude Code, OpenAI Codex, and GitHub Copilot.

## Build & Development Commands

```bash
# Install all dependencies (dev + security)
uv sync --all-extras

# Run linter
uv run ruff check .

# Run formatter
uv run ruff format .

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov --cov-fail-under=90

# Run type checker
uv run mypy skills/ scripts/ --ignore-missing-imports

# Run security scan
uv run bandit -r skills/ -ll --skip B101
uv run pip-audit --strict

# Validate SKILL.md files
uv run python scripts/validate_skills.py --verbose
uv run python scripts/validate_skills.py --json  # CI-friendly output

# Run specific skill
uv run skills/validate/scripts/validator.py --vault /path/to/vault
```

## Architecture

### Directory Structure

```
wep4you-agent-skills/
├── .claude-plugin/
│   ├── marketplace.json       # Marketplace definition
│   └── plugin.json            # Plugin metadata (name, version, author, etc.)
├── commands/
│   └── validate.md            # Slash command (obsidian:validate)
├── skills/
│   └── validate/    # Flat structure (no subcategories)
├── templates/
│   ├── skill-template/        # Generic template
│   └── obsidian/              # Obsidian-specific template
├── scripts/
│   └── validate_skills.py     # SKILL.md validation CLI
└── tests/                     # Pytest test suite
```

### Skill Structure

Each skill in `skills/<skill-name>/` contains:
- `SKILL.md` - Required: name, description, version, author, license in frontmatter
- `scripts/` - Python scripts with PEP 723 inline dependencies
- `config/` - YAML configuration templates
- `references/` - Additional documentation

### PEP 723 Script Format

All skill scripts use inline dependencies:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
```

## Code Style

- **Ruff**: line-length=100, Python 3.10+, security rules enabled (S, B, C90, ANN)
- **Naming**: snake_case for files/functions, PascalCase for classes, kebab-case for skills
- **Type hints**: Required for all functions (mypy strict mode)
- **YAML**: 2-space indentation, quote wikilinks

## Git Workflow

### ⛔ NEVER Push Directly to Main

**ALL changes MUST go through Pull Requests.** Direct pushes to `main` are forbidden.

```bash
# ❌ WRONG - Never do this
git checkout main
git commit -m "..."
git push  # FORBIDDEN!

# ✅ CORRECT - Always use feature branches
git worktree add ../wep4you-agent-skills-wt/feature-name -b feature/feature-name
cd ../wep4you-agent-skills-wt/feature-name
# ... make changes ...
git push -u origin feature/feature-name
# Create PR on GitHub, get review, merge
```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

## Commit Messages

- Use conventional commits format: `type(scope): description`
- Types: feat, fix, chore, docs, refactor, test, style
- Keep subject line under 72 characters
- **DO NOT include** "Generated with Claude Code" or "Co-Authored-By: Claude" signatures
- Focus on what changed and why, not how it was generated

## Security Requirements

All skills must pass:
1. **ruff** with security rules (S)
2. **bandit** security linting
3. **pip-audit** CVE scanning
4. **mypy** type checking
5. Pre-commit hooks for automated checks

## CI/CD Pipeline

GitHub Actions runs these jobs:
- `lint` - ruff check + format + uv.lock validation
- `security` - bandit + pip-audit + safety
- `test` - pytest across Python 3.10, 3.11, 3.12
- `typecheck` - mypy strict
- `validate-skills` - SKILL.md + config validation

### Running CI Locally

Before pushing code, run all CI checks locally to catch issues early:

```bash
# 1. Linting (required)
uv run ruff check .           # Must pass with no errors
uv run ruff format --check .  # Must show "X files already formatted"

# 2. Type checking (required)
uv run mypy skills/ scripts/ --ignore-missing-imports

# 3. Security scanning (required)
uv run bandit -r skills/ -ll --skip B101  # Skip assert warnings
uv run pip-audit                          # Check for CVEs

# 4. Tests (required)
uv run pytest                 # All tests must pass

# 5. Skill validation (required)
uv run python scripts/validate_skills.py --verbose  # Warnings OK, errors fail
```

### Quick CI Check (All-in-One)

```bash
# Run all checks in sequence (stops on first failure)
uv run ruff check . && \
uv run ruff format --check . && \
uv run mypy skills/ scripts/ --ignore-missing-imports && \
uv run bandit -r skills/ -ll --skip B101 && \
uv run pip-audit && \
uv run pytest && \
uv run python scripts/validate_skills.py --verbose

# Success output: "All 7 SKILL.md file(s) validated successfully"
```

### Common CI Fixes

**Ruff errors (E501, F401, etc.)**
```bash
uv run ruff check . --fix    # Auto-fix where possible
uv run ruff format .         # Format all files
```

**Mypy type errors**
- Add type hints to function parameters and return values
- Use `TextIO | None` instead of `Any` for file-like objects
- Import types from `typing` module

**Bandit security warnings (S603, S607)**
- Use absolute paths for subprocess calls: `/usr/bin/env`
- Add `# noqa: S603` only for trusted internal paths

**Skill validation errors**
- Ensure SKILL.md `name` field uses kebab-case (e.g., `obsidian-commands`)
- Include required frontmatter: name, description, version, license

---

## UV Best Practices

### Creating New Skills

Use the automated setup script:

```bash
# Create a new skill from template
uv run scripts/create_skill.py <category> <skill-name>

# Examples
uv run scripts/create_skill.py obsidian vault-backup --author "Your Name"
uv run scripts/create_skill.py obsidian link-checker --description "Check broken links"
```

### PEP 723 Inline Dependencies

All skill scripts MUST use PEP 723 inline script metadata:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
#     "requests>=2.31",
# ]
# ///
```

**Key rules:**
- Always specify `requires-python = ">=3.10"`
- Pin minimum versions with `>=` (e.g., `pyyaml>=6.0`)
- Keep dependencies minimal - only what the script needs
- Use the shebang `#!/usr/bin/env -S uv run --script` for direct execution

### Lock File Management

```bash
# Check if uv.lock is in sync with pyproject.toml
uv lock --check

# Update lock file after changing dependencies
uv lock

# Sync environment with lock file
uv sync
```

**CI enforces** `uv lock --check` - PRs will fail if lock file is out of sync.

### Running Skills

```bash
# Run a skill script directly (uses inline dependencies)
uv run skills/validate/scripts/validator.py --vault /path

# Or make it executable
chmod +x skills/validate/scripts/validator.py
./skills/validate/scripts/validator.py --vault /path
```

---

## Cross-Platform Compatibility

This skills marketplace is compatible with multiple AI coding assistants.

### Supported Platforms

| Platform | Config Location | Status |
|----------|-----------------|--------|
| Claude Code | `~/.claude/skills/` | ✅ Primary |
| OpenAI Codex | `~/.openai/codex/skills/` | ✅ Supported |
| GitHub Copilot | `~/.github/copilot/skills/` | ✅ Supported |
| Cursor | `~/.cursor/skills/` | ✅ Supported |

### Installation

```bash
# Install all skills for Claude Code (default)
uv run scripts/install_skills.py

# Install for specific platform
uv run scripts/install_skills.py --platform codex
uv run scripts/install_skills.py --platform copilot

# Selective installation by category
uv run scripts/install_skills.py --category obsidian

# Install specific skill only
uv run scripts/install_skills.py --skill validate

# Combine filters
uv run scripts/install_skills.py --platform codex --category obsidian

# List available skills
uv run scripts/install_skills.py --list
uv run scripts/install_skills.py --list --json  # JSON format

# Copy instead of symlink (for distribution)
uv run scripts/install_skills.py --copy
```

### Selective Installation Patterns

**By Category**: Install only skills from a specific domain:
```bash
uv run scripts/install_skills.py --category obsidian   # PKM/note-taking
```

**By Skill**: Install a single skill:
```bash
uv run scripts/install_skills.py --skill validate
```

**Combined**: Platform + Category + Skill filters can be combined:
```bash
uv run scripts/install_skills.py --platform copilot --category obsidian
```

### Platform-Specific Notes

**Claude Code**: Skills are auto-discovered from `~/.claude/skills/`. Use SKILL.md frontmatter for triggers.

**OpenAI Codex**: Place skills in `~/.openai/codex/skills/`. Codex uses similar discovery patterns.

**GitHub Copilot**: Skills go in `~/.github/copilot/skills/`. Compatible with Agent Skills spec.

**Cursor**: Uses `~/.cursor/skills/`. Full PEP 723 inline dependency support.

---

## Development Workflow: TDD + Beads + SubAgents

### 1. TDD - Test Driven Development (MANDATORY)

**EVERY task MUST follow this cycle:**

```
+-------------------------------------------------------------+
|  1. RED:   Write tests FIRST -> Tests MUST FAIL             |
|  2. GREEN: Implement code -> ONLY until tests pass          |
|  3. REFACTOR: Improve code -> Tests stay green              |
+-------------------------------------------------------------+
```

**Rules:**
- Tests FIRST - no code without prior tests
- Tests MUST initially fail - green tests at creation = wrong tests
- Terminal AND Claude Code modes must be tested
- No shortcuts - TDD is NOT skipped

### 2. Beads - Task Planning & Tracking

This project uses **beads** (`bd`) for issue tracking. Issues are stored in `.beads/` and tracked in git.

**Use Beads for:**
- Multi-session tasks
- Tasks with dependencies
- Discovered work during implementation

#### Quick Reference

```bash
bd ready              # Find available work (no blockers)
bd list --status=open # All open issues
bd show <id>          # View issue details
bd create --title="..." --type=task --priority=2
bd update <id> --status=in_progress
bd close <id>         # Complete work
bd close <id1> <id2>  # Close multiple at once
bd sync               # Sync with git remote
```

#### Bead Structure for Autonomous SubAgents

```markdown
## Goal
[Clear, measurable goal]

## TDD - Tests FIRST
[Concrete test cases to create]

## To Create / To Change
[Table with files and changes]

## Success Criteria
[Checkboxes with verifiable criteria]

## Ralph-Wiggum Start
[Complete command with --max-iterations 20]
```

#### Workflow Pattern

1. **Start**: Run `bd ready` to find actionable work
2. **Claim**: Use `bd update <id> --status=in_progress`
3. **Work**: Implement the task
4. **Complete**: Use `bd close <id>`
5. **Sync**: Always run `bd sync` at session end

#### Key Concepts

- **Dependencies**: Issues can block other issues. `bd ready` shows only unblocked work.
- **Priority**: P0=critical, P1=high, P2=medium, P3=low, P4=backlog (use numbers, not words)
- **Types**: task, bug, feature, epic, question, docs

### 3. SubAgent Control (Ralph-Wiggum)

**Principle:** Main-Agent controls only, SubAgents work.

```
Main Agent (Orchestration)
├── bd ready -> Get next Bead
├── bd show <id> -> Check details
├── /ralph-wiggum:ralph-loop "..." -> Start SubAgent
│   └── SubAgent works autonomously (max 20 iterations)
│       └── Output: <promise>BEAD X DONE</promise>
├── bd close <id> -> Close Bead
└── Continue to next Bead
```

**Rules for Main-Agent:**
1. NO code changes in Main-Agent - only orchestration
2. Beads must contain ALL info for autonomous SubAgent
3. After each Bead: `bd close <id>` + brief summary

#### Ralph-Wiggum Usage

When using Ralph-Wiggum loops, **both** the `--completion-promise` flag AND the `<promise>` tag in the prompt are required:

```bash
# CORRECT - Promise flag matches promise tag text
/ralph-wiggum:ralph-loop "Do task X. When done, output <promise>TASK DONE</promise>" --completion-promise "TASK DONE" --max-iterations 20

# WRONG - Missing --completion-promise flag (runs infinitely!)
/ralph-wiggum:ralph-loop "Do task X. Output <promise>TASK DONE</promise> when done."

# WRONG - Promise text doesn't match flag
/ralph-wiggum:ralph-loop "Output <promise>COMPLETE</promise>" --completion-promise "DONE"
```

**Key rules:**
1. Always set `--completion-promise "TEXT"` flag
2. The TEXT must exactly match what's between `<promise>TEXT</promise>` in prompt
3. Always set `--max-iterations 20` (standard for feature tasks)
4. Use short, unique promise texts (e.g., "BEAD 1 DONE", "TESTS PASS")

---

## Plugin Versioning

**CRITICAL:** When bumping versions, you MUST update BOTH files:

1. `.claude-plugin/plugin.json` → `"version": "X.Y.Z"` (Claude Code reads this!)
2. `skills/<skill>/SKILL.md` → `version: "X.Y.Z"` (Skill metadata)

### Version Bump Checklist

```bash
# 1. Update plugin.json (Claude Code uses this for updates)
# Edit .claude-plugin/plugin.json → "version": "X.Y.Z"

# 2. Update SKILL.md for changed skills
# Edit skills/<skill>/SKILL.md → version: "X.Y.Z"

# 3. Commit both changes together
git add .claude-plugin/plugin.json skills/*/SKILL.md
git commit -m "chore: Bump version to X.Y.Z"
```

### Why Both Files?

- **plugin.json**: Claude Code marketplace reads this to detect updates
- **SKILL.md**: Individual skill metadata for documentation and discovery

If you only update SKILL.md, Claude Code won't detect the new version!

---

## Session Completion Protocol

**When ending a work session**, complete ALL steps below. Work is NOT complete until `git push` succeeds.

### Mandatory Checklist

```bash
# 1. Check status
git status

# 2. Stage and commit code
git add <files>
git commit -m "..."

# 3. Sync beads
bd sync

# 4. Push to remote (MANDATORY)
git push

# 5. Verify
git status  # MUST show "up to date with origin"
```

### Critical Rules

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- If push fails, resolve and retry until it succeeds
- Create issues for any remaining/discovered work before ending session

---

## Git Worktree Best Practices

This project uses **git worktrees** for parallel feature development. Following this structure prevents conflicts and keeps the main directory stable.

### Directory Structure

```
/Users/<user>/dev/
├── wep4you-agent-skills/           # Main repo - ALWAYS on 'main' branch
│   └── .beads/                     # Beads database (shared across worktrees)
└── wep4you-agent-skills-wt/        # Worktree parent directory
    ├── feature-auth/               # Feature worktree
    ├── fix-validation/             # Bugfix worktree
    └── ...
```

### Key Rules

1. **Main directory stays on `main`**: Never checkout feature branches in the main repo directory
2. **Worktrees in sibling folder**: All feature work happens in `../wep4you-agent-skills-wt/`
3. **One branch per worktree**: Each worktree tracks exactly one branch
4. **Beads shared**: The `.beads/` database in main repo is accessible from all worktrees

### Creating a Feature Worktree

```bash
# From main repo directory
cd /Users/<user>/dev/wep4you-agent-skills

# Create new feature branch + worktree
git worktree add ../wep4you-agent-skills-wt/feature-name -b feature/feature-name

# Or checkout existing remote branch
git worktree add ../wep4you-agent-skills-wt/feature-name feature/feature-name
```

### Working in a Worktree

```bash
# Switch to worktree
cd ../wep4you-agent-skills-wt/feature-name

# Work normally - commits go to the feature branch
git add .
git commit -m "feat: add feature"
git push -u origin feature/feature-name

# Beads commands work (finds .beads in main repo)
bd ready
bd sync
```

### Cleaning Up After Merge

```bash
# From main repo
cd /Users/<user>/dev/wep4you-agent-skills

# Remove worktree (after PR merged)
git worktree remove ../wep4you-agent-skills-wt/feature-name

# Delete local branch
git branch -d feature/feature-name

# Clean up any stale worktree references
git worktree prune
```

### Listing Worktrees

```bash
git worktree list
```

### Troubleshooting

**"fatal: 'feature/x' is already checked out"**
→ Branch is in use by another worktree. Use `git worktree list` to find it.

**Beads not found in worktree**
→ Run `bd` commands from main repo, or ensure `.beads/` symlink exists.

**Worktree folder exists but branch deleted**
→ Run `git worktree prune` to clean up orphaned references.

<!-- bv-agent-instructions-v1 -->

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Dolt-powered version control with native sync
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs via Dolt:

- Each write auto-commits to Dolt history
- Use `bd dolt push`/`bd dolt pull` for remote sync
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- END BEADS INTEGRATION -->
