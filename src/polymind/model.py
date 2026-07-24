"""Typed domain models for canonical skills and future provider projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class DiagnosticCategory(StrEnum):
    """Validation layers kept separate to avoid false assurance."""

    SPEC = "spec"
    POLICY = "polymind-policy"
    SECURITY = "security"


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    category: DiagnosticCategory
    code: str
    message: str
    path: str
    severity: Severity = Severity.ERROR

    def as_dict(self) -> dict[str, str]:
        return {
            "category": self.category.value,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "severity": self.severity.value,
        }


class AtomicCapability(StrEnum):
    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    SHELL_READONLY = "shell.readonly"
    SHELL_EXECUTE = "shell.execute"
    NETWORK_READ = "network.read"
    NETWORK_WRITE = "network.write"
    BROWSER_READ = "browser.read"
    BROWSER_WRITE = "browser.write"
    SECRET_ACCESS = "secret.access"


class PermissionMode(StrEnum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class Capability:
    declaration: str
    actions: frozenset[AtomicCapability]


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    name: str
    description: str
    license: str | None
    compatibility: str | None
    metadata: dict[str, str]


@dataclass(frozen=True, slots=True)
class SkillManifest:
    schema_version: str
    source: str
    license: str
    capabilities: tuple[Capability, ...]
    approval_required_for_mutation: bool
    scripts: tuple[dict[str, Any], ...] = ()
    dependencies: tuple[str, ...] = ()
    allowed_placeholders: tuple[str, ...] = ()

    @property
    def actions(self) -> frozenset[AtomicCapability]:
        return frozenset(
            action for capability in self.capabilities for action in capability.actions
        )


@dataclass(frozen=True, slots=True)
class SkillPackage:
    root: Path
    skill_md: Path
    metadata: SkillMetadata
    manifest: SkillManifest


@dataclass(frozen=True, slots=True)
class Overlay:
    provider: str
    disabled_actions: frozenset[AtomicCapability] = frozenset()
    permission_modes: dict[AtomicCapability, PermissionMode] = field(default_factory=dict)

    def effective_actions(
        self, declared_actions: frozenset[AtomicCapability]
    ) -> frozenset[AtomicCapability]:
        if not self.disabled_actions <= declared_actions:
            unknown = sorted(action.value for action in self.disabled_actions - declared_actions)
            raise ValueError(f"overlay references undeclared actions: {', '.join(unknown)}")
        if not set(self.permission_modes) <= declared_actions:
            unknown = sorted(
                action.value for action in set(self.permission_modes) - declared_actions
            )
            raise ValueError(f"overlay references undeclared actions: {', '.join(unknown)}")
        return frozenset(
            action
            for action in declared_actions - self.disabled_actions
            if self.permission_modes.get(action, PermissionMode.ALLOW) is not PermissionMode.DENY
        )


@dataclass(frozen=True, slots=True)
class Projection:
    provider: str
    source: SkillPackage
    destination: Path
    effective_actions: frozenset[AtomicCapability]

    def assert_narrower_than_source(self) -> None:
        if not self.effective_actions <= self.source.manifest.actions:
            raise ValueError("projection broadens canonical capabilities")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    packages: tuple[SkillPackage, ...]
    diagnostics: tuple[Diagnostic, ...]

    @property
    def valid(self) -> bool:
        return not any(item.severity is Severity.ERROR for item in self.diagnostics)

    def as_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "package_count": len(self.packages),
            "diagnostics": [item.as_dict() for item in self.diagnostics],
        }
