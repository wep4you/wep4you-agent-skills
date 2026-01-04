#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Validate Command - Simplified vault validation

Provides a simplified interface for vault validation:
- obsidian:validate            Validate vault (report mode)
- obsidian:validate --fix      Validate and auto-fix issues
- obsidian:validate --type X   Validate only specific note type

Usage:
    uv run validate_command.py --vault /path/to/vault
    uv run validate_command.py --vault /path/to/vault --fix
    uv run validate_command.py --vault /path/to/vault --type project
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import validator from same directory
sys.path.insert(0, str(Path(__file__).parent))
from validator import VaultValidator

# ANSI colors
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


def show_mode_deprecation() -> None:
    """Show deprecation warning for --mode flag."""
    warning = f"""
{COLOR_YELLOW}{COLOR_BOLD}DEPRECATION WARNING{COLOR_RESET}
{COLOR_YELLOW}The '--mode auto' flag is deprecated and will be removed in v2.0.0.{COLOR_RESET}
{COLOR_CYAN}Use '--fix' instead.{COLOR_RESET}
"""
    print(warning, file=sys.stderr)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian Vault Validator (obsidian:validate)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Options:
  --fix              Auto-fix issues (replaces --mode auto)
  --type <type>      Validate only a specific note type
  --path <path>      Validate only a specific path
  --report <file>    Save report to file
  --no-jsonl         Disable audit logging

Examples:
  %(prog)s --vault .
  %(prog)s --vault . --fix
  %(prog)s --vault . --type project
  %(prog)s --vault ~/notes --fix --report report.md
        """,
    )

    parser.add_argument(
        "--vault",
        type=str,
        default=".",
        help="Path to vault (default: current directory)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues (replaces --mode auto)",
    )
    parser.add_argument(
        "--mode",
        choices=["report", "auto", "interactive"],
        help=argparse.SUPPRESS,  # Hidden - deprecated
    )
    parser.add_argument(
        "--type",
        dest="note_type",
        help="Validate only specific note type",
    )
    parser.add_argument(
        "--path",
        help="Validate only specific path",
    )
    parser.add_argument(
        "--report",
        metavar="FILE",
        help="Save report to file",
    )
    parser.add_argument(
        "--no-jsonl",
        action="store_true",
        help="Disable JSONL audit logging",
    )
    parser.add_argument(
        "--jsonl",
        metavar="FILE",
        help="Custom path for JSONL audit log",
    )

    args = parser.parse_args()

    # Handle --mode deprecation
    mode = "report"
    if args.fix:
        mode = "auto"
    elif args.mode:
        if args.mode == "auto":
            show_mode_deprecation()
        mode = args.mode

    # Create validator
    validator = VaultValidator(args.vault, mode)

    # Filter by note type if specified
    path_filter = args.path
    if args.note_type and validator.settings:
        # Get folder hints for the specified type
        note_types = validator.settings.note_types
        if args.note_type in note_types:
            config = note_types[args.note_type]
            if config.folder_hints:
                # Use first folder hint as path filter
                path_filter = config.folder_hints[0]
                print(f"📂 Filtering to type '{args.note_type}' ({path_filter})")
        else:
            print(f"⚠️  Unknown note type: {args.note_type}")
            print(f"   Available: {', '.join(note_types.keys())}")

    # Run validation
    summary = validator.run_validation(path_filter)
    fixes_applied = 0

    # Run fixes if in auto mode
    if mode == "auto" and summary["total_issues"] > 0:
        fixes_applied = validator.run_fixes()

        # Re-validate
        print("\n🔄 Re-validating after fixes...\n")
        validator.issues = {k: [] for k in validator.issues.keys()}
        validator.run_validation(path_filter)

    # Generate report if requested
    if args.report:
        validator.generate_report(args.report)

    # Log to JSONL by default
    if not args.no_jsonl:
        jsonl_path = args.jsonl if args.jsonl else None
        validator.log_to_jsonl(jsonl_path, fixes_applied)

    # Exit code based on remaining issues
    remaining_issues = sum(len(v) for v in validator.issues.values())
    return 0 if remaining_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
