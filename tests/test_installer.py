from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import polymind.installer as installer_module
from polymind.installer import (
    LOCK_RELATIVE,
    InstallConflictError,
    InstallError,
    ProjectionInstaller,
    default_projection_source,
)
from polymind.projection import ProjectionCompiler

ROOT = Path(__file__).parents[1]


@pytest.fixture
def source_projection(tmp_path: Path) -> Path:
    destination = tmp_path / "source-projection"
    shutil.copytree(ROOT / "dist/repo", destination)
    return destination


@pytest.fixture
def downstream(tmp_path: Path) -> Path:
    target = tmp_path / "downstream"
    target.mkdir()
    target.joinpath("AGENTS.md").write_text("# Target-owned instructions\n", encoding="utf-8")
    target.joinpath("CLAUDE.md").write_text("# Target-owned Claude rules\n", encoding="utf-8")
    unrelated = target / ".agents/skills/unrelated-skill/SKILL.md"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("unrelated\n", encoding="utf-8")
    return target


def _update_projected_file(source: Path, relative: str, suffix: str) -> None:
    path = source / relative
    path.chmod(path.stat().st_mode | 0o200)
    path.write_text(path.read_text(encoding="utf-8") + suffix, encoding="utf-8")
    path.chmod(path.stat().st_mode & ~0o222)
    lock_path = source / "projection.lock.json"
    lock_path.chmod(lock_path.stat().st_mode | 0o200)
    lock: Any = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["files"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lock_path.chmod(lock_path.stat().st_mode & ~0o222)


def test_default_source_ignores_cwd_projection_and_prefers_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "venv/lib/python3.11/site-packages/polymind"
    bundled = package / "_projection"
    bundled.mkdir(parents=True)
    bundled.joinpath("projection.lock.json").write_text("{}\n", encoding="utf-8")
    cwd = tmp_path / "untrusted-repository"
    cwd_projection = cwd / "dist/repo"
    cwd_projection.mkdir(parents=True)
    cwd_projection.joinpath("projection.lock.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(installer_module, "__file__", str(package / "installer.py"))
    monkeypatch.chdir(cwd)

    assert default_projection_source() == bundled


def test_default_source_uses_module_anchored_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    package = repository / "src/polymind"
    package.mkdir(parents=True)
    repository.joinpath("pyproject.toml").write_text("[project]\n", encoding="utf-8")
    checkout = repository / "dist/repo"
    checkout.mkdir(parents=True)
    checkout.joinpath("projection.lock.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(installer_module, "__file__", str(package / "installer.py"))

    assert default_projection_source() == checkout


def test_dry_run_diff_is_non_mutating_and_preserves_target_files(
    source_projection: Path, downstream: Path
) -> None:
    before_agents = downstream.joinpath("AGENTS.md").read_bytes()
    before_claude = downstream.joinpath("CLAUDE.md").read_bytes()

    result = ProjectionInstaller(source_projection, downstream).run(show_diff=True)

    assert result.changes
    assert not result.applied
    assert "--- /dev/null" in result.diff
    assert not downstream.joinpath(LOCK_RELATIVE).exists()
    assert downstream.joinpath("AGENTS.md").read_bytes() == before_agents
    assert downstream.joinpath("CLAUDE.md").read_bytes() == before_claude
    assert downstream.joinpath(".agents/skills/unrelated-skill/SKILL.md").is_file()


def test_wheel_bytecode_cache_is_not_treated_as_projection_content(
    source_projection: Path, downstream: Path
) -> None:
    cache = source_projection / (
        ".agents/skills/maintaining-agent-docs/scripts/__pycache__/validate.cpython-314.pyc"
    )
    cache.parent.mkdir()
    cache.write_bytes(b"wheel-generated-bytecode")

    ProjectionInstaller(source_projection, downstream).run(apply=True)

    assert not downstream.joinpath(cache.relative_to(source_projection)).exists()


def test_apply_check_and_fresh_install_rollback(source_projection: Path, downstream: Path) -> None:
    installer = ProjectionInstaller(source_projection, downstream)

    applied = installer.run(apply=True)
    checked = installer.run(check=True)

    assert applied.applied
    assert checked.changes == ()
    assert downstream.joinpath(LOCK_RELATIVE).is_file()
    assert downstream.joinpath(".agents/skills/starting-new-project/SKILL.md").is_file()
    assert downstream.joinpath(".claude/skills/starting-new-project/SKILL.md").is_file()

    rolled_back = installer.run(rollback=True)

    assert rolled_back.rolled_back
    assert not downstream.joinpath(LOCK_RELATIVE).exists()
    assert not downstream.joinpath(".agents/skills/starting-new-project").exists()
    assert downstream.joinpath(".agents/skills/unrelated-skill/SKILL.md").is_file()
    assert downstream.joinpath("AGENTS.md").read_text(encoding="utf-8").startswith("# Target-owned")


def test_managed_update_can_roll_back_one_generation(
    source_projection: Path, downstream: Path
) -> None:
    relative = ".agents/skills/starting-new-project/SKILL.md"
    installer = ProjectionInstaller(source_projection, downstream)
    installer.run(apply=True)
    original = downstream.joinpath(relative).read_bytes()
    _update_projected_file(source_projection, relative, "\nPhase 8 update fixture.\n")

    updated = installer.run(apply=True)

    assert f"MODIFY {relative}" in updated.changes
    assert downstream.joinpath(relative).read_bytes() != original

    installer.run(rollback=True)

    assert downstream.joinpath(relative).read_bytes() == original
    assert installer.run().changes == (f"MODIFY {relative}",)


def test_target_drift_and_unowned_skill_conflicts_fail_closed(
    source_projection: Path, downstream: Path, tmp_path: Path
) -> None:
    installer = ProjectionInstaller(source_projection, downstream)
    installer.run(apply=True)
    managed = downstream / ".agents/skills/starting-new-project/SKILL.md"
    managed.chmod(managed.stat().st_mode | 0o200)
    managed.write_text("drift\n", encoding="utf-8")

    with pytest.raises(InstallConflictError, match="drift"):
        installer.run()

    occupied = tmp_path / "occupied"
    conflict = occupied / ".claude/skills/starting-new-project/SKILL.md"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("human-owned\n", encoding="utf-8")
    with pytest.raises(InstallConflictError, match="unowned"):
        ProjectionInstaller(source_projection, occupied).run()


def test_interrupted_update_restores_previous_install(
    source_projection: Path, downstream: Path
) -> None:
    relative = ".agents/skills/starting-new-project/SKILL.md"
    baseline = ProjectionInstaller(source_projection, downstream)
    baseline.run(apply=True)
    before_file = downstream.joinpath(relative).read_bytes()
    before_lock = downstream.joinpath(LOCK_RELATIVE).read_bytes()
    _update_projected_file(source_projection, relative, "\nInterrupted update.\n")

    interrupted = ProjectionInstaller(source_projection, downstream)
    original_replace: Callable[[Path, Path], None] = interrupted._replace
    calls = 0

    def fail_once(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise OSError("simulated install interruption")
        original_replace(source, destination)

    interrupted._replace = fail_once
    with pytest.raises(OSError, match="simulated install interruption"):
        interrupted.run(apply=True)

    assert downstream.joinpath(relative).read_bytes() == before_file
    assert downstream.joinpath(LOCK_RELATIVE).read_bytes() == before_lock


def test_interrupted_rollback_restores_current_install(
    source_projection: Path, downstream: Path
) -> None:
    installer = ProjectionInstaller(source_projection, downstream)
    installer.run(apply=True)
    lock_before = downstream.joinpath(LOCK_RELATIVE).read_bytes()
    skill_path = downstream / ".agents/skills/starting-new-project/SKILL.md"
    skill_before = skill_path.read_bytes()
    original_replace: Callable[[Path, Path], None] = installer._replace
    calls = 0

    def fail_once(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("simulated rollback interruption")
        original_replace(source, destination)

    installer._replace = fail_once
    with pytest.raises(OSError, match="simulated rollback interruption"):
        installer.run(rollback=True)

    assert downstream.joinpath(LOCK_RELATIVE).read_bytes() == lock_before
    assert skill_path.read_bytes() == skill_before


def test_symlinked_target_path_is_rejected(
    source_projection: Path, downstream: Path, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = downstream / ".claude/skills/analyzing-workflow-patterns"
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(InstallConflictError, match="symlinked"):
        ProjectionInstaller(source_projection, downstream).run()


def test_symlinked_source_and_target_roots_are_rejected(
    source_projection: Path, downstream: Path, tmp_path: Path
) -> None:
    source_link = tmp_path / "source-link"
    target_link = tmp_path / "target-link"
    try:
        source_link.symlink_to(source_projection, target_is_directory=True)
        target_link.symlink_to(downstream, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(InstallError, match="source projection.*non-symlinked"):
        ProjectionInstaller(source_link, downstream)
    with pytest.raises(InstallError, match="target root.*non-symlinked"):
        ProjectionInstaller(source_projection, target_link)


def test_contributor_fixture_adds_a_fourth_skill_to_both_projections(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "authoring-repo"
    repository.mkdir()
    for directory in ("skills", "adapters", "examples"):
        shutil.copytree(ROOT / directory, repository / directory)
    shutil.copytree(
        ROOT / "tests/fixtures/contributor/fourth-skill",
        repository / "skills/fourth-skill",
    )
    shutil.copy2(ROOT / "AGENTS.md", repository / "AGENTS.md")
    shutil.copy2(ROOT / "CLAUDE.md", repository / "CLAUDE.md")

    ProjectionCompiler(repository, Path("dist/repo")).sync(apply=True)

    assert repository.joinpath("dist/repo/.agents/skills/fourth-skill/SKILL.md").is_file()
    assert repository.joinpath("dist/repo/.claude/skills/fourth-skill/SKILL.md").is_file()
    catalog: Any = json.loads(
        repository.joinpath("dist/repo/catalog/skills.json").read_text(encoding="utf-8")
    )
    assert {item["name"] for item in catalog["skills"]} >= {"fourth-skill"}
