"""Release evidence generation and fail-closed provenance validation."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from polymind import __version__

_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_WORKFLOW_PATH = ".github/workflows/release.yml"


class ReleaseEvidenceError(RuntimeError):
    """Release evidence is missing, malformed, inconsistent, or untrusted."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _expected_artifacts(repository_root: Path, version: str) -> tuple[Path, Path]:
    dist = repository_root / "dist"
    return (
        dist / f"polymind_constellation-{version}-py3-none-any.whl",
        dist / f"polymind_constellation-{version}.tar.gz",
    )


def _changelog_section(repository_root: Path, version: str) -> str:
    changelog = repository_root / "CHANGELOG.md"
    try:
        text = changelog.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ReleaseEvidenceError(f"cannot read CHANGELOG.md: {error}") from error
    heading = re.search(rf"^## {re.escape(version)}(?:\s+-[^\n]*)?$", text, re.MULTILINE)
    if heading is None:
        raise ReleaseEvidenceError(f"CHANGELOG.md has no release section for {version}")
    next_heading = re.search(r"^## ", text[heading.end() :], re.MULTILINE)
    end = heading.end() + next_heading.start() if next_heading is not None else len(text)
    return text[heading.start() : end].strip() + "\n"


def write_release_evidence(
    repository_root: Path,
    *,
    repository: str,
    commit: str,
    ref: str,
    commit_identity: str,
    commit_issuer: str,
    workflow: str = _WORKFLOW_PATH,
    manifest_path: Path = Path("dist/release-manifest.json"),
    checksums_path: Path = Path("dist/SHA256SUMS"),
    notes_path: Path = Path("dist/RELEASE_NOTES.md"),
) -> tuple[Path, Path, Path]:
    """Write deterministic release metadata after validating tag identity and artifacts."""
    root = repository_root.resolve()
    version = __version__
    tag = f"v{version}"
    if _REPOSITORY_PATTERN.fullmatch(repository) is None:
        raise ReleaseEvidenceError("repository must use the owner/name form")
    if _COMMIT_PATTERN.fullmatch(commit) is None:
        raise ReleaseEvidenceError("commit must be a lowercase 40-character Git SHA")
    if ref != f"refs/tags/{tag}":
        raise ReleaseEvidenceError(f"release ref must be refs/tags/{tag}")
    if workflow != _WORKFLOW_PATH:
        raise ReleaseEvidenceError(f"release workflow must be {_WORKFLOW_PATH}")
    _validate_commit_signer(commit_identity, commit_issuer)

    artifacts = _expected_artifacts(root, version)
    missing = [path.name for path in artifacts if not path.is_file() or path.is_symlink()]
    if missing:
        raise ReleaseEvidenceError(
            f"release artifacts are missing or symlinked: {', '.join(missing)}"
        )
    records = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in artifacts
    ]
    manifest = {
        "schema_version": "1",
        "framework_version": version,
        "source": {
            "repository": repository,
            "commit": commit,
            "ref": ref,
            "tag": tag,
            "workflow": workflow,
        },
        "artifacts": records,
        "attestation": {
            "required": True,
            "predicate_type": "https://slsa.dev/provenance/v1",
            "signer": "GitHub Actions OIDC via Sigstore",
        },
        "commit_signature": {
            "required": True,
            "tool": "gitsign",
            "certificate_identity": commit_identity,
            "certificate_oidc_issuer": commit_issuer,
        },
        "notice": "This manifest is integrity metadata; CI-issued attestation proves provenance.",
    }
    checksum_text = "".join(f"{record['sha256']}  {record['path']}\n" for record in records)
    notes = (
        _changelog_section(root, version) + "\n## SHA-256\n\n```text\n" + checksum_text + "```\n"
    )
    outputs = []
    for relative, content in (
        (manifest_path, _json_bytes(manifest)),
        (checksums_path, checksum_text.encode()),
        (notes_path, notes.encode()),
    ):
        target = relative if relative.is_absolute() else root / relative
        try:
            target.resolve(strict=False).relative_to(root)
        except ValueError as error:
            raise ReleaseEvidenceError(
                f"release evidence path escapes repository: {relative}"
            ) from error
        if target.is_symlink():
            raise ReleaseEvidenceError(f"release evidence output must not be a symlink: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        outputs.append(target)
    return outputs[0], outputs[1], outputs[2]


def _read_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ReleaseEvidenceError(f"release manifest is missing or symlinked: {path}")
    try:
        loaded: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(f"cannot parse release manifest: {error}") from error
    if not isinstance(loaded, dict):
        raise ReleaseEvidenceError("release manifest must be a JSON object")
    return dict(loaded)


def _validate_commit_signer(identity: str, issuer: str) -> None:
    if not identity or len(identity) > 500 or any(character.isspace() for character in identity):
        raise ReleaseEvidenceError("commit certificate identity is invalid")
    parsed_issuer = urlsplit(issuer)
    if (
        parsed_issuer.scheme != "https"
        or not parsed_issuer.netloc
        or parsed_issuer.query
        or parsed_issuer.fragment
    ):
        raise ReleaseEvidenceError("commit certificate OIDC issuer must be an HTTPS URL")


def _git_output(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=root, check=False, capture_output=True, text=True
    )  # noqa: S603
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[:500]
        raise ReleaseEvidenceError(f"Git provenance check failed: {detail}")
    return completed.stdout.strip()


def validate_release_evidence(
    repository_root: Path,
    manifest_path: Path = Path("dist/release-manifest.json"),
    *,
    check_git: bool = True,
) -> tuple[str, int]:
    """Validate artifact hashes and optionally require the tag/commit Git chain."""
    root = repository_root.resolve()
    resolved_manifest = manifest_path if manifest_path.is_absolute() else root / manifest_path
    manifest = _read_manifest(resolved_manifest)
    if manifest.get("schema_version") != "1" or manifest.get("framework_version") != __version__:
        raise ReleaseEvidenceError("release manifest schema or framework version is invalid")
    source = manifest.get("source")
    artifacts = manifest.get("artifacts")
    attestation = manifest.get("attestation")
    commit_signature = manifest.get("commit_signature")
    if not isinstance(source, dict) or not isinstance(artifacts, list):
        raise ReleaseEvidenceError("release manifest is missing source or artifact records")
    if not isinstance(attestation, dict) or attestation.get("required") is not True:
        raise ReleaseEvidenceError("release manifest must require a signed artifact attestation")
    if (
        not isinstance(commit_signature, dict)
        or commit_signature.get("required") is not True
        or commit_signature.get("tool") != "gitsign"
    ):
        raise ReleaseEvidenceError("release manifest must require a Gitsign commit signature")
    commit_identity = commit_signature.get("certificate_identity")
    commit_issuer = commit_signature.get("certificate_oidc_issuer")
    if not isinstance(commit_identity, str) or not isinstance(commit_issuer, str):
        raise ReleaseEvidenceError("release manifest commit signer policy is invalid")
    _validate_commit_signer(commit_identity, commit_issuer)
    repository = source.get("repository")
    commit = source.get("commit")
    ref = source.get("ref")
    tag = source.get("tag")
    workflow = source.get("workflow")
    if not isinstance(repository, str) or _REPOSITORY_PATTERN.fullmatch(repository) is None:
        raise ReleaseEvidenceError("release manifest repository identity is invalid")
    if not isinstance(commit, str) or _COMMIT_PATTERN.fullmatch(commit) is None:
        raise ReleaseEvidenceError("release manifest commit identity is invalid")
    if tag != f"v{__version__}" or ref != f"refs/tags/{tag}" or workflow != _WORKFLOW_PATH:
        raise ReleaseEvidenceError("release manifest tag, ref, or workflow identity is invalid")

    expected_paths = {
        path.relative_to(root).as_posix(): path for path in _expected_artifacts(root, __version__)
    }
    recorded_paths: set[str] = set()
    for record in artifacts:
        if not isinstance(record, dict):
            raise ReleaseEvidenceError("release manifest contains a non-object artifact record")
        raw_path = record.get("path")
        digest = record.get("sha256")
        size = record.get("bytes")
        if not isinstance(raw_path, str) or PurePosixPath(raw_path).as_posix() != raw_path:
            raise ReleaseEvidenceError("release manifest contains an invalid artifact path")
        path = expected_paths.get(raw_path)
        if path is None or path.is_symlink() or not path.is_file():
            raise ReleaseEvidenceError(
                f"release artifact is unexpected, missing, or symlinked: {raw_path}"
            )
        if not isinstance(digest, str) or digest != _sha256(path) or size != path.stat().st_size:
            raise ReleaseEvidenceError(f"release artifact digest or size mismatch: {raw_path}")
        recorded_paths.add(raw_path)
    if recorded_paths != set(expected_paths):
        raise ReleaseEvidenceError(
            "release manifest does not describe exactly the expected artifacts"
        )

    if check_git:
        head = _git_output(root, "rev-parse", "--verify", "HEAD")
        tagged = _git_output(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
        if head != commit or tagged != commit:
            raise ReleaseEvidenceError("release tag, manifest commit, and HEAD do not match")
        for arguments in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
            completed = subprocess.run(["git", *arguments], cwd=root, check=False)  # noqa: S603
            if completed.returncode != 0:
                raise ReleaseEvidenceError(
                    "tracked source changes exist during release verification"
                )
    return commit, len(recorded_paths)


def validate_release_attestation(
    repository_root: Path,
    manifest_path: Path = Path("dist/release-manifest.json"),
    bundle_path: Path = Path("dist/release-attestation.sigstore.json"),
    *,
    commit_identity: str,
    commit_issuer: str,
) -> tuple[str, int]:
    """Verify release integrity plus the Sigstore identity bound to its Git source."""
    root = repository_root.resolve()
    commit, artifact_count = validate_release_evidence(root, manifest_path, check_git=True)
    manifest = _read_manifest(
        manifest_path if manifest_path.is_absolute() else root / manifest_path
    )
    source = manifest["source"]
    signature = manifest["commit_signature"]
    repository = source["repository"]
    ref = source["ref"]
    _validate_commit_signer(commit_identity, commit_issuer)
    if (
        signature["certificate_identity"] != commit_identity
        or signature["certificate_oidc_issuer"] != commit_issuer
    ):
        raise ReleaseEvidenceError("expected commit signer does not match the release manifest")

    bundle = bundle_path if bundle_path.is_absolute() else root / bundle_path
    try:
        resolved_bundle = bundle.resolve(strict=True)
        resolved_bundle.relative_to(root)
    except (OSError, ValueError) as error:
        raise ReleaseEvidenceError(
            f"attestation bundle is missing or outside the repository: {bundle_path}"
        ) from error
    if bundle.is_symlink() or not bundle.is_file():
        raise ReleaseEvidenceError(f"attestation bundle is missing or symlinked: {bundle_path}")
    gitsign = shutil.which("gitsign")
    if gitsign is None:
        raise ReleaseEvidenceError("Gitsign is required for release commit verification")
    signed_commit = subprocess.run(  # noqa: S603
        [
            gitsign,
            "verify",
            f"--certificate-identity={commit_identity}",
            f"--certificate-oidc-issuer={commit_issuer}",
            commit,
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if signed_commit.returncode != 0:
        detail = (signed_commit.stderr or signed_commit.stdout).strip()[:500]
        raise ReleaseEvidenceError(f"Gitsign commit verification failed: {detail}")
    executable = shutil.which("gh")
    if executable is None:
        raise ReleaseEvidenceError("GitHub CLI with attestation support is required")

    signer_workflow = f"{repository}/{_WORKFLOW_PATH}"
    for artifact in _expected_artifacts(root, __version__):
        command = [
            executable,
            "attestation",
            "verify",
            str(artifact),
            "--repo",
            repository,
            "--bundle",
            str(resolved_bundle),
            "--signer-workflow",
            signer_workflow,
            "--source-digest",
            commit,
            "--source-ref",
            ref,
            "--predicate-type",
            "https://slsa.dev/provenance/v1",
        ]
        completed = subprocess.run(  # noqa: S603
            command, cwd=root, check=False, capture_output=True, text=True
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()[:500]
            raise ReleaseEvidenceError(
                f"Sigstore attestation verification failed for {artifact.name}: {detail}"
            )
    return commit, artifact_count
