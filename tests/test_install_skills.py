"""
Tests for scripts/install_skills.py
"""

from __future__ import annotations

import sys
from unittest.mock import patch

from install_skills import (
    SUPPORTED_PLATFORMS,
    SkillInfo,
    discover_skills,
    find_project_root,
    get_install_path,
    install_skill,
    install_skills,
    list_skills,
    main,
    parse_args,
)


class TestSkillInfo:
    """Test SkillInfo dataclass"""

    def test_to_dict(self, tmp_path):
        skill = SkillInfo(
            name="test-skill",
            category="",
            path=tmp_path,
            description="Test description",
        )
        d = skill.to_dict()
        assert d["name"] == "test-skill"
        assert d["description"] == "Test description"


class TestDiscoverSkills:
    """Test skill discovery (flat structure)"""

    def test_discover_skills(self, tmp_path):
        # Create flat skill structure
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
---
""")

        skills = discover_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert skills[0].category == ""  # Flat structure

    def test_discover_no_skills(self, tmp_path):
        skills = discover_skills(tmp_path)
        assert len(skills) == 0

    def test_discover_missing_dir(self, tmp_path):
        missing = tmp_path / "nonexistent"
        skills = discover_skills(missing)
        assert len(skills) == 0

    def test_discover_extracts_description(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: My awesome skill
version: 1.0.0
---
""")

        skills = discover_skills(tmp_path)
        assert len(skills) == 1
        assert "awesome" in skills[0].description


class TestGetInstallPath:
    """Test install path detection"""

    def test_claude_code_path(self):
        path = get_install_path("claude-code")
        assert path is not None
        assert "claude" in str(path).lower()

    def test_codex_path(self):
        path = get_install_path("codex")
        assert path is not None

    def test_copilot_path(self):
        path = get_install_path("copilot")
        assert path is not None

    def test_cursor_path(self):
        path = get_install_path("cursor")
        assert path is not None

    def test_unknown_platform(self):
        path = get_install_path("unknown-platform")
        assert path is None

    def test_all_platforms_defined(self):
        for platform in SUPPORTED_PLATFORMS:
            path = get_install_path(platform)
            assert path is not None, f"No path for {platform}"


class TestInstallSkill:
    """Test skill installation (flat structure)"""

    def test_install_with_symlink(self, tmp_path):
        # Create source skill
        source = tmp_path / "source" / "skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("test")

        skill = SkillInfo(name="skill", category="", path=source)
        target = tmp_path / "target"

        result = install_skill(skill, target, use_symlink=True)
        assert result is True
        assert (target / "skill").is_symlink()

    def test_install_with_copy(self, tmp_path):
        # Create source skill
        source = tmp_path / "source" / "skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("test")

        skill = SkillInfo(name="skill", category="", path=source)
        target = tmp_path / "target"

        result = install_skill(skill, target, use_symlink=False)
        assert result is True
        assert (target / "skill").is_dir()
        assert not (target / "skill").is_symlink()

    def test_install_overwrites_existing(self, tmp_path):
        # Create source and existing target
        source = tmp_path / "source" / "skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("new")

        target = tmp_path / "target"
        existing = target / "skill"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("old")

        skill = SkillInfo(name="skill", category="", path=source)
        result = install_skill(skill, target, use_symlink=False)

        assert result is True
        assert (target / "skill" / "SKILL.md").read_text() == "new"


class TestInstallSkills:
    """Test batch installation"""

    def test_install_multiple(self, tmp_path):
        # Create skills (flat structure)
        for i in range(3):
            skill_dir = tmp_path / "source" / f"skill-{i}"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("test")

        skills = []
        for i in range(3):
            skill_path = tmp_path / "source" / f"skill-{i}"
            skills.append(SkillInfo(name=f"skill-{i}", category="", path=skill_path))

        # Mock get_install_path to return tmp target
        target = tmp_path / "target"
        with patch("install_skills.get_install_path", return_value=target):
            success, failed = install_skills(skills, "claude-code")

        assert success == 3
        assert failed == 0

    def test_install_unsupported_platform(self, tmp_path, capsys):
        skills = [SkillInfo(name="test", category="", path=tmp_path)]

        with patch("install_skills.get_install_path", return_value=None):
            success, failed = install_skills(skills, "unknown")

        assert success == 0
        assert failed == 1


class TestListSkills:
    """Test skill listing"""

    def test_list_table(self, tmp_path, capsys):
        skills = [
            SkillInfo(name="skill-a", category="", path=tmp_path, description="Desc A"),
            SkillInfo(name="skill-b", category="", path=tmp_path, description="Desc B"),
        ]

        list_skills(skills)
        captured = capsys.readouterr()
        assert "skill-a" in captured.out
        assert "skill-b" in captured.out

    def test_list_json(self, tmp_path, capsys):
        skills = [SkillInfo(name="test", category="", path=tmp_path)]

        list_skills(skills, json_output=True)
        captured = capsys.readouterr()
        assert '"name": "test"' in captured.out


class TestParseArgs:
    """Test argument parsing"""

    def test_default_args(self):
        with patch.object(sys, "argv", ["install_skills.py"]):
            args = parse_args()
            assert args.platform == "claude-code"
            assert args.list_skills is False

    def test_platform_arg(self):
        with patch.object(sys, "argv", ["install_skills.py", "--platform", "codex"]):
            args = parse_args()
            assert args.platform == "codex"

    def test_list_flag(self):
        with patch.object(sys, "argv", ["install_skills.py", "--list"]):
            args = parse_args()
            assert args.list_skills is True

    def test_skill_filter(self):
        with patch.object(sys, "argv", ["install_skills.py", "--skill", "my-skill"]):
            args = parse_args()
            assert args.skill_filter == "my-skill"

    def test_copy_flag(self):
        with patch.object(sys, "argv", ["install_skills.py", "--copy"]):
            args = parse_args()
            assert args.copy is True


class TestFindProjectRoot:
    """Test project root detection"""

    def test_finds_root(self):
        root = find_project_root()
        assert (root / "pyproject.toml").exists()


class TestMain:
    """Test main entry point"""

    def test_main_list(self, capsys):
        with patch.object(sys, "argv", ["install_skills.py", "--list"]):
            exit_code = main()
            captured = capsys.readouterr()
            assert "Available Skills" in captured.out
            assert exit_code == 0

    def test_main_list_json(self, capsys):
        with patch.object(sys, "argv", ["install_skills.py", "--list", "--json"]):
            exit_code = main()
            captured = capsys.readouterr()
            assert '"name"' in captured.out
            assert exit_code == 0

    def test_main_no_skills(self, tmp_path):
        with patch.object(sys, "argv", ["install_skills.py", "--skills-dir", str(tmp_path)]):
            exit_code = main()
            assert exit_code == 1

    def test_main_skill_not_found(self):
        with patch.object(sys, "argv", ["install_skills.py", "--skill", "nonexistent-skill"]):
            exit_code = main()
            assert exit_code == 1
