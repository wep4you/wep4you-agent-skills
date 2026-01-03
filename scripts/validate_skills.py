#!/usr/bin/env python3
"""
SKILL.md and Plugin Validation Script

Validates all SKILL.md files and plugin structure against the Agent Skills specification.
Used by pre-commit hooks and CI/CD pipeline.

Usage:
    python scripts/validate_skills.py
    python scripts/validate_skills.py --verbose
    python scripts/validate_skills.py --json
    python scripts/validate_skills.py --skill validate
    python scripts/validate_skills.py --plugin          # Validate plugin structure
    python scripts/validate_skills.py --plugin --verbose
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of validating a single skill."""

    skill_name: str
    skill_path: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "skill_name": self.skill_name,
            "skill_path": self.skill_path,
            "valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class PluginValidationResult:
    """Result of validating plugin structure."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    plugin_version: str | None = None
    skill_versions: dict[str, str] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "plugin_version": self.plugin_version,
            "skill_versions": self.skill_versions,
        }


def extract_frontmatter(content: str) -> dict[str, str] | None:
    """Extract YAML frontmatter from SKILL.md content."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter: dict[str, str] = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()

    return frontmatter


def validate_skill_md(skill_path: Path, verbose: bool = False) -> ValidationResult:
    """Validate a single SKILL.md file."""
    result = ValidationResult(
        skill_name=skill_path.name,
        skill_path=str(skill_path),
    )
    skill_file = skill_path / "SKILL.md"

    if not skill_file.exists():
        result.errors.append("Missing SKILL.md file")
        return result

    content = skill_file.read_text(encoding="utf-8")

    # Check for frontmatter
    frontmatter = extract_frontmatter(content)
    if frontmatter is None:
        result.errors.append("Missing YAML frontmatter (must start with ---)")
        return result

    # Required fields: name
    if "name" not in frontmatter:
        result.errors.append("Missing required 'name' field in frontmatter")
    elif not frontmatter["name"]:
        result.errors.append("'name' field is empty")
    elif not re.match(r"^[a-z0-9-]+$", frontmatter["name"]):
        result.errors.append("'name' must be kebab-case (a-z, 0-9, hyphens)")
    elif len(frontmatter["name"]) > 64:
        result.errors.append("'name' exceeds 64 character limit")

    # Required fields: description
    if "description" not in frontmatter:
        result.errors.append("Missing required 'description' field in frontmatter")
    elif not frontmatter["description"]:
        result.errors.append("'description' field is empty")
    elif len(frontmatter["description"]) > 1024:
        result.errors.append("'description' exceeds 1024 character limit")

    # Recommended fields (warnings)
    if "version" not in frontmatter:
        result.warnings.append("Missing recommended 'version' field")
    elif frontmatter["version"] and not re.match(r"^\d+\.\d+\.\d+$", frontmatter["version"]):
        result.warnings.append("'version' should follow semver format (x.y.z)")

    if "author" not in frontmatter:
        result.warnings.append("Missing recommended 'author' field")

    if "license" not in frontmatter:
        result.warnings.append("Missing recommended 'license' field")

    # Check required directories
    if not (skill_path / "scripts").exists() and not (skill_path / "config").exists():
        result.warnings.append("Skill has neither 'scripts/' nor 'config/' directory")

    # Check file size (recommended < 500 lines)
    lines = content.count("\n")
    if lines > 500:
        result.warnings.append(f"SKILL.md has {lines} lines (recommended < 500)")

    return result


def validate_plugin(root_path: Path, verbose: bool = False) -> PluginValidationResult:
    """Validate plugin structure (.claude-plugin/ directory)."""
    result = PluginValidationResult()
    plugin_dir = root_path / ".claude-plugin"

    # Check .claude-plugin directory exists
    if not plugin_dir.exists():
        result.errors.append("Missing .claude-plugin/ directory")
        return result

    # Validate plugin.json
    plugin_json_path = plugin_dir / "plugin.json"
    if not plugin_json_path.exists():
        result.errors.append("Missing .claude-plugin/plugin.json")
    else:
        try:
            plugin_data = json.loads(plugin_json_path.read_text(encoding="utf-8"))

            # Required fields
            if "name" not in plugin_data:
                result.errors.append("plugin.json: Missing required 'name' field")
            if "version" not in plugin_data:
                result.errors.append("plugin.json: Missing required 'version' field")
            else:
                result.plugin_version = plugin_data["version"]
            if "skills" not in plugin_data:
                result.errors.append("plugin.json: Missing required 'skills' field")

            # Recommended fields
            if "description" not in plugin_data:
                result.warnings.append("plugin.json: Missing recommended 'description' field")
            if "author" not in plugin_data:
                result.warnings.append("plugin.json: Missing recommended 'author' field")
            if "license" not in plugin_data:
                result.warnings.append("plugin.json: Missing recommended 'license' field")

        except json.JSONDecodeError as e:
            result.errors.append(f"plugin.json: Invalid JSON - {e}")

    # Validate marketplace.json (optional but recommended)
    marketplace_json_path = plugin_dir / "marketplace.json"
    if not marketplace_json_path.exists():
        result.warnings.append("Missing .claude-plugin/marketplace.json (recommended)")
    else:
        try:
            json.loads(marketplace_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            result.errors.append(f"marketplace.json: Invalid JSON - {e}")

    # Check commands directory
    commands_dir = root_path / "commands"
    if not commands_dir.exists():
        result.warnings.append("Missing commands/ directory (recommended for slash commands)")
    else:
        # Validate command files have frontmatter
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text(encoding="utf-8")
            if not content.startswith("---"):
                result.warnings.append(f"commands/{cmd_file.name}: Missing YAML frontmatter")

    # Collect skill versions for comparison
    skills_dir = root_path / "skills"
    if skills_dir.exists():
        for skill_md in skills_dir.rglob("SKILL.md"):
            skill_name = skill_md.parent.name
            content = skill_md.read_text(encoding="utf-8")
            frontmatter = extract_frontmatter(content)
            if frontmatter and "version" in frontmatter:
                result.skill_versions[skill_name] = frontmatter["version"]

    return result


def print_plugin_results(
    result: PluginValidationResult, verbose: bool = False, json_output: bool = False
) -> int:
    """Print plugin validation results and return exit code."""
    if json_output:
        output = {"plugin_validation": result.to_dict()}
        print(json.dumps(output, indent=2))
        return 0 if result.is_valid else 1

    if result.errors:
        print(f"\n{'=' * 60}")
        print(f"Plugin Validation Failed: {len(result.errors)} error(s)")
        print(f"{'=' * 60}")
        for error in result.errors:
            print(f"  ❌ {error}")
        return 1

    if verbose and result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")

    if verbose and result.skill_versions:
        print(f"\nPlugin version: {result.plugin_version}")
        print("Skill versions:")
        for skill, version in result.skill_versions.items():
            print(f"  - {skill}: {version}")

    print("✅ Plugin structure validated successfully")
    return 0


def validate_all_skills(
    skills_root: Path,
    verbose: bool = False,
    json_output: bool = False,
    skill_filter: str | None = None,
) -> tuple[list[ValidationResult], int]:
    """Validate all SKILL.md files in the skills directory."""
    results: list[ValidationResult] = []

    if not skills_root.exists():
        if json_output:
            print(json.dumps({"error": f"Skills directory not found: {skills_root}"}))
        else:
            print(f"Error: Skills directory not found: {skills_root}")
        return results, 1

    # Search recursively for SKILL.md files
    for skill_md in skills_root.rglob("SKILL.md"):
        skill_path = skill_md.parent

        # Filter by skill name if specified
        if skill_filter and skill_path.name != skill_filter:
            continue

        if verbose and not json_output:
            print(f"Validating: {skill_path.relative_to(skills_root)}")

        result = validate_skill_md(skill_path, verbose)
        results.append(result)

    return results, 0


def print_results(
    results: list[ValidationResult], verbose: bool = False, json_output: bool = False
) -> int:
    """Print validation results and return exit code."""
    if json_output:
        output = {
            "total_skills": len(results),
            "valid_skills": sum(1 for r in results if r.is_valid),
            "skills": [r.to_dict() for r in results],
        }
        print(json.dumps(output, indent=2))
        return 0 if all(r.is_valid for r in results) else 1

    if not results:
        print("Warning: No SKILL.md files found")
        return 0

    errors_count = sum(len(r.errors) for r in results)
    warnings_count = sum(len(r.warnings) for r in results)

    if errors_count > 0:
        print(f"\n{'=' * 60}")
        print(f"SKILL.md Validation Failed: {errors_count} error(s)")
        print(f"{'=' * 60}")
        for result in results:
            if result.errors:
                print(f"\n  {result.skill_name}:")
                for error in result.errors:
                    print(f"    ❌ {error}")
        return 1

    if verbose and warnings_count > 0:
        print(f"\nWarnings ({warnings_count}):")
        for result in results:
            if result.warnings:
                print(f"\n  {result.skill_name}:")
                for warning in result.warnings:
                    print(f"    ⚠️  {warning}")

    print(f"✅ All {len(results)} SKILL.md file(s) validated successfully")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md files and plugin structure"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose output with warnings"
    )
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")
    parser.add_argument("--skill", "-s", type=str, help="Validate only a specific skill by name")
    parser.add_argument(
        "--plugin", "-p", action="store_true", help="Validate plugin structure (.claude-plugin/)"
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path(__file__).parent.parent / "skills",
        help="Path to skills directory",
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Path to project root directory (for plugin validation)",
    )
    args = parser.parse_args()

    exit_code = 0

    # Plugin validation
    if args.plugin:
        plugin_result = validate_plugin(args.root_dir, args.verbose)
        exit_code = print_plugin_results(plugin_result, args.verbose, args.json)
        if exit_code != 0:
            return exit_code

    # Skill validation (default behavior or when not using --plugin alone)
    if not args.plugin or args.skill:
        results, error = validate_all_skills(args.skills_dir, args.verbose, args.json, args.skill)
        if error:
            return error
        exit_code = print_results(results, args.verbose, args.json)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
