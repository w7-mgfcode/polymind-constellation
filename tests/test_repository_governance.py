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
SCHEMA_DIGESTS = {
    "github-issue-forms.schema.json": (
        "c2722dbf00334ce4fdeffa960b8c9047caf4f1cbb8f3809663f4d604b1d3ae76"
    ),
    "github-issue-config.schema.json": (
        "899e718f4b8c965413b07ec63d8f089792a10c42409270db560b9a7ec0224a5a"
    ),
}


def _load_json(path: Path) -> dict[str, Any]:
    loaded: Any = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("filename", "expected"), SCHEMA_DIGESTS.items())
def test_vendored_schema_digest_and_metaschema(filename: str, expected: str) -> None:
    path = SCHEMA_ROOT / filename
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    Draft7Validator.check_schema(_load_json(path))


@pytest.mark.parametrize(
    "path",
    sorted((ROOT / ".github/ISSUE_TEMPLATE").glob("*.yml")),
    ids=lambda path: path.name,
)
def test_issue_templates_match_pinned_schemas(path: Path) -> None:
    schema_name = (
        "github-issue-config.schema.json"
        if path.name == "config.yml"
        else "github-issue-forms.schema.json"
    )
    validator = Draft7Validator(_load_json(SCHEMA_ROOT / schema_name))
    errors = sorted(validator.iter_errors(_load_yaml(path)), key=lambda error: list(error.path))
    assert not errors, "\n".join(
        f"{path}:{'/'.join(str(item) for item in error.path)}: {error.message}" for error in errors
    )


def test_project_license_metadata_is_apache_2() -> None:
    license_path = ROOT / "LICENSE"
    assert hashlib.sha256(license_path.read_bytes()).hexdigest() == (
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
    )

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE"]

    report = validate_repository(ROOT / "skills")
    assert report.valid
    assert {package.metadata.license for package in report.packages} == {"Apache-2.0"}
    assert {package.manifest.license for package in report.packages} == {"Apache-2.0"}
