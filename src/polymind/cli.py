"""Command-line interface for Polymind Constellation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from polymind import __version__
from polymind.catalog import (
    CatalogError,
    activate_skill,
    catalog_document,
    read_resource,
    render_activation,
    render_catalog,
    render_resource_json,
)
from polymind.conformance import (
    ConformanceError,
    combine_conformance_reports,
    evaluate_ollama_models,
    probe_installed_clients,
    render_conformance,
    run_static_conformance,
)
from polymind.installer import InstallError, ProjectionInstaller, default_projection_source
from polymind.projection import ProjectionCompiler, ProjectionError
from polymind.release import ReleaseEvidenceError, write_release_evidence
from polymind.validation import validate_repository
from polymind.verify import run_verification, verification_passed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="polymind")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate canonical skill packages")
    validate.add_argument("path", nargs="?", default="skills", type=Path)
    validate.add_argument("--format", choices=("text", "json"), default="text")

    verify = subparsers.add_parser("verify", help="run the repository verification contract")
    verify.add_argument("--root", type=Path, default=Path.cwd())
    verify.add_argument("--release", action="store_true")
    verify.add_argument(
        "--provenance-manifest", type=Path, default=Path("dist/release-manifest.json")
    )
    verify.add_argument(
        "--attestation-bundle",
        type=Path,
        default=Path("dist/release-attestation.sigstore.json"),
    )
    verify.add_argument("--commit-identity", default="")
    verify.add_argument("--commit-issuer", default="")

    release_manifest = subparsers.add_parser(
        "release-manifest", help="generate checksums and release provenance metadata"
    )
    release_manifest.add_argument("--root", type=Path, default=Path.cwd())
    release_manifest.add_argument("--repository", required=True)
    release_manifest.add_argument("--commit", required=True)
    release_manifest.add_argument("--ref", required=True)
    release_manifest.add_argument("--commit-identity", required=True)
    release_manifest.add_argument("--commit-issuer", required=True)
    release_manifest.add_argument("--workflow", default=".github/workflows/release.yml")

    catalog = subparsers.add_parser("catalog", help="list compact canonical skill metadata")
    catalog.add_argument("--skills-root", type=Path, default=Path("skills"))
    catalog.add_argument("--format", choices=("json", "xml", "markdown"), default="json")

    activate = subparsers.add_parser(
        "activate", help="return one skill's instructions and resource manifest"
    )
    activate.add_argument("name")
    activate.add_argument("--skills-root", type=Path, default=Path("skills"))
    activate.add_argument("--format", choices=("json", "markdown"), default="json")

    resource = subparsers.add_parser(
        "resource", help="read one activated skill resource without executing it"
    )
    resource.add_argument("name")
    resource.add_argument("path")
    resource.add_argument("--skills-root", type=Path, default=Path("skills"))
    resource.add_argument("--format", choices=("json", "raw"), default="json")
    resource.add_argument("--max-bytes", type=int, default=256 * 1024)

    agent_docs = subparsers.add_parser(
        "validate-agent-docs", help="validate repository agent documentation"
    )
    agent_docs.add_argument("path", nargs="?", default=Path.cwd(), type=Path)
    agent_docs.add_argument("--check", action="store_true")
    agent_docs.add_argument("--diff", action="store_true")
    agent_docs.add_argument("--strict", action="store_true")
    agent_docs.add_argument("--quiet", action="store_true")
    agent_docs.add_argument("--check-remote", action="store_true")
    agent_docs.add_argument("--remote-timeout", type=float, default=5.0)
    agent_docs.add_argument("--duplication-threshold", type=int, default=88)
    agent_docs.add_argument("--secret-allowlist", action="append", default=[], type=Path)

    conformance = subparsers.add_parser(
        "conformance", help="run the Phase 7 cross-provider conformance matrix"
    )
    conformance.add_argument("--root", type=Path, default=Path.cwd())
    conformance.add_argument("--format", choices=("json", "markdown"), default="json")
    conformance.add_argument("--probe-installed", action="store_true")
    conformance.add_argument("--ollama-model", action="append", default=[])
    conformance.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")

    install = subparsers.add_parser(
        "install", help="safely install generated skills into a downstream repository"
    )
    install.add_argument("target", type=Path)
    install.add_argument("--source", type=Path)
    modes = install.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--rollback", action="store_true")
    install.add_argument("--diff", action="store_true")
    install.add_argument("--break-stale-lock", action="store_true")

    for command in ("sync", "sync-adapters"):
        sync = subparsers.add_parser(command, help="build deterministic provider projections")
        sync.add_argument("--output-root", type=Path, default=Path("dist/repo"))
        modes = sync.add_mutually_exclusive_group()
        modes.add_argument("--apply", action="store_true")
        modes.add_argument("--check", action="store_true")
        modes.add_argument("--dry-run", action="store_true")
        sync.add_argument("--break-stale-lock", action="store_true")
    return parser


def _validate(path: Path, output_format: str) -> int:
    report = validate_repository(path)
    if output_format == "json":
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        for item in report.diagnostics:
            print(
                f"{item.severity.value}: {item.category.value}: {item.code}: "
                f"{item.path}: {item.message}"
            )
        print(
            f"validated {len(report.packages)} package(s); {len(report.diagnostics)} diagnostic(s)"
        )
    return 0 if report.valid else 1


def _verify(
    root: Path,
    *,
    release: bool = False,
    provenance_manifest: Path = Path("dist/release-manifest.json"),
    attestation_bundle: Path = Path("dist/release-attestation.sigstore.json"),
    commit_identity: str = "",
    commit_issuer: str = "",
) -> int:
    results = run_verification(
        root.resolve(),
        release=release,
        provenance_manifest=provenance_manifest,
        attestation_bundle=attestation_bundle,
        commit_identity=commit_identity,
        commit_issuer=commit_issuer,
    )
    for result in results:
        print(f"[{result.status}] {result.name}: {result.detail}")
    return 0 if verification_passed(results) else 1


def _release_manifest(args: argparse.Namespace) -> int:
    try:
        manifest, checksums, notes = write_release_evidence(
            args.root,
            repository=args.repository,
            commit=args.commit,
            ref=args.ref,
            commit_identity=args.commit_identity,
            commit_issuer=args.commit_issuer,
            workflow=args.workflow,
        )
    except ReleaseEvidenceError as error:
        print(f"release evidence error: {error}", file=sys.stderr)
        return 1
    print(f"release manifest: {manifest}")
    print(f"release checksums: {checksums}")
    print(f"release notes: {notes}")
    return 0


def _catalog(skills_root: Path, output_format: str) -> int:
    try:
        document = catalog_document(skills_root)
        sys.stdout.write(render_catalog(document, output_format))
    except CatalogError as error:
        print(f"catalog error: {error}", file=sys.stderr)
        return 1
    return 0


def _activate(skills_root: Path, name: str, output_format: str) -> int:
    try:
        document = activate_skill(skills_root, name)
        sys.stdout.write(render_activation(document, output_format))
    except CatalogError as error:
        print(f"activation error: {error}", file=sys.stderr)
        return 1
    return 0


def _resource(
    skills_root: Path, name: str, resource_path: str, output_format: str, max_bytes: int
) -> int:
    try:
        record, content = read_resource(skills_root, name, resource_path, max_bytes=max_bytes)
        if output_format == "json":
            sys.stdout.write(render_resource_json(record, content))
        else:
            sys.stdout.flush()
            sys.stdout.buffer.write(content)
    except CatalogError as error:
        print(f"resource error: {error}", file=sys.stderr)
        return 1
    return 0


def _validate_agent_docs(root: Path, args: argparse.Namespace) -> int:
    repository_root = Path(__file__).parents[2]
    script = repository_root / "skills/maintaining-agent-docs/scripts/validate.py"
    if not script.is_file():
        print(f"agent-docs validator not found: {script}", file=sys.stderr)
        return 2
    command = [
        sys.executable,
        str(script),
        "--duplication-threshold",
        str(args.duplication_threshold),
        "--remote-timeout",
        str(args.remote_timeout),
    ]
    for flag in ("check", "diff", "strict", "quiet", "check_remote"):
        if getattr(args, flag):
            command.append(f"--{flag.replace('_', '-')}")
    for allowlist in args.secret_allowlist:
        command.extend(("--secret-allowlist", str(allowlist)))
    command.append(str(root))
    return subprocess.run(command, cwd=repository_root, check=False).returncode  # noqa: S603


def _conformance(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    try:
        reports = [run_static_conformance(root)]
        if args.probe_installed:
            reports.append(probe_installed_clients(root))
        if args.ollama_model:
            reports.append(evaluate_ollama_models(root, args.ollama_model, args.ollama_endpoint))
        report = combine_conformance_reports(reports)
        sys.stdout.write(render_conformance(report, args.format))
    except (CatalogError, ConformanceError) as error:
        print(f"conformance error: {error}", file=sys.stderr)
        return 1
    return 0 if report["status"] != "fail" else 1


def _install(args: argparse.Namespace) -> int:
    try:
        source = args.source if args.source is not None else default_projection_source()
        result = ProjectionInstaller(source, args.target).run(
            apply=args.apply,
            check=args.check,
            rollback=args.rollback,
            show_diff=args.diff,
            break_stale_lock=args.break_stale_lock,
        )
    except (InstallError, OSError) as error:
        print(f"install error: {error}", file=sys.stderr)
        return 1
    mode = (
        "rollback"
        if args.rollback
        else "check"
        if args.check
        else "apply"
        if args.apply
        else "dry-run"
    )
    print(f"installation {mode}: {result.target_root}")
    if result.source_projection is not None:
        print(f"source projection: {result.source_projection}")
        print(f"source projection SHA-256: {result.source_projection_sha256}")
        print(f"framework version: {__version__}")
    if result.changes:
        for change in result.changes:
            print(change)
    else:
        print("NO CHANGES")
    if result.diff:
        sys.stdout.write(result.diff)
    if not args.apply and not args.check and not args.rollback:
        print("dry-run only; inspect the plan and pass --apply to write managed skills")
    return 0


def _sync(
    root: Path,
    output_root: Path,
    *,
    apply: bool,
    check: bool,
    break_stale_lock: bool,
) -> int:
    try:
        result = ProjectionCompiler(root, output_root).sync(
            apply=apply,
            check=check,
            break_stale_lock=break_stale_lock,
        )
    except ProjectionError as error:
        print(f"projection error: {error}", file=sys.stderr)
        return 1
    mode = "check" if check else "apply" if apply else "dry-run"
    print(f"projection {mode}: {result.output_root}")
    if result.changes:
        for change in result.changes:
            print(change)
    else:
        print("NO CHANGES")
    if not apply and not check:
        print("dry-run only; pass --apply to write generated artifacts")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "validate":
        return _validate(args.path, args.format)
    if args.command == "verify":
        return _verify(
            args.root,
            release=args.release,
            provenance_manifest=args.provenance_manifest,
            attestation_bundle=args.attestation_bundle,
            commit_identity=args.commit_identity,
            commit_issuer=args.commit_issuer,
        )
    if args.command == "release-manifest":
        return _release_manifest(args)
    if args.command == "catalog":
        return _catalog(args.skills_root, args.format)
    if args.command == "activate":
        return _activate(args.skills_root, args.name, args.format)
    if args.command == "resource":
        return _resource(args.skills_root, args.name, args.path, args.format, args.max_bytes)
    if args.command == "validate-agent-docs":
        return _validate_agent_docs(args.path, args)
    if args.command == "conformance":
        return _conformance(args)
    if args.command == "install":
        return _install(args)
    if args.command in {"sync", "sync-adapters"}:
        return _sync(
            Path.cwd(),
            args.output_root,
            apply=args.apply,
            check=args.check,
            break_stale_lock=args.break_stale_lock,
        )
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
