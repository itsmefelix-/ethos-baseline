#!/usr/bin/env python3
"""Validate that a repo conforms to the Praxis baseplate structure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_DIRS = [
    "context",
    "planning",
    "docs",
    "data",
    "exports",
    "reports",
    "tools",
]

REQUIRED_FILES = [
    "BASEPLATE_VERSION",
    "MISSION.md",
    "context/README.md",
    "context/map.md",
    "planning/README.md",
    "planning/interview.md",
    "planning/roadmap.md",
    "docs/TELOS.md",
    "docs/DATA_SOURCES.md",
]

PLACEHOLDER_TOKENS = ["__REPO_NAME__", "__BASEPLATE_VERSION__"]
PLACEHOLDER_HINT = "_TODO"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=Path.cwd(), help="Repository root to validate (default: current directory)")
    parser.add_argument("--expected-version", help="Optional baseplate version string to compare against")
    parser.add_argument("--strict", action="store_true", help="Treat warnings (e.g., TODO placeholders) as errors")
    return parser.parse_args()


def read_version(repo_root: Path) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    version_file = repo_root / "BASEPLATE_VERSION"
    if not version_file.exists():
        errors.append("Missing BASEPLATE_VERSION file")
        return None, errors
    version = version_file.read_text(encoding="utf-8").strip()
    if not version:
        errors.append("BASEPLATE_VERSION is empty")
        return None, errors
    return version, errors


def check_dirs(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_DIRS:
        path = repo_root / rel
        if not path.exists() or not path.is_dir():
            errors.append(f"Missing directory: {rel}")
    return errors


def check_files(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        path = repo_root / rel
        if not path.exists() or not path.is_file():
            errors.append(f"Missing file: {rel}")
    return errors


def find_placeholders(repo_root: Path, paths: Iterable[Path]) -> list[str]:
    warnings: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(repo_root)
        hits = [token for token in PLACEHOLDER_TOKENS if token in text]
        if hits:
            warnings.append(f"Placeholders {hits} detected in {rel}")
        if PLACEHOLDER_HINT in text:
            warnings.append(f"Todo placeholder still present in {rel}")
    return warnings


def main() -> None:
    args = parse_args()
    repo_root = args.path.resolve()

    errors = []
    warnings = []

    errors.extend(check_dirs(repo_root))
    errors.extend(check_files(repo_root))

    version, version_errors = read_version(repo_root)
    errors.extend(version_errors)
    if version and args.expected_version and version != args.expected_version:
        warnings.append(
            f"Baseplate version mismatch: repo has {version}, expected {args.expected_version}"
        )

    placeholder_paths = [
        repo_root / "context" / "README.md",
        repo_root / "docs" / "TELOS.md",
        repo_root / "MISSION.md",
    ]
    warnings.extend(find_placeholders(repo_root, placeholder_paths))

    if errors:
        print("Baseplate check: FAIL")
        for msg in errors:
            print(f"  ERROR: {msg}")
    else:
        print("Baseplate check: PASS")

    if warnings:
        level = "ERROR" if args.strict else "WARN"
        for msg in warnings:
            print(f"  {level}: {msg}")
        if args.strict:
            errors.extend(warnings)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
