#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Vault Validator & Auto-Fix Tool
Validates Obsidian vault against standards and auto-fixes common issues
Version: 2.0.0 - Refactored to use skills.core modules

Usage:
    uv run scripts/validator.py --vault /path/to/vault
    uv run scripts/validator.py --vault . --mode auto
    uv run scripts/validator.py --vault . --no-jsonl  # Disable audit logging
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Import local modules (must be before conditional imports per E402)
from skills.validate.scripts.auto_fix import AutoFixer  # noqa: E402
from skills.validate.scripts.reporter import ValidationReporter  # noqa: E402

# Try to import from skills.core (preferred)
CORE_AVAILABLE = False
try:
    from skills.core.models import NoteTypeConfig, Settings
    from skills.core.settings import (
        infer_note_type_from_path,
        load_settings,
        should_exclude,
    )

    CORE_AVAILABLE = True
except ImportError:
    # Fallback: Try legacy settings_loader for backward compatibility
    Settings = None  # type: ignore[misc,assignment]
    NoteTypeConfig = None  # type: ignore[misc,assignment]
    try:
        _config_scripts = Path(__file__).parent.parent.parent / "config" / "scripts"
        if str(_config_scripts) not in sys.path:
            sys.path.insert(0, str(_config_scripts))
        from settings_loader import (  # type: ignore[no-redef]
            Settings,
            infer_note_type_from_path,
            load_settings,
        )
        from settings_loader import (
            should_exclude as _settings_should_exclude,
        )

        # Wrap for consistent interface — signature must match core version
        def should_exclude(
            settings: Settings,
            file_path: Path,
            vault_path: Path | None = None,
        ) -> bool:
            result: bool = _settings_should_exclude(settings, file_path)
            return result

        CORE_AVAILABLE = True
    except ImportError:
        pass


def get_note_type(settings: Settings, type_name: str) -> NoteTypeConfig | None:
    """Get note type configuration by name."""
    return settings.note_types.get(type_name)


def get_core_properties(settings: Settings) -> list[str]:
    """Get core properties from settings."""
    return settings.core_properties


class VaultValidator:
    """Main validator class with settings.yaml support and code block detection"""

    def __init__(self, vault_path: str, mode: str = "report"):
        self.vault_path = Path(vault_path)
        self.mode = mode  # report, auto, interactive

        # Load settings.yaml (single source of truth)
        self.settings: Settings | None = None
        if CORE_AVAILABLE:
            try:
                self.settings = load_settings(self.vault_path)
                print(f"  Using settings.yaml (methodology: {self.settings.methodology})")
            except FileNotFoundError:
                print("  No settings.yaml found - using defaults")
            except Exception as e:
                print(f"  Error loading settings.yaml: {e}")

        # Use hardcoded defaults for auto_fix settings
        self.auto_fix_config = {
            "empty_types": True,
            "daily_links": True,
            "wikilink_quotes": True,
            "invalid_created": True,
            "title_properties": True,
            "date_mismatches": True,
            "missing_properties": True,
        }

        self.issues: dict[str, list[str]] = {
            "missing_frontmatter": [],  # Files with no frontmatter at all
            "empty_types": [],
            "missing_properties": [],  # Files missing required frontmatter properties
            "invalid_daily_links": [],
            "unquoted_wikilinks": [],
            "invalid_created": [],
            "title_properties": [],
            "date_mismatches": [],
            "type_mismatches": [],
            "folder_underscores": [],
        }

        # Set required_properties from settings or fallback
        if self.settings and CORE_AVAILABLE:
            self.required_properties = get_core_properties(self.settings)
        else:
            self.required_properties = ["type", "up", "created", "daily", "collection", "related"]

        self.fixed_count = 0
        self.skipped_files = 0

        # Load type rules from settings or use defaults
        self.type_rules: dict[str, str]
        if self.settings:
            self.type_rules = self._build_type_rules_from_settings()
        else:
            self.type_rules = {
                "Atlas/Maps/": "map",
                "Atlas/Dots/": "dot",
                "Atlas/Sources/": "source",
                "+/copilot-conversations/": "conversation",
                "+/": "source",
                "Efforts/Projects/": "project",
                "Efforts/Works/": "work",
                "Efforts/Areas/": "area",
                "Calendar/daily/": "daily",
                "Calendar/weekly/": "weekly",
                "Calendar/monthly/": "monthly",
            }

        # Initialize auto-fixer and reporter
        methodology = self.settings.methodology if self.settings else "default"
        self.auto_fixer = AutoFixer(
            self.vault_path,
            self.auto_fix_config,
            self.infer_type,
        )
        self.reporter = ValidationReporter(
            self.vault_path,
            self.mode,
            methodology,
        )

    def _build_type_rules_from_settings(self) -> dict[str, str]:
        """Build type_rules dict from settings.yaml note_types."""
        rules: dict[str, str] = {}
        if not self.settings:
            return rules

        for type_name, config in self.settings.note_types.items():
            for folder_hint in config.folder_hints:
                rules[folder_hint] = type_name

        return rules

    def _get_required_properties_for_type(self, type_name: str | None) -> list[str]:
        """Get required properties for a specific note type."""
        if not type_name or not self.settings or not CORE_AVAILABLE:
            return self.required_properties

        note_type = get_note_type(self.settings, type_name)
        if note_type:
            return note_type.required_properties

        return self.required_properties

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from validation"""
        # Use settings.yaml if available
        if self.settings and CORE_AVAILABLE:
            return should_exclude(self.settings, file_path, self.vault_path)

        # Fall back to default exclusions
        relative_path = str(file_path.relative_to(self.vault_path))

        # Default exclude paths
        default_exclude_paths = ["x/", ".obsidian/", ".git/", ".claude/"]
        for pattern in default_exclude_paths:
            if pattern in relative_path:
                return True

        # Exclude system files in vault root
        default_exclude_files = ["AGENTS.md", "CLAUDE.md", "README.md"]
        if file_path.name in default_exclude_files and file_path.parent == self.vault_path:
            return True

        return False

    def scan_vault(self, path_filter: str | None = None) -> list[Path]:
        """Scan vault for markdown files"""
        pattern = f"{path_filter}**/*.md" if path_filter else "**/*.md"

        files = []
        for md_file in self.vault_path.glob(pattern):
            # Skip excluded files
            if self.should_exclude_file(md_file):
                self.skipped_files += 1
                continue
            files.append(md_file)

        return files

    def extract_frontmatter_only(self, content: str) -> str | None:
        """Extract only the frontmatter section, excluding code blocks"""
        lines = content.split("\n")
        frontmatter_lines = []
        in_frontmatter = False
        frontmatter_count = 0

        for line in lines:
            if line.strip() == "---":
                frontmatter_count += 1
                if frontmatter_count == 1:
                    in_frontmatter = True
                    frontmatter_lines.append(line)
                elif frontmatter_count == 2:
                    frontmatter_lines.append(line)
                    break
            elif in_frontmatter:
                frontmatter_lines.append(line)

        return "\n".join(frontmatter_lines) if frontmatter_lines else None

    def validate_file(self, file_path: Path) -> dict[str, list[str]]:
        """Run all validation checks on a single file"""
        file_issues: dict[str, list[str]] = {}

        try:
            content = file_path.read_text()
            relative_path = str(file_path.relative_to(self.vault_path))

            # Extract frontmatter only (excluding code blocks in content)
            frontmatter = self.extract_frontmatter_only(content)
            if not frontmatter:
                # No frontmatter - this is an error, all notes must have frontmatter
                self.issues["missing_frontmatter"].append(relative_path)
                return file_issues

            # Check 1: Empty type field (only in frontmatter)
            if re.search(r"^type:\s*$", frontmatter, re.MULTILINE):
                self.issues["empty_types"].append(relative_path)

            # Check 1b: Missing required properties
            # Get type-specific required properties if settings.yaml is available
            inferred_type = self.infer_type(relative_path)
            required_props = self._get_required_properties_for_type(inferred_type)

            # Skip Calendar daily notes (they have type: daily and don't need all properties)
            is_daily_note = bool(re.search(r"^type:\s*daily\s*$", frontmatter, re.MULTILINE))
            if not is_daily_note:
                missing = []
                for prop in required_props:
                    # Check if property exists (with or without value)
                    if not re.search(rf"^{prop}:", frontmatter, re.MULTILINE):
                        missing.append(prop)
                if missing:
                    msg = f"{relative_path} (missing: {', '.join(missing)})"
                    self.issues["missing_properties"].append(msg)

            # Check 2: Full-path daily links (only in frontmatter)
            if re.search(r'^daily: "\[\[Calendar/daily/', frontmatter, re.MULTILINE):
                self.issues["invalid_daily_links"].append(relative_path)

            # Check 3: Unquoted wikilinks in frontmatter
            # More precise check - only match property lines in frontmatter
            for line in frontmatter.split("\n"):
                if re.match(r"^[a-z_]+: \[\[.*\]\]\s*$", line) and not re.search(r'"\[\[', line):
                    self.issues["unquoted_wikilinks"].append(relative_path)
                    break

            # Check 4: Invalid created date format (only in frontmatter)
            # Matches both unquoted and quoted wikilinks: [[date]] or "[[date]]"
            if re.search(r'^created: "?\[\[', frontmatter, re.MULTILINE):
                self.issues["invalid_created"].append(relative_path)

            # Check 5: Title properties in frontmatter (not in code blocks)
            for line in frontmatter.split("\n"):
                if line.strip().startswith("title:") and line.strip() != "---":
                    self.issues["title_properties"].append(relative_path)
                    break

            # Check 6: Date consistency (only in frontmatter)
            created_match = re.search(r"^created: (\d{4}-\d{2}-\d{2})", frontmatter, re.MULTILINE)
            daily_match = re.search(
                r'^daily: "\[\[.*?(\d{4}-\d{2}-\d{2})', frontmatter, re.MULTILINE
            )
            if created_match and daily_match:
                if created_match.group(1) != daily_match.group(1):
                    self.issues["date_mismatches"].append(relative_path)

        except Exception as e:
            print(f"Error validating {file_path}: {e}", file=sys.stderr)

        return file_issues

    def infer_type(self, file_path: str) -> str | None:
        """Infer note type from file location"""
        # Use settings.yaml if available
        if self.settings and CORE_AVAILABLE:
            inferred = infer_note_type_from_path(self.settings, Path(file_path))
            if inferred:
                return inferred

        # Fall back to type_rules
        for location_prefix, note_type in self.type_rules.items():
            if file_path.startswith(location_prefix):
                return note_type
        return None

    def run_validation(self, path_filter: str | None = None) -> dict[str, Any]:
        """Run all validation checks"""
        print("  Scanning vault...")
        files = self.scan_vault(path_filter)

        if self.skipped_files > 0:
            print(f"  Found {len(files)} markdown files ({self.skipped_files} excluded)\n")
        else:
            print(f"  Found {len(files)} markdown files\n")

        for file_path in files:
            self.validate_file(file_path)

        return self.reporter.generate_summary(self.issues)

    def run_fixes(self) -> int:
        """Run all auto-fixes"""
        return self.auto_fixer.run_all_fixes(self.issues)

    def generate_report(self, output_path: str | None = None) -> str:
        """Generate detailed markdown report"""
        return self.reporter.generate_report(self.issues, output_path)

    def log_to_jsonl(self, output_path: str | Path | None = None, fixes_applied: int = 0) -> None:
        """Append validation result as JSON line to JSONL file for audit trail."""
        self.reporter.log_to_jsonl(self.issues, output_path, fixes_applied)


def main() -> None:
    parser = argparse.ArgumentParser(description="Vault Validator & Auto-Fix Tool v2.0.0")
    parser.add_argument("--vault", default=".", help="Vault path (default: current directory)")
    parser.add_argument(
        "--mode",
        choices=["report", "auto", "interactive"],
        default="report",
        help="Validation mode",
    )
    parser.add_argument("--path", help="Specific path to validate (optional)")
    parser.add_argument("--report", help="Save report to file")
    parser.add_argument("--check", help="Run specific check only")
    parser.add_argument(
        "--no-jsonl",
        action="store_true",
        help="Disable JSONL audit logging (enabled by default to .claude/logs/validate.jsonl)",
    )
    parser.add_argument(
        "--jsonl",
        help="Custom path for JSONL audit log (default: .claude/logs/validate.jsonl)",
    )

    args = parser.parse_args()

    validator = VaultValidator(args.vault, args.mode)

    # Run validation
    summary = validator.run_validation(args.path)
    fixes_applied = 0

    # Run fixes if in auto mode
    if args.mode == "auto" and summary["total_issues"] > 0:
        fixes_applied = validator.run_fixes()

        # Re-validate
        print("\n  Re-validating after fixes...\n")
        validator.issues = {k: [] for k in validator.issues.keys()}
        validator.run_validation(args.path)

    # Generate report if requested
    if args.report:
        validator.generate_report(args.report)

    # Log to JSONL by default (unless --no-jsonl specified)
    if not args.no_jsonl:
        jsonl_path = args.jsonl if args.jsonl else None  # None = use default path
        validator.log_to_jsonl(jsonl_path, fixes_applied)

    # Exit code based on remaining issues
    remaining_issues = sum(len(v) for v in validator.issues.values())
    sys.exit(0 if remaining_issues == 0 else 1)


if __name__ == "__main__":
    main()
