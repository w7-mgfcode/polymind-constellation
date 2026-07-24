"""Deterministic, offline validation for canonical Agent Skills packages."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml

from polymind.capabilities import normalize_capabilities
from polymind.discovery import discover_skill_directories
from polymind.model import (
    Capability,
    Diagnostic,
    DiagnosticCategory,
    Severity,
    SkillManifest,
    SkillMetadata,
    SkillPackage,
    ValidationReport,
)

_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FRONTMATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_UNRESOLVED_MARKER_PATTERN = re.compile(r"\b(?:TODO|FIXME|TBD|CHANGEME)\b")
_TEMPLATE_VARIABLE_PATTERN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
_ALLOWED_TOP_LEVEL_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
_FORBIDDEN_CANONICAL_FIELDS = {"allowed-tools"}
_REQUIRED_POLYMIND_METADATA = {
    "polymind.version",
    "polymind.tags",
    "polymind.risk",
}
_SCRIPT_FIELDS = {
    "path",
    "runtime",
    "dependencies",
    "inputs",
    "outputs",
    "side_effects",
    "dry_run",
}


def _diagnostic(
    category: DiagnosticCategory,
    code: str,
    message: str,
    path: Path,
    severity: Severity = Severity.ERROR,
) -> Diagnostic:
    return Diagnostic(category, code, message, path.as_posix(), severity)


def _is_contained(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return (
            None,
            "",
            [
                _diagnostic(
                    DiagnosticCategory.SPEC,
                    "SKILL_READ_FAILED",
                    f"cannot read SKILL.md as UTF-8: {error}",
                    path,
                )
            ],
        )

    match = _FRONTMATTER_PATTERN.match(text)
    if match is None:
        return (
            None,
            text,
            [
                _diagnostic(
                    DiagnosticCategory.SPEC,
                    "FRONTMATTER_MISSING",
                    "SKILL.md must begin with YAML frontmatter delimited by ---",
                    path,
                )
            ],
        )

    try:
        loaded: Any = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "YAML_INVALID",
                f"invalid YAML frontmatter: {error}",
                path,
            )
        )
        return None, text[match.end() :], diagnostics
    if not isinstance(loaded, dict) or not all(isinstance(key, str) for key in loaded):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "FRONTMATTER_NOT_MAPPING",
                "frontmatter must be a mapping with string keys",
                path,
            )
        )
        return None, text[match.end() :], diagnostics
    return dict(loaded), text[match.end() :], diagnostics


def _validate_metadata(
    raw: Mapping[str, Any], package_root: Path, *, canonical: bool
) -> tuple[SkillMetadata | None, list[Diagnostic]]:
    path = package_root / "SKILL.md"
    diagnostics: list[Diagnostic] = []
    unknown = sorted(set(raw) - _ALLOWED_TOP_LEVEL_FIELDS)
    for field in unknown:
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "UNKNOWN_TOP_LEVEL_FIELD",
                f"unknown top-level frontmatter field: {field}",
                path,
            )
        )
    if canonical:
        for field in sorted(set(raw) & _FORBIDDEN_CANONICAL_FIELDS):
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.POLICY,
                    "PROVIDER_FIELD_FORBIDDEN",
                    f"provider-specific field is forbidden in canonical SKILL.md: {field}",
                    path,
                )
            )

    name = raw.get("name")
    description = raw.get("description")
    if not isinstance(name, str):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "NAME_REQUIRED",
                "name is required and must be a string",
                path,
            )
        )
    elif not 1 <= len(name) <= 64 or _NAME_PATTERN.fullmatch(name) is None:
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "NAME_INVALID",
                "name must be 1-64 lowercase letters, digits, or single hyphens",
                path,
            )
        )
    elif name != package_root.name:
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "NAME_DIRECTORY_MISMATCH",
                f"name {name!r} must equal directory name {package_root.name!r}",
                path,
            )
        )

    if not isinstance(description, str):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "DESCRIPTION_REQUIRED",
                "description is required and must be a string",
                path,
            )
        )
    elif not 1 <= len(description) <= 1024:
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "DESCRIPTION_LENGTH",
                "description must contain 1-1024 characters",
                path,
            )
        )
    elif not re.search(
        r"\b(?:do not|not for|avoid|instead|never|without|before modifying|zero writes?)\b",
        description,
        re.IGNORECASE,
    ):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "NEGATIVE_TRIGGER_MISSING",
                "description should state a negative trigger boundary",
                path,
                Severity.WARNING,
            )
        )

    optional_strings: dict[str, str | None] = {}
    for field in ("license", "compatibility"):
        value = raw.get(field)
        if value is not None and not isinstance(value, str):
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.SPEC,
                    "FIELD_TYPE",
                    f"{field} must be a string when present",
                    path,
                )
            )
            optional_strings[field] = None
        else:
            optional_strings[field] = value

    raw_metadata = raw.get("metadata", {})
    metadata: dict[str, str] = {}
    if not isinstance(raw_metadata, dict):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.SPEC,
                "METADATA_TYPE",
                "metadata must be a mapping of string keys to string values",
                path,
            )
        )
    else:
        for key, value in raw_metadata.items():
            if not isinstance(key, str) or not isinstance(value, str):
                diagnostics.append(
                    _diagnostic(
                        DiagnosticCategory.SPEC,
                        "METADATA_VALUE_TYPE",
                        "metadata keys and values must be strings",
                        path,
                    )
                )
                continue
            metadata[key] = value
        for key in sorted(_REQUIRED_POLYMIND_METADATA - set(metadata)):
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.POLICY,
                    "POLYMIND_METADATA_MISSING",
                    f"required Polymind metadata key is missing: {key}",
                    path,
                )
            )

    if not isinstance(name, str) or not isinstance(description, str):
        return None, diagnostics
    return (
        SkillMetadata(
            name=name,
            description=description,
            license=optional_strings["license"],
            compatibility=optional_strings["compatibility"],
            metadata=metadata,
        ),
        diagnostics,
    )


def _load_manifest(path: Path) -> tuple[SkillManifest | None, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    if not path.is_file():
        return None, [
            _diagnostic(
                DiagnosticCategory.POLICY,
                "MANIFEST_MISSING",
                "canonical package requires skill.toml",
                path,
            )
        ]
    try:
        raw: Any = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        return None, [
            _diagnostic(
                DiagnosticCategory.POLICY,
                "MANIFEST_INVALID",
                f"cannot parse skill.toml: {error}",
                path,
            )
        ]

    if not isinstance(raw, dict):
        return None, [
            _diagnostic(
                DiagnosticCategory.POLICY,
                "MANIFEST_NOT_MAPPING",
                "skill.toml must contain a TOML table",
                path,
            )
        ]

    schema_version = raw.get("schema_version")
    if not isinstance(schema_version, str):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "SCHEMA_VERSION_REQUIRED",
                "skill.toml schema_version must be a string",
                path,
            )
        )

    provenance = raw.get("provenance")
    source = provenance.get("source") if isinstance(provenance, dict) else None
    license_name = provenance.get("license") if isinstance(provenance, dict) else None
    if not isinstance(source, str) or not isinstance(license_name, str):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "PROVENANCE_REQUIRED",
                "skill.toml requires string provenance.source and provenance.license",
                path,
            )
        )

    capability_table = raw.get("capabilities", {})
    declarations = capability_table.get("actions") if isinstance(capability_table, dict) else None
    capabilities: tuple[Capability, ...] = ()
    if not isinstance(declarations, list) or not all(
        isinstance(item, str) for item in declarations
    ):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "CAPABILITIES_TYPE",
                "capabilities.actions must be an array of strings",
                path,
            )
        )
    else:
        try:
            capabilities = normalize_capabilities(declarations)
        except ValueError as error:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.SECURITY,
                    "CAPABILITY_UNKNOWN",
                    str(error),
                    path,
                )
            )

    approval = raw.get("approval_required_for_mutation")
    if not isinstance(approval, bool):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "APPROVAL_FLAG_REQUIRED",
                "approval_required_for_mutation must be a boolean",
                path,
            )
        )

    raw_scripts = raw.get("scripts", [])
    scripts: tuple[dict[str, Any], ...] = ()
    if not isinstance(raw_scripts, list) or not all(isinstance(item, dict) for item in raw_scripts):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "SCRIPTS_TYPE",
                "scripts must be an array of tables",
                path,
            )
        )
    else:
        scripts = tuple(dict(item) for item in raw_scripts)

    raw_dependencies = raw.get("dependencies", [])
    dependencies: tuple[str, ...] = ()
    if not isinstance(raw_dependencies, list) or not all(
        isinstance(item, str) for item in raw_dependencies
    ):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "DEPENDENCIES_TYPE",
                "dependencies must be an array of strings",
                path,
            )
        )
    else:
        dependencies = tuple(raw_dependencies)

    raw_placeholders = raw.get("allowed_placeholders", [])
    allowed_placeholders: tuple[str, ...] = ()
    if not isinstance(raw_placeholders, list) or not all(
        isinstance(item, str) and re.fullmatch(r"[A-Z][A-Z0-9_]*", item)
        for item in raw_placeholders
    ):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "PLACEHOLDER_ALLOWLIST_TYPE",
                "allowed_placeholders must be an array of uppercase variable names",
                path,
            )
        )
    elif len(raw_placeholders) != len(set(raw_placeholders)):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "PLACEHOLDER_ALLOWLIST_DUPLICATE",
                "allowed_placeholders must not contain duplicates",
                path,
            )
        )
    else:
        allowed_placeholders = tuple(sorted(raw_placeholders))

    if any(item.severity is Severity.ERROR for item in diagnostics):
        return None, diagnostics
    assert isinstance(schema_version, str)
    assert isinstance(source, str)
    assert isinstance(license_name, str)
    assert isinstance(approval, bool)
    return (
        SkillManifest(
            schema_version=schema_version,
            source=source,
            license=license_name,
            capabilities=capabilities,
            approval_required_for_mutation=approval,
            scripts=scripts,
            dependencies=dependencies,
            allowed_placeholders=allowed_placeholders,
        ),
        diagnostics,
    )


def _local_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("#"):
        return None
    return unquote(parsed.path)


def _strip_markdown_code(text: str) -> str:
    without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", without_fences)


def _validate_package_files(
    package_root: Path, body: str, allowed_placeholders: frozenset[str]
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    skill_path = package_root / "SKILL.md"
    line_count = len(skill_path.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "SKILL_LINE_BUDGET",
                f"SKILL.md has {line_count} lines; target is at most 500",
                skill_path,
                Severity.WARNING,
            )
        )
    token_estimate = len(re.findall(r"\w+|[^\w\s]", body))
    if token_estimate > 5000:
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "SKILL_TOKEN_BUDGET",
                f"SKILL.md estimated token count is {token_estimate}; target is at most 5000",
                skill_path,
                Severity.WARNING,
            )
        )
    if not body.strip():
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "SKILL_BODY_EMPTY",
                "SKILL.md must contain instructions after frontmatter",
                skill_path,
            )
        )

    root = package_root.resolve()
    text_suffixes = {
        ".json",
        ".md",
        ".py",
        ".sh",
        ".tmpl",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
    package_paths = sorted(package_root.rglob("*"))
    for resource_path in package_paths:
        if resource_path.is_symlink():
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.SECURITY,
                    "RESOURCE_SYMLINK",
                    "symlinked package resources are forbidden",
                    resource_path,
                )
            )
    text_paths = sorted(
        path
        for path in package_paths
        if not path.is_symlink()
        and path.is_file()
        and (path.suffix in text_suffixes or path.name == "SKILL.md")
    )
    used_placeholders: set[str] = set()
    for resource_path in text_paths:
        if not _is_contained(resource_path, root):
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.SECURITY,
                    "RESOURCE_ESCAPE",
                    "text resource resolves outside the skill package",
                    resource_path,
                )
            )
            continue
        try:
            text = resource_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.POLICY,
                    "RESOURCE_READ_FAILED",
                    f"cannot read text resource: {error}",
                    resource_path,
                )
            )
            continue
        prose_text = _strip_markdown_code(text) if resource_path.suffix == ".md" else text
        if _UNRESOLVED_MARKER_PATTERN.search(prose_text):
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.POLICY,
                    "PLACEHOLDER_UNRESOLVED",
                    "unresolved work marker found in package text",
                    resource_path,
                )
            )
        found_placeholders = set(_TEMPLATE_VARIABLE_PATTERN.findall(text))
        used_placeholders.update(found_placeholders)
        for placeholder in sorted(found_placeholders - allowed_placeholders):
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.POLICY,
                    "PLACEHOLDER_UNDECLARED",
                    f"template variable is not declared in skill.toml: {placeholder}",
                    resource_path,
                )
            )
        if resource_path.suffix != ".md":
            continue
        for raw_target in _MARKDOWN_LINK_PATTERN.findall(prose_text):
            target = _local_link_target(raw_target)
            if not target:
                continue
            candidate = resource_path.parent / target
            if Path(target).is_absolute():
                diagnostics.append(
                    _diagnostic(
                        DiagnosticCategory.SECURITY,
                        "REFERENCE_ABSOLUTE",
                        f"absolute package reference is forbidden: {target}",
                        resource_path,
                    )
                )
                continue
            try:
                candidate.resolve(strict=False).relative_to(root)
            except ValueError:
                diagnostics.append(
                    _diagnostic(
                        DiagnosticCategory.SECURITY,
                        "REFERENCE_ESCAPE",
                        f"reference escapes the skill package: {target}",
                        resource_path,
                    )
                )
                continue
            if not candidate.exists():
                diagnostics.append(
                    _diagnostic(
                        DiagnosticCategory.POLICY,
                        "REFERENCE_BROKEN",
                        f"referenced package resource does not exist: {target}",
                        resource_path,
                    )
                )
    for placeholder in sorted(allowed_placeholders - used_placeholders):
        diagnostics.append(
            _diagnostic(
                DiagnosticCategory.POLICY,
                "PLACEHOLDER_ALLOWLIST_UNUSED",
                f"declared template variable is not used: {placeholder}",
                package_root / "skill.toml",
                Severity.WARNING,
            )
        )
    return diagnostics


def _validate_scripts(package_root: Path, manifest: SkillManifest) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    root = package_root.resolve()
    manifest_path = package_root / "skill.toml"
    for index, script in enumerate(manifest.scripts):
        missing = sorted(_SCRIPT_FIELDS - set(script))
        if missing:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.POLICY,
                    "SCRIPT_DECLARATION_INCOMPLETE",
                    f"scripts[{index}] is missing: {', '.join(missing)}",
                    manifest_path,
                )
            )
        raw_path = script.get("path")
        if not isinstance(raw_path, str):
            continue
        candidate = package_root / raw_path
        if Path(raw_path).is_absolute():
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.SECURITY,
                    "SCRIPT_ABSOLUTE",
                    f"script path must be package-relative: {raw_path}",
                    manifest_path,
                )
            )
            continue
        try:
            candidate.resolve(strict=False).relative_to(root)
        except ValueError:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.SECURITY,
                    "SCRIPT_ESCAPE",
                    f"script path escapes the package: {raw_path}",
                    manifest_path,
                )
            )
            continue
        if not candidate.is_file():
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.POLICY,
                    "SCRIPT_MISSING",
                    f"declared script does not exist: {raw_path}",
                    manifest_path,
                )
            )
    return diagnostics


def validate_skill(
    package_root: Path, *, canonical: bool = True
) -> tuple[SkillPackage | None, list[Diagnostic]]:
    skill_path = package_root / "SKILL.md"
    if not skill_path.is_file():
        return None, [
            _diagnostic(
                DiagnosticCategory.SPEC,
                "SKILL_MD_MISSING",
                "skill package must contain SKILL.md",
                skill_path,
            )
        ]

    manifest_path = package_root / "skill.toml"
    escaped_files = [
        path
        for path in (skill_path, manifest_path)
        if path.exists() and not _is_contained(path, package_root)
    ]
    if escaped_files:
        return None, [
            _diagnostic(
                DiagnosticCategory.SECURITY,
                "PACKAGE_FILE_ESCAPE",
                "canonical package file resolves outside the skill directory",
                path,
            )
            for path in escaped_files
        ]

    raw_metadata, body, diagnostics = _parse_frontmatter(skill_path)
    metadata: SkillMetadata | None = None
    if raw_metadata is not None:
        metadata, metadata_diagnostics = _validate_metadata(
            raw_metadata, package_root, canonical=canonical
        )
        diagnostics.extend(metadata_diagnostics)

    manifest, manifest_diagnostics = _load_manifest(manifest_path)
    diagnostics.extend(manifest_diagnostics)
    allowed_placeholders = (
        frozenset(manifest.allowed_placeholders) if manifest is not None else frozenset()
    )
    diagnostics.extend(_validate_package_files(package_root, body, allowed_placeholders))
    if manifest is not None:
        diagnostics.extend(_validate_scripts(package_root, manifest))

    package = None
    if metadata is not None and manifest is not None:
        package = SkillPackage(package_root, skill_path, metadata, manifest)
    return package, diagnostics


def validate_repository(skills_root: Path, *, canonical: bool = True) -> ValidationReport:
    directories, diagnostics = discover_skill_directories(skills_root)
    packages: list[SkillPackage] = []
    names: dict[str, Path] = {}
    for directory in directories:
        package, package_diagnostics = validate_skill(directory, canonical=canonical)
        diagnostics.extend(package_diagnostics)
        if package is None:
            continue
        previous = names.get(package.metadata.name)
        if previous is not None:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCategory.SPEC,
                    "DUPLICATE_SKILL_NAME",
                    f"skill name duplicates package at {previous.as_posix()}",
                    package.skill_md,
                )
            )
        else:
            names[package.metadata.name] = directory
        packages.append(package)

    diagnostics.sort(key=lambda item: (item.path, item.category.value, item.code, item.message))
    return ValidationReport(tuple(packages), tuple(diagnostics))


def diagnostic_codes(report: ValidationReport) -> set[str]:
    """Convenience helper for tests and integrations."""
    return {item.code for item in report.diagnostics}


def has_errors(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(item.severity is Severity.ERROR for item in diagnostics)
