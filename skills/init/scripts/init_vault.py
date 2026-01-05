#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Vault Initializer

Creates a new Obsidian vault with a chosen PKM methodology and settings.yaml configuration.

Usage:
    # Interactive mode (prompts for methodology)
    uv run init_vault.py --vault /path/to/vault

    # Flag-based mode (specify methodology)
    uv run init_vault.py --vault /path/to/vault --methodology lyt-ace

    # Dry-run mode (show what would be created)
    uv run init_vault.py --vault /path/to/vault --methodology para --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Add repository root to path for importing methodology loader
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config.methodologies.loader import METHODOLOGIES  # noqa: E402
from skills.core.models import WizardConfig  # noqa: E402
from skills.core.utils import apply_ranking_system  # noqa: E402
from skills.core.vault import (  # noqa: E402
    create_folder_structure,
    create_gitignore,
    init_git_repo,
)
from skills.init.scripts.content_generators import (  # noqa: E402
    create_agent_docs,
    create_all_bases_file,
    create_folder_mocs,
    create_home_note,
    create_readme,
    create_sample_notes,
    create_settings_yaml,
    create_template_notes,
)
from skills.init.scripts.vault_utils import reset_vault  # noqa: E402
from skills.init.scripts.wizard import (  # noqa: E402
    detect_existing_vault,
    prompt_existing_vault_action,
    wizard_full_flow,
    wizard_step_git_init,
    wizard_step_git_reset,
)

# =============================================================================
# Git Operations
# =============================================================================


def git_commit_changes(vault_path: Path, message: str, dry_run: bool = False) -> bool:
    """Commit all changes to an existing git repository."""
    git_path = shutil.which("git")
    if not git_path:
        print("  Git not found in PATH")
        return False

    if not (vault_path / ".git").exists():
        print("  Not a git repository")
        return False

    if dry_run:
        print(f'[DRY RUN] Would commit: "{message}"')
        return True

    try:
        subprocess.run(  # noqa: S603
            [git_path, "add", "."],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(  # noqa: S603
            [git_path, "status", "--porcelain"],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            print("  No changes to commit")
            return True
        subprocess.run(  # noqa: S603
            [git_path, "commit", "-m", message],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f'Committed changes: "{message}"')
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Git commit failed: {e}")
        return False


# =============================================================================
# Main Initialization
# =============================================================================


def print_methodologies() -> None:
    """Print available methodologies."""
    print("\nAvailable methodologies:\n")
    for key, method in METHODOLOGIES.items():
        print(f"  {key:15} - {method['name']}")
        print(f"  {' ' * 17} {method['description']}")
        print(f"  {' ' * 17} Folders: {', '.join(method['folders'])}\n")


def choose_methodology_interactive() -> str:  # pragma: no cover
    """Interactively choose a methodology."""
    print_methodologies()
    while True:
        choice = input("Select methodology (lyt-ace/para/zettelkasten/minimal): ").strip().lower()
        if choice in METHODOLOGIES:
            return choice
        print(f"Invalid choice: {choice}. Please try again.")


def show_migration_hint(has_existing_content: bool) -> None:
    """Show hint about future migration feature."""
    if has_existing_content:
        print("\n" + "-" * 40)
        print("NOTE: Migration Feature Coming Soon")
        print("-" * 40)
        print("Your existing content remains untouched.")


def init_vault(
    vault_path: Path,
    methodology: str | None = None,
    dry_run: bool = False,
    use_wizard: bool = False,
    use_defaults: bool = False,
    note_types_filter: list[str] | None = None,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
    ranking_system: str = "rank",
) -> None:
    """Initialize an Obsidian vault with chosen methodology."""
    detection = detect_existing_vault(vault_path)
    has_existing = detection["exists"] and detection["has_content"]

    if not dry_run:
        vault_path.mkdir(parents=True, exist_ok=True)

    config: WizardConfig | None = None

    if use_wizard and methodology is None:
        config = wizard_full_flow(vault_path)
        if config is None:
            return
        methodology = config.methodology
        note_types = dict(config.note_types)
        for type_name, type_config in config.custom_note_types.items():
            note_types[type_name] = type_config.to_dict()
        note_types = apply_ranking_system(note_types, config.ranking_system)
        core_properties = config.core_properties
        create_samples = config.create_samples
    else:
        if has_existing and not use_defaults:
            print()
            print(f"  Vault: {vault_path}")
            action = prompt_existing_vault_action(detection)
            if action == "abort":
                print("\n  Initialization cancelled.")
                return
            if action == "reset":
                reset_vault(vault_path)

        if methodology is None:
            methodology = choose_methodology_interactive()

        method_config = METHODOLOGIES[methodology]
        note_types = method_config["note_types"]
        note_types = apply_ranking_system(note_types, ranking_system)
        core_properties = method_config["core_properties"]
        create_samples = True

    if note_types_filter:
        note_types = {k: v for k, v in note_types.items() if k in note_types_filter}

    print(f"\n{'=' * 60}")
    print(f"Initializing vault at: {vault_path}")
    print(f"Methodology: {METHODOLOGIES[methodology]['name']}")
    print(f"{'=' * 60}")

    if dry_run:
        print("\n*** DRY RUN MODE - No files will be created ***\n")

    # Create vault structure and content
    create_folder_structure(vault_path, methodology, dry_run, note_types_filter)
    create_settings_yaml(
        vault_path,
        methodology,
        dry_run,
        config,
        note_types_filter,
        core_properties_filter,
        custom_properties,
        per_type_properties,
    )
    create_readme(vault_path, methodology, dry_run)
    create_home_note(vault_path, methodology, dry_run)
    create_agent_docs(vault_path, methodology, dry_run)

    if create_samples:
        create_sample_notes(
            vault_path,
            methodology,
            note_types,
            core_properties,
            dry_run,
            core_properties_filter,
            custom_properties,
            per_type_properties,
        )

    create_template_notes(
        vault_path,
        methodology,
        note_types,
        core_properties,
        dry_run,
        core_properties_filter,
        custom_properties,
        per_type_properties,
    )
    create_all_bases_file(vault_path, methodology, dry_run)
    create_folder_mocs(vault_path, methodology, dry_run, note_types_filter)
    create_gitignore(vault_path, dry_run)

    if config is not None and config.init_git:
        print("\nInitializing git repository...")
        method_config = METHODOLOGIES[methodology]
        init_git_repo(vault_path, f"Initial vault setup with {method_config['name']}", dry_run)

    if has_existing:
        show_migration_hint(has_existing)

    print(f"\n{'=' * 60}")
    print("Vault initialization complete!")
    print(f"{'=' * 60}")

    if not dry_run:
        print(f"\nYour vault is ready at: {vault_path}")
        print("\nNext steps:")
        print("  1. Open the vault in Obsidian")
        print("  2. Explore the sample notes")
        print("  3. Run validation: /obsidian:validate")


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


def main() -> int:  # pragma: no cover
    """Main entry point."""
    import json
    import os

    from_wrapper = os.environ.get("INIT_FROM_WRAPPER") == "1"
    raw_args = sys.argv[1:]

    has_methodology = "-m" in raw_args or "--methodology" in raw_args
    is_query = "--list" in raw_args or "--list-note-types" in raw_args or "--check" in raw_args

    if has_methodology and not from_wrapper and not is_query:
        error_msg = {
            "error": "Direct call not allowed",
            "message": "This script must be called through the wrapper.",
        }
        print(json.dumps(error_msg, indent=2))
        return 1

    parser = argparse.ArgumentParser(
        description="Initialize an Obsidian vault with a PKM methodology",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("vault", type=Path, nargs="?", help="Path to the vault")
    parser.add_argument("--vault", type=Path, dest="vault_legacy", help=argparse.SUPPRESS)
    parser.add_argument("-m", "--methodology", choices=list(METHODOLOGIES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true", help="List available methodologies")
    parser.add_argument("--wizard", action="store_true")
    parser.add_argument("--defaults", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--git", action="store_true")
    parser.add_argument("--git-keep", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--list-note-types", metavar="METHODOLOGY")
    parser.add_argument("--note-types", help="Comma-separated list of note types")
    parser.add_argument("--core-properties", help="Comma-separated list of core properties")
    parser.add_argument("--custom-properties", help="Comma-separated list of custom properties")
    parser.add_argument("--per-type-props", help="Per-type properties")
    parser.add_argument("--ranking-system", choices=["rank", "priority"], default="rank")

    args = parser.parse_args()

    if args.list:
        print_methodologies()
        return 0

    if args.list_note_types:
        methodology = args.list_note_types
        if methodology not in METHODOLOGIES:
            print(json.dumps({"error": f"Unknown methodology: {methodology}"}))
            return 1
        note_types = METHODOLOGIES[methodology].get("note_types", {})
        print(json.dumps(note_types, indent=2))
        return 0

    vault_path = args.vault or args.vault_legacy

    if not vault_path:
        print("Error: Vault path is required.", file=sys.stderr)
        return 1

    detection = detect_existing_vault(vault_path)
    has_existing = detection["exists"] and detection["has_content"]

    if args.check:
        if not detection["exists"]:
            status = "empty"
        elif not detection["has_content"]:
            status = "new"
        else:
            status = "existing"

        result = {
            "status": status,
            "path": str(vault_path),
            "folders": detection["folder_count"],
            "files": detection["file_count"],
            "has_obsidian": detection["has_obsidian"],
            "has_claude_config": detection["has_claude_config"],
        }
        print(json.dumps(result, indent=2))
        return 0

    needs_interactive = (
        args.wizard
        or (args.methodology is None and not args.defaults)
        or (args.reset and not args.defaults)
        or (has_existing and not args.defaults)
    )

    if needs_interactive and not is_interactive():
        result = {
            "error": "interactive_required",
            "message": "Use: init_vault.py <path> -m <methodology> --defaults",
            "path": str(vault_path),
            "has_existing_content": has_existing,
        }
        print(json.dumps(result, indent=2))
        return 0

    use_wizard = args.wizard or (args.methodology is None and not args.defaults)
    git_action_after_reset = None

    if args.reset:
        if detection["exists"]:
            print(f"\nResetting vault at: {vault_path}")
            if is_interactive():
                confirm = input("Are you sure? (yes/no): ")
                if confirm.strip().lower() != "yes":
                    print("Reset cancelled.")
                    return 0

            git_existed = (vault_path / ".git").exists()

            # Handle git reset: if --git is passed and .git exists, delete it
            if git_existed and args.git:
                shutil.rmtree(vault_path / ".git")
                print("  - Removed: .git/ (will be re-initialized)")
            # Interactive mode without --git flag
            elif git_existed and not args.git and not use_wizard and is_interactive():
                git_action_after_reset = wizard_step_git_reset()
                if git_action_after_reset == "reset":
                    shutil.rmtree(vault_path / ".git")
                    print("  - Removed: .git/")

            reset_vault(vault_path)

            if not git_existed and not args.git and not use_wizard and is_interactive():
                if wizard_step_git_init():
                    git_action_after_reset = "init"

    # Parse filters
    note_types_filter = None
    if args.note_types:
        note_types_filter = [t.strip() for t in args.note_types.split(",") if t.strip()]

    core_properties_filter = None
    if args.core_properties:
        core_properties_filter = [p.strip() for p in args.core_properties.split(",") if p.strip()]

    custom_properties_list = None
    if args.custom_properties:
        custom_properties_list = [p.strip() for p in args.custom_properties.split(",") if p.strip()]

    per_type_properties: dict[str, list[str]] = {}
    if args.per_type_props:
        for type_spec in args.per_type_props.split(";"):
            if ":" in type_spec:
                type_name, props = type_spec.split(":", 1)
                type_name = type_name.strip()
                prop_list = [p.strip() for p in props.split(",") if p.strip()]
                if type_name and prop_list:
                    per_type_properties[type_name] = prop_list

    try:
        init_vault(
            vault_path,
            args.methodology,
            args.dry_run,
            use_wizard=use_wizard,
            use_defaults=args.defaults,
            note_types_filter=note_types_filter,
            core_properties_filter=core_properties_filter,
            custom_properties=custom_properties_list,
            per_type_properties=per_type_properties if per_type_properties else None,
            ranking_system=args.ranking_system,
        )

        if not use_wizard:
            methodology_name = args.methodology or "minimal"
            if args.git or git_action_after_reset in ("init", "reset"):
                print("\nInitializing git repository...")
                method_config = METHODOLOGIES[methodology_name]
                commit_msg = f"Initial vault setup with {method_config['name']}"
                init_git_repo(vault_path, commit_msg, args.dry_run)
            elif args.git_keep or git_action_after_reset == "keep":
                print("\nCommitting changes...")
                commit_msg = f"Vault updated with {methodology_name}"
                git_commit_changes(vault_path, commit_msg, args.dry_run)

        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except EOFError:
        print("\nInteractive input required. Use --defaults for non-interactive mode.")
        return 1
    except KeyboardInterrupt:
        print("\n\nInitialization cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
