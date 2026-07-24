from __future__ import annotations

import json
import os
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from polymind.projection import (
    ProjectionCompiler,
    ProjectionConflictError,
    ProjectionDriftError,
    ProjectionError,
)


@pytest.fixture
def projection_repo(tmp_path: Path) -> Path:
    source = Path(__file__).parents[1]
    repository = tmp_path / "repository"
    repository.mkdir()
    shutil.copytree(source / "skills", repository / "skills")
    shutil.copytree(source / "adapters", repository / "adapters")
    shutil.copytree(source / "examples", repository / "examples")
    shutil.copy2(source / "AGENTS.md", repository / "AGENTS.md")
    shutil.copy2(source / "CLAUDE.md", repository / "CLAUDE.md")
    return repository


def test_dry_run_is_non_mutating(projection_repo: Path) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    result = compiler.sync()
    assert result.changes
    assert not result.applied
    assert not (projection_repo / "dist/repo").exists()


def test_apply_is_idempotent_and_check_detects_no_drift(projection_repo: Path) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    first = compiler.sync(apply=True)
    assert first.applied
    assert compiler.sync(apply=True).changes == ()
    assert compiler.sync(check=True).changes == ()

    output = projection_repo / "dist/repo"
    agent_names = {path.name for path in (output / ".agents/skills").iterdir() if path.is_dir()}
    claude_names = {path.name for path in (output / ".claude/skills").iterdir() if path.is_dir()}
    assert (
        agent_names
        == claude_names
        == {
            "analyzing-workflow-patterns",
            "maintaining-agent-docs",
            "starting-new-project",
        }
    )
    agent_skill = output / ".agents/skills/starting-new-project/SKILL.md"
    claude_skill = output / ".claude/skills/starting-new-project/SKILL.md"
    assert "allowed-tools:" not in agent_skill.read_text(encoding="utf-8")
    assert "allowed-tools:" in claude_skill.read_text(encoding="utf-8")
    assert output.joinpath("projection.lock.json").stat().st_mode & 0o222 == 0
    assert output.joinpath("opencode.local.example.json").stat().st_mode & 0o222 == 0
    assert (
        output.joinpath("opencode.local.example.json").read_bytes()
        == projection_repo.joinpath("examples/opencode-local/opencode.json").read_bytes()
    )


def test_catalog_is_data_only_and_contains_three_skills(projection_repo: Path) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    compiler.sync(apply=True)
    catalog: Any = json.loads(
        (projection_repo / "dist/repo/catalog/skills.json").read_text(encoding="utf-8")
    )
    assert len(catalog["skills"]) == 3
    assert all("execute" not in entry for entry in catalog["skills"])
    assert all(entry["package_path"].startswith(".agents/skills/") for entry in catalog["skills"])


def test_unrelated_gemini_settings_are_preserved(projection_repo: Path) -> None:
    settings = projection_repo / "dist/repo/.gemini/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"theme": "dark"}\n', encoding="utf-8")
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    compiler.sync(apply=True)
    merged: Any = json.loads(settings.read_text(encoding="utf-8"))
    assert merged["theme"] == "dark"
    assert merged["context"]["fileName"] == ["AGENTS.md"]

    settings.chmod(0o644)
    merged["theme"] = "light"
    settings.write_text(json.dumps(merged), encoding="utf-8")
    assert compiler.sync(check=True).changes == ()


def test_conflicting_gemini_owned_value_is_refused(projection_repo: Path) -> None:
    settings = projection_repo / "dist/repo/.gemini/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"context": {"fileName": ["GEMINI.md"]}}', encoding="utf-8")
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    with pytest.raises(ProjectionConflictError, match="conflicts"):
        compiler.sync(apply=True)


def test_hand_edits_and_unknown_projection_files_are_refused(projection_repo: Path) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    compiler.sync(apply=True)
    skill = projection_repo / "dist/repo/.agents/skills/starting-new-project/SKILL.md"
    skill.chmod(0o644)
    skill.write_text(skill.read_text(encoding="utf-8") + "\nmanual edit\n", encoding="utf-8")
    with pytest.raises(ProjectionConflictError, match="drift"):
        compiler.sync(apply=True)

    clean_repo = projection_repo.parent / "clean-repository"
    shutil.copytree(projection_repo, clean_repo)
    clean_output = clean_repo / "dist/repo"
    shutil.rmtree(clean_output)
    clean_compiler = ProjectionCompiler(clean_repo, Path("dist/repo"))
    clean_compiler.sync(apply=True)
    unknown = clean_output / ".claude/skills/manual.txt"
    unknown.write_text("manual", encoding="utf-8")
    with pytest.raises(ProjectionConflictError, match="unknown files"):
        clean_compiler.sync(apply=True)


def test_non_generated_destination_is_refused(projection_repo: Path) -> None:
    destination = projection_repo / "dist/repo/.agents/skills/manual"
    destination.mkdir(parents=True)
    destination.joinpath("SKILL.md").write_text("human content", encoding="utf-8")
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    with pytest.raises(ProjectionConflictError, match="non-generated"):
        compiler.sync(apply=True)


def test_overlay_cannot_broaden_or_add_unknown_fields(projection_repo: Path) -> None:
    overlay = projection_repo / "adapters/claude/overlays/maintaining-agent-docs.toml"
    text = overlay.read_text(encoding="utf-8")
    overlay.write_text(
        text.replace('["filesystem.read"]', '["filesystem.read", "network.write"]'),
        encoding="utf-8",
    )
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    with pytest.raises(ProjectionError, match="broadens"):
        compiler.sync()

    overlay.write_text(
        text.replace("allowed-tools =", 'model = "unsafe"\nallowed-tools ='), encoding="utf-8"
    )
    with pytest.raises(ProjectionError, match="non-allowlisted"):
        compiler.sync()


def test_output_path_escape_is_rejected(projection_repo: Path) -> None:
    with pytest.raises(ProjectionError, match="inside the repository"):
        ProjectionCompiler(projection_repo, projection_repo.parent / "outside")
    with pytest.raises(ProjectionError, match="direct root projection"):
        ProjectionCompiler(projection_repo, projection_repo)


def test_active_and_stale_locks_fail_closed(projection_repo: Path) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    lock = projection_repo / "dist/.repo.polymind-sync.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("active", encoding="utf-8")
    with pytest.raises(ProjectionConflictError, match="active"):
        compiler.sync()

    old = time.time() - compiler.stale_lock_seconds - 10
    os.utime(lock, (old, old))
    assert compiler.sync(break_stale_lock=True).changes
    assert not lock.exists()


@pytest.mark.parametrize("failure_call", range(1, 19))
def test_apply_rolls_back_after_every_replacement_failure(
    projection_repo: Path, failure_call: int
) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    compiler.sync(apply=True)
    output = projection_repo / "dist/repo"
    before = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    source = projection_repo / "skills/analyzing-workflow-patterns/references/output-quality.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nParity note.\n", encoding="utf-8")

    original_replace: Callable[[Path, Path], None] = compiler._replace
    calls = 0

    def fail_once(source_path: Path, destination_path: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == failure_call:
            raise OSError("simulated interruption")
        original_replace(source_path, destination_path)

    compiler._replace = fail_once
    with pytest.raises(OSError, match="simulated interruption"):
        compiler.sync(apply=True)
    after = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert calls >= failure_call
    assert after == before


def test_digest_identical_symlink_substitution_is_refused(projection_repo: Path) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    compiler.sync(apply=True)
    output = projection_repo / "dist/repo"
    target = output / ".agents/skills/starting-new-project/SKILL.md"
    identical = projection_repo / "identical-skill.md"
    identical.write_bytes(target.read_bytes())
    target.unlink()
    try:
        target.symlink_to(identical)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(ProjectionConflictError, match="symlinked"):
        compiler.sync(check=True)


def test_check_reports_canonical_drift(projection_repo: Path) -> None:
    compiler = ProjectionCompiler(projection_repo, Path("dist/repo"))
    compiler.sync(apply=True)
    source = projection_repo / "skills/starting-new-project/references/discovery-questions.md"
    source.write_text(
        source.read_text(encoding="utf-8") + "\nNew canonical line.\n", encoding="utf-8"
    )
    with pytest.raises(ProjectionDriftError, match="MODIFY"):
        compiler.sync(check=True)
