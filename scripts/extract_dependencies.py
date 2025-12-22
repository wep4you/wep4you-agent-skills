#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Skill Dependency Extraction Tool

Extracts and validates PEP 723 inline dependencies from all skill scripts.
Generates consolidated requirements for security scanning.

Usage:
    uv run scripts/extract_dependencies.py
    uv run scripts/extract_dependencies.py --format requirements
    uv run scripts/extract_dependencies.py --json
    uv run scripts/extract_dependencies.py --skills-dir ./skills

Examples:
    # List all dependencies with their sources
    uv run scripts/extract_dependencies.py

    # Generate requirements.txt format for pip-audit
    uv run scripts/extract_dependencies.py --format requirements > requirements-skills.txt

    # JSON output for CI integration
    uv run scripts/extract_dependencies.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScriptDependencies:
    """Dependencies extracted from a single script."""

    script_path: str
    skill_name: str
    python_requires: str
    dependencies: list[str] = field(default_factory=list)
    parse_error: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON output."""
        return {
            "script_path": self.script_path,
            "skill_name": self.skill_name,
            "python_requires": self.python_requires,
            "dependencies": self.dependencies,
            "parse_error": self.parse_error,
        }


def extract_pep723_block(content: str) -> str | None:
    """Extract PEP 723 script metadata block from file content."""
    # Match the /// script block
    pattern = r"^# /// script\s*\n((?:#[^\n]*\n)*?)# ///"
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        return match.group(1)
    return None


def parse_pep723_metadata(block: str) -> dict[str, object]:
    """Parse PEP 723 metadata block into structured data."""
    metadata: dict[str, object] = {
        "requires-python": "",
        "dependencies": [],
    }

    # Remove comment prefixes and join lines
    lines = []
    for line in block.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            line = line[1:].strip()
        if line:
            lines.append(line)

    # Simple TOML-like parsing for the metadata
    current_key = None
    current_list: list[str] = []
    in_list = False

    for line in lines:
        if "=" in line and not in_list:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if value.startswith("["):
                in_list = True
                current_key = key
                current_list = []
                # Check for single-line list
                if value.endswith("]"):
                    in_list = False
                    # Parse single-line list
                    list_content = value[1:-1].strip()
                    if list_content:
                        items = [s.strip().strip("\"'") for s in list_content.split(",")]
                        metadata[key] = [i for i in items if i]
                    else:
                        metadata[key] = []
            else:
                metadata[key] = value.strip("\"'")
        elif in_list:
            if line.strip() == "]":
                in_list = False
                if current_key:
                    metadata[current_key] = current_list
            else:
                # Extract dependency from list item
                item = line.strip().rstrip(",").strip("\"'")
                if item:
                    current_list.append(item)

    return metadata


def extract_script_dependencies(script_path: Path) -> ScriptDependencies:
    """Extract dependencies from a single script file."""
    # Determine skill name from path
    parts = script_path.parts
    skill_name = "unknown"
    for i, part in enumerate(parts):
        if part == "skills" and i + 2 < len(parts):
            skill_name = parts[i + 2]  # skills/<category>/<skill-name>
            break
        if part == "scripts" and i > 0:
            skill_name = parts[i - 1]
            break

    try:
        content = script_path.read_text(encoding="utf-8")
    except Exception as e:
        return ScriptDependencies(
            script_path=str(script_path),
            skill_name=skill_name,
            python_requires="",
            parse_error=f"Failed to read file: {e}",
        )

    block = extract_pep723_block(content)
    if not block:
        return ScriptDependencies(
            script_path=str(script_path),
            skill_name=skill_name,
            python_requires="",
            parse_error="No PEP 723 metadata block found",
        )

    try:
        metadata = parse_pep723_metadata(block)
        deps = metadata.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []

        return ScriptDependencies(
            script_path=str(script_path),
            skill_name=skill_name,
            python_requires=str(metadata.get("requires-python", "")),
            dependencies=deps,
        )
    except Exception as e:
        return ScriptDependencies(
            script_path=str(script_path),
            skill_name=skill_name,
            python_requires="",
            parse_error=f"Failed to parse metadata: {e}",
        )


def find_skill_scripts(skills_dir: Path) -> list[Path]:
    """Find all Python scripts in skills directory."""
    scripts: list[Path] = []
    for script in skills_dir.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" in str(script) or "test_" in script.name:
            continue
        scripts.append(script)
    return sorted(scripts)


def extract_all_dependencies(
    skills_dir: Path,
) -> tuple[list[ScriptDependencies], dict[str, list[str]]]:
    """Extract dependencies from all skill scripts."""
    scripts = find_skill_scripts(skills_dir)
    results: list[ScriptDependencies] = []
    consolidated: dict[str, list[str]] = {}

    for script in scripts:
        deps = extract_script_dependencies(script)
        results.append(deps)

        # Consolidate unique dependencies
        for dep in deps.dependencies:
            # Normalize dependency name (before version specifier)
            base_name = re.split(r"[<>=!~\[]", dep)[0].strip().lower()
            if base_name not in consolidated:
                consolidated[base_name] = []
            if dep not in consolidated[base_name]:
                consolidated[base_name].append(dep)

    return results, consolidated


def print_results(
    results: list[ScriptDependencies],
    consolidated: dict[str, list[str]],
    output_format: str = "table",
    json_output: bool = False,
) -> int:
    """Print extraction results."""
    if json_output:
        output = {
            "scripts": [r.to_dict() for r in results],
            "consolidated": consolidated,
            "total_scripts": len(results),
            "total_unique_packages": len(consolidated),
            "errors": [r.script_path for r in results if r.parse_error],
        }
        print(json.dumps(output, indent=2))
        return 0

    if output_format == "requirements":
        # Output requirements.txt format
        all_deps: set[str] = set()
        for deps_list in consolidated.values():
            all_deps.update(deps_list)
        for dep in sorted(all_deps):
            print(dep)
        return 0

    # Table format (default)
    print("=" * 70)
    print("PEP 723 Dependency Extraction Report")
    print("=" * 70)

    errors = [r for r in results if r.parse_error]
    valid = [r for r in results if not r.parse_error]

    print(f"\nScanned: {len(results)} scripts")
    print(f"Valid:   {len(valid)}")
    print(f"Errors:  {len(errors)}")

    if valid:
        print("\n" + "-" * 70)
        print("Dependencies by Script")
        print("-" * 70)
        for r in valid:
            deps_str = ", ".join(r.dependencies) if r.dependencies else "(none)"
            print(f"\n  {r.skill_name}/scripts/{Path(r.script_path).name}")
            print(f"    Python: {r.python_requires}")
            print(f"    Deps:   {deps_str}")

    if consolidated:
        print("\n" + "-" * 70)
        print("Consolidated Unique Packages")
        print("-" * 70)
        for pkg, versions in sorted(consolidated.items()):
            print(f"  {pkg}: {', '.join(versions)}")

    if errors:
        print("\n" + "-" * 70)
        print("Errors")
        print("-" * 70)
        for r in errors:
            print(f"  {r.script_path}: {r.parse_error}")

    print("\n" + "=" * 70)
    return 1 if errors else 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract PEP 723 dependencies from skill scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=None,
        help="Skills directory (default: auto-detect)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "requirements"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    return parser.parse_args()


def find_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    project_root = find_project_root()
    skills_dir = args.skills_dir or project_root / "skills"

    if not skills_dir.exists():
        if args.json_output:
            print(json.dumps({"error": f"Skills directory not found: {skills_dir}"}))
        else:
            print(f"Error: Skills directory not found: {skills_dir}", file=sys.stderr)
        return 1

    results, consolidated = extract_all_dependencies(skills_dir)

    return print_results(
        results,
        consolidated,
        output_format=args.format,
        json_output=args.json_output,
    )


if __name__ == "__main__":
    sys.exit(main())
