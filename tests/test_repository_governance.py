from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from jsonschema import Draft7Validator

from polymind.validation import validate_repository

ROOT = Path(__file__).parents[1]
SCHEMA_ROOT = ROOT / ".github/schemas"

# Pinned SHA-256 digests of vendored upstream artifacts. These intentionally
# fail closed: any change to the bytes they cover must be a deliberate refresh,
# not an accidental edit. To update one after a reviewed upstream/license change,
# recompute with `sha256sum <file>` (or `_sha256(<file>)` below) and paste the
# new hex digest here in the same commit as the file change.
#   - SCHEMA_DIGESTS: the vendored SchemaStore issue-form/config JSON schemas.
#   - LICENSE_DIGEST: the repository LICENSE text (Apache-2.0).
SCHEMA_DIGESTS = {
    "github-issue-forms.schema.json": (
        "c2722dbf00334ce4fdeffa960b8c9047caf4f1cbb8f3809663f4d604b1d3ae76"
    ),
    "github-issue-config.schema.json": (
        "899e718f4b8c965413b07ec63d8f089792a10c42409270db560b9a7ec0224a5a"
    ),
}
LICENSE_DIGEST = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


def _sha256(path: Path) -> str:
    """Hex SHA-256 of a file; use to recompute a pinned digest above on refresh."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    loaded: Any = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _issue_template_paths() -> list[Path]:
    """All issue-template files (.yml and .yaml), deterministically sorted.

    Fails closed: a missing or empty ISSUE_TEMPLATE directory raises here so the
    parametrized test cannot pass silently by collecting zero cases.
    """
    directory = ROOT / ".github/ISSUE_TEMPLATE"
    paths = sorted(
        (path for path in directory.glob("*") if path.suffix in {".yml", ".yaml"}),
        key=lambda path: path.name,
    )
    if not paths:
        raise AssertionError(f"no issue templates found under {directory}")
    return paths


@pytest.mark.parametrize(("filename", "expected"), SCHEMA_DIGESTS.items())
def test_vendored_schema_digest_and_metaschema(filename: str, expected: str) -> None:
    path = SCHEMA_ROOT / filename
    assert _sha256(path) == expected
    Draft7Validator.check_schema(_load_json(path))


@pytest.mark.parametrize("path", _issue_template_paths(), ids=lambda path: path.name)
def test_issue_templates_match_pinned_schemas(path: Path) -> None:
    schema_name = (
        "github-issue-config.schema.json"
        if path.stem == "config"
        else "github-issue-forms.schema.json"
    )
    validator = Draft7Validator(_load_json(SCHEMA_ROOT / schema_name))
    errors = sorted(validator.iter_errors(_load_yaml(path)), key=lambda error: list(error.path))
    assert not errors, "\n".join(
        f"{path}:{'/'.join(str(item) for item in error.path)}: {error.message}" for error in errors
    )


def test_project_license_metadata_is_apache_2() -> None:
    license_path = ROOT / "LICENSE"
    # LICENSE_DIGEST pins the canonical Apache-2.0 text from
    # https://www.apache.org/licenses/LICENSE-2.0.txt
    assert _sha256(license_path) == LICENSE_DIGEST

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE"]

    report = validate_repository(ROOT / "skills")
    assert report.valid
    assert {package.metadata.license for package in report.packages} == {"Apache-2.0"}
    assert {package.manifest.license for package in report.packages} == {"Apache-2.0"}
