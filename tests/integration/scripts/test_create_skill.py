"""
Tests for scripts/create_skill.py
"""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest
from create_skill import (
    create_skill_structure,
    find_project_root,
    get_template_dir,
    main,
    parse_args,
    print_success,
    update_config_template,
    update_script_template,
    update_skill_md,
    validate_category,
    validate_skill_name,
)


class TestValidateSkillName:
    """Test skill name validation"""

    def test_valid_simple_name(self):
        assert validate_skill_name("vault-backup") is True

    def test_valid_single_word(self):
        assert validate_skill_name("validator") is True

    def test_valid_with_numbers(self):
        assert validate_skill_name("skill-v2") is True

    def test_invalid_uppercase(self):
        assert validate_skill_name("Vault-Backup") is False

    def test_invalid_underscore(self):
        assert validate_skill_name("vault_backup") is False

    def test_invalid_starts_with_number(self):
        assert validate_skill_name("2fast") is False

    def test_invalid_too_long(self):
        long_name = "a" * 65
        assert validate_skill_name(long_name) is False

    def test_valid_max_length(self):
        max_name = "a" * 64
        assert validate_skill_name(max_name) is True

    def test_invalid_empty(self):
        assert validate_skill_name("") is False

    def test_invalid_double_hyphen(self):
        assert validate_skill_name("vault--backup") is False


class TestValidateCategory:
    """Test category validation"""

    def test_known_category_obsidian(self, tmp_path):
        assert validate_category("obsidian", tmp_path) is True

    def test_unknown_category_not_exists(self, tmp_path):
        assert validate_category("unknown", tmp_path) is False

    def test_unknown_category_homeassistant(self, tmp_path):
        assert validate_category("homeassistant", tmp_path) is False

    def test_unknown_category_development(self, tmp_path):
        assert validate_category("development", tmp_path) is False

    def test_unknown_category_exists(self, tmp_path):
        (tmp_path / "custom").mkdir()
        assert validate_category("custom", tmp_path) is True


class TestGetTemplateDir:
    """Test template directory selection"""

    def test_uses_category_template_when_exists(self, tmp_path):
        # Create category-specific template
        cat_template = tmp_path / "templates" / "obsidian"
        cat_template.mkdir(parents=True)
        (cat_template / "SKILL.md").write_text("obsidian template")

        # Also create generic template
        generic = tmp_path / "templates" / "skill-template"
        generic.mkdir(parents=True)
        (generic / "SKILL.md").write_text("generic template")

        result = get_template_dir(tmp_path, "obsidian")
        assert result == cat_template

    def test_falls_back_to_generic_when_no_category_template(self, tmp_path):
        # Only create generic template
        generic = tmp_path / "templates" / "skill-template"
        generic.mkdir(parents=True)
        (generic / "SKILL.md").write_text("generic template")

        result = get_template_dir(tmp_path, "custom-category")
        assert result == generic

    def test_falls_back_when_category_dir_exists_but_no_skill_md(self, tmp_path):
        # Create category dir without SKILL.md
        cat_template = tmp_path / "templates" / "obsidian"
        cat_template.mkdir(parents=True)

        # Create generic template
        generic = tmp_path / "templates" / "skill-template"
        generic.mkdir(parents=True)
        (generic / "SKILL.md").write_text("generic template")

        result = get_template_dir(tmp_path, "obsidian")
        assert result == generic


class TestCreateSkillStructure:
    """Test skill directory creation"""

    def test_creates_skill_directory(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "SKILL.md").write_text("---\nname: template\n---")
        (template_dir / "scripts").mkdir()
        (template_dir / "scripts" / "main.py").write_text("# script")

        skill_path = create_skill_structure(
            skills_dir=skills_dir,
            template_dir=template_dir,
            category="obsidian",
            skill_name="test-skill",
            author="Test",
            description="Test",
            license_type="MIT",
        )

        assert skill_path.exists()
        assert (skill_path / "SKILL.md").exists()
        assert (skill_path / "scripts" / "main.py").exists()

    def test_creates_category_directory(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "SKILL.md").write_text("test")

        create_skill_structure(
            skills_dir=skills_dir,
            template_dir=template_dir,
            category="newcategory",
            skill_name="test-skill",
            author="Test",
            description="Test",
            license_type="MIT",
        )

        assert (skills_dir / "newcategory").exists()

    def test_raises_if_skill_exists(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "obsidian" / "existing").mkdir(parents=True)
        template_dir = tmp_path / "template"
        template_dir.mkdir()

        with pytest.raises(FileExistsError):
            create_skill_structure(
                skills_dir=skills_dir,
                template_dir=template_dir,
                category="obsidian",
                skill_name="existing",
                author="Test",
                description="Test",
                license_type="MIT",
            )


class TestUpdateSkillMd:
    """Test SKILL.md updates"""

    def test_updates_frontmatter(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: template
version: 1.0.0
author: Template
license: MIT
description: Template description
---

# Your Skill Name
""")

        update_skill_md(
            skill_path=tmp_path,
            skill_name="my-skill",
            author="John Doe",
            description="My description",
            license_type="Apache-2.0",
        )

        content = skill_md.read_text()
        assert "name: my-skill" in content
        assert "author: John Doe" in content
        assert "license: Apache-2.0" in content

    def test_replaces_placeholders(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: template
---

# Your Skill Name

Use your-skill-name and your-skill here.
""")

        update_skill_md(
            skill_path=tmp_path,
            skill_name="vault-backup",
            author="Test",
            description="",
            license_type="MIT",
        )

        content = skill_md.read_text()
        assert "Your Skill Name" not in content
        assert "your-skill-name" not in content


class TestUpdateScriptTemplate:
    """Test script template updates"""

    def test_updates_script(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script = scripts_dir / "main.py"
        script.write_text("""
Your Skill Name - Main Script
Your skill description
your-skill config
""")

        update_script_template(tmp_path, "my-tool")

        content = script.read_text()
        assert "Your Skill Name" not in content
        assert "My Tool" in content


class TestUpdateConfigTemplate:
    """Test config template updates"""

    def test_updates_config(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config = config_dir / "default.yaml"
        config.write_text("skill: your-skill\npath: /your-skill/")

        update_config_template(tmp_path, "my-skill")

        content = config.read_text()
        assert "your-skill" not in content
        assert "my-skill" in content


class TestPrintSuccess:
    """Test success message output"""

    def test_prints_skill_info(self, capsys, tmp_path):
        print_success(tmp_path / "my-skill", "my-skill", "obsidian")
        captured = capsys.readouterr()
        assert "my-skill" in captured.out
        assert "Created skill" in captured.out
        assert "Next steps" in captured.out


class TestParseArgs:
    """Test argument parsing"""

    def test_required_args(self):
        with patch.object(sys, "argv", ["create_skill.py", "obsidian", "my-skill"]):
            args = parse_args()
            assert args.category == "obsidian"
            assert args.skill_name == "my-skill"

    def test_optional_args(self):
        with patch.object(
            sys,
            "argv",
            [
                "create_skill.py",
                "obsidian",
                "my-skill",
                "--author",
                "John",
                "--description",
                "Desc",
                "--license",
                "Apache",
            ],
        ):
            args = parse_args()
            assert args.author == "John"
            assert args.description == "Desc"
            assert args.license_type == "Apache"


class TestFindProjectRoot:
    """Test project root detection"""

    def test_finds_root(self):
        root = find_project_root()
        assert (root / "pyproject.toml").exists()


class TestMain:
    """Test main entry point"""

    def test_invalid_skill_name(self):
        with patch.object(sys, "argv", ["create_skill.py", "obsidian", "Invalid_Name"]):
            exit_code = main()
            assert exit_code == 1

    def test_missing_template(self, tmp_path):
        argv = ["create_skill.py", "obsidian", "test-skill", "--skills-dir", str(tmp_path)]
        with patch.object(sys, "argv", argv):
            with patch("create_skill.find_project_root", return_value=tmp_path):
                exit_code = main()
                assert exit_code == 1

    def test_successful_creation(self, tmp_path):
        # Setup template
        template_dir = tmp_path / "templates" / "skill-template"
        template_dir.mkdir(parents=True)
        (template_dir / "SKILL.md").write_text("---\nname: template\n---\n# Your Skill Name")
        (template_dir / "scripts").mkdir()
        (template_dir / "scripts" / "main.py").write_text("# Your Skill Name")
        (template_dir / "config").mkdir()
        (template_dir / "config" / "default.yaml").write_text("skill: your-skill")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        argv = ["create_skill.py", "obsidian", "new-skill", "--skills-dir", str(skills_dir)]
        with patch.object(sys, "argv", argv):
            with patch("create_skill.find_project_root", return_value=tmp_path):
                exit_code = main()
                assert exit_code == 0

        assert (skills_dir / "obsidian" / "new-skill" / "SKILL.md").exists()

    def test_skill_already_exists(self, tmp_path):
        # Setup template
        template_dir = tmp_path / "templates" / "skill-template"
        template_dir.mkdir(parents=True)
        (template_dir / "SKILL.md").write_text("test")

        skills_dir = tmp_path / "skills"
        (skills_dir / "obsidian" / "existing").mkdir(parents=True)

        with patch.object(
            sys,
            "argv",
            ["create_skill.py", "obsidian", "existing", "--skills-dir", str(skills_dir)],
        ):
            with patch("create_skill.find_project_root", return_value=tmp_path):
                exit_code = main()
                assert exit_code == 1

    def test_uses_category_template(self, tmp_path, capsys):
        # Setup category-specific template (obsidian)
        cat_template = tmp_path / "templates" / "obsidian"
        cat_template.mkdir(parents=True)
        (cat_template / "SKILL.md").write_text("---\nname: obsidian-template\n---\n# Obsidian")
        (cat_template / "scripts").mkdir()
        (cat_template / "scripts" / "main.py").write_text("# Obsidian script")

        # Also create generic template
        generic = tmp_path / "templates" / "skill-template"
        generic.mkdir(parents=True)
        (generic / "SKILL.md").write_text("---\nname: generic\n---\n# Generic")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        argv = ["create_skill.py", "obsidian", "my-vault-skill", "--skills-dir", str(skills_dir)]
        with patch.object(sys, "argv", argv):
            with patch("create_skill.find_project_root", return_value=tmp_path):
                exit_code = main()
                assert exit_code == 0

        # Verify category template was used
        captured = capsys.readouterr()
        assert "category template" in captured.out
        assert (skills_dir / "obsidian" / "my-vault-skill" / "SKILL.md").exists()

    def test_falls_back_to_generic_template(self, tmp_path, capsys):
        # Only create generic template
        generic = tmp_path / "templates" / "skill-template"
        generic.mkdir(parents=True)
        (generic / "SKILL.md").write_text("---\nname: generic\n---\n# Generic")
        (generic / "scripts").mkdir()
        (generic / "scripts" / "main.py").write_text("# script")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        argv = ["create_skill.py", "custom", "new-tool", "--skills-dir", str(skills_dir)]
        with patch.object(sys, "argv", argv):
            with patch("create_skill.find_project_root", return_value=tmp_path):
                exit_code = main()
                assert exit_code == 0

        # Verify generic template was used
        captured = capsys.readouterr()
        assert "generic template" in captured.out
