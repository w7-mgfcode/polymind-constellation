from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from polymind.cli import main


def _validator() -> Path:
    return (
        Path(__file__).parents[1] / "skills" / "maintaining-agent-docs" / "scripts" / "validate.py"
    )


def _run(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_validator()), *arguments, str(root)],
        check=False,
        text=True,
        capture_output=True,
    )


def _write_valid_docs(root: Path) -> None:
    root.joinpath("AGENTS.md").write_text(
        """# Project instructions

## Setup and install
Run the documented bootstrap command.

## Build and run
Use the repository scripts.

## Test and verify
Run the deterministic verification contract.

## Project structure
Keep packages within their owned directories.

## Safety and conventions
Preserve unrelated work and review every diff.

<!-- BEGIN maintaining-agent-docs:root -->
Generated facts live in this uniquely owned region.
<!-- END maintaining-agent-docs:root -->
""",
        encoding="utf-8",
    )
    root.joinpath("CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")


def test_agent_docs_validator_accepts_safe_profile(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    result = _run(tmp_path, "--check", "--strict")
    assert result.returncode == 0, result.stdout
    assert "0 error(s), 0 warning(s)" in result.stdout


def test_marker_nesting_order_and_uniqueness_are_enforced(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    tmp_path.joinpath("README.md").write_text(
        """<!-- END maintaining-agent-docs:early -->
<!-- BEGIN maintaining-agent-docs:dup -->
<!-- BEGIN maintaining-agent-docs:nested -->
<!-- END maintaining-agent-docs:nested -->
<!-- END maintaining-agent-docs:dup -->
<!-- BEGIN maintaining-agent-docs:dup -->
<!-- END maintaining-agent-docs:dup -->
""",
        encoding="utf-8",
    )
    result = _run(tmp_path, "--check")
    assert result.returncode == 1
    assert "MARKER_ORDER" in result.stdout
    assert "MARKER_NESTED" in result.stdout
    assert "MARKER_DUPLICATE" in result.stdout


def test_yaml_link_escape_and_redacted_secret_are_rejected(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    token = "sk-abcdefghijklmnopqrstuvwxyz123456"
    tmp_path.joinpath("README.md").write_text(
        f"Read [outside](../outside.md).\n\nExample token: {token}\n", encoding="utf-8"
    )
    skill = tmp_path / "skills/example/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: [broken\ndescription: bad\n---\n", encoding="utf-8")
    result = _run(tmp_path, "--check")
    assert result.returncode == 1
    assert "LINK_ESCAPE" in result.stdout
    assert "YAML_INVALID" in result.stdout
    assert "SECRET_DETECTED" in result.stdout
    assert token not in result.stdout


def test_hashed_fixture_allowlist_suppresses_only_known_value(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    token = "sk-abcdefghijklmnopqrstuvwxyz123456"
    tmp_path.joinpath("README.md").write_text(f"Fixture: {token}\n", encoding="utf-8")
    allowlist = tmp_path / "fixture-secret-hashes.txt"
    allowlist.write_text(hashlib.sha256(token.encode()).hexdigest() + "\n", encoding="utf-8")
    result = _run(tmp_path, "--check", "--strict", "--secret-allowlist", str(allowlist))
    assert result.returncode == 0, result.stdout


def test_semantic_duplication_threshold_and_diff_are_deterministic(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    duplicate = (
        "All production changes require review, deterministic tests, documented rollback, "
        "and explicit approval before deployment."
    )
    with tmp_path.joinpath("AGENTS.md").open("a", encoding="utf-8") as stream:
        stream.write("\n" + duplicate + "\n")
    tmp_path.joinpath("CLAUDE.md").write_text("@AGENTS.md\n\n" + duplicate + "\n", encoding="utf-8")
    result = _run(tmp_path, "--check", "--strict", "--diff", "--duplication-threshold", "90")
    assert result.returncode == 1
    assert "POLICY_DUPLICATION" in result.stdout
    assert "duplicate blocks removed" in result.stdout


def test_gemini_context_profile_is_parsed_as_json(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    settings = tmp_path / ".gemini/settings.json"
    settings.parent.mkdir()
    settings.write_text('{"context": {"fileName": ["AGENTS.md"]}}\n', encoding="utf-8")
    assert _run(tmp_path, "--check", "--strict").returncode == 0
    settings.write_text('{"context": {"fileName": ["GEMINI.md"]}}\n', encoding="utf-8")
    result = _run(tmp_path, "--check", "--strict")
    assert result.returncode == 1
    assert "GEMINI_CONTEXT" in result.stdout


def test_framework_cli_exposes_package_relative_validator(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    assert main(["validate-agent-docs", "--check", "--strict", str(tmp_path)]) == 0
