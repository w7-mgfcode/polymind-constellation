"""Data-only catalog, activation, and bounded resource reads."""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

from polymind.host_contract import map_host_permissions
from polymind.model import Severity, SkillPackage
from polymind.validation import validate_repository

MAX_RESOURCE_BYTES = 1024 * 1024
_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CatalogError(RuntimeError):
    """Catalog or activation failed closed."""


@dataclass(frozen=True, slots=True)
class ResourceRecord:
    path: str
    kind: str
    media_type: str
    size: int
    sha256: str
    text: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "kind": self.kind,
            "media_type": self.media_type,
            "bytes": self.size,
            "sha256": self.sha256,
            "text": self.text,
        }


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _tags(package: SkillPackage) -> list[str]:
    return [
        item.strip()
        for item in package.metadata.metadata["polymind.tags"].split(",")
        if item.strip()
    ]


def load_valid_packages(skills_root: Path) -> tuple[SkillPackage, ...]:
    """Load a canonical repository only when every package validates."""
    report = validate_repository(skills_root)
    errors = [item for item in report.diagnostics if item.severity is Severity.ERROR]
    if errors:
        summary = "; ".join(f"{item.code}: {item.path}" for item in errors)
        raise CatalogError(f"canonical validation failed: {summary}")
    return tuple(sorted(report.packages, key=lambda package: package.metadata.name))


def build_catalog(
    packages: tuple[SkillPackage, ...], *, package_prefix: str = "skills"
) -> dict[str, object]:
    """Build a compact discovery catalog without loading skill instructions."""
    prefix = package_prefix.rstrip("/")
    entries: list[dict[str, object]] = []
    for package in packages:
        entries.append(
            {
                "name": package.metadata.name,
                "description": package.metadata.description,
                "package_path": f"{prefix}/{package.metadata.name}",
                "version": package.metadata.metadata["polymind.version"],
                "tags": _tags(package),
                "capabilities": sorted(action.value for action in package.manifest.actions),
                "risk": package.metadata.metadata["polymind.risk"],
            }
        )
    return {
        "schema_version": "1",
        "operation": "catalog",
        "execution": "none",
        "skills": entries,
    }


def catalog_document(skills_root: Path, *, package_prefix: str | None = None) -> dict[str, object]:
    prefix = package_prefix if package_prefix is not None else skills_root.as_posix()
    return build_catalog(load_valid_packages(skills_root), package_prefix=prefix)


def _resource_kind(relative: Path) -> str:
    if relative == Path("skill.toml"):
        return "manifest"
    return relative.parts[0] if len(relative.parts) > 1 else "package"


def _is_text(content: bytes) -> bool:
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return b"\x00" not in content


def _resource_manifest(package: SkillPackage) -> tuple[ResourceRecord, ...]:
    root = package.root.resolve()
    records: list[ResourceRecord] = []
    for path in sorted(package.root.rglob("*")):
        if path.is_symlink():
            raise CatalogError(f"activation rejects symlinked package resources: {path}")
        if not path.is_file():
            continue
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError) as error:
            raise CatalogError(f"package resource escapes its base directory: {path}") from error
        relative = path.relative_to(package.root)
        if relative == Path("SKILL.md"):
            continue
        content = path.read_bytes()
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        records.append(
            ResourceRecord(
                relative.as_posix(),
                _resource_kind(relative),
                media_type,
                len(content),
                _sha256_bytes(content),
                _is_text(content),
            )
        )
    return tuple(records)


def _package_digest(skill_md: bytes, resources: tuple[ResourceRecord, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(b"SKILL.md\0")
    digest.update(skill_md)
    for resource in resources:
        digest.update(resource.path.encode())
        digest.update(b"\0")
        digest.update(resource.sha256.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _select_package(packages: tuple[SkillPackage, ...], name: str) -> SkillPackage:
    if _NAME_PATTERN.fullmatch(name) is None:
        raise CatalogError(f"invalid skill name: {name!r}")
    for package in packages:
        if package.metadata.name == name:
            return package
    raise CatalogError(f"unknown skill: {name}")


def activate_skill(
    skills_root: Path, name: str, *, package_prefix: str | None = None
) -> dict[str, object]:
    """Return instructions and metadata without executing or granting anything."""
    package = _select_package(load_valid_packages(skills_root), name)
    resources = _resource_manifest(package)
    skill_md = package.skill_md.read_bytes()
    try:
        skill_text = skill_md.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CatalogError(f"SKILL.md is not UTF-8: {package.skill_md}") from error
    actions = frozenset(action.value for action in package.manifest.actions)
    prefix = package_prefix if package_prefix is not None else skills_root.as_posix()
    return {
        "schema_version": "1",
        "operation": "activate",
        "execution": "none",
        "permissions_granted": [],
        "name": package.metadata.name,
        "version": package.metadata.metadata["polymind.version"],
        "description": package.metadata.description,
        "base_directory": f"{prefix.rstrip('/')}/{package.metadata.name}",
        "package_digest": _package_digest(skill_md, resources),
        "capabilities": sorted(actions),
        "permission_requirements": [
            requirement.as_dict() for requirement in map_host_permissions(actions)
        ],
        "approval_required_for_mutation": package.manifest.approval_required_for_mutation,
        "skill_md": skill_text,
        "resources": [resource.as_dict() for resource in resources],
    }


def _safe_resource_path(raw_path: str) -> PurePosixPath:
    if "\\" in raw_path:
        raise CatalogError("resource path must use portable forward slashes")
    candidate = PurePosixPath(raw_path)
    if (
        not raw_path
        or candidate.is_absolute()
        or candidate.as_posix() != raw_path
        or "." in candidate.parts
        or ".." in candidate.parts
    ):
        raise CatalogError("resource path must be a normalized package-relative path")
    if raw_path == "SKILL.md":
        raise CatalogError("SKILL.md is returned by activation, not the resource endpoint")
    return candidate


def read_resource(
    skills_root: Path,
    name: str,
    resource_path: str,
    *,
    max_bytes: int = 256 * 1024,
) -> tuple[dict[str, object], bytes]:
    """Read exactly one manifested resource with path and output bounds."""
    if not 1 <= max_bytes <= MAX_RESOURCE_BYTES:
        raise CatalogError(f"max_bytes must be between 1 and {MAX_RESOURCE_BYTES}")
    package = _select_package(load_valid_packages(skills_root), name)
    resources = {record.path: record for record in _resource_manifest(package)}
    normalized = _safe_resource_path(resource_path).as_posix()
    record = resources.get(normalized)
    if record is None:
        raise CatalogError(f"resource is not in the activated package manifest: {normalized}")
    if record.size > max_bytes:
        raise CatalogError(f"resource exceeds output limit ({record.size} > {max_bytes} bytes)")
    candidate = package.root.joinpath(*PurePosixPath(normalized).parts)
    try:
        candidate.resolve(strict=True).relative_to(package.root.resolve())
    except (OSError, ValueError) as error:
        raise CatalogError("resource escapes its activated package base") from error
    if candidate.is_symlink():
        raise CatalogError("resource became a symlink after activation")
    content = candidate.read_bytes()
    if _sha256_bytes(content) != record.sha256:
        raise CatalogError("resource changed after manifest creation")
    return record.as_dict(), content


def _markdown_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def render_catalog(document: dict[str, object], output_format: str) -> str:
    """Render a catalog deterministically as JSON, XML, or Markdown."""
    if output_format == "json":
        return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    skills: Any = document["skills"]
    if output_format == "markdown":
        lines = [
            "# Skill catalog",
            "",
            "Discovery metadata only. Cataloging does not activate skills or execute code.",
            "",
            "| Name | Version | Description | Capabilities | Risk |",
            "|---|---|---|---|---|",
        ]
        for skill in skills:
            lines.append(
                "| "
                + " | ".join(
                    (
                        _markdown_escape(skill["name"]),
                        _markdown_escape(skill["version"]),
                        _markdown_escape(skill["description"]),
                        _markdown_escape(", ".join(skill["capabilities"])),
                        _markdown_escape(skill["risk"]),
                    )
                )
                + " |"
            )
        return "\n".join(lines) + "\n"
    if output_format == "xml":
        root = ET.Element(
            "skill-catalog",
            {"schema-version": str(document["schema_version"]), "execution": "none"},
        )
        for skill in skills:
            node = ET.SubElement(root, "skill")
            for field in ("name", "version", "description", "package_path", "risk"):
                ET.SubElement(node, field.replace("_", "-")).text = str(skill[field])
            tags = ET.SubElement(node, "tags")
            for tag in skill["tags"]:
                ET.SubElement(tags, "tag").text = str(tag)
            capabilities = ET.SubElement(node, "capabilities")
            for action in skill["capabilities"]:
                ET.SubElement(capabilities, "capability").text = str(action)
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"
    raise CatalogError(f"unsupported catalog format: {output_format}")


def render_activation(document: dict[str, object], output_format: str) -> str:
    """Render activation data without executing resources."""
    if output_format == "json":
        return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output_format != "markdown":
        raise CatalogError(f"unsupported activation format: {output_format}")
    capabilities = ", ".join(str(item) for item in cast(list[object], document["capabilities"]))
    lines = [
        f"# Activated skill: {document['name']}",
        "",
        f"- Version: `{document['version']}`",
        f"- Base directory: `{document['base_directory']}`",
        f"- Package digest: `{document['package_digest']}`",
        f"- Capabilities: {capabilities or 'none'}",
        "- Execution: none; no permissions granted",
        "",
        "## SKILL.md",
        "",
        "````markdown",
        str(document["skill_md"]).rstrip(),
        "````",
        "",
        "## Resource manifest",
        "",
        "Read one resource at a time through the resource endpoint.",
        "",
        "| Path | Kind | Bytes | SHA-256 | Text |",
        "|---|---|---:|---|---|",
    ]
    for resource in cast(list[dict[str, object]], document["resources"]):
        lines.append(
            f"| {_markdown_escape(resource['path'])} | {_markdown_escape(resource['kind'])} "
            f"| {resource['bytes']} | `{resource['sha256']}` | {resource['text']} |"
        )
    return "\n".join(lines) + "\n"


def render_resource_json(record: dict[str, object], content: bytes) -> str:
    """Render one resource with UTF-8 text or bounded base64 content."""
    document = dict(record)
    if bool(record["text"]):
        document["encoding"] = "utf-8"
        document["content"] = content.decode("utf-8")
    else:
        document["encoding"] = "base64"
        document["content"] = base64.b64encode(content).decode("ascii")
    document["operation"] = "resource"
    document["execution"] = "none"
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
