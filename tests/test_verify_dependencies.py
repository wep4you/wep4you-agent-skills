"""
Tests for scripts/verify_dependencies.py
"""

from __future__ import annotations

import sys
from unittest.mock import patch

from verify_dependencies import (
    KNOWN_PACKAGES,
    VerificationResult,
    check_lock_file_exists,
    check_typosquatting,
    find_project_root,
    main,
    parse_args,
    parse_lock_file,
    print_results,
    verify_dependencies,
    verify_hash_format,
    verify_lock_file_sync,
)


class TestVerificationResult:
    """Test VerificationResult dataclass"""

    def test_is_valid_default(self):
        result = VerificationResult()
        assert result.is_valid is True

    def test_is_valid_with_errors(self):
        result = VerificationResult(hash_errors=["error"])
        assert result.is_valid is False

    def test_is_valid_lock_missing(self):
        result = VerificationResult(lock_file_exists=False)
        assert result.is_valid is False

    def test_is_valid_lock_invalid(self):
        result = VerificationResult(lock_file_valid=False)
        assert result.is_valid is False

    def test_to_dict(self):
        result = VerificationResult(
            packages_verified=10,
            hash_errors=["error1"],
            suspicious_packages=["pkg1"],
        )
        d = result.to_dict()
        assert d["packages_verified"] == 10
        assert d["hash_errors"] == ["error1"]
        assert d["suspicious_packages"] == ["pkg1"]
        assert d["valid"] is False


class TestCheckLockFileExists:
    """Test lock file existence check"""

    def test_exists(self, tmp_path):
        (tmp_path / "uv.lock").write_text("test")
        assert check_lock_file_exists(tmp_path) is True

    def test_not_exists(self, tmp_path):
        assert check_lock_file_exists(tmp_path) is False


class TestVerifyLockFileSync:
    """Test lock file sync verification"""

    def test_success(self):
        # Test with real project root
        root = find_project_root()
        is_synced, _msg = verify_lock_file_sync(root)
        assert is_synced is True

    def test_uv_not_found(self, tmp_path):
        with patch("shutil.which", return_value=None):
            is_synced, msg = verify_lock_file_sync(tmp_path)
            assert is_synced is False
            assert "not found" in msg


class TestParseLockFile:
    """Test lock file parsing"""

    def test_parse_simple(self, tmp_path):
        lock_content = """version = 1

[[package]]
name = "pyyaml"
version = "6.0"
sdist = { url = "...", hash = "sha256:abc123def456" }
wheels = [
    { url = "...", hash = "sha256:789ghi012jkl" },
]

[[package]]
name = "requests"
version = "2.31.0"
"""
        (tmp_path / "uv.lock").write_text(lock_content)
        packages = parse_lock_file(tmp_path)
        assert len(packages) == 2
        assert packages[0]["name"] == "pyyaml"
        assert "sha256:abc123def456" in packages[0]["hashes"]

    def test_parse_no_hashes(self, tmp_path):
        lock_content = """[[package]]
name = "test"
version = "1.0"
"""
        (tmp_path / "uv.lock").write_text(lock_content)
        packages = parse_lock_file(tmp_path)
        assert len(packages) == 1
        assert "hashes" not in packages[0]


class TestCheckTyposquatting:
    """Test typosquatting detection"""

    def test_known_package(self):
        warnings = check_typosquatting("pyyaml")
        assert len(warnings) == 0

    def test_suspicious_python_prefix(self):
        warnings = check_typosquatting("python-unknown")
        assert len(warnings) > 0
        assert "python-" in warnings[0]

    def test_suspicious_py_prefix(self):
        warnings = check_typosquatting("py-unknown")
        assert len(warnings) > 0

    def test_suspicious_python_suffix(self):
        warnings = check_typosquatting("something-python")
        assert len(warnings) > 0

    def test_normal_package(self):
        warnings = check_typosquatting("normal-package")
        assert len(warnings) == 0

    def test_known_packages_list(self):
        # All known packages should pass without warnings
        for pkg in KNOWN_PACKAGES:
            warnings = check_typosquatting(pkg)
            assert len(warnings) == 0


class TestVerifyHashFormat:
    """Test hash format verification"""

    def test_valid_sha256(self):
        valid_hash = "sha256:" + "a" * 64
        assert verify_hash_format(valid_hash) is True

    def test_invalid_prefix(self):
        invalid_hash = "md5:" + "a" * 64
        assert verify_hash_format(invalid_hash) is False

    def test_invalid_length(self):
        invalid_hash = "sha256:" + "a" * 32
        assert verify_hash_format(invalid_hash) is False

    def test_invalid_chars(self):
        invalid_hash = "sha256:" + "g" * 64
        assert verify_hash_format(invalid_hash) is False


class TestVerifyDependencies:
    """Test full verification"""

    def test_missing_lock_file(self, tmp_path):
        result = verify_dependencies(tmp_path)
        assert result.lock_file_exists is False
        assert result.is_valid is False

    def test_real_project(self):
        root = find_project_root()
        result = verify_dependencies(root)
        assert result.lock_file_exists is True
        assert result.lock_file_valid is True
        assert result.packages_verified > 0

    def test_with_typosquatting_check(self):
        root = find_project_root()
        result = verify_dependencies(root, check_typo=True)
        assert result.is_valid is True


class TestPrintResults:
    """Test result printing"""

    def test_json_output_valid(self, capsys):
        result = VerificationResult(packages_verified=10)
        exit_code = print_results(result, json_output=True)
        captured = capsys.readouterr()
        assert '"valid": true' in captured.out
        assert exit_code == 0

    def test_json_output_invalid(self, capsys):
        result = VerificationResult(hash_errors=["error"])
        exit_code = print_results(result, json_output=True)
        captured = capsys.readouterr()
        assert '"valid": false' in captured.out
        assert exit_code == 1

    def test_table_output_valid(self, capsys):
        result = VerificationResult(packages_verified=10)
        exit_code = print_results(result)
        captured = capsys.readouterr()
        assert "Packages verified: 10" in captured.out
        assert exit_code == 0

    def test_table_output_missing_lock(self, capsys):
        result = VerificationResult(lock_file_exists=False)
        exit_code = print_results(result)
        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert exit_code == 1

    def test_table_output_invalid_lock(self, capsys):
        result = VerificationResult(lock_file_valid=False, hash_errors=["sync error"])
        exit_code = print_results(result)
        captured = capsys.readouterr()
        assert "validation failed" in captured.out.lower()
        assert exit_code == 1

    def test_table_output_with_warnings(self, capsys):
        result = VerificationResult(
            packages_verified=5,
            suspicious_packages=["test: suspicious"],
        )
        print_results(result)
        captured = capsys.readouterr()
        assert "Suspicious packages" in captured.out


class TestParseArgs:
    """Test argument parsing"""

    def test_default_args(self):
        with patch.object(sys, "argv", ["verify_dependencies.py"]):
            args = parse_args()
            assert args.json_output is False
            assert args.check_typo is False

    def test_json_flag(self):
        with patch.object(sys, "argv", ["verify_dependencies.py", "--json"]):
            args = parse_args()
            assert args.json_output is True

    def test_typosquatting_flag(self):
        with patch.object(sys, "argv", ["verify_dependencies.py", "--check-typosquatting"]):
            args = parse_args()
            assert args.check_typo is True


class TestFindProjectRoot:
    """Test project root detection"""

    def test_finds_root(self):
        root = find_project_root()
        assert (root / "pyproject.toml").exists()


class TestMain:
    """Test main entry point"""

    def test_main_success(self):
        with patch.object(sys, "argv", ["verify_dependencies.py"]):
            exit_code = main()
            assert exit_code == 0

    def test_main_json(self, capsys):
        with patch.object(sys, "argv", ["verify_dependencies.py", "--json"]):
            exit_code = main()
            captured = capsys.readouterr()
            assert "valid" in captured.out
            assert exit_code == 0

    def test_main_missing_dir(self, tmp_path):
        missing = tmp_path / "nonexistent"
        argv = ["verify_dependencies.py", "--project-dir", str(missing)]
        with patch.object(sys, "argv", argv):
            exit_code = main()
            assert exit_code == 1
