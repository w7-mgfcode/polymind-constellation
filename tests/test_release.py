from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

from polymind import __version__

ROOT = Path(__file__).parents[1]


def test_framework_version_is_consistent() -> None:
    project = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads(ROOT.joinpath("uv.lock").read_text(encoding="utf-8"))
    root_package = next(
        package for package in lock["package"] if package["name"] == "polymind-constellation"
    )

    assert project["project"]["version"] == __version__ == "0.8.1"
    assert root_package["version"] == __version__


def test_generated_lock_records_the_framework_version() -> None:
    lock = ROOT.joinpath("dist/repo/projection.lock.json").read_text(encoding="utf-8")

    assert f'"generated_by": "polymind-constellation/{__version__}"' in lock


def test_compatibility_manifest_has_dated_distinct_support_states() -> None:
    manifest = tomllib.loads(ROOT.joinpath("adapters/providers.toml").read_text(encoding="utf-8"))

    assert manifest["freshness_days"] == 90
    assert {provider["support_status"] for provider in manifest["providers"]} == {
        "tested",
        "static-only",
        "unsupported",
    }
    assert all(provider["evidence_date"] == "2026-07-22" for provider in manifest["providers"])
    assert all(provider["evidence_scope"] for provider in manifest["providers"])


def test_support_matrix_names_every_manifest_provider_and_state() -> None:
    manifest = tomllib.loads(ROOT.joinpath("adapters/providers.toml").read_text(encoding="utf-8"))
    documentation = ROOT.joinpath("docs/provider-compatibility.md").read_text(encoding="utf-8")

    for provider in manifest["providers"]:
        assert f"| {provider['name']} |" in documentation
        assert f"`{provider['support_status']}`" in documentation


def test_wheel_configuration_bundles_the_generated_projection() -> None:
    project = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    wheel = project["tool"]["hatch"]["build"]["targets"]["wheel"]

    assert wheel["force-include"]["dist/repo"] == "polymind/_projection"


def test_sdist_configuration_bundles_the_generated_projection() -> None:
    project = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    sdist = project["tool"]["hatch"]["build"]["targets"]["sdist"]

    assert sdist["force-include"]["dist/repo"] == "dist/repo"


def test_workflows_pin_every_third_party_action_to_a_commit() -> None:
    for workflow in ROOT.joinpath(".github/workflows").glob("*.yml"):
        content = workflow.read_text(encoding="utf-8")
        references = re.findall(r"^\s*uses:\s*([^\s#]+)", content, re.MULTILINE)
        assert references
        assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in references)


def test_release_workflow_uses_trusted_publishing_and_signed_provenance() -> None:
    path = ROOT / ".github/workflows/release.yml"
    content = path.read_text(encoding="utf-8")
    workflow = yaml.load(content, Loader=yaml.BaseLoader)
    jobs = workflow["jobs"]

    assert workflow["on"]["push"]["tags"] == ["v*.*.*"]
    assert jobs["build"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
        "attestations": "write",
        "artifact-metadata": "write",
    }
    assert jobs["pypi-publish"]["environment"]["name"] == "pypi"
    assert jobs["pypi-publish"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }
    assert "pypa/gh-action-pypi-publish@" in content
    assert "actions/attest@" in content
    assert "scripts/verify --release" in content
    assert "gitsign_0.16.1_linux_amd64" in content
    assert "4a29a1f4b9add1f0f6d9a3e9e6ba0cffa121b971be82d62bb1496d7d1d877b0a" in content
    assert "vars.RELEASE_COMMIT_IDENTITY" in content
    assert "vars.RELEASE_COMMIT_OIDC_ISSUER" in content
    assert "password:" not in content
    assert "twine upload" not in content


def test_github_release_waits_for_successful_pypi_publication() -> None:
    content = ROOT.joinpath(".github/workflows/release.yml").read_text(encoding="utf-8")
    workflow = yaml.load(content, Loader=yaml.BaseLoader)

    assert workflow["jobs"]["github-release"]["needs"] == ["build", "pypi-publish"]
