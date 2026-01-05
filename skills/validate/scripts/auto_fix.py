#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Auto-fix module for vault validation.

This module handles automatic fixing of common frontmatter issues:
- Empty type fields
- Missing properties
- Full-path daily links
- Unquoted wikilinks
- Invalid created date formats
- Title properties
- Date mismatches
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class AutoFixer:
    """Handles automatic fixing of frontmatter issues."""

    def __init__(
        self,
        vault_path: Path,
        auto_fix_config: dict[str, bool],
        type_inferrer: Callable[[str], str | None],
    ):
        """Initialize auto-fixer.

        Args:
            vault_path: Path to the vault root
            auto_fix_config: Configuration for which fixes to apply
            type_inferrer: Function to infer note type from file path
        """
        self.vault_path = vault_path
        self.auto_fix_config = auto_fix_config
        self.type_inferrer = type_inferrer

    def fix_empty_types(self, issues: list[str]) -> int:
        """Fix empty type fields.

        Args:
            issues: List of relative file paths with empty type fields

        Returns:
            Number of files fixed
        """
        if not self.auto_fix_config.get("empty_types", True):
            return 0

        fixed = 0
        for file_rel_path in issues:
            file_path = self.vault_path / file_rel_path
            inferred_type = self.type_inferrer(file_rel_path)

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
                    print(f"  Fixed empty type in: {file_rel_path} -> {inferred_type}")
                    fixed += 1
            except Exception as e:
                print(f"  Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_missing_properties(self, issues: list[str]) -> int:
        """Add missing properties to frontmatter.

        Properties are handled as follows:
        - type: inferred from folder location
        - Other properties: set to empty string for user to fill in

        Args:
            issues: List of issue strings in format "path (missing: prop1, prop2)"

        Returns:
            Number of files fixed
        """
        if not self.auto_fix_config.get("missing_properties", True):
            return 0

        fixed = 0
        for entry in issues:
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
                    inferred_type = self.type_inferrer(file_rel_path)
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
                    print(f"  Added missing properties to: {file_rel_path} -> {added_props}")
                    fixed += 1
            except Exception as e:
                print(f"  Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_daily_links(self, issues: list[str]) -> int:
        """Convert full-path daily links to basename format.

        Args:
            issues: List of relative file paths with invalid daily links

        Returns:
            Number of files fixed
        """
        if not self.auto_fix_config.get("daily_links", True):
            return 0

        fixed = 0
        pattern = r'daily: "\[\[Calendar/daily/\d{4}/\d{2}/(\d{4}-\d{2}-\d{2})\]\]"'
        replacement = r'daily: "[[\1]]"'

        for file_rel_path in issues:
            file_path = self.vault_path / file_rel_path

            try:
                content = file_path.read_text()
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"  Fixed daily link in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"  Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_unquoted_wikilinks(self, issues: list[str]) -> int:
        """Add quotes to wikilinks in frontmatter.

        Args:
            issues: List of relative file paths with unquoted wikilinks

        Returns:
            Number of files fixed
        """
        if not self.auto_fix_config.get("wikilink_quotes", True):
            return 0

        fixed = 0

        for file_rel_path in issues:
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
                    print(f"  Fixed unquoted wikilinks in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"  Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_invalid_created(self, issues: list[str]) -> int:
        """Fix invalid created date format (wikilinks to plain dates).

        Args:
            issues: List of relative file paths with invalid created dates

        Returns:
            Number of files fixed
        """
        if not self.auto_fix_config.get("invalid_created", True):
            return 0

        fixed = 0
        pattern = r"^created: \[\[(\d{4}-\d{2}-\d{2})\]\].*$"
        replacement = r"created: \1"

        for file_rel_path in issues:
            file_path = self.vault_path / file_rel_path

            try:
                content = file_path.read_text()
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                if new_content != content:
                    file_path.write_text(new_content)
                    print(f"  Fixed created date in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"  Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_title_properties(self, issues: list[str]) -> int:
        """Remove title properties from frontmatter.

        Args:
            issues: List of relative file paths with title properties

        Returns:
            Number of files fixed
        """
        if not self.auto_fix_config.get("title_properties", True):
            return 0

        fixed = 0

        for file_rel_path in issues:
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
                    print(f"  Removed title property from: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"  Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def fix_date_mismatches(self, issues: list[str]) -> int:
        """Synchronize created and daily dates.

        Args:
            issues: List of relative file paths with date mismatches

        Returns:
            Number of files fixed
        """
        if not self.auto_fix_config.get("date_mismatches", True):
            return 0

        fixed = 0

        for file_rel_path in issues:
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
                    print(f"  Synchronized dates in: {file_rel_path}")
                    fixed += 1
            except Exception as e:
                print(f"  Error fixing {file_rel_path}: {e}", file=sys.stderr)

        return fixed

    def run_all_fixes(self, issues: dict[str, list[str]]) -> int:
        """Run all auto-fixes on the provided issues.

        Args:
            issues: Dictionary mapping issue type to list of affected files

        Returns:
            Total number of files fixed
        """
        print("\n  Running auto-fixes...\n")

        total_fixed = 0
        total_fixed += self.fix_empty_types(issues.get("empty_types", []))
        total_fixed += self.fix_missing_properties(issues.get("missing_properties", []))
        total_fixed += self.fix_daily_links(issues.get("invalid_daily_links", []))
        total_fixed += self.fix_unquoted_wikilinks(issues.get("unquoted_wikilinks", []))
        total_fixed += self.fix_invalid_created(issues.get("invalid_created", []))
        total_fixed += self.fix_title_properties(issues.get("title_properties", []))
        total_fixed += self.fix_date_mismatches(issues.get("date_mismatches", []))

        print(f"\n  Total fixes applied: {total_fixed}")
        return total_fixed
