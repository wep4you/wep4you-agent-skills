#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Vault Validator & Auto-Fix Tool
Validates Obsidian vault against standards and auto-fixes common issues
Version: 1.6.0 - Removed legacy validator.yaml, settings.yaml is single source of truth

Usage:
    uv run scripts/validator.py --vault /path/to/vault
    uv run scripts/validator.py --vault . --mode auto
    uv run scripts/validator.py --vault . --no-jsonl  # Disable audit logging
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# PyYAML is always available via uv inline dependencies

# Try to import settings_loader for integrated configuration
SETTINGS_LOADER_AVAILABLE = False
try:
    # Add config scripts to path
    _config_scripts = Path(__file__).parent.parent.parent / "config" / "scripts"
    if str(_config_scripts) not in sys.path:
        sys.path.insert(0, str(_config_scripts))
    from settings_loader import (
        Settings,
        get_core_properties,
        get_note_type,
        infer_note_type_from_path,
        load_settings,
    )
    from settings_loader import should_exclude as settings_should_exclude

    SETTINGS_LOADER_AVAILABLE = True
except ImportError:
    Settings = None  # type: ignore[misc,assignment]


class VaultValidator:
    """Main validator class with settings.yaml support and code block detection"""

    def __init__(self, vault_path: str, mode: str = "report"):
        self.vault_path = Path(vault_path)
        self.mode = mode  # report, auto, interactive

        # Load settings.yaml (single source of truth)
        self.settings: Settings | None = None
        if SETTINGS_LOADER_AVAILABLE:
            try:
                self.settings = load_settings(self.vault_path)
                print(f"✅ Using settings.yaml (methodology: {self.settings.methodology})")
            except FileNotFoundError:
                print("⚠️  No settings.yaml found - using defaults")
            except Exception as e:
                print(f"⚠️  Error loading settings.yaml: {e}")

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
        if self.settings and SETTINGS_LOADER_AVAILABLE:
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
        if not type_name or not self.settings or not SETTINGS_LOADER_AVAILABLE:
            return self.required_properties

        note_type = get_note_type(self.settings, type_name)
        if note_type:
            return note_type.required_properties

        return self.required_properties

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from validation"""
        # Use settings.yaml if available
        if self.settings and SETTINGS_LOADER_AVAILABLE:
            return settings_should_exclude(self.settings, file_path)

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
            if re.search(r"^created: \[\[", frontmatter, re.MULTILINE):
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
        if self.settings and SETTINGS_LOADER_AVAILABLE:
            inferred = infer_note_type_from_path(self.settings, Path(file_path))
            if inferred:
                return inferred

        # Fall back to type_rules
        for location_prefix, note_type in self.type_rules.items():
            if file_path.startswith(location_prefix):
                return note_type
        return None

    def fix_empty_types(self) -> int:
        """Fix empty type fields"""
        if not self.auto_fix_config.get("empty_types", True):
            return 0

        fixed = 0
        for file_rel_path in self.issues["empty_types"]:
            file_path = self.vault_path / file_rel_path
            inferred_type = self.infer_type(file_rel_path)

            if not inferred_type:
                # Skip silently if we can't infer type (likely excluded file)
                continue

            try:
                content = file_path.read_text()
                new_content = re.sub(
                    r"^type:\s*$", f"type: {inferred_type}", content, flags=re.MULTILINE
                )
                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"✅ Fixed empty type in: {file_rel_path} → {inferred_type}")
                    fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_missing_properties(self) -> int:
        """Add missing properties to frontmatter.

        - type: inferred from folder location
        - Other properties: set to empty string for user to fill in
        """
        if not self.auto_fix_config.get("empty_types", True):
            return 0

        fixed = 0
        for entry in self.issues["missing_properties"]:
            # Parse entry format: "path (missing: prop1, prop2)"
            if "(missing:" not in entry:
                continue

            file_rel_path = entry.split(" (missing:")[0]
            missing_props = entry.split("(missing: ")[1].rstrip(")").split(", ")

            file_path = self.vault_path / file_rel_path

            # Build properties to add
            props_to_add: list[str] = []

            for prop in missing_props:
                if prop == "type":
                    # Infer type from folder
                    inferred_type = self.infer_type(file_rel_path)
                    if inferred_type:
                        props_to_add.append(f"type: {inferred_type}")
                else:
                    # Set other properties to empty string
                    props_to_add.append(f"{prop}:")

            if not props_to_add:
                continue

            try:
                content = file_path.read_text()
                lines = content.split("\n")
                new_lines = []
                inserted = False

                for i, line in enumerate(lines):
                    new_lines.append(line)
                    # Insert properties after first ---
                    if line.strip() == "---" and not inserted and i == 0:
                        new_lines.extend(props_to_add)
                        inserted = True

                if inserted:
                    new_content = "\n".join(new_lines)
                    file_path.write_text(new_content)
                    added_props = ", ".join(p.split(":")[0] for p in props_to_add)
                    print(f"✅ Added missing properties to: {file_rel_path} → {added_props}")
                    fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_daily_links(self) -> int:
        """Convert full-path daily links to basename format"""
        if not self.auto_fix_config.get("daily_links", True):
            return 0

        fixed = 0
        pattern = r'daily: "\[\[Calendar/daily/\d{4}/\d{2}/(\d{4}-\d{2}-\d{2})\]\]"'
        replacement = r'daily: "[[\1]]"'

        for file_rel_path in self.issues["invalid_daily_links"]:
            file_path = self.vault_path / file_rel_path

            try:
                content = file_path.read_text()
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"✅ Fixed daily link in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_unquoted_wikilinks(self) -> int:
        """Add quotes to wikilinks in frontmatter"""
        if not self.auto_fix_config.get("wikilink_quotes", True):
            return 0

        fixed = 0

        for file_rel_path in self.issues["unquoted_wikilinks"]:
            file_path = self.vault_path / file_rel_path

            try:
                content = file_path.read_text()
                lines = content.split("\n")
                new_lines = []
                in_frontmatter = False
                frontmatter_count = 0

                for line in lines:
                    if line.strip() == "---":
                        frontmatter_count += 1
                        in_frontmatter = frontmatter_count == 1
                        new_lines.append(line)
                    elif in_frontmatter and re.match(r"^(\w+): (\[\[.*?\]\])$", line):
                        # Add quotes
                        new_line = re.sub(r"^(\w+): (\[\[.*?\]\])$", r'\1: "\2"', line)
                        new_lines.append(new_line)
                    else:
                        new_lines.append(line)

                new_content = "\n".join(new_lines)
                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"✅ Fixed unquoted wikilinks in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_invalid_created(self) -> int:
        """Fix invalid created date format"""
        if not self.auto_fix_config.get("invalid_created", True):
            return 0

        fixed = 0
        pattern = r"^created: \[\[(\d{4}-\d{2}-\d{2})\]\].*$"
        replacement = r"created: \1"

        for file_rel_path in self.issues["invalid_created"]:
            file_path = self.vault_path / file_rel_path

            try:
                content = file_path.read_text()
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"✅ Fixed created date in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_title_properties(self) -> int:
        """Remove title properties from frontmatter"""
        if not self.auto_fix_config.get("title_properties", True):
            return 0

        fixed = 0

        for file_rel_path in self.issues["title_properties"]:
            file_path = self.vault_path / file_rel_path

            try:
                content = file_path.read_text()
                lines = content.split("\n")
                new_lines = []
                in_frontmatter = False
                frontmatter_count = 0

                for line in lines:
                    if line.strip() == "---":
                        frontmatter_count += 1
                        in_frontmatter = frontmatter_count == 1
                        new_lines.append(line)
                    elif in_frontmatter and line.strip().startswith("title:"):
                        # Skip this line
                        continue
                    else:
                        new_lines.append(line)

                new_content = "\n".join(new_lines)
                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"✅ Removed title property from: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_date_mismatches(self) -> int:
        """Synchronize created and daily dates"""
        if not self.auto_fix_config.get("date_mismatches", True):
            return 0

        fixed = 0

        for file_rel_path in self.issues["date_mismatches"]:
            file_path = self.vault_path / file_rel_path

            try:
                content = file_path.read_text()

                # Extract created date
                created_match = re.search(r"^created: (\d{4}-\d{2}-\d{2})", content, re.MULTILINE)
                if not created_match:
                    continue

                created_date = created_match.group(1)

                # Update daily link to match
                new_content = re.sub(
                    r'^daily: "\[\[\d{4}-\d{2}-\d{2}\]\]"',
                    f'daily: "[[{created_date}]]"',
                    content,
                    flags=re.MULTILINE,
                )

                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"✅ Synchronized dates in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def run_validation(self, path_filter: str | None = None) -> dict[str, Any]:
        """Run all validation checks"""
        print("🔍 Scanning vault...")
        files = self.scan_vault(path_filter)

        if self.skipped_files > 0:
            print(f"📊 Found {len(files)} markdown files ({self.skipped_files} excluded)\n")
        else:
            print(f"📊 Found {len(files)} markdown files\n")

        for file_path in files:
            self.validate_file(file_path)

        return self.generate_summary()

    def run_fixes(self) -> int:
        """Run all auto-fixes"""
        print("\n🔧 Running auto-fixes...\n")

        total_fixed = 0
        total_fixed += self.fix_empty_types()
        total_fixed += self.fix_missing_properties()
        total_fixed += self.fix_daily_links()
        total_fixed += self.fix_unquoted_wikilinks()
        total_fixed += self.fix_invalid_created()
        total_fixed += self.fix_title_properties()
        total_fixed += self.fix_date_mismatches()

        print(f"\n✅ Total fixes applied: {total_fixed}")
        return total_fixed

    def generate_summary(self) -> dict[str, Any]:
        """Generate validation summary"""
        total_issues = sum(len(v) for v in self.issues.values())

        summary = {
            "total_issues": total_issues,
            "issues_by_type": {k: len(v) for k, v in self.issues.items() if v},
        }

        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60 + "\n")

        if total_issues == 0:
            print("✅ No issues found! Vault is compliant with standards.\n")
        else:
            print(f"⚠️  Found {total_issues} issues:\n")
            for issue_type, files in self.issues.items():
                if files:
                    count = len(files)
                    print(f"  - {issue_type.replace('_', ' ').title()}: {count}")

        print("\n" + "=" * 60 + "\n")

        return summary

    def generate_report(self, output_path: str | None = None) -> str:
        """Generate detailed markdown report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_issues = sum(len(v) for v in self.issues.values())

        methodology = self.settings.methodology if self.settings else "default"
        report = f"""# Vault Validation Report

**Date**: {timestamp}
**Mode**: {self.mode}
**Methodology**: {methodology}
**Total Issues**: {total_issues}

---

## Summary

"""

        for issue_type, files in self.issues.items():
            if files:
                report += f"\n### {issue_type.replace('_', ' ').title()} ({len(files)} files)\n\n"
                for file_path in files[:10]:  # Limit to first 10
                    report += f"- `{file_path}`\n"
                if len(files) > 10:
                    report += f"\n... and {len(files) - 10} more\n"

        if output_path:
            Path(output_path).write_text(report)
            print(f"📄 Report saved to: {output_path}")

        return report

    def get_default_jsonl_path(self) -> Path:
        """Get default JSONL log path: .claude/logs/validate.jsonl"""
        return self.vault_path / ".claude" / "logs" / "validate.jsonl"

    def log_to_jsonl(self, output_path: str | Path | None = None, fixes_applied: int = 0) -> None:
        """Append validation result as JSON line to JSONL file for audit trail.

        Each line is a complete JSON object with:
        - timestamp: ISO format datetime
        - vault_path: Absolute path to vault
        - mode: Validation mode (report/auto/interactive)
        - total_issues: Count of all issues found
        - issues_by_type: Dict of issue type -> count
        - issues_detail: Dict of issue type -> list of affected files
        - fixes_applied: Number of auto-fixes applied (if mode=auto)
        - config_version: Version from config file

        Args:
            output_path: Path to JSONL file. If None, uses default .claude/logs/validate.jsonl
            fixes_applied: Number of fixes applied in auto mode
        """
        timestamp = datetime.now().isoformat()
        total_issues = sum(len(v) for v in self.issues.values())

        methodology = self.settings.methodology if self.settings else "default"
        log_entry = {
            "timestamp": timestamp,
            "vault_path": str(self.vault_path.absolute()),
            "mode": self.mode,
            "methodology": methodology,
            "total_issues": total_issues,
            "issues_by_type": {k: len(v) for k, v in self.issues.items() if v},
            "issues_detail": {k: v for k, v in self.issues.items() if v},
            "fixes_applied": fixes_applied,
        }

        # Use default path if not specified
        jsonl_path = Path(output_path) if output_path else self.get_default_jsonl_path()

        # Create parent directories if they don't exist
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to JSONL file (create if doesn't exist)
        with open(jsonl_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"📝 Logged to JSONL: {jsonl_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vault Validator & Auto-Fix Tool v1.6.0")
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
        print("\n🔄 Re-validating after fixes...\n")
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
