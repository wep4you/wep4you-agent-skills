#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Automated Skill Setup Script

Creates a new skill from the template with proper structure and PEP 723 headers.

Usage:
    uv run scripts/create_skill.py <category> <skill-name>
    uv run scripts/create_skill.py obsidian my-new-skill --author "John Doe"

Examples:
    uv run scripts/create_skill.py obsidian vault-backup
    uv run scripts/create_skill.py obsidian link-checker --description "Check broken links"
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml


def validate_skill_name(name: str) -> bool:
    """Validate skill name follows kebab-case convention."""
    pattern = r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$"
    return bool(re.match(pattern, name)) and len(name) <= 64


def validate_category(category: str, skills_dir: Path) -> bool:
    """Validate category exists or is a known category."""
    known_categories = {"obsidian"}
    category_path = skills_dir / category
    return category in known_categories or category_path.exists()


def get_template_dir(project_root: Path, category: str) -> Path:
    """Get the appropriate template directory for a category.

    Returns category-specific template if it exists, otherwise falls back
    to the generic skill-template.
    """
    category_template = project_root / "templates" / category
    generic_template = project_root / "templates" / "skill-template"

    if category_template.exists() and (category_template / "SKILL.md").exists():
        return category_template
    return generic_template


def create_skill_structure(
    skills_dir: Path,
    template_dir: Path,
    category: str,
    skill_name: str,
    author: str,
    description: str,
    license_type: str,
) -> Path:
    """Create skill directory structure from template."""
    skill_path = skills_dir / category / skill_name

    if skill_path.exists():
        raise FileExistsError(f"Skill already exists: {skill_path}")

    # Create category directory if needed
    (skills_dir / category).mkdir(parents=True, exist_ok=True)

    # Copy template
    shutil.copytree(template_dir, skill_path)

    return skill_path


def update_skill_md(
    skill_path: Path,
    skill_name: str,
    author: str,
    description: str,
    license_type: str,
) -> None:
    """Update SKILL.md with provided values."""
    skill_md = skill_path / "SKILL.md"
    content = skill_md.read_text()

    # Parse and update frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            frontmatter["name"] = skill_name
            frontmatter["author"] = author
            frontmatter["license"] = license_type
            if description:
                frontmatter["description"] = description

            # Rebuild content
            new_frontmatter = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
            new_content = f"---\n{new_frontmatter}---{parts[2]}"

            # Replace placeholders in body
            title = skill_name.replace("-", " ").title()
            new_content = new_content.replace("Your Skill Name", title)
            new_content = new_content.replace("your-skill-name", skill_name)
            new_content = new_content.replace("your-skill", skill_name)

            skill_md.write_text(new_content)


def update_script_template(skill_path: Path, skill_name: str) -> None:
    """Update main.py script with skill-specific values."""
    script_path = skill_path / "scripts" / "main.py"
    if script_path.exists():
        content = script_path.read_text()
        title = skill_name.replace("-", " ").title()
        content = content.replace("Your Skill Name", title)
        content = content.replace("Your skill description", f"{title} - Main Script")
        content = content.replace("your-skill", skill_name)
        script_path.write_text(content)


def update_config_template(skill_path: Path, skill_name: str) -> None:
    """Update config template with skill-specific values."""
    for config_file in (skill_path / "config").glob("*.yaml"):
        content = config_file.read_text()
        content = content.replace("your-skill", skill_name)
        config_file.write_text(content)


def print_success(skill_path: Path, skill_name: str, category: str) -> None:
    """Print success message with next steps."""
    print(f"\n✅ Created skill: {skill_name}")
    print(f"   Location: {skill_path}")
    print("\n📝 Next steps:")
    print(f"   1. Edit {skill_path}/SKILL.md with your skill description")
    print(f"   2. Implement your logic in {skill_path}/scripts/main.py")
    print(f"   3. Update configuration in {skill_path}/config/")
    print(f"   4. Add tests in tests/test_{skill_name.replace('-', '_')}.py")
    print(f"   5. Run validation: uv run python scripts/validate_skills.py --skill {skill_name}")
    print("\n🚀 Run your skill:")
    print(f"   uv run {skill_path}/scripts/main.py --help")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a new skill from template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s obsidian vault-backup
    %(prog)s obsidian link-checker --author "John Doe"
    %(prog)s obsidian frontmatter-fixer --description "Fix frontmatter issues"
        """,
    )
    parser.add_argument(
        "category",
        help="Skill category (obsidian)",
    )
    parser.add_argument(
        "skill_name",
        help="Skill name in kebab-case (e.g., vault-backup)",
    )
    parser.add_argument(
        "--author",
        default="Your Name",
        help="Author name (default: 'Your Name')",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Brief skill description",
    )
    parser.add_argument(
        "--license",
        dest="license_type",
        default="MIT",
        help="License type (default: MIT)",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=None,
        help="Skills directory (default: auto-detect)",
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

    # Find project directories
    project_root = find_project_root()
    skills_dir = args.skills_dir or project_root / "skills"

    # Get category-specific template or fall back to generic
    template_dir = get_template_dir(project_root, args.category)

    # Validate inputs
    if not validate_skill_name(args.skill_name):
        print(f"❌ Error: Invalid skill name '{args.skill_name}'", file=sys.stderr)
        print("   Must be kebab-case, start with letter, max 64 chars", file=sys.stderr)
        print("   Example: vault-backup, my-cool-skill", file=sys.stderr)
        return 1

    if not template_dir.exists():
        print(f"❌ Error: Template not found at {template_dir}", file=sys.stderr)
        return 1

    # Show which template is being used
    template_type = "category" if template_dir.name == args.category else "generic"
    print(f"📋 Using {template_type} template: {template_dir.name}")

    if not validate_category(args.category, skills_dir):
        print(f"⚠️  Warning: Unknown category '{args.category}'", file=sys.stderr)
        print("   Known categories: obsidian")
        # Continue anyway - allow custom categories

    try:
        # Create skill structure
        skill_path = create_skill_structure(
            skills_dir=skills_dir,
            template_dir=template_dir,
            category=args.category,
            skill_name=args.skill_name,
            author=args.author,
            description=args.description,
            license_type=args.license_type,
        )

        # Update templates with skill-specific values
        update_skill_md(
            skill_path=skill_path,
            skill_name=args.skill_name,
            author=args.author,
            description=args.description,
            license_type=args.license_type,
        )
        update_script_template(skill_path, args.skill_name)
        update_config_template(skill_path, args.skill_name)

        print_success(skill_path, args.skill_name, args.category)
        return 0

    except FileExistsError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error creating skill: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
