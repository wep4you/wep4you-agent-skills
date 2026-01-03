"""
Tests for scripts/validate_skills.py
"""

from __future__ import annotations

import json
import sys
from unittest.mock import patch

from validate_skills import (
    PluginValidationResult,
    ValidationResult,
    extract_frontmatter,
    main,
    print_plugin_results,
    print_results,
    validate_all_skills,
    validate_plugin,
    validate_skill_md,
)


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_is_valid_with_no_errors(self):
        result = ValidationResult(skill_name="test", skill_path="/path")
        assert result.is_valid is True

    def test_is_valid_with_errors(self):
        result = ValidationResult(skill_name="test", skill_path="/path", errors=["Some error"])
        assert result.is_valid is False

    def test_to_dict(self):
        result = ValidationResult(
            skill_name="test-skill",
            skill_path="/path/to/skill",
            errors=["error1"],
            warnings=["warning1"],
        )
        d = result.to_dict()
        assert d["skill_name"] == "test-skill"
        assert d["skill_path"] == "/path/to/skill"
        assert d["valid"] is False
        assert d["errors"] == ["error1"]
        assert d["warnings"] == ["warning1"]


class TestExtractFrontmatter:
    """Test frontmatter extraction"""

    def test_valid_frontmatter(self):
        content = """---
name: test-skill
description: A test skill
version: 1.0.0
---

# Content here
"""
        result = extract_frontmatter(content)
        assert result is not None
        assert result["name"] == "test-skill"
        assert result["description"] == "A test skill"
        assert result["version"] == "1.0.0"

    def test_no_frontmatter(self):
        content = "# Just a heading\n\nNo frontmatter here."
        result = extract_frontmatter(content)
        assert result is None

    def test_empty_frontmatter(self):
        content = """---

---

# Empty frontmatter
"""
        result = extract_frontmatter(content)
        assert result == {}


class TestValidateSkillMd:
    """Test single skill validation"""

    def test_missing_skill_md(self, tmp_path):
        result = validate_skill_md(tmp_path)
        assert "Missing SKILL.md file" in result.errors

    def test_missing_frontmatter(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# No frontmatter")
        result = validate_skill_md(tmp_path)
        assert "Missing YAML frontmatter" in result.errors[0]

    def test_missing_name(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
description: A skill without name
---
""")
        result = validate_skill_md(tmp_path)
        assert any("Missing required 'name'" in e for e in result.errors)

    def test_empty_name(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name:
description: A skill with empty name
---
""")
        result = validate_skill_md(tmp_path)
        assert any("'name' field is empty" in e for e in result.errors)

    def test_invalid_name_format(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: Invalid_Name
description: A skill with wrong name format
---
""")
        result = validate_skill_md(tmp_path)
        assert any("kebab-case" in e for e in result.errors)

    def test_name_too_long(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        long_name = "a" * 65
        skill_file.write_text(f"""---
name: {long_name}
description: A skill with too long name
---
""")
        result = validate_skill_md(tmp_path)
        assert any("64 character limit" in e for e in result.errors)

    def test_missing_description(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
---
""")
        result = validate_skill_md(tmp_path)
        assert any("Missing required 'description'" in e for e in result.errors)

    def test_empty_description(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description:
---
""")
        result = validate_skill_md(tmp_path)
        assert any("'description' field is empty" in e for e in result.errors)

    def test_valid_skill(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A valid test skill
version: 1.0.0
author: Test Author
license: MIT
---
""")
        # Create scripts directory
        (tmp_path / "scripts").mkdir()
        result = validate_skill_md(tmp_path)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_missing_version_warning(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A valid test skill
---
""")
        (tmp_path / "scripts").mkdir()
        result = validate_skill_md(tmp_path)
        assert any("Missing recommended 'version'" in w for w in result.warnings)

    def test_invalid_version_format_warning(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A valid test skill
version: v1.0
---
""")
        (tmp_path / "scripts").mkdir()
        result = validate_skill_md(tmp_path)
        assert any("semver format" in w for w in result.warnings)

    def test_missing_directories_warning(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A valid test skill
version: 1.0.0
author: Test
license: MIT
---
""")
        result = validate_skill_md(tmp_path)
        assert any("scripts/" in w or "config/" in w for w in result.warnings)


class TestValidateAllSkills:
    """Test all skills validation"""

    def test_missing_skills_directory(self, tmp_path):
        missing_dir = tmp_path / "nonexistent"
        results, error = validate_all_skills(missing_dir)
        assert error == 1
        assert len(results) == 0

    def test_empty_skills_directory(self, tmp_path):
        results, error = validate_all_skills(tmp_path)
        assert error == 0
        assert len(results) == 0

    def test_single_valid_skill(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
version: 1.0.0
author: Test
license: MIT
---
""")
        (skill_dir / "scripts").mkdir()
        results, error = validate_all_skills(tmp_path)
        assert error == 0
        assert len(results) == 1
        assert results[0].is_valid

    def test_skill_filter(self, tmp_path):
        # Create two skills
        for name in ["skill-a", "skill-b"]:
            skill_dir = tmp_path / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"""---
name: {name}
description: Test skill {name}
---
""")
        results, _error = validate_all_skills(tmp_path, skill_filter="skill-a")
        assert len(results) == 1
        assert results[0].skill_name == "skill-a"


class TestPrintResults:
    """Test result printing"""

    def test_json_output_valid(self, tmp_path, capsys):
        results = [ValidationResult(skill_name="test", skill_path="/path", errors=[], warnings=[])]
        exit_code = print_results(results, json_output=True)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["total_skills"] == 1
        assert output["valid_skills"] == 1
        assert exit_code == 0

    def test_json_output_invalid(self, tmp_path, capsys):
        results = [
            ValidationResult(skill_name="test", skill_path="/path", errors=["Error"], warnings=[])
        ]
        exit_code = print_results(results, json_output=True)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["valid_skills"] == 0
        assert exit_code == 1

    def test_no_results(self, capsys):
        exit_code = print_results([])
        captured = capsys.readouterr()
        assert "No SKILL.md files found" in captured.out
        assert exit_code == 0

    def test_verbose_warnings(self, capsys):
        results = [
            ValidationResult(
                skill_name="test", skill_path="/path", errors=[], warnings=["Warning1"]
            )
        ]
        exit_code = print_results(results, verbose=True)
        captured = capsys.readouterr()
        assert "Warning1" in captured.out
        assert exit_code == 0


class TestEdgeCases:
    """Test edge cases for better coverage"""

    def test_description_too_long(self, tmp_path):
        """Test description exceeding 1024 chars"""
        skill_file = tmp_path / "SKILL.md"
        long_desc = "x" * 1025
        skill_file.write_text(f"""---
name: test-skill
description: {long_desc}
---
""")
        result = validate_skill_md(tmp_path)
        assert any("1024 character limit" in e for e in result.errors)

    def test_skill_md_too_many_lines(self, tmp_path):
        """Test SKILL.md with more than 500 lines"""
        skill_file = tmp_path / "SKILL.md"
        many_lines = "\n".join(["# Line"] * 510)
        skill_file.write_text(f"""---
name: test-skill
description: A test skill
version: 1.0.0
author: Test
license: MIT
---

{many_lines}
""")
        (tmp_path / "scripts").mkdir()
        result = validate_skill_md(tmp_path)
        assert any("lines" in w and "500" in w for w in result.warnings)

    def test_missing_directory_json_output(self, tmp_path, capsys):
        """Test JSON output when skills directory is missing"""
        missing_dir = tmp_path / "nonexistent"
        _results, error = validate_all_skills(missing_dir, json_output=True)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "error" in output
        assert error == 1

    def test_print_results_with_errors(self, capsys):
        """Test printing results with validation errors"""
        results = [
            ValidationResult(
                skill_name="broken-skill",
                skill_path="/path/to/skill",
                errors=["Missing name", "Invalid format"],
                warnings=[],
            )
        ]
        exit_code = print_results(results, verbose=False, json_output=False)
        captured = capsys.readouterr()
        assert "Validation Failed" in captured.out
        assert "broken-skill" in captured.out
        assert "Missing name" in captured.out
        assert exit_code == 1


class TestMain:
    """Test main entry point"""

    def test_main_with_real_skills(self):
        # Test with actual skills directory
        with patch.object(sys, "argv", ["validate-skills.py"]):
            exit_code = main()
            assert exit_code == 0

    def test_main_with_json_output(self, capsys):
        with patch.object(sys, "argv", ["validate-skills.py", "--json"]):
            exit_code = main()
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "total_skills" in output
            assert exit_code == 0

    def test_main_with_verbose(self):
        with patch.object(sys, "argv", ["validate-skills.py", "--verbose"]):
            exit_code = main()
            assert exit_code == 0

    def test_main_with_missing_directory(self, tmp_path):
        """Test main with non-existent skills directory"""
        missing_dir = tmp_path / "nonexistent"
        with patch.object(sys, "argv", ["validate-skills.py", "--skills-dir", str(missing_dir)]):
            exit_code = main()
            assert exit_code == 1

    def test_main_with_invalid_skill(self, tmp_path):
        """Test main with invalid skill that causes error"""
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter")

        with patch.object(sys, "argv", ["validate-skills.py", "--skills-dir", str(tmp_path)]):
            exit_code = main()
            assert exit_code == 1


class TestPluginValidationResult:
    """Test PluginValidationResult dataclass"""

    def test_is_valid_with_no_errors(self):
        result = PluginValidationResult()
        assert result.is_valid is True

    def test_is_valid_with_errors(self):
        result = PluginValidationResult(errors=["Some error"])
        assert result.is_valid is False

    def test_to_dict(self):
        result = PluginValidationResult(
            errors=["error1"],
            warnings=["warning1"],
            plugin_version="1.0.0",
            skill_versions={"test": "1.0.0"},
        )
        d = result.to_dict()
        assert d["valid"] is False
        assert d["errors"] == ["error1"]
        assert d["warnings"] == ["warning1"]
        assert d["plugin_version"] == "1.0.0"
        assert d["skill_versions"] == {"test": "1.0.0"}


class TestValidatePlugin:
    """Test plugin validation"""

    def test_missing_plugin_dir(self, tmp_path):
        result = validate_plugin(tmp_path)
        assert "Missing .claude-plugin/ directory" in result.errors

    def test_missing_plugin_json(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        result = validate_plugin(tmp_path)
        assert "Missing .claude-plugin/plugin.json" in result.errors

    def test_invalid_plugin_json(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text("invalid json{")
        result = validate_plugin(tmp_path)
        assert any("Invalid JSON" in e for e in result.errors)

    def test_missing_required_fields(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text("{}")
        result = validate_plugin(tmp_path)
        assert any("Missing required 'name'" in e for e in result.errors)
        assert any("Missing required 'version'" in e for e in result.errors)
        assert any("Missing required 'skills'" in e for e in result.errors)

    def test_missing_recommended_fields(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            '{"name": "test", "version": "1.0.0", "skills": []}'
        )
        result = validate_plugin(tmp_path)
        assert any("Missing recommended 'description'" in w for w in result.warnings)
        assert any("Missing recommended 'author'" in w for w in result.warnings)
        assert any("Missing recommended 'license'" in w for w in result.warnings)

    def test_missing_marketplace_json_warning(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            '{"name": "test", "version": "1.0.0", "skills": [], '
            '"description": "desc", "author": "auth", "license": "MIT"}'
        )
        result = validate_plugin(tmp_path)
        assert any("marketplace.json" in w for w in result.warnings)

    def test_invalid_marketplace_json(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            '{"name": "test", "version": "1.0.0", "skills": []}'
        )
        (plugin_dir / "marketplace.json").write_text("not valid json")
        result = validate_plugin(tmp_path)
        assert any("marketplace.json" in e and "Invalid JSON" in e for e in result.errors)

    def test_missing_commands_dir_warning(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            '{"name": "test", "version": "1.0.0", "skills": []}'
        )
        result = validate_plugin(tmp_path)
        assert any("commands/" in w for w in result.warnings)

    def test_command_without_frontmatter(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            '{"name": "test", "version": "1.0.0", "skills": []}'
        )
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "test.md").write_text("# No frontmatter")
        result = validate_plugin(tmp_path)
        assert any("test.md" in w and "frontmatter" in w for w in result.warnings)

    def test_valid_plugin(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            '{"name": "test", "version": "1.0.0", "skills": [], '
            '"description": "desc", "author": "auth", "license": "MIT"}'
        )
        (plugin_dir / "marketplace.json").write_text('{"name": "marketplace"}')
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "test.md").write_text("---\ndescription: test\n---\n")
        result = validate_plugin(tmp_path)
        assert result.is_valid
        assert result.plugin_version == "1.0.0"

    def test_collects_skill_versions(self, tmp_path):
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            '{"name": "test", "version": "1.0.0", "skills": []}'
        )
        skills_dir = tmp_path / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\nversion: 2.0.0\n---\n")
        result = validate_plugin(tmp_path)
        assert "test-skill" in result.skill_versions
        assert result.skill_versions["test-skill"] == "2.0.0"


class TestPrintPluginResults:
    """Test plugin result printing"""

    def test_json_output_valid(self, capsys):
        result = PluginValidationResult(plugin_version="1.0.0")
        exit_code = print_plugin_results(result, json_output=True)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["plugin_validation"]["valid"] is True
        assert exit_code == 0

    def test_json_output_invalid(self, capsys):
        result = PluginValidationResult(errors=["Error"])
        exit_code = print_plugin_results(result, json_output=True)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["plugin_validation"]["valid"] is False
        assert exit_code == 1

    def test_print_with_errors(self, capsys):
        result = PluginValidationResult(errors=["Missing plugin.json"])
        exit_code = print_plugin_results(result)
        captured = capsys.readouterr()
        assert "Plugin Validation Failed" in captured.out
        assert "Missing plugin.json" in captured.out
        assert exit_code == 1

    def test_verbose_with_warnings(self, capsys):
        result = PluginValidationResult(warnings=["Warning1"])
        exit_code = print_plugin_results(result, verbose=True)
        captured = capsys.readouterr()
        assert "Warning1" in captured.out
        assert exit_code == 0

    def test_verbose_with_versions(self, capsys):
        result = PluginValidationResult(
            plugin_version="1.0.0", skill_versions={"skill1": "2.0.0"}
        )
        exit_code = print_plugin_results(result, verbose=True)
        captured = capsys.readouterr()
        assert "1.0.0" in captured.out
        assert "skill1" in captured.out
        assert exit_code == 0


class TestMainPlugin:
    """Test main with --plugin flag"""

    def test_main_with_plugin_flag(self):
        with patch.object(sys, "argv", ["validate-skills.py", "--plugin"]):
            exit_code = main()
            assert exit_code == 0

    def test_main_with_plugin_and_verbose(self, capsys):
        with patch.object(sys, "argv", ["validate-skills.py", "--plugin", "--verbose"]):
            exit_code = main()
            captured = capsys.readouterr()
            assert "Plugin version" in captured.out or "validated successfully" in captured.out
            assert exit_code == 0

    def test_main_with_plugin_and_json(self, capsys):
        with patch.object(sys, "argv", ["validate-skills.py", "--plugin", "--json"]):
            exit_code = main()
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "plugin_validation" in output
            assert exit_code == 0

    def test_main_plugin_missing_dir(self, tmp_path):
        with patch.object(
            sys, "argv", ["validate-skills.py", "--plugin", "--root-dir", str(tmp_path)]
        ):
            exit_code = main()
            assert exit_code == 1
