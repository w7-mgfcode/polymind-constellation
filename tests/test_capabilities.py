from __future__ import annotations

from pathlib import Path

import pytest

from polymind.capabilities import normalize_capabilities, normalize_capability
from polymind.model import (
    AtomicCapability,
    Overlay,
    PermissionMode,
    Projection,
    SkillManifest,
    SkillMetadata,
    SkillPackage,
)


def test_compound_capability_expands_to_atomic_actions() -> None:
    capability = normalize_capability("filesystem")
    assert capability.actions == {
        AtomicCapability.FILESYSTEM_READ,
        AtomicCapability.FILESYSTEM_WRITE,
    }


@pytest.mark.parametrize("declaration", ["filesystem.delete", "network.any", "custom"])
def test_unknown_capability_fails_closed(declaration: str) -> None:
    with pytest.raises(ValueError, match="unknown capability"):
        normalize_capability(declaration)


def test_normalization_is_deterministic_and_rejects_duplicates() -> None:
    first = normalize_capabilities(["network.read", "filesystem.read"])
    second = normalize_capabilities(["filesystem.read", "network.read"])
    assert first == second
    with pytest.raises(ValueError, match="duplicate capability"):
        normalize_capabilities(["filesystem.read", "filesystem.read"])


def test_overlay_can_narrow_but_not_reference_undeclared_actions(tmp_path: Path) -> None:
    capabilities = normalize_capabilities(["filesystem"])
    manifest = SkillManifest("1", "original:test", "Proprietary", capabilities, True)
    package = SkillPackage(
        tmp_path,
        tmp_path / "SKILL.md",
        SkillMetadata("test", "test", "Proprietary", None, {}),
        manifest,
    )
    overlay = Overlay(
        "claude",
        disabled_actions=frozenset({AtomicCapability.FILESYSTEM_WRITE}),
        permission_modes={AtomicCapability.FILESYSTEM_READ: PermissionMode.ASK},
    )
    effective = overlay.effective_actions(manifest.actions)
    assert effective == {AtomicCapability.FILESYSTEM_READ}
    Projection("claude", package, tmp_path / "projection", effective).assert_narrower_than_source()

    invalid = Overlay("claude", disabled_actions=frozenset({AtomicCapability.NETWORK_WRITE}))
    with pytest.raises(ValueError, match="undeclared actions"):
        invalid.effective_actions(manifest.actions)


def test_projection_rejects_broadened_action_set(tmp_path: Path) -> None:
    manifest = SkillManifest(
        "1",
        "original:test",
        "Proprietary",
        normalize_capabilities(["filesystem.read"]),
        False,
    )
    package = SkillPackage(
        tmp_path,
        tmp_path / "SKILL.md",
        SkillMetadata("test", "test", "Proprietary", None, {}),
        manifest,
    )
    projection = Projection(
        "claude",
        package,
        tmp_path / "projection",
        frozenset({AtomicCapability.FILESYSTEM_READ, AtomicCapability.NETWORK_READ}),
    )
    with pytest.raises(ValueError, match="broadens"):
        projection.assert_narrower_than_source()
