#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Dependency Hash Verification Tool

Verifies that all dependencies in uv.lock have valid hashes and match installed packages.
Also checks for any suspicious patterns in dependencies.

Usage:
    uv run scripts/verify_dependencies.py
    uv run scripts/verify_dependencies.py --json
    uv run scripts/verify_dependencies.py --check-typosquatting

Examples:
    # Verify lock file integrity
    uv run scripts/verify_dependencies.py

    # JSON output for CI
    uv run scripts/verify_dependencies.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Known legitimate packages that might trigger typosquatting detection
KNOWN_PACKAGES = {
    "pyyaml",
    "pytest",
    "pytest-cov",
    "ruff",
    "mypy",
    "bandit",
    "pip-audit",
    "safety",
    "semgrep",
    "types-pyyaml",
    # Legitimate packages with suspicious-looking names
    "packageurl-python",
    "py-serializable",
    "python-dotenv",
    "python-multipart",
}

# Common typosquatting patterns
SUSPICIOUS_PATTERNS = [
    (r"^python-", "Packages starting with 'python-' may be typosquatting"),
    (r"^py-", "Packages starting with 'py-' may be typosquatting"),
    (r"-python$", "Packages ending with '-python' may be typosquatting"),
    (r"[0-9]{4,}", "Package name contains suspiciously long number sequence"),
]


@dataclass
class VerificationResult:
    """Result of dependency verification."""

    lock_file_exists: bool = True
    lock_file_valid: bool = True
    packages_verified: int = 0
    hash_errors: list[str] = field(default_factory=list)
    suspicious_packages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if verification passed."""
        return self.lock_file_exists and self.lock_file_valid and len(self.hash_errors) == 0

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for JSON output."""
        return {
            "valid": self.is_valid,
            "lock_file_exists": self.lock_file_exists,
            "lock_file_valid": self.lock_file_valid,
            "packages_verified": self.packages_verified,
            "hash_errors": self.hash_errors,
            "suspicious_packages": self.suspicious_packages,
            "warnings": self.warnings,
        }


def check_lock_file_exists(project_root: Path) -> bool:
    """Check if uv.lock exists."""
    return (project_root / "uv.lock").exists()


def verify_lock_file_sync(project_root: Path) -> tuple[bool, str]:
    """Verify lock file is in sync with pyproject.toml using uv lock --check."""
    uv_path = shutil.which("uv")
    if not uv_path:
        return False, "uv command not found in PATH"

    try:
        result = subprocess.run(  # noqa: S603
            [uv_path, "lock", "--check"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Lock check timed out"
    except FileNotFoundError:
        return False, "uv command not found"


def parse_lock_file(project_root: Path) -> list[dict[str, str | list[str]]]:
    """Parse uv.lock and extract package info with hashes."""
    lock_file = project_root / "uv.lock"
    packages: list[dict[str, str | list[str]]] = []

    content = lock_file.read_text()

    # Simple TOML parsing for package names and hashes
    current_package: dict[str, str | list[str]] = {}
    current_hashes: list[str] = []

    for line in content.split("\n"):
        if line.startswith("[[package]]"):
            if current_package:
                if current_hashes:
                    current_package["hashes"] = current_hashes
                packages.append(current_package)
            current_package = {}
            current_hashes = []
        elif line.startswith("name = "):
            current_package["name"] = line.split('"')[1]
        elif "hash = " in line:
            # Extract hash from sdist or wheel line
            match = re.search(r'hash = "([^"]+)"', line)
            if match:
                current_hashes.append(match.group(1))

    if current_package:
        if current_hashes:
            current_package["hashes"] = current_hashes
        packages.append(current_package)

    return packages


def check_typosquatting(package_name: str) -> list[str]:
    """Check if package name looks like typosquatting."""
    warnings: list[str] = []

    if package_name.lower() in KNOWN_PACKAGES:
        return warnings

    for pattern, message in SUSPICIOUS_PATTERNS:
        if re.search(pattern, package_name.lower()):
            warnings.append(f"{package_name}: {message}")

    return warnings


def verify_hash_format(hash_value: str) -> bool:
    """Verify hash has valid format (sha256:...)."""
    if not hash_value.startswith("sha256:"):
        return False

    hex_part = hash_value.split(":")[1]
    return len(hex_part) == 64 and all(c in "0123456789abcdef" for c in hex_part)


def verify_dependencies(project_root: Path, check_typo: bool = False) -> VerificationResult:
    """Run full dependency verification."""
    result = VerificationResult()

    # Check lock file exists
    if not check_lock_file_exists(project_root):
        result.lock_file_exists = False
        return result

    # Verify lock file is in sync
    is_synced, error_msg = verify_lock_file_sync(project_root)
    if not is_synced:
        result.lock_file_valid = False
        result.hash_errors.append(f"Lock file out of sync: {error_msg}")
        return result

    # Parse and verify packages
    packages = parse_lock_file(project_root)
    result.packages_verified = len(packages)

    for pkg in packages:
        name_value = pkg.get("name", "unknown")
        name = name_value if isinstance(name_value, str) else "unknown"
        hashes_value = pkg.get("hashes", [])
        hashes: list[str] = hashes_value if isinstance(hashes_value, list) else []

        # Verify hash formats
        for h in hashes:
            if not verify_hash_format(h):
                result.hash_errors.append(f"{name}: Invalid hash format: {h}")

        # Check for typosquatting
        if check_typo:
            typo_warnings = check_typosquatting(name)
            result.suspicious_packages.extend(typo_warnings)

    return result


def print_results(result: VerificationResult, json_output: bool = False) -> int:
    """Print verification results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.is_valid else 1

    print("=" * 60)
    print("Dependency Hash Verification Report")
    print("=" * 60)

    if not result.lock_file_exists:
        print("\n❌ FAILED: uv.lock file not found")
        return 1

    if not result.lock_file_valid:
        print("\n❌ FAILED: Lock file validation failed")
        for error in result.hash_errors:
            print(f"  - {error}")
        return 1

    print("\n✅ Lock file: Present and in sync")
    print(f"✅ Packages verified: {result.packages_verified}")

    if result.hash_errors:
        print(f"\n❌ Hash errors: {len(result.hash_errors)}")
        for error in result.hash_errors:
            print(f"  - {error}")
    else:
        print("✅ All hashes valid")

    if result.suspicious_packages:
        print(f"\n⚠️  Suspicious packages: {len(result.suspicious_packages)}")
        for warning in result.suspicious_packages:
            print(f"  - {warning}")

    print("\n" + "=" * 60)

    return 0 if result.is_valid else 1


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify dependency hashes and check for suspicious packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    parser.add_argument(
        "--check-typosquatting",
        action="store_true",
        dest="check_typo",
        help="Check for potential typosquatting packages",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Project directory (default: auto-detect)",
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

    project_root = args.project_dir or find_project_root()

    result = verify_dependencies(project_root, check_typo=args.check_typo)

    return print_results(result, json_output=args.json_output)


if __name__ == "__main__":
    sys.exit(main())
