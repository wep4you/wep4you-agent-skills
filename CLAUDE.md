# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

> **Primary documentation**: See [AGENTS.md](AGENTS.md) for complete project instructions, commands, and workflows.

## Claude-Specific Notes

- Use `uv run` for all Python commands (not `python` directly)
- Prefer parallel tool calls when operations are independent
- Use the Task tool with `subagent_type=Explore` for codebase exploration
- Always run `bd sync` before ending a session

## Quick Reference

```bash
# Essential commands
uv sync --all-extras        # Install dependencies
uv run pytest               # Run tests
uv run ruff check .         # Lint
bd ready                    # Find work
bd sync                     # Sync issues
```

For full documentation, architecture, and workflows, see [AGENTS.md](AGENTS.md).
