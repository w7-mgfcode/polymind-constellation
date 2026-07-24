from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from polymind import __version__
from polymind.release import (
    ReleaseEvidenceError,
    validate_release_attestation,
    validate_release_evidence,
    write_release_evidence,
)
from polymind.verify import _check_release_provenance

COMMIT_IDENTITY = "release@example.invalid"
COMMIT_ISSUER = "https://issuer.example.invalid"


def _release_root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    dist = root / "dist"
    dist.mkdir(parents=True)
    root.joinpath("CHANGELOG.md").write_text(
        f"# Changelog\n\n## {__version__} - 2026-07-23\n\n- Harden release evidence.\n",
        encoding="utf-8",
    )
    dist.joinpath(f"polymind_constellation-{__version__}-py3-none-any.whl").write_bytes(b"wheel")
    dist.joinpath(f"polymind_constellation-{__version__}.tar.gz").write_bytes(b"sdist")
    return root


def _attestation_stub(
    root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    gh_exit_code: int = 0,
    gitsign_exit_code: int = 0,
) -> Path:
    bundle = root / "dist/release-attestation.sigstore.json"
    bundle.write_text("{}\n", encoding="utf-8")
    executable_root = tmp_path / "bin"
    executable_root.mkdir(exist_ok=True)
    for name, exit_code in (("gh", gh_exit_code), ("gitsign", gitsign_exit_code)):
        executable = executable_root / name
        executable.write_text(f"#!/bin/sh\nexit {exit_code}\n", encoding="utf-8")
        executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{executable_root}:/usr/bin:/bin")
    return bundle


def test_release_evidence_records_artifacts_notes_and_attestation_requirement(
    tmp_path: Path,
) -> None:
    root = _release_root(tmp_path)
    commit = "a" * 40

    manifest, checksums, notes = write_release_evidence(
        root,
        repository="owner/repository",
        commit=commit,
        ref=f"refs/tags/v{__version__}",
        commit_identity=COMMIT_IDENTITY,
        commit_issuer=COMMIT_ISSUER,
    )

    assert validate_release_evidence(root, manifest, check_git=False) == (commit, 2)
    assert checksums.read_text(encoding="utf-8").count("  dist/") == 2
    rendered_notes = notes.read_text(encoding="utf-8")
    assert f"## {__version__}" in rendered_notes
    assert "## SHA-256" in rendered_notes
    assert '"required": true' in manifest.read_text(encoding="utf-8")


def test_release_evidence_rejects_artifact_drift(tmp_path: Path) -> None:
    root = _release_root(tmp_path)
    manifest, _, _ = write_release_evidence(
        root,
        repository="owner/repository",
        commit="b" * 40,
        ref=f"refs/tags/v{__version__}",
        commit_identity=COMMIT_IDENTITY,
        commit_issuer=COMMIT_ISSUER,
    )
    root.joinpath(f"dist/polymind_constellation-{__version__}-py3-none-any.whl").write_bytes(
        b"tampered"
    )

    with pytest.raises(ReleaseEvidenceError, match="digest or size mismatch"):
        validate_release_evidence(root, manifest, check_git=False)


def test_release_gate_rejects_missing_manifest_even_when_wheel_exists(tmp_path: Path) -> None:
    root = _release_root(tmp_path)

    result = _check_release_provenance(
        root,
        Path("dist/release-manifest.json"),
        Path("dist/release-attestation.sigstore.json"),
        COMMIT_IDENTITY,
        COMMIT_ISSUER,
    )

    assert result.status == "fail"
    assert "manifest is missing" in result.detail


def test_release_gate_rejects_missing_git_provenance(tmp_path: Path) -> None:
    root = _release_root(tmp_path)
    write_release_evidence(
        root,
        repository="owner/repository",
        commit="c" * 40,
        ref=f"refs/tags/v{__version__}",
        commit_identity=COMMIT_IDENTITY,
        commit_issuer=COMMIT_ISSUER,
    )

    result = _check_release_provenance(
        root,
        Path("dist/release-manifest.json"),
        Path("dist/release-attestation.sigstore.json"),
        COMMIT_IDENTITY,
        COMMIT_ISSUER,
    )

    assert result.status == "fail"
    assert "Git provenance check failed" in result.detail


def test_release_gate_accepts_matching_tag_commit_and_clean_tracked_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _release_root(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Release Test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "release@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "add", "CHANGELOG.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "release source"], cwd=root, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    subprocess.run(["git", "tag", f"v{__version__}"], cwd=root, check=True)
    write_release_evidence(
        root,
        repository="owner/repository",
        commit=commit,
        ref=f"refs/tags/v{__version__}",
        commit_identity=COMMIT_IDENTITY,
        commit_issuer=COMMIT_ISSUER,
    )
    _attestation_stub(root, tmp_path, monkeypatch)

    result = _check_release_provenance(
        root,
        Path("dist/release-manifest.json"),
        Path("dist/release-attestation.sigstore.json"),
        COMMIT_IDENTITY,
        COMMIT_ISSUER,
    )

    assert result.status == "pass"
    assert commit[:12] in result.detail

    root.joinpath("CHANGELOG.md").write_text("tracked drift\n", encoding="utf-8")
    drifted = _check_release_provenance(
        root,
        Path("dist/release-manifest.json"),
        Path("dist/release-attestation.sigstore.json"),
        COMMIT_IDENTITY,
        COMMIT_ISSUER,
    )
    assert drifted.status == "fail"
    assert "tracked source changes" in drifted.detail


def test_release_gate_rejects_missing_or_invalid_sigstore_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _release_root(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Release Test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "release@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "add", "CHANGELOG.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "release source"], cwd=root, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(["git", "tag", f"v{__version__}"], cwd=root, check=True)
    manifest, _, _ = write_release_evidence(
        root,
        repository="owner/repository",
        commit=commit,
        ref=f"refs/tags/v{__version__}",
        commit_identity=COMMIT_IDENTITY,
        commit_issuer=COMMIT_ISSUER,
    )

    with pytest.raises(ReleaseEvidenceError, match="attestation bundle is missing"):
        validate_release_attestation(
            root,
            manifest,
            commit_identity=COMMIT_IDENTITY,
            commit_issuer=COMMIT_ISSUER,
        )

    bundle = _attestation_stub(root, tmp_path, monkeypatch, gitsign_exit_code=1)
    with pytest.raises(ReleaseEvidenceError, match="Gitsign commit verification failed"):
        validate_release_attestation(
            root,
            manifest,
            bundle,
            commit_identity=COMMIT_IDENTITY,
            commit_issuer=COMMIT_ISSUER,
        )

    bundle = _attestation_stub(root, tmp_path, monkeypatch, gh_exit_code=1)
    with pytest.raises(ReleaseEvidenceError, match="Sigstore attestation verification failed"):
        validate_release_attestation(
            root,
            manifest,
            bundle,
            commit_identity=COMMIT_IDENTITY,
            commit_issuer=COMMIT_ISSUER,
        )
