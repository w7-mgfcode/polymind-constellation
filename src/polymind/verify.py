"""Repository verification orchestration."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from polymind.catalog import CatalogError
from polymind.conformance import ConformanceError, run_static_conformance
from polymind.model import Severity
from polymind.projection import ProjectionError, check_projection
from polymind.release import ReleaseEvidenceError, validate_release_attestation
from polymind.validation import validate_repository

_MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: str
    detail: str


def _run(command: list[str], root: Path) -> CheckResult:
    completed = subprocess.run(command, cwd=root, text=True, check=False)  # noqa: S603
    display_command = command[2:] if command[:2] == [sys.executable, "-m"] else command
    status = "pass" if completed.returncode == 0 else "fail"
    return CheckResult(" ".join(display_command), status, f"exit {completed.returncode}")


def _check_docs(root: Path) -> CheckResult:
    failures: list[str] = []
    candidates = [
        root / "README.md",
        root / "AGENTS.md",
        root / "CLAUDE.md",
        root / "CONTRIBUTING.md",
        root / "CHANGELOG.md",
    ]
    candidates.extend(sorted((root / "docs").rglob("*.md")))
    for markdown in candidates:
        if not markdown.is_file():
            continue
        text = markdown.read_text(encoding="utf-8")
        outside_fences = "\n".join(text.split("```")[::2])
        for raw_target in _MARKDOWN_LINK_PATTERN.findall(outside_fences):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith("#"):
                continue
            candidate = markdown.parent / parsed.path
            if not candidate.exists():
                failures.append(f"{markdown.relative_to(root)} -> {target}")
    if failures:
        return CheckResult("docs", "fail", "; ".join(failures))
    return CheckResult("docs", "pass", "local Markdown links resolve")


def _check_canonical(root: Path) -> CheckResult:
    report = validate_repository(root / "skills")
    for diagnostic in report.diagnostics:
        print(
            f"{diagnostic.severity.value}: {diagnostic.category.value}: "
            f"{diagnostic.code}: {diagnostic.path}: {diagnostic.message}"
        )
    error_count = sum(item.severity is Severity.ERROR for item in report.diagnostics)
    if error_count:
        return CheckResult("canonical-skills", "fail", f"{error_count} error(s)")
    return CheckResult("canonical-skills", "pass", f"{len(report.packages)} package(s) validated")


def _check_skills_ref(root: Path) -> CheckResult:
    executable = shutil.which("skills-ref")
    if executable is None:
        return CheckResult("skills-ref", "skip", "optional reference validator is not installed")
    report = validate_repository(root / "skills")
    for package in report.packages:
        completed = subprocess.run(  # noqa: S603
            [executable, "validate", str(package.root)], cwd=root, check=False
        )
        if completed.returncode != 0:
            return CheckResult(
                "skills-ref", "fail", f"reference validation failed for {package.metadata.name}"
            )
    return CheckResult("skills-ref", "pass", f"validated {len(report.packages)} package(s)")


def _check_actionlint(root: Path) -> CheckResult:
    executable = shutil.which("actionlint")
    if executable is None:
        return CheckResult("actionlint", "skip", "optional pinned binary is not installed")
    completed = subprocess.run([executable], cwd=root, check=False)  # noqa: S603
    status = "pass" if completed.returncode == 0 else "fail"
    return CheckResult("actionlint", status, f"exit {completed.returncode}")


def _check_projection(root: Path) -> CheckResult:
    try:
        result = check_projection(root)
    except ProjectionError as error:
        return CheckResult("projection-drift", "fail", str(error))
    return CheckResult(
        "projection-drift", "pass", f"no drift under {result.output_root.relative_to(root)}"
    )


def _check_conformance(root: Path) -> CheckResult:
    try:
        report = run_static_conformance(root)
    except (CatalogError, ConformanceError) as error:
        return CheckResult("phase7-static-conformance", "fail", str(error))
    checks = report.get("checks")
    failures = (
        [item for item in checks if isinstance(item, dict) and item.get("status") == "fail"]
        if isinstance(checks, list)
        else []
    )
    if report.get("status") != "pass":
        return CheckResult(
            "phase7-static-conformance",
            "fail",
            f"{len(failures)} failed check(s)",
        )
    return CheckResult(
        "phase7-static-conformance",
        "pass",
        f"{len(checks) if isinstance(checks, list) else 0} checks passed",
    )


def _check_release_provenance(
    root: Path,
    manifest_path: Path,
    attestation_bundle: Path,
    commit_identity: str,
    commit_issuer: str,
) -> CheckResult:
    try:
        commit, artifact_count = validate_release_attestation(
            root,
            manifest_path,
            attestation_bundle,
            commit_identity=commit_identity,
            commit_issuer=commit_issuer,
        )
    except ReleaseEvidenceError as error:
        return CheckResult("release-provenance", "fail", str(error))
    return CheckResult(
        "release-provenance",
        "pass",
        f"{artifact_count} artifact(s) match tagged commit {commit[:12]}",
    )


def run_verification(
    root: Path,
    *,
    release: bool = False,
    provenance_manifest: Path = Path("dist/release-manifest.json"),
    attestation_bundle: Path = Path("dist/release-attestation.sigstore.json"),
    commit_identity: str = "",
    commit_issuer: str = "",
) -> tuple[CheckResult, ...]:
    checks = [
        _run([sys.executable, "-m", "ruff", "check", "."], root),
        _run([sys.executable, "-m", "ruff", "format", "--check", "."], root),
        _run([sys.executable, "-m", "mypy", "src", "tests"], root),
        _run([sys.executable, "-m", "pytest"], root),
        _check_canonical(root),
        _check_docs(root),
        _check_actionlint(root),
        _check_skills_ref(root),
        _check_projection(root),
        _check_conformance(root),
    ]
    if release:
        checks.append(
            _check_release_provenance(
                root,
                provenance_manifest,
                attestation_bundle,
                commit_identity,
                commit_issuer,
            )
        )
    return tuple(checks)


def verification_passed(results: tuple[CheckResult, ...]) -> bool:
    return all(result.status != "fail" for result in results)
