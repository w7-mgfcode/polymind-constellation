from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

from polymind.validation import validate_repository


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_provenance_files_are_mapped_and_present() -> None:
    root = Path(__file__).parents[1]
    provenance: Any = json.loads(
        (root / "docs/provenance/dynamous-community-skills.json").read_text(encoding="utf-8")
    )
    migration: Any = json.loads(
        (root / "docs/provenance/migration-map.json").read_text(encoding="utf-8")
    )
    source_files = {entry["path"]: entry for entry in provenance["files"]}
    mapped_files = {entry["source_path"]: entry for entry in migration["entries"]}
    assert len(source_files) == len(mapped_files) == 19
    assert source_files.keys() == mapped_files.keys()
    for source_path, mapping in mapped_files.items():
        target = root / mapping["target_path"]
        assert target.is_file(), source_path
        assert not target.is_symlink(), source_path
        if mapping["transformation"] == "exact copy":
            assert _sha256(target) == source_files[source_path]["sha256"]


def test_migrated_packages_preserve_parity_contracts() -> None:
    root = Path(__file__).parents[1]
    report = validate_repository(root / "skills")
    assert report.valid
    assert {package.metadata.name for package in report.packages} == {
        "analyzing-workflow-patterns",
        "maintaining-agent-docs",
        "starting-new-project",
    }

    analyzer = root / "skills/analyzing-workflow-patterns"
    legacy = analyzer.joinpath("references/profiles/legacy-five-flow.md").read_text(
        encoding="utf-8"
    )
    assert all(f"| {phase} |" in legacy for phase in range(11))
    assert "Hard stop before" in legacy
    assert (root / "skills/analyzing-workflow-patterns/assets/fit-matrix.md").is_file()

    starter = (root / "skills/starting-new-project/SKILL.md").read_text(encoding="utf-8")
    assert "Ask exactly\n   one targeted question per turn" in starter
    assert "Ask for approval of the plan" in starter
    assert "Create these exact files?" in starter

    maintainer = (root / "skills/maintaining-agent-docs/SKILL.md").read_text(encoding="utf-8")
    assert "Show a unified diff" in maintainer
    assert "Preserve human-authored content" in maintainer
    assert (root / "skills/maintaining-agent-docs/scripts/validate.py").is_file()


def test_every_skill_has_trigger_parity_cases_and_neutral_frontmatter() -> None:
    root = Path(__file__).parents[1]
    for manifest_path in sorted((root / "skills").glob("*/skill.toml")):
        raw = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        assert len(raw["triggers"]["positive"]) >= 2
        assert len(raw["triggers"]["negative"]) >= 2
        skill_text = manifest_path.with_name("SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill_text.split("---", 2)[1]
        assert "allowed-tools:" not in frontmatter
