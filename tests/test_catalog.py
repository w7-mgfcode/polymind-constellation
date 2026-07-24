from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from polymind.catalog import (
    MAX_RESOURCE_BYTES,
    CatalogError,
    activate_skill,
    catalog_document,
    read_resource,
    render_activation,
    render_catalog,
    render_resource_json,
)
from polymind.host_contract import map_host_permission
from polymind.model import AtomicCapability, PermissionMode

SkillFactory = Callable[..., Path]
ROOT = Path(__file__).parents[1]


def test_catalog_is_compact_stable_and_available_in_three_formats() -> None:
    first: Any = catalog_document(ROOT / "skills")
    second = catalog_document(ROOT / "skills")
    assert first == second
    assert first["operation"] == "catalog"
    assert first["execution"] == "none"
    assert [entry["name"] for entry in first["skills"]] == [
        "analyzing-workflow-patterns",
        "maintaining-agent-docs",
        "starting-new-project",
    ]
    serialized = render_catalog(first, "json")
    assert '"skill_md"' not in serialized
    assert "# Core protocol" not in serialized

    xml_output = render_catalog(first, "xml")
    root = ET.fromstring(xml_output)
    assert root.tag == "skill-catalog"
    assert root.attrib["execution"] == "none"
    assert len(root.findall("skill")) == 3

    markdown = render_catalog(first, "markdown")
    assert "| Name | Version | Description | Capabilities | Risk |" in markdown
    assert "does not activate skills or execute code" in markdown


def test_activation_returns_one_skill_body_manifest_and_no_grants() -> None:
    document: Any = activate_skill(ROOT / "skills", "analyzing-workflow-patterns")
    assert document["operation"] == "activate"
    assert document["execution"] == "none"
    assert document["permissions_granted"] == []
    assert document["base_directory"] == (ROOT / "skills/analyzing-workflow-patterns").as_posix()
    assert "# Analyzing Workflow Patterns" in document["skill_md"]
    paths = {entry["path"] for entry in document["resources"]}
    assert "references/scoring.md" in paths
    assert "SKILL.md" not in paths
    assert len(document["package_digest"]) == 64
    requirements = document["permission_requirements"]
    assert all(requirement["mode"] in {"ask", "deny"} for requirement in requirements)

    markdown = render_activation(document, "markdown")
    assert "Execution: none; no permissions granted" in markdown
    assert "Read one resource at a time" in markdown


def test_resource_reads_exactly_one_manifested_file() -> None:
    record, content = read_resource(
        ROOT / "skills", "analyzing-workflow-patterns", "references/scoring.md"
    )
    assert record["path"] == "references/scoring.md"
    assert b"Normalized scoring model" in content
    rendered = json.loads(render_resource_json(record, content))
    assert rendered["operation"] == "resource"
    assert rendered["execution"] == "none"
    assert rendered["encoding"] == "utf-8"
    assert "Legacy five-flow profile" not in rendered["content"]


@pytest.mark.parametrize(
    "path",
    [
        "../SKILL.md",
        "/etc/passwd",
        "references/../SKILL.md",
        "references\\scoring.md",
        "references//scoring.md",
        "SKILL.md",
    ],
)
def test_resource_path_attacks_fail_closed(path: str) -> None:
    with pytest.raises(CatalogError):
        read_resource(ROOT / "skills", "analyzing-workflow-patterns", path)


def test_activation_rejects_symlinks_even_when_they_currently_resolve_inside(
    make_skill: SkillFactory,
) -> None:
    package = make_skill()
    reference = package / "references/real.md"
    reference.parent.mkdir()
    reference.write_text("safe reference\n", encoding="utf-8")
    try:
        reference.with_name("alias.md").symlink_to(reference.name)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    with pytest.raises(CatalogError, match="RESOURCE_SYMLINK"):
        activate_skill(package.parent, package.name)


def test_resource_output_limit_is_bounded(make_skill: SkillFactory) -> None:
    package = make_skill()
    asset = package / "assets/payload.bin"
    asset.parent.mkdir()
    asset.write_bytes(b"x" * 64)
    with pytest.raises(CatalogError, match="exceeds output limit"):
        read_resource(package.parent, package.name, "assets/payload.bin", max_bytes=32)
    with pytest.raises(CatalogError, match="max_bytes"):
        read_resource(
            package.parent,
            package.name,
            "assets/payload.bin",
            max_bytes=MAX_RESOURCE_BYTES + 1,
        )


def test_declared_scripts_are_data_and_never_execute(make_skill: SkillFactory) -> None:
    script_declaration = """
[[scripts]]
path = "scripts/write-marker.py"
runtime = "python>=3.11"
dependencies = []
inputs = "None"
outputs = "A marker if incorrectly executed"
side_effects = "Writes a marker"
dry_run = false
"""
    package = make_skill(manifest_extra=script_declaration)
    script = package / "scripts/write-marker.py"
    script.parent.mkdir()
    marker = package / "executed.txt"
    script.write_text("from pathlib import Path\nPath('executed.txt').write_text('bad')\n")

    document: Any = activate_skill(package.parent, package.name)
    assert not marker.exists()
    script_record = next(
        entry for entry in document["resources"] if entry["path"] == "scripts/write-marker.py"
    )
    assert script_record["kind"] == "scripts"
    read_resource(package.parent, package.name, "scripts/write-marker.py")
    assert not marker.exists()


def test_permission_mapping_covers_all_atomic_actions_and_denies_unknowns() -> None:
    mapped = {action.value: map_host_permission(action.value) for action in AtomicCapability}
    assert set(mapped) == {action.value for action in AtomicCapability}
    assert mapped["filesystem.read"].mode is PermissionMode.ASK
    assert mapped["shell.readonly"].mode is PermissionMode.ASK
    assert mapped["network.write"].mode is PermissionMode.DENY
    assert map_host_permission("host.superuser").mode is PermissionMode.DENY


def test_reference_harness_lists_activates_and_rejects_execution() -> None:
    harness = ROOT / "examples/local_harness.py"
    source = harness.read_text(encoding="utf-8")
    assert "import openai" not in source
    assert "import anthropic" not in source
    assert "import ollama" not in source
    listed = subprocess.run(  # noqa: S603
        [sys.executable, str(harness), "list"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert listed.returncode == 0, listed.stderr
    assert len(json.loads(listed.stdout)["skills"]) == 3

    activated = subprocess.run(  # noqa: S603
        [sys.executable, str(harness), "activate", "maintaining-agent-docs"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert activated.returncode == 0, activated.stderr
    assert json.loads(activated.stdout)["execution"] == "none"

    rejected = subprocess.run(  # noqa: S603
        [sys.executable, str(harness), "execute", "maintaining-agent-docs"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode == 2
    assert "invalid choice" in rejected.stderr


def test_opencode_example_is_local_credential_free_and_fail_closed() -> None:
    path = ROOT / "examples/opencode-local/opencode.json"
    text = path.read_text(encoding="utf-8")
    config = json.loads(text)
    options = config["provider"]["lmstudio"]["options"]
    assert options == {"baseURL": "http://127.0.0.1:1234/v1"}
    assert "apiKey" not in text
    assert "/home/" not in text and "\\Users\\" not in text
    assert config["permission"]["skill"]["*"] == "ask"
    for permission in ("edit", "bash", "webfetch", "websearch", "external_directory"):
        assert config["permission"][permission] == "deny"


def test_opencode_discovers_projected_skills_with_opt_in_local_model(tmp_path: Path) -> None:
    if os.environ.get("POLYMIND_RUN_LOCAL_PROVIDER_TESTS") != "1":
        pytest.skip("set POLYMIND_RUN_LOCAL_PROVIDER_TESTS=1 with OpenCode and LM Studio running")
    executable = shutil.which("opencode")
    if executable is None:
        pytest.skip("OpenCode is not installed")
    shutil.copytree(ROOT / "dist/repo", tmp_path / "repo")
    repository = tmp_path / "repo"
    shutil.copy2(repository / "opencode.local.example.json", repository / "opencode.json")
    prompt = (
        "Use the native skill tool. List the exact available skill names only, "
        "one per line, without activating a skill."
    )
    completed = subprocess.run(  # noqa: S603
        [executable, "run", "--model", "lmstudio/local-model", prompt],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    for name in (
        "analyzing-workflow-patterns",
        "maintaining-agent-docs",
        "starting-new-project",
    ):
        assert name in completed.stdout
