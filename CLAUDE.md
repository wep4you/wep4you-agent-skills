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

## Ralph-Wiggum Usage (WICHTIG)

When using Ralph-Wiggum loops, **both** the `--completion-promise` flag AND the `<promise>` tag in the prompt are required:

```bash
# CORRECT - Promise flag matches promise tag text
/ralph-wiggum:ralph-loop "Do task X. When done, output <promise>TASK DONE</promise>" --completion-promise "TASK DONE" --max-iterations 10

# WRONG - Missing --completion-promise flag (runs infinitely!)
/ralph-wiggum:ralph-loop "Do task X. Output <promise>TASK DONE</promise> when done."

# WRONG - Promise text doesn't match flag
/ralph-wiggum:ralph-loop "Output <promise>COMPLETE</promise>" --completion-promise "DONE"
```

**Key rules:**
1. Always set `--completion-promise "TEXT"` flag
2. The TEXT must exactly match what's between `<promise>TEXT</promise>` in prompt
3. Always set `--max-iterations N` as safety fallback
4. Use short, unique promise texts (e.g., "FIX 1 COMPLETE", "TESTS PASS")
