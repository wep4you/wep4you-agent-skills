#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Cross-Platform Skill Installation Script

Installs skills for various AI coding assistants:
- Claude Code
- OpenAI Codex
- GitHub Copilot
- Cursor

Usage:
    uv run scripts/install_skills.py
    uv run scripts/install_skills.py --platform claude-code
    uv run scripts/install_skills.py --platform codex --skill obsidian-validator
    uv run scripts/install_skills.py --list

Examples:
    # Install all skills for Claude Code
    uv run scripts/install_skills.py --platform claude-code

    # Install specific skill for GitHub Copilot
    uv run scripts/install_skills.py --platform copilot --skill obsidian-validator

    # List available skills
    uv run scripts/install_skills.py --list
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

# Platform-specific installation paths
PLATFORM_PATHS = {
    "claude-code": {
        "darwin": Path.home() / ".claude" / "skills",
        "linux": Path.home() / ".claude" / "skills",
        "win32": Path.home() / ".claude" / "skills",
    },
    "codex": {
        "darwin": Path.home() / ".openai" / "codex" / "skills",
        "linux": Path.home() / ".openai" / "codex" / "skills",
        "win32": Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "skills",
    },
    "copilot": {
        "darwin": Path.home() / ".github" / "copilot" / "skills",
        "linux": Path.home() / ".github" / "copilot" / "skills",
        "win32": Path.home() / "AppData" / "Local" / "GitHub" / "Copilot" / "skills",
    },
    "cursor": {
        "darwin": Path.home() / ".cursor" / "skills",
        "linux": Path.home() / ".cursor" / "skills",
        "win32": Path.home() / "AppData" / "Local" / "Cursor" / "skills",
    },
}

SUPPORTED_PLATFORMS = list(PLATFORM_PATHS.keys())


@dataclass
class SkillInfo:
    """Information about a skill."""

    name: str
    category: str
    path: Path
    description: str = ""

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "path": str(self.path),
            "description": self.description,
        }


def find_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def _extract_description(skill_md: Path) -> str:
    """Extract description from SKILL.md frontmatter."""
    try:
        content = skill_md.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 2:
                for line in parts[1].split("\n"):
                    if line.startswith("description:"):
                        return line.split(":", 1)[1].strip().strip(">-\"'")
    except Exception:  # noqa: S110
        pass  # Ignore parsing errors, description is optional
    return ""


def discover_skills(skills_dir: Path) -> list[SkillInfo]:
    """Discover all available skills (flat structure).

    Looks for skills directly in skills_dir (e.g., skills/validate).
    """
    skills: list[SkillInfo] = []

    if not skills_dir.exists():
        return skills

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue

        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            skills.append(
                SkillInfo(
                    name=skill_dir.name,
                    category="",  # Flat structure, no category
                    path=skill_dir,
                    description=_extract_description(skill_md),
                )
            )

    return skills


def get_install_path(platform: str) -> Path | None:
    """Get installation path for the current OS and platform."""
    os_name = sys.platform
    paths = PLATFORM_PATHS.get(platform, {})
    return paths.get(os_name)


def install_skill(skill: SkillInfo, target_dir: Path, use_symlink: bool = True) -> bool:
    """Install a single skill to target directory."""
    target_path = target_dir / skill.name

    try:
        # Create parent directories
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing installation
        if target_path.exists() or target_path.is_symlink():
            if target_path.is_symlink():
                target_path.unlink()
            else:
                shutil.rmtree(target_path)

        if use_symlink:
            # Create symlink (preferred for development)
            target_path.symlink_to(skill.path, target_is_directory=True)
        else:
            # Copy files (for production/distribution)
            shutil.copytree(skill.path, target_path)

        return True
    except Exception as e:
        print(f"  ❌ Failed to install {skill.name}: {e}", file=sys.stderr)
        return False


def install_skills(
    skills: list[SkillInfo],
    platform: str,
    use_symlink: bool = True,
) -> tuple[int, int]:
    """Install skills for a specific platform."""
    target_dir = get_install_path(platform)
    if not target_dir:
        print(f"❌ Unsupported OS for platform {platform}: {sys.platform}", file=sys.stderr)
        return 0, len(skills)

    print(f"\n📦 Installing {len(skills)} skill(s) for {platform}")
    print(f"   Target: {target_dir}")
    print(f"   Method: {'symlink' if use_symlink else 'copy'}\n")

    success = 0
    failed = 0

    for skill in skills:
        if install_skill(skill, target_dir, use_symlink):
            print(f"  ✅ {skill.name}")
            success += 1
        else:
            failed += 1

    return success, failed


def list_skills(skills: list[SkillInfo], json_output: bool = False) -> None:
    """List available skills."""
    if json_output:
        print(json.dumps([s.to_dict() for s in skills], indent=2))
        return

    print("\n📚 Available Skills\n")

    for skill in sorted(skills, key=lambda s: s.name):
        desc = f" - {skill.description}" if skill.description else ""
        print(f"  └── {skill.name}{desc}")
    print()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Install skills for AI coding assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported platforms: {", ".join(SUPPORTED_PLATFORMS)}

Examples:
    %(prog)s --platform claude-code
    %(prog)s --platform codex --skill obsidian-validator
    %(prog)s --list --json
        """,
    )
    parser.add_argument(
        "--platform",
        choices=SUPPORTED_PLATFORMS,
        default="claude-code",
        help="Target platform (default: claude-code)",
    )
    parser.add_argument(
        "--skill",
        dest="skill_filter",
        help="Install only this skill (by name)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of creating symlinks",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_skills",
        help="List available skills without installing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON (with --list)",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=None,
        help="Skills directory (default: auto-detect)",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    project_root = find_project_root()
    skills_dir = args.skills_dir or project_root / "skills"

    # Discover skills
    skills = discover_skills(skills_dir)

    if not skills:
        print("❌ No skills found", file=sys.stderr)
        return 1

    # List mode
    if args.list_skills:
        list_skills(skills, json_output=args.json_output)
        return 0

    # Filter by skill name if specified
    if args.skill_filter:
        skills = [s for s in skills if s.name == args.skill_filter]
        if not skills:
            print(f"❌ Skill not found: {args.skill_filter}", file=sys.stderr)
            return 1

    # Install skills
    success, failed = install_skills(
        skills,
        platform=args.platform,
        use_symlink=not args.copy,
    )

    print(f"\n{'=' * 40}")
    print(f"Installed: {success}, Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
