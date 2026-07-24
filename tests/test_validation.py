from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from polymind.model import DiagnosticCategory, Severity
from polymind.validation import diagnostic_codes, validate_repository

SkillFactory = Callable[..., Path]


def test_repository_fixture_skill_is_valid() -> None:
    root = Path(__file__).parents[1]
    report = validate_repository(root / "tests" / "fixtures" / "valid")
    assert report.valid
    assert [package.metadata.name for package in report.packages] == ["inspecting-skill-packages"]


def test_checked_in_invalid_fixture_stays_invalid() -> None:
    root = Path(__file__).parents[1]
    report = validate_repository(root / "tests" / "fixtures" / "invalid")
    assert not report.valid
    assert diagnostic_codes(report) >= {"UNKNOWN_TOP_LEVEL_FIELD"}


def test_folded_description_is_accepted(make_skill: SkillFactory) -> None:
    package = make_skill()
    report = validate_repository(package.parent)
    assert report.valid
    assert report.packages[0].metadata.description.startswith("Inspect a canonical")


def test_malformed_yaml_is_a_spec_error(make_skill: SkillFactory) -> None:
    package = make_skill()
    package.joinpath("SKILL.md").write_text(
        "---\nname: [broken\ndescription: broken\n---\nBody\n", encoding="utf-8"
    )
    report = validate_repository(package.parent)
    assert "YAML_INVALID" in diagnostic_codes(report)
    assert not report.valid


@pytest.mark.parametrize("field", ["version", "tags"])
def test_unknown_top_level_portability_fields_are_rejected(
    make_skill: SkillFactory, field: str
) -> None:
    package = make_skill(extra_frontmatter=f'{field}: "not-portable"\n')
    report = validate_repository(package.parent)
    assert "UNKNOWN_TOP_LEVEL_FIELD" in diagnostic_codes(report)
    assert any(item.category is DiagnosticCategory.SPEC for item in report.diagnostics)


def test_non_string_metadata_value_is_rejected(make_skill: SkillFactory) -> None:
    package = make_skill(
        metadata=(
            "  polymind.version: 1\n"
            '  polymind.tags: "validation,test"\n'
            '  polymind.risk: "read-only"'
        )
    )
    report = validate_repository(package.parent)
    assert "METADATA_VALUE_TYPE" in diagnostic_codes(report)


def test_provider_permission_field_is_policy_error(make_skill: SkillFactory) -> None:
    package = make_skill(extra_frontmatter="allowed-tools: Read, Glob\n")
    report = validate_repository(package.parent)
    matching = [item for item in report.diagnostics if item.code == "PROVIDER_FIELD_FORBIDDEN"]
    assert matching[0].category is DiagnosticCategory.POLICY
    assert matching[0].severity is Severity.ERROR


def test_broken_reference_is_reported(make_skill: SkillFactory) -> None:
    package = make_skill(body="# Example\n\nRead [details](references/missing.md).\n")
    report = validate_repository(package.parent)
    assert "REFERENCE_BROKEN" in diagnostic_codes(report)


def test_reference_traversal_is_security_error(make_skill: SkillFactory) -> None:
    package = make_skill(body="# Example\n\nRead [outside](../../outside.md).\n")
    report = validate_repository(package.parent)
    matching = [item for item in report.diagnostics if item.code == "REFERENCE_ESCAPE"]
    assert matching[0].category is DiagnosticCategory.SECURITY


def test_symlinked_resource_escape_is_security_error(make_skill: SkillFactory) -> None:
    package = make_skill(body="# Example\n\nRead [outside](references/outside.md).\n")
    outside = package.parent.parent / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    references = package / "references"
    references.mkdir()
    try:
        references.joinpath("outside.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    report = validate_repository(package.parent)
    assert "REFERENCE_ESCAPE" in diagnostic_codes(report)
    assert "RESOURCE_SYMLINK" in diagnostic_codes(report)


def test_symlinked_internal_resource_is_security_error(make_skill: SkillFactory) -> None:
    package = make_skill(body="# Example\n\nRead [details](details-link.md).\n")
    details = package / "details.md"
    details.write_text("details\n", encoding="utf-8")
    try:
        package.joinpath("details-link.md").symlink_to(details)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    report = validate_repository(package.parent)

    assert not report.valid
    assert "RESOURCE_SYMLINK" in diagnostic_codes(report)


def test_symlinked_skills_root_is_security_error(tmp_path: Path) -> None:
    source = Path(__file__).parents[1] / "tests/fixtures/valid"
    skills_root = tmp_path / "skills"
    try:
        skills_root.symlink_to(source, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    report = validate_repository(skills_root)

    assert not report.valid
    assert not report.packages
    assert "SKILLS_ROOT_SYMLINK" in diagnostic_codes(report)


def test_symlinked_package_directory_is_security_error(
    make_skill: SkillFactory, tmp_path: Path
) -> None:
    package = make_skill()
    external_root = tmp_path / "external"
    external_root.mkdir()
    external = external_root / package.name
    package.rename(external)
    try:
        package.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    report = validate_repository(package.parent)

    assert not report.valid
    assert not report.packages
    assert "PACKAGE_SYMLINK" in diagnostic_codes(report)


def test_duplicate_names_are_rejected(make_skill: SkillFactory) -> None:
    first = make_skill(directory="first", name="same-name")
    second = make_skill(directory="second", name="same-name")
    report = validate_repository(first.parent)
    assert second.parent == first.parent
    assert "DUPLICATE_SKILL_NAME" in diagnostic_codes(report)


def test_unknown_capability_is_security_error(make_skill: SkillFactory) -> None:
    package = make_skill(actions='"filesystem.superuser"')
    report = validate_repository(package.parent)
    matching = [item for item in report.diagnostics if item.code == "CAPABILITY_UNKNOWN"]
    assert matching[0].category is DiagnosticCategory.SECURITY
    assert not report.valid


def test_unresolved_placeholder_is_rejected(make_skill: SkillFactory) -> None:
    package = make_skill(body="# Example\n\n" + "TO" + "DO: replace this text.\n")
    report = validate_repository(package.parent)
    assert "PLACEHOLDER_UNRESOLVED" in diagnostic_codes(report)


def test_missing_and_incomplete_script_declaration_is_rejected(
    make_skill: SkillFactory,
) -> None:
    package = make_skill(
        manifest_extra=('\n[[scripts]]\npath = "scripts/not-there.py"\nruntime = "python>=3.11"\n')
    )
    report = validate_repository(package.parent)
    codes = diagnostic_codes(report)
    assert "SCRIPT_DECLARATION_INCOMPLETE" in codes
    assert "SCRIPT_MISSING" in codes


def test_json_diagnostics_are_stable_and_machine_readable(make_skill: SkillFactory) -> None:
    package = make_skill(body="# Example\n\nRead [missing](missing.md).\n")
    first = validate_repository(package.parent).as_dict()
    second = validate_repository(package.parent).as_dict()
    assert first == second
    assert first["valid"] is False
    assert isinstance(first["diagnostics"], list)
