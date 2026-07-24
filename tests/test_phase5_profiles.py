from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def _text(path: str) -> str:
    return ROOT.joinpath(path).read_text(encoding="utf-8")


def test_all_canonical_skills_are_phase5_versions() -> None:
    for path in sorted(ROOT.glob("skills/*/SKILL.md")):
        frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
        metadata = yaml.safe_load(frontmatter)
        assert metadata["metadata"]["polymind.version"] == "2.0.0"
        assert "portable" in metadata["metadata"]["polymind.tags"]


def test_every_selectable_profile_declares_prerequisites_behavior_and_validation() -> None:
    profiles = [
        *ROOT.glob("skills/starting-new-project/references/profiles/*.md"),
        *ROOT.glob("skills/analyzing-workflow-patterns/references/profiles/*.md"),
    ]
    assert len(profiles) >= 7
    for profile in profiles:
        content = profile.read_text(encoding="utf-8")
        assert "## Prerequisites" in content, profile
        assert "## Behavior" in content, profile
        assert "## Validation" in content, profile


def test_grouped_provider_profiles_have_individual_contracts() -> None:
    grouped = {
        "skills/maintaining-agent-docs/references/provider-shims.md": 4,
        "skills/starting-new-project/references/assistant-adapters.md": 4,
    }
    for path, profile_count in grouped.items():
        content = _text(path)
        assert content.count("### Prerequisites") == profile_count
        assert content.count("### Behavior") == profile_count
        assert content.count("### Validation") == profile_count


def test_project_start_has_two_boundaries_and_four_host_profiles() -> None:
    skill = _text("skills/starting-new-project/SKILL.md")
    assert "Phase A: discover, research, and recommend" in skill
    assert "Phase B: scaffold after approval" in skill
    assert "Ask exactly\n   one targeted question per turn" in skill
    assert "Create these exact files?" in skill
    assert "scripts/verify" in skill
    for name in ("github", "gitlab", "local-only", "no-ci"):
        profile = _text(f"skills/starting-new-project/references/profiles/{name}.md")
        assert "## Prerequisites" in profile
        assert "## Validation" in profile


def test_volatile_fact_rows_have_source_date_and_applicability() -> None:
    ledger = _text("skills/starting-new-project/references/volatile-facts.md")
    rows = [line for line in ledger.splitlines() if line.startswith("| ") and "https://" in line]
    assert len(rows) >= 5
    for row in rows:
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert len(columns) == 4
        assert columns[1].startswith("https://")
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", columns[2])
        assert columns[3]


def test_flow_count_scales_with_complexity_and_hard_stop_remains() -> None:
    skill = _text("skills/analyzing-workflow-patterns/SKILL.md")
    assert "three flows for a bounded change" in skill
    assert "four for a cross-cutting change" in skill
    assert "five for a high-risk" in skill
    assert "stop" in skill.casefold()
    assert "separately approves" in skill


def test_scoring_weights_and_direction_are_consistent() -> None:
    scoring = _text("skills/analyzing-workflow-patterns/references/scoring.md")
    weights = [float(value) for value in re.findall(r"\| (0\.(?:25|20|15|10)) \|", scoring)]
    assert sum(weights[:6]) == 1.0
    assert "higher value is better" in scoring
    assert "efficiency = 10 - cost" in scoring
    values = {
        "repository_fit": 8,
        "delivery_confidence": 7,
        "maintainability": 6,
        "reversibility": 9,
        "safety": 8,
        "efficiency": 7,
    }
    score = (
        values["repository_fit"] * 0.25
        + values["delivery_confidence"] * 0.20
        + values["maintainability"] * 0.15
        + values["reversibility"] * 0.15
        + values["safety"] * 0.15
        + values["efficiency"] * 0.10
    )
    assert round(score, 2) == 7.55


def test_legacy_analyzer_profile_preserves_owner_authored_contract() -> None:
    profile = _text("skills/analyzing-workflow-patterns/references/profiles/legacy-five-flow.md")
    assert all(f"| {phase} |" in profile for phase in range(11))
    for variant in ("LIGHTWEIGHT", "STANDARD", "STRICT", "AGENTIC", "GITHUB_NATIVE"):
        assert variant in profile
    assert "Hard stop before" in profile
