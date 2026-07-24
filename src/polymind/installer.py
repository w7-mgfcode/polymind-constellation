"""Conflict-safe installation of generated skill projections into downstream repos."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import shutil
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from polymind import __version__
from polymind.validation import validate_repository

LOCK_RELATIVE = Path(".polymind/polymind-constellation.lock.json")
ROLLBACK_RELATIVE = Path(".polymind/polymind-constellation.rollback")
OPERATION_LOCK_RELATIVE = Path(".polymind/polymind-constellation.installing")
_SKILL_PREFIXES = (PurePosixPath(".agents/skills"), PurePosixPath(".claude/skills"))
_TEXT_DIFF_LIMIT = 256 * 1024
_TOTAL_DIFF_LIMIT = 1024 * 1024


class InstallError(RuntimeError):
    """Base class for downstream installation failures."""


class InstallConflictError(InstallError):
    """Target state is unmanaged, drifted, unsafe, or concurrently changing."""


class InstallDriftError(InstallError):
    """Installed content differs from the selected source projection."""


@dataclass(frozen=True, slots=True)
class InstallResult:
    target_root: Path
    changes: tuple[str, ...]
    diff: str
    applied: bool
    checked: bool
    rolled_back: bool
    source_projection: Path | None = None
    source_projection_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectionContent:
    roots: tuple[PurePosixPath, ...]
    files: dict[str, bytes]
    modes: dict[str, int]
    projection_digest: str


def default_projection_source() -> Path:
    """Prefer the wheel bundle, then a module-anchored source checkout projection."""
    package_root = Path(__file__).resolve().parent
    bundled = package_root / "_projection"
    if bundled.joinpath("projection.lock.json").is_file():
        return bundled
    checkout = package_root.parents[1] / "dist/repo"
    if (
        package_root.parent.name == "src"
        and package_root.parents[1].joinpath("pyproject.toml").is_file()
        and checkout.joinpath("projection.lock.json").is_file()
    ):
        return checkout
    raise InstallError(
        "no trusted default projection found; install a release wheel containing the projection "
        "bundle or pass --source explicitly"
    )


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _safe_relative(raw: str) -> PurePosixPath:
    candidate = PurePosixPath(raw)
    if (
        not raw
        or "\\" in raw
        or candidate.is_absolute()
        or candidate.as_posix() != raw
        or "." in candidate.parts
        or ".." in candidate.parts
    ):
        raise InstallConflictError(f"invalid managed path: {raw!r}")
    return candidate


def _under_skill_prefix(relative: PurePosixPath) -> bool:
    return any(relative.is_relative_to(prefix) for prefix in _SKILL_PREFIXES)


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        loaded: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InstallConflictError(f"cannot parse {label}: {error}") from error
    if not isinstance(loaded, dict):
        raise InstallConflictError(f"{label} must be a JSON object")
    return dict(loaded)


class ProjectionInstaller:
    """Install generated per-skill directories while preserving target-owned files."""

    stale_lock_seconds = 300

    def __init__(self, source_projection: Path, target_root: Path) -> None:
        if source_projection.is_symlink():
            raise InstallError("source projection must be a non-symlinked directory")
        if target_root.is_symlink():
            raise InstallError("target root must be an existing non-symlinked directory")
        try:
            self.source_projection = source_projection.resolve(strict=True)
            self.target_root = target_root.resolve(strict=True)
        except OSError as error:
            raise InstallError(f"cannot resolve source or target: {error}") from error
        if not self.source_projection.is_dir():
            raise InstallError("source projection must be a non-symlinked directory")
        if not self.target_root.is_dir():
            raise InstallError("target root must be an existing non-symlinked directory")
        if self.target_root == self.source_projection:
            raise InstallError("source projection and target root must differ")
        self._replace: Callable[[Path, Path], None] = lambda source, destination: os.replace(
            source, destination
        )

    @property
    def _lock_path(self) -> Path:
        return self.target_root / LOCK_RELATIVE

    @property
    def _rollback_path(self) -> Path:
        return self.target_root / ROLLBACK_RELATIVE

    @property
    def _operation_lock(self) -> Path:
        return self.target_root / OPERATION_LOCK_RELATIVE

    def _assert_safe_target_path(self, relative: PurePosixPath) -> Path:
        if relative.is_absolute() or not relative.parts:
            raise InstallConflictError(f"invalid target path: {relative}")
        current = self.target_root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise InstallConflictError(f"symlinked target path is forbidden: {relative}")
        try:
            current.parent.resolve(strict=False).relative_to(self.target_root)
        except ValueError as error:
            raise InstallConflictError(f"target path escapes repository: {relative}") from error
        return current

    def _acquire_operation_lock(self, break_stale_lock: bool) -> None:
        self._assert_safe_target_path(PurePosixPath(OPERATION_LOCK_RELATIVE.as_posix()))
        self._operation_lock.parent.mkdir(parents=True, exist_ok=True)
        payload = _json_bytes({"pid": os.getpid(), "created_at": int(time.time())})
        try:
            descriptor = os.open(self._operation_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            age = time.time() - self._operation_lock.stat().st_mtime
            if break_stale_lock and age > self.stale_lock_seconds:
                self._operation_lock.unlink()
                return self._acquire_operation_lock(False)
            state = "stale" if age > self.stale_lock_seconds else "active"
            raise InstallConflictError(
                f"install lock is {state}: {self._operation_lock} (age={age:.1f}s)"
            ) from error
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)

    def _release_operation_lock(self) -> None:
        self._operation_lock.unlink(missing_ok=True)

    def _load_source(self) -> ProjectionContent:
        source_lock_path = self.source_projection / "projection.lock.json"
        source_lock = _read_json_object(source_lock_path, "source projection lock")
        raw_hashes = source_lock.get("files")
        if source_lock.get("schema_version") != "1" or not isinstance(raw_hashes, dict):
            raise InstallConflictError("source projection lock has an unsupported schema")

        for relative, canonical in (
            (Path(".agents/skills"), True),
            (Path(".claude/skills"), False),
        ):
            report = validate_repository(self.source_projection / relative, canonical=canonical)
            errors = [item.code for item in report.diagnostics if item.severity.value == "error"]
            if errors:
                raise InstallConflictError(
                    f"source {relative.as_posix()} projection is invalid: {', '.join(errors)}"
                )

        roots: list[PurePosixPath] = []
        names_by_prefix: list[set[str]] = []
        for prefix in _SKILL_PREFIXES:
            directory = self.source_projection / Path(prefix.as_posix())
            names = {
                child.name
                for child in directory.iterdir()
                if child.is_dir() and not child.is_symlink()
            }
            names_by_prefix.append(names)
            roots.extend(prefix / name for name in sorted(names))
        if not names_by_prefix or names_by_prefix[0] != names_by_prefix[1]:
            raise InstallConflictError("source provider projections have different skill sets")

        files: dict[str, bytes] = {}
        modes: dict[str, int] = {}
        for root in roots:
            source_root = self.source_projection / Path(root.as_posix())
            for path in sorted(source_root.rglob("*")):
                if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                    continue
                if path.is_symlink():
                    raise InstallConflictError(f"source projection contains a symlink: {path}")
                if not path.is_file():
                    continue
                relative_path = path.relative_to(self.source_projection).as_posix()
                expected_hash = raw_hashes.get(relative_path)
                if not isinstance(expected_hash, str) or _sha256_file(path) != expected_hash:
                    raise InstallConflictError(
                        f"source projection digest mismatch or missing entry: {relative_path}"
                    )
                files[relative_path] = path.read_bytes()
                modes[relative_path] = path.stat().st_mode & 0o777
        return ProjectionContent(tuple(roots), files, modes, _sha256_file(source_lock_path))

    def _load_installed_lock(self) -> dict[str, Any] | None:
        if not self._lock_path.exists():
            return None
        if self._lock_path.is_symlink() or not self._lock_path.is_file():
            raise InstallConflictError("installed lock must be a regular file")
        lock = _read_json_object(self._lock_path, "installed lock")
        if lock.get("schema_version") != "1":
            raise InstallConflictError("installed lock has an unsupported schema")
        return lock

    def _lock_roots_and_hashes(
        self, lock: dict[str, Any]
    ) -> tuple[tuple[PurePosixPath, ...], dict[str, str]]:
        raw_roots = lock.get("managed_roots")
        raw_files = lock.get("files")
        if not isinstance(raw_roots, list) or not isinstance(raw_files, dict):
            raise InstallConflictError("installed lock is missing managed roots or files")
        roots: list[PurePosixPath] = []
        for raw in raw_roots:
            if not isinstance(raw, str):
                raise InstallConflictError("installed lock contains a non-string root")
            root = _safe_relative(raw)
            if not _under_skill_prefix(root) or len(root.parts) != 3:
                raise InstallConflictError(f"installed lock contains an unsafe root: {raw}")
            roots.append(root)
        hashes: dict[str, str] = {}
        for raw, digest in raw_files.items():
            if not isinstance(raw, str) or not isinstance(digest, str):
                raise InstallConflictError("installed lock contains invalid file data")
            relative = _safe_relative(raw)
            if not any(relative.is_relative_to(root) for root in roots):
                raise InstallConflictError(f"installed file is outside managed roots: {raw}")
            hashes[raw] = digest
        return tuple(roots), hashes

    def _assert_installed_clean(self, lock: dict[str, Any] | None) -> None:
        if lock is None:
            return
        roots, hashes = self._lock_roots_and_hashes(lock)
        actual: set[str] = set()
        for root in roots:
            target_root = self._assert_safe_target_path(root)
            if not target_root.is_dir():
                raise InstallConflictError(f"managed skill directory is missing: {root}")
            for path in target_root.rglob("*"):
                if path.is_symlink():
                    raise InstallConflictError(f"managed path became a symlink: {path}")
                if path.is_file():
                    relative = path.relative_to(self.target_root).as_posix()
                    actual.add(relative)
                    expected = hashes.get(relative)
                    if expected is None or _sha256_file(path) != expected:
                        raise InstallConflictError(f"managed file drift detected: {relative}")
        missing = sorted(set(hashes) - actual)
        if missing:
            raise InstallConflictError(f"managed files are missing: {', '.join(missing)}")

    def _assert_first_install_clear(self, content: ProjectionContent) -> None:
        conflicts = [
            root.as_posix()
            for root in content.roots
            if self._assert_safe_target_path(root).exists()
        ]
        if conflicts:
            raise InstallConflictError(
                "refusing to overwrite unowned skill directories: " + ", ".join(conflicts)
            )
        if self._rollback_path.exists():
            raise InstallConflictError("orphaned Polymind rollback state exists without a lock")

    def _new_lock(self, content: ProjectionContent) -> dict[str, object]:
        return {
            "schema_version": "1",
            "framework_version": __version__,
            "source_projection_sha256": content.projection_digest,
            "managed_roots": [root.as_posix() for root in content.roots],
            "files": {
                relative: _sha256_bytes(data) for relative, data in sorted(content.files.items())
            },
            "notice": ("Digests detect managed-file drift; they do not prove provenance or trust."),
        }

    def _current_files(self, lock: dict[str, Any] | None) -> dict[str, bytes]:
        if lock is None:
            return {}
        _, hashes = self._lock_roots_and_hashes(lock)
        return {relative: (self.target_root / Path(relative)).read_bytes() for relative in hashes}

    def _changes(self, current: dict[str, bytes], desired: dict[str, bytes]) -> tuple[str, ...]:
        changes: list[str] = []
        for relative in sorted(set(current) | set(desired)):
            if relative not in current:
                changes.append(f"ADD {relative}")
            elif relative not in desired:
                changes.append(f"REMOVE {relative}")
            elif current[relative] != desired[relative]:
                changes.append(f"MODIFY {relative}")
        return tuple(changes)

    def _render_diff(self, current: dict[str, bytes], desired: dict[str, bytes]) -> str:
        sections: list[str] = []
        size = 0
        for relative in sorted(set(current) | set(desired)):
            before = current.get(relative)
            after = desired.get(relative)
            if before == after:
                continue
            try:
                before_text = "" if before is None else before.decode("utf-8")
                after_text = "" if after is None else after.decode("utf-8")
            except UnicodeDecodeError:
                rendered = f"Binary files differ: {relative}\n"
            else:
                if len(before_text) + len(after_text) > _TEXT_DIFF_LIMIT:
                    rendered = f"Text diff omitted above {_TEXT_DIFF_LIMIT} bytes: {relative}\n"
                else:
                    rendered = "".join(
                        difflib.unified_diff(
                            before_text.splitlines(keepends=True),
                            after_text.splitlines(keepends=True),
                            fromfile=f"a/{relative}" if before is not None else "/dev/null",
                            tofile=f"b/{relative}" if after is not None else "/dev/null",
                        )
                    )
            encoded_size = len(rendered.encode())
            if size + encoded_size > _TOTAL_DIFF_LIMIT:
                sections.append("Diff output truncated at 1 MiB.\n")
                break
            sections.append(rendered)
            size += encoded_size
        return "".join(sections)

    def _stage_content(self, stage: Path, content: ProjectionContent) -> Path:
        for relative, data in content.files.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(content.modes[relative] & ~0o222)
        lock_path = stage / LOCK_RELATIVE
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_bytes(_json_bytes(self._new_lock(content)))
        lock_path.chmod(0o444)
        return lock_path

    def _restore_after_failure(
        self,
        roots: tuple[PurePosixPath, ...],
        backup: Path,
        previous_lock_exists: bool,
        lock_touched: bool,
    ) -> None:
        for root in roots:
            destination = self.target_root / Path(root.as_posix())
            saved = backup / Path(root.as_posix())
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()
            if saved.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(saved, destination)
        if lock_touched:
            if self._lock_path.exists():
                self._lock_path.chmod(self._lock_path.stat().st_mode | 0o200)
                self._lock_path.unlink()
            saved_lock = backup / LOCK_RELATIVE
            if previous_lock_exists and saved_lock.exists():
                self._lock_path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(saved_lock, self._lock_path)

    def _write_rollback_snapshot(
        self,
        snapshot: Path,
        backup: Path,
        previous_lock: dict[str, Any] | None,
        current_lock: Path,
    ) -> None:
        roots: tuple[PurePosixPath, ...] = ()
        if previous_lock is not None:
            roots, _ = self._lock_roots_and_hashes(previous_lock)
            for root in roots:
                saved = backup / Path(root.as_posix())
                if saved.exists():
                    destination = snapshot / "files" / Path(root.as_posix())
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(saved, destination)
            previous_path = snapshot / "previous-lock.json"
            previous_path.parent.mkdir(parents=True, exist_ok=True)
            previous_path.write_bytes(_json_bytes(previous_lock))
        metadata = {
            "schema_version": "1",
            "expected_current_lock_sha256": _sha256_file(current_lock),
            "previous_lock_present": previous_lock is not None,
            "previous_managed_roots": [root.as_posix() for root in roots],
        }
        snapshot.mkdir(parents=True, exist_ok=True)
        snapshot.joinpath("snapshot.json").write_bytes(_json_bytes(metadata))

    def _apply(
        self,
        content: ProjectionContent,
        previous_lock: dict[str, Any] | None,
    ) -> None:
        previous_roots: tuple[PurePosixPath, ...] = ()
        if previous_lock is not None:
            previous_roots, _ = self._lock_roots_and_hashes(previous_lock)
        all_roots = tuple(sorted(set(previous_roots) | set(content.roots)))
        for root in all_roots:
            self._assert_safe_target_path(root)
        self._assert_safe_target_path(PurePosixPath(LOCK_RELATIVE.as_posix()))
        self._assert_safe_target_path(PurePosixPath(ROLLBACK_RELATIVE.as_posix()))

        with (
            tempfile.TemporaryDirectory(
                prefix=".polymind-install-stage-", dir=self.target_root.parent
            ) as stage_name,
            tempfile.TemporaryDirectory(
                prefix=".polymind-install-backup-", dir=self.target_root.parent
            ) as backup_name,
        ):
            stage = Path(stage_name)
            backup = Path(backup_name)
            staged_lock = self._stage_content(stage, content)
            previous_lock_exists = self._lock_path.exists()
            previous_rollback_backup = backup / "previous-rollback"
            touched_roots: list[PurePosixPath] = []
            lock_touched = False
            rollback_touched = False
            try:
                for root in all_roots:
                    destination = self.target_root / Path(root.as_posix())
                    saved = backup / Path(root.as_posix())
                    staged = stage / Path(root.as_posix())
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if destination.exists():
                        saved.parent.mkdir(parents=True, exist_ok=True)
                        self._replace(destination, saved)
                        touched_roots.append(root)
                    if staged.exists():
                        self._replace(staged, destination)
                        if root not in touched_roots:
                            touched_roots.append(root)
                if previous_lock_exists:
                    saved_lock = backup / LOCK_RELATIVE
                    saved_lock.parent.mkdir(parents=True, exist_ok=True)
                    self._replace(self._lock_path, saved_lock)
                    lock_touched = True
                self._lock_path.parent.mkdir(parents=True, exist_ok=True)
                self._replace(staged_lock, self._lock_path)
                lock_touched = True
                new_lock = self._load_installed_lock()
                assert new_lock is not None
                self._assert_installed_clean(new_lock)

                rollback_stage = stage / "rollback-snapshot"
                self._write_rollback_snapshot(
                    rollback_stage, backup, previous_lock, self._lock_path
                )
                if self._rollback_path.exists():
                    self._replace(self._rollback_path, previous_rollback_backup)
                    rollback_touched = True
                self._replace(rollback_stage, self._rollback_path)
                rollback_touched = True
            except BaseException:
                if rollback_touched:
                    if self._rollback_path.exists():
                        shutil.rmtree(self._rollback_path)
                    if previous_rollback_backup.exists():
                        os.replace(previous_rollback_backup, self._rollback_path)
                self._restore_after_failure(
                    tuple(touched_roots), backup, previous_lock_exists, lock_touched
                )
                raise

    def _rollback(self) -> InstallResult:
        self._assert_safe_target_path(PurePosixPath(ROLLBACK_RELATIVE.as_posix()))
        current_lock = self._load_installed_lock()
        if current_lock is None:
            raise InstallConflictError("nothing is installed")
        self._assert_installed_clean(current_lock)
        snapshot_path = self._rollback_path / "snapshot.json"
        if not snapshot_path.is_file() or snapshot_path.is_symlink():
            raise InstallConflictError("no rollback snapshot is available")
        snapshot = _read_json_object(snapshot_path, "rollback snapshot")
        if snapshot.get("schema_version") != "1" or snapshot.get(
            "expected_current_lock_sha256"
        ) != _sha256_file(self._lock_path):
            raise InstallConflictError("rollback snapshot does not match the current install")
        previous_present = snapshot.get("previous_lock_present") is True
        previous_lock: dict[str, Any] | None = None
        if previous_present:
            previous_lock = _read_json_object(
                self._rollback_path / "previous-lock.json", "rollback previous lock"
            )
        current_roots, _ = self._lock_roots_and_hashes(current_lock)
        previous_roots: tuple[PurePosixPath, ...] = ()
        if previous_lock is not None:
            previous_roots, _ = self._lock_roots_and_hashes(previous_lock)
        all_roots = tuple(sorted(set(current_roots) | set(previous_roots)))

        with tempfile.TemporaryDirectory(
            prefix=".polymind-rollback-backup-", dir=self.target_root.parent
        ) as backup_name:
            backup = Path(backup_name)
            snapshot_backup = backup / "rollback-snapshot"
            if any(path.is_symlink() for path in self._rollback_path.rglob("*")):
                raise InstallConflictError("rollback snapshot contains a symlink")
            shutil.copytree(self._rollback_path, snapshot_backup)
            touched_roots: list[PurePosixPath] = []
            lock_touched = False
            try:
                for root in all_roots:
                    destination = self._assert_safe_target_path(root)
                    current_saved = backup / "current" / Path(root.as_posix())
                    previous_saved = snapshot_backup / "files" / Path(root.as_posix())
                    if destination.exists():
                        current_saved.parent.mkdir(parents=True, exist_ok=True)
                        self._replace(destination, current_saved)
                        touched_roots.append(root)
                    if previous_saved.exists():
                        if previous_saved.is_symlink() or any(
                            path.is_symlink() for path in previous_saved.rglob("*")
                        ):
                            raise InstallConflictError(
                                f"rollback snapshot contains a symlink: {root}"
                            )
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(previous_saved, destination)
                        if root not in touched_roots:
                            touched_roots.append(root)
                current_lock_saved = backup / "current-lock.json"
                self._replace(self._lock_path, current_lock_saved)
                lock_touched = True
                if previous_lock is not None:
                    self._lock_path.write_bytes(_json_bytes(previous_lock))
                    self._lock_path.chmod(0o444)
                    self._assert_installed_clean(previous_lock)
                self._rollback_path.chmod(self._rollback_path.stat().st_mode | 0o700)
                shutil.rmtree(self._rollback_path)
            except BaseException:
                for root in touched_roots:
                    destination = self.target_root / Path(root.as_posix())
                    if destination.is_dir():
                        shutil.rmtree(destination)
                    current_saved = backup / "current" / Path(root.as_posix())
                    if current_saved.exists():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(current_saved, destination)
                current_lock_saved = backup / "current-lock.json"
                if lock_touched and current_lock_saved.exists():
                    if self._lock_path.exists():
                        self._lock_path.chmod(self._lock_path.stat().st_mode | 0o200)
                        self._lock_path.unlink()
                    os.replace(current_lock_saved, self._lock_path)
                if not self._rollback_path.exists():
                    shutil.copytree(snapshot_backup, self._rollback_path)
                raise
        return InstallResult(
            self.target_root,
            tuple(f"ROLLBACK {root.as_posix()}" for root in all_roots),
            "",
            False,
            False,
            True,
        )

    def run(
        self,
        *,
        apply: bool = False,
        check: bool = False,
        rollback: bool = False,
        show_diff: bool = False,
        break_stale_lock: bool = False,
    ) -> InstallResult:
        """Plan, check, apply, or roll back one downstream installation."""
        if sum((apply, check, rollback)) > 1:
            raise InstallError("apply, check, and rollback modes are mutually exclusive")
        self._acquire_operation_lock(break_stale_lock)
        try:
            if rollback:
                return self._rollback()
            content = self._load_source()
            installed_lock = self._load_installed_lock()
            if installed_lock is None:
                self._assert_first_install_clear(content)
            else:
                self._assert_installed_clean(installed_lock)
            current = self._current_files(installed_lock)
            changes = self._changes(current, content.files)
            rendered_diff = self._render_diff(current, content.files) if show_diff else ""
            if check and changes:
                raise InstallDriftError("installation drift:\n" + "\n".join(changes))
            if apply and changes:
                self._apply(content, installed_lock)
            return InstallResult(
                self.target_root,
                changes,
                rendered_diff,
                apply and bool(changes),
                check,
                False,
                self.source_projection,
                content.projection_digest,
            )
        finally:
            self._release_operation_lock()
