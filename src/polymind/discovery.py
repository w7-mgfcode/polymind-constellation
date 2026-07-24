"""Canonical skill discovery under skills/ only."""

from __future__ import annotations

from pathlib import Path

from polymind.model import Diagnostic, DiagnosticCategory


def discover_skill_directories(skills_root: Path) -> tuple[list[Path], list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    if skills_root.is_symlink():
        diagnostics.append(
            Diagnostic(
                DiagnosticCategory.SECURITY,
                "SKILLS_ROOT_SYMLINK",
                "canonical skills root must not be a symlink",
                skills_root.as_posix(),
            )
        )
        return [], diagnostics
    if not skills_root.exists():
        diagnostics.append(
            Diagnostic(
                DiagnosticCategory.POLICY,
                "SKILLS_ROOT_MISSING",
                "canonical skills directory does not exist",
                skills_root.as_posix(),
            )
        )
        return [], diagnostics
    if not skills_root.is_dir():
        diagnostics.append(
            Diagnostic(
                DiagnosticCategory.SECURITY,
                "SKILLS_ROOT_NOT_DIRECTORY",
                "canonical skills path must be a directory",
                skills_root.as_posix(),
            )
        )
        return [], diagnostics

    root = skills_root.resolve()
    directories: list[Path] = []
    for child in sorted(skills_root.iterdir(), key=lambda path: path.name):
        if child.name.startswith("."):
            continue
        if child.is_symlink():
            diagnostics.append(
                Diagnostic(
                    DiagnosticCategory.SECURITY,
                    "PACKAGE_SYMLINK",
                    "skill package directory must not be a symlink",
                    child.as_posix(),
                )
            )
            continue
        try:
            child.resolve().relative_to(root)
        except ValueError:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCategory.SECURITY,
                    "PACKAGE_ESCAPE",
                    "skill directory resolves outside the canonical skills root",
                    child.as_posix(),
                )
            )
            continue
        if child.is_dir():
            directories.append(child)
    return directories, diagnostics
