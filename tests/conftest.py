from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def make_skill(tmp_path: Path) -> Callable[..., Path]:
    skills_root = tmp_path / "skills"
    skills_root.mkdir()

    def factory(
        directory: str = "example-skill",
        *,
        name: str | None = None,
        description: str = (
            "Inspect a canonical package when validation is requested; "
            "do not generate provider projections."
        ),
        metadata: str = (
            '  polymind.version: "1.0.0"\n'
            '  polymind.tags: "validation,test"\n'
            '  polymind.risk: "read-only"'
        ),
        extra_frontmatter: str = "",
        body: str = "# Example\n\nInspect the package.\n",
        actions: str = '"filesystem.read"',
        manifest_extra: str = "",
    ) -> Path:
        package = skills_root / directory
        package.mkdir()
        skill_name = name or directory
        package.joinpath("SKILL.md").write_text(
            "---\n"
            f"name: {skill_name}\n"
            f"description: >-\n  {description}\n"
            "license: Proprietary\n"
            "compatibility: Requires repository read access.\n"
            "metadata:\n"
            f"{metadata}\n"
            f"{extra_frontmatter}"
            "---\n\n"
            f"{body}",
            encoding="utf-8",
        )
        package.joinpath("skill.toml").write_text(
            'schema_version = "1"\n'
            "approval_required_for_mutation = false\n"
            "dependencies = []\n\n"
            "[provenance]\n"
            'source = "original:test"\n'
            'license = "Proprietary"\n\n'
            "[capabilities]\n"
            f"actions = [{actions}]\n"
            f"{manifest_extra}",
            encoding="utf-8",
        )
        return package

    return factory
