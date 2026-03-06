"""
Tests for scripts/extract_dependencies.py
"""

from __future__ import annotations

import sys
from unittest.mock import patch

from extract_dependencies import (
    ScriptDependencies,
    extract_all_dependencies,
    extract_pep723_block,
    extract_script_dependencies,
    find_project_root,
    find_skill_scripts,
    main,
    parse_args,
    parse_pep723_metadata,
    print_results,
)


class TestScriptDependencies:
    """Test ScriptDependencies dataclass"""

    def test_to_dict(self):
        deps = ScriptDependencies(
            script_path="/path/to/script.py",
            skill_name="test-skill",
            python_requires=">=3.10",
            dependencies=["pyyaml>=6.0"],
        )
        d = deps.to_dict()
        assert d["script_path"] == "/path/to/script.py"
        assert d["skill_name"] == "test-skill"
        assert d["python_requires"] == ">=3.10"
        assert d["dependencies"] == ["pyyaml>=6.0"]
        assert d["parse_error"] is None

    def test_to_dict_with_error(self):
        deps = ScriptDependencies(
            script_path="/path/to/script.py",
            skill_name="test-skill",
            python_requires="",
            parse_error="Some error",
        )
        d = deps.to_dict()
        assert d["parse_error"] == "Some error"


class TestExtractPep723Block:
    """Test PEP 723 block extraction"""

    def test_extracts_block(self):
        content = """#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///

import sys
"""
        block = extract_pep723_block(content)
        assert block is not None
        assert "requires-python" in block
        assert "dependencies" in block

    def test_no_block(self):
        content = "#!/usr/bin/env python\nimport sys\n"
        block = extract_pep723_block(content)
        assert block is None

    def test_multiline_dependencies(self):
        content = """# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
#     "requests>=2.31",
# ]
# ///
"""
        block = extract_pep723_block(content)
        assert block is not None
        assert "pyyaml" in block
        assert "requests" in block


class TestParsePep723Metadata:
    """Test PEP 723 metadata parsing"""

    def test_parse_simple(self):
        block = """# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
"""
        metadata = parse_pep723_metadata(block)
        assert metadata["requires-python"] == ">=3.10"
        assert metadata["dependencies"] == ["pyyaml>=6.0"]

    def test_parse_multiline_deps(self):
        block = """# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
#     "requests>=2.31",
# ]
"""
        metadata = parse_pep723_metadata(block)
        assert metadata["requires-python"] == ">=3.10"
        assert "pyyaml>=6.0" in metadata["dependencies"]
        assert "requests>=2.31" in metadata["dependencies"]

    def test_parse_empty_deps(self):
        block = """# requires-python = ">=3.10"
# dependencies = []
"""
        metadata = parse_pep723_metadata(block)
        assert metadata["dependencies"] == []

    def test_parse_no_deps(self):
        block = """# requires-python = ">=3.10"
"""
        metadata = parse_pep723_metadata(block)
        assert metadata["dependencies"] == []


class TestExtractScriptDependencies:
    """Test script dependency extraction"""

    def test_extract_valid_script(self, tmp_path):
        script = tmp_path / "skills" / "obsidian" / "test-skill" / "scripts" / "main.py"
        script.parent.mkdir(parents=True)
        script.write_text("""#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///

import yaml
""")
        deps = extract_script_dependencies(script)
        assert deps.skill_name == "test-skill"
        assert deps.python_requires == ">=3.10"
        assert "pyyaml>=6.0" in deps.dependencies
        assert deps.parse_error is None

    def test_extract_no_metadata(self, tmp_path):
        script = tmp_path / "script.py"
        script.write_text("import sys\n")
        deps = extract_script_dependencies(script)
        assert deps.parse_error == "No PEP 723 metadata block found"

    def test_extract_unreadable_file(self, tmp_path):
        script = tmp_path / "nonexistent.py"
        deps = extract_script_dependencies(script)
        assert deps.parse_error is not None
        assert "Failed to read file" in deps.parse_error


class TestFindSkillScripts:
    """Test script discovery"""

    def test_finds_scripts(self, tmp_path):
        # Create skill structure
        skill_dir = tmp_path / "obsidian" / "test-skill" / "scripts"
        skill_dir.mkdir(parents=True)
        (skill_dir / "main.py").write_text("# script")
        (skill_dir / "helper.py").write_text("# helper")

        scripts = find_skill_scripts(tmp_path)
        assert len(scripts) == 2

    def test_ignores_pycache(self, tmp_path):
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "cache.py").write_text("# cache")
        (tmp_path / "main.py").write_text("# script")

        scripts = find_skill_scripts(tmp_path)
        assert len(scripts) == 1

    def test_ignores_test_files(self, tmp_path):
        (tmp_path / "main.py").write_text("# script")
        (tmp_path / "test_main.py").write_text("# test")

        scripts = find_skill_scripts(tmp_path)
        assert len(scripts) == 1


class TestExtractAllDependencies:
    """Test full extraction"""

    def test_extracts_and_consolidates(self, tmp_path):
        # Create two skills with overlapping deps
        skill1 = tmp_path / "skill1" / "scripts"
        skill1.mkdir(parents=True)
        (skill1 / "main.py").write_text("""# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "requests>=2.31"]
# ///
""")

        skill2 = tmp_path / "skill2" / "scripts"
        skill2.mkdir(parents=True)
        (skill2 / "main.py").write_text("""# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
""")

        results, consolidated = extract_all_dependencies(tmp_path)
        assert len(results) == 2
        assert "pyyaml" in consolidated
        assert "requests" in consolidated


class TestPrintResults:
    """Test result printing"""

    def test_json_output(self, capsys):
        results = [
            ScriptDependencies(
                script_path="/path/to/script.py",
                skill_name="test",
                python_requires=">=3.10",
                dependencies=["pyyaml>=6.0"],
            )
        ]
        consolidated = {"pyyaml": ["pyyaml>=6.0"]}
        exit_code = print_results(results, consolidated, json_output=True)
        captured = capsys.readouterr()
        assert "total_scripts" in captured.out
        assert exit_code == 0

    def test_requirements_output(self, capsys):
        results = []
        consolidated = {"pyyaml": ["pyyaml>=6.0"], "requests": ["requests>=2.31"]}
        exit_code = print_results(results, consolidated, output_format="requirements")
        captured = capsys.readouterr()
        assert "pyyaml>=6.0" in captured.out
        assert "requests>=2.31" in captured.out
        assert exit_code == 0

    def test_table_output_with_errors(self, capsys):
        results = [
            ScriptDependencies(
                script_path="/path/to/script.py",
                skill_name="test",
                python_requires="",
                parse_error="Some error",
            )
        ]
        exit_code = print_results(results, {})
        captured = capsys.readouterr()
        assert "Errors" in captured.out
        assert exit_code == 1


class TestParseArgs:
    """Test argument parsing"""

    def test_default_args(self):
        with patch.object(sys, "argv", ["extract_dependencies.py"]):
            args = parse_args()
            assert args.format == "table"
            assert args.json_output is False

    def test_json_flag(self):
        with patch.object(sys, "argv", ["extract_dependencies.py", "--json"]):
            args = parse_args()
            assert args.json_output is True

    def test_format_requirements(self):
        with patch.object(sys, "argv", ["extract_dependencies.py", "--format", "requirements"]):
            args = parse_args()
            assert args.format == "requirements"


class TestFindProjectRoot:
    """Test project root detection"""

    def test_finds_root(self):
        root = find_project_root()
        assert (root / "pyproject.toml").exists()


class TestMain:
    """Test main entry point"""

    def test_main_success(self):
        with patch.object(sys, "argv", ["extract_dependencies.py"]):
            exit_code = main()
            assert exit_code == 0

    def test_main_json(self, capsys):
        with patch.object(sys, "argv", ["extract_dependencies.py", "--json"]):
            exit_code = main()
            captured = capsys.readouterr()
            assert "total_scripts" in captured.out
            assert exit_code == 0

    def test_main_missing_dir(self, tmp_path):
        missing = tmp_path / "nonexistent"
        with patch.object(sys, "argv", ["extract_dependencies.py", "--skills-dir", str(missing)]):
            exit_code = main()
            assert exit_code == 1

    def test_main_missing_dir_json(self, tmp_path, capsys):
        missing = tmp_path / "nonexistent"
        with patch.object(
            sys, "argv", ["extract_dependencies.py", "--skills-dir", str(missing), "--json"]
        ):
            exit_code = main()
            captured = capsys.readouterr()
            assert "error" in captured.out
            assert exit_code == 1
