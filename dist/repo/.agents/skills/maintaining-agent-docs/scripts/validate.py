#!/usr/bin/env python3
"""Validate repository agent documentation without mutating it."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

import yaml

DOC_FILES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md", "llms.txt")
SHIMS = ("CLAUDE.md", "GEMINI.md")
COMPLETENESS = {
    "setup/install": re.compile(r"setup|install|bootstrap", re.IGNORECASE),
    "build/run": re.compile(r"build|run|start|usage", re.IGNORECASE),
    "test/verify": re.compile(r"test|verif|definition of done|lint|check", re.IGNORECASE),
    "structure/layout": re.compile(r"structure|layout|directory|project", re.IGNORECASE),
    "safety/conventions": re.compile(
        r"safe|security|convention|style|do/?n.?t|rules", re.IGNORECASE
    ),
}
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    "assigned secret": re.compile(
        r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
        re.IGNORECASE,
    ),
}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
MARKER_RE = re.compile(
    r"<!--\s*(BEGIN|END)\s+maintaining-agent-docs"
    r"(?::([a-z0-9][a-z0-9._/-]*))?(?:\s+\(generated\))?\s*-->",
    re.IGNORECASE,
)
SKIP_PARTS = {".git", "node_modules", ".venv"}


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str
    path: str
    code: str
    message: str


@dataclass(slots=True)
class Report:
    findings: list[Finding] = field(default_factory=list)
    diffs: list[str] = field(default_factory=list)

    def add(self, severity: str, path: Path | str, code: str, message: str) -> None:
        self.findings.append(Finding(severity, str(path), code, message))

    def count(self, severity: str) -> int:
        return sum(item.severity == severity for item in self.findings)


def _relative(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _strip_code(text: str) -> str:
    return re.sub(r"`[^`]*`", "", re.sub(r"```.*?```", "", text, flags=re.DOTALL))


def _paragraphs(text: str) -> list[tuple[str, str]]:
    stripped = _strip_code(text)
    blocks: list[tuple[str, str]] = []
    for raw in re.split(r"\n\s*\n", stripped):
        visible = " ".join(
            line.strip().lstrip("#>*-0123456789. ")
            for line in raw.splitlines()
            if line.strip() and not line.lstrip().startswith("<!--")
        ).strip()
        normalized = " ".join(re.findall(r"[a-z0-9]+", visible.casefold()))
        if len(normalized.split()) >= 8:
            blocks.append((raw, normalized))
    return blocks


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _link_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    return value.split(maxsplit=1)[0]


def _load_allowlist(paths: list[Path], root: Path, report: Report) -> set[str]:
    allowed: set[str] = set()
    for path in paths:
        candidate = path if path.is_absolute() else root / path
        try:
            lines = candidate.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            report.add("ERROR", _relative(candidate, root), "ALLOWLIST_READ", str(error))
            continue
        for line_number, raw in enumerate(lines, 1):
            value = raw.strip()
            if not value or value.startswith("#"):
                continue
            if re.fullmatch(r"[a-f0-9]{64}", value) is None:
                report.add(
                    "ERROR",
                    _relative(candidate, root),
                    "ALLOWLIST_FORMAT",
                    f"line {line_number} must contain a lowercase SHA-256 digest",
                )
                continue
            allowed.add(value)
    return allowed


def _check_frontmatter(root: Path, report: Report) -> None:
    for path in sorted(root.rglob("SKILL.md")):
        if SKIP_PARTS.intersection(path.parts):
            continue
        rel = _relative(path, root)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            report.add("ERROR", rel, "SKILL_READ", str(error))
            continue
        match = FRONTMATTER_RE.match(text)
        if match is None:
            report.add("ERROR", rel, "FRONTMATTER_MISSING", "missing YAML frontmatter")
            continue
        try:
            metadata: Any = yaml.safe_load(match.group(1))
        except yaml.YAMLError as error:
            report.add("ERROR", rel, "YAML_INVALID", str(error).splitlines()[0])
            continue
        if not isinstance(metadata, dict):
            report.add("ERROR", rel, "FRONTMATTER_TYPE", "frontmatter must be a mapping")
            continue
        name = metadata.get("name")
        description = metadata.get("description")
        if not isinstance(name, str) or re.fullmatch(r"[a-z0-9-]{1,64}", name) is None:
            report.add("ERROR", rel, "SKILL_NAME", "name must be lowercase/hyphen and <=64 chars")
        if not isinstance(description, str) or not 1 <= len(description) <= 1024:
            report.add("ERROR", rel, "SKILL_DESCRIPTION", "description must be 1-1024 chars")


def _check_markers(path: Path, root: Path, text: str, report: Report) -> None:
    stack: list[str] = []
    seen: set[str] = set()
    for match in MARKER_RE.finditer(text):
        action, raw_identifier = match.group(1).upper(), match.group(2)
        identifier = (raw_identifier or "").casefold()
        if not identifier:
            report.add(
                "WARN",
                _relative(path, root),
                "MARKER_IDENTIFIER",
                "managed-region marker has no unique identifier",
            )
            identifier = "<legacy>"
        if action == "BEGIN":
            if stack:
                report.add(
                    "ERROR",
                    _relative(path, root),
                    "MARKER_NESTED",
                    f"region {identifier!r} begins inside {stack[-1]!r}",
                )
            if identifier in seen:
                report.add(
                    "ERROR",
                    _relative(path, root),
                    "MARKER_DUPLICATE",
                    f"region identifier {identifier!r} is reused",
                )
            seen.add(identifier)
            stack.append(identifier)
        elif not stack:
            report.add(
                "ERROR",
                _relative(path, root),
                "MARKER_ORDER",
                f"END for {identifier!r} appears before BEGIN",
            )
        else:
            active = stack.pop()
            if identifier != active:
                report.add(
                    "ERROR",
                    _relative(path, root),
                    "MARKER_MISMATCH",
                    f"END {identifier!r} does not match BEGIN {active!r}",
                )
    for identifier in stack:
        report.add(
            "ERROR",
            _relative(path, root),
            "MARKER_UNCLOSED",
            f"region {identifier!r} has no END marker",
        )


def _check_links(
    path: Path,
    root: Path,
    text: str,
    report: Report,
    remote_links: list[tuple[Path, str]],
) -> None:
    for raw in LINK_RE.findall(_strip_code(text)):
        target = _link_target(raw)
        parsed = urlsplit(target)
        if parsed.scheme in {"http", "https"}:
            remote_links.append((path, target))
            continue
        if not target or target.startswith("#") or parsed.scheme == "mailto":
            continue
        decoded = unquote(parsed.path)
        if parsed.scheme or parsed.netloc or Path(decoded).is_absolute():
            report.add(
                "ERROR",
                _relative(path, root),
                "LINK_UNSAFE",
                f"local link must be repository-relative: {target}",
            )
            continue
        candidate = path.parent / decoded
        if not _is_within(candidate, root):
            report.add(
                "ERROR",
                _relative(path, root),
                "LINK_ESCAPE",
                f"local link escapes repository root: {target}",
            )
        elif not candidate.exists():
            report.add(
                "ERROR",
                _relative(path, root),
                "LINK_BROKEN",
                f"local link does not resolve: {target}",
            )


def _check_secrets(path: Path, root: Path, text: str, allowlist: set[str], report: Report) -> None:
    for label, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(0)
            digest = hashlib.sha256(value.encode()).hexdigest()
            if digest in allowlist:
                continue
            report.add(
                "ERROR",
                _relative(path, root),
                "SECRET_DETECTED",
                f"possible {label}; value redacted; allowlist digest {digest}",
            )


def _check_duplication(
    root: Path,
    agents_text: str,
    shim: Path,
    text: str,
    threshold: int,
    report: Report,
) -> None:
    agents_blocks = _paragraphs(agents_text)
    duplicate_raw: list[str] = []
    for raw, normalized in _paragraphs(text):
        score = max(
            (
                difflib.SequenceMatcher(None, normalized, candidate).ratio() * 100
                for _, candidate in agents_blocks
            ),
            default=0.0,
        )
        if score >= threshold:
            duplicate_raw.append(raw)
    if not duplicate_raw:
        return
    rel = _relative(shim, root)
    report.add(
        "WARN",
        rel,
        "POLICY_DUPLICATION",
        f"{len(duplicate_raw)} normalized block(s) match AGENTS.md at >= {threshold}%",
    )
    proposed = text
    for raw in duplicate_raw:
        proposed = proposed.replace(raw, "")
    report.diffs.append(
        "".join(
            difflib.unified_diff(
                text.splitlines(keepends=True),
                proposed.splitlines(keepends=True),
                fromfile=str(rel),
                tofile=f"{rel} (duplicate blocks removed)",
            )
        )
    )


def _gemini_loads_agents(root: Path, report: Report) -> bool:
    settings = root / ".gemini/settings.json"
    if not settings.is_file():
        return False
    try:
        data: Any = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        report.add("ERROR", _relative(settings, root), "GEMINI_SETTINGS", str(error))
        return False
    context = data.get("context") if isinstance(data, dict) else None
    filenames = context.get("fileName") if isinstance(context, dict) else None
    if isinstance(filenames, str):
        return filenames == "AGENTS.md"
    return isinstance(filenames, list) and "AGENTS.md" in filenames


def _check_remote_links(
    root: Path, links: list[tuple[Path, str]], timeout: float, report: Report
) -> None:
    for path, target in sorted(set(links), key=lambda item: item[1]):
        request = Request(target, method="HEAD", headers={"User-Agent": "polymind-doc-validator/2"})
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                status = getattr(response, "status", 200)
            if status >= 400:
                report.add(
                    "ERROR", _relative(path, root), "REMOTE_LINK", f"HTTP {status}: {target}"
                )
        except HTTPError as error:
            severity = "WARN" if error.code in {401, 403, 405, 429} else "ERROR"
            report.add(
                severity,
                _relative(path, root),
                "REMOTE_LINK",
                f"HTTP {error.code}: {target}",
            )
        except (URLError, TimeoutError, OSError) as error:
            report.add(
                "WARN",
                _relative(path, root),
                "REMOTE_LINK_UNAVAILABLE",
                f"could not verify {target}: {error}",
            )


def check(
    root: Path,
    report: Report,
    *,
    duplication_threshold: int,
    allowlist: set[str],
    check_remote: bool,
    timeout: float,
) -> None:
    present = {name: root / name for name in DOC_FILES if (root / name).is_file()}
    agents = present.get("AGENTS.md")
    agents_text = agents.read_text(encoding="utf-8") if agents else ""
    if agents is None:
        report.add("WARN", "AGENTS.md", "AGENTS_MISSING", "canonical instructions not found")
    else:
        for label, pattern in COMPLETENESS.items():
            if pattern.search(agents_text) is None:
                report.add("INFO", "AGENTS.md", "SECTION_NOT_FOUND", f"no {label} section found")

    remote_links: list[tuple[Path, str]] = []
    for name, path in present.items():
        text = path.read_text(encoding="utf-8")
        _check_markers(path, root, text, report)
        _check_links(path, root, text, report, remote_links)
        _check_secrets(path, root, text, allowlist, report)
        if agents is not None and name in SHIMS:
            _check_duplication(root, agents_text, path, text, duplication_threshold, report)

    claude = present.get("CLAUDE.md")
    if claude and "@AGENTS.md" not in claude.read_text(encoding="utf-8"):
        report.add(
            "ERROR", "CLAUDE.md", "CLAUDE_IMPORT", "selected Claude shim must import @AGENTS.md"
        )
    gemini = present.get("GEMINI.md")
    if gemini and "AGENTS.md" not in gemini.read_text(encoding="utf-8"):
        report.add(
            "ERROR", "GEMINI.md", "GEMINI_POINTER", "selected Gemini shim must point to AGENTS.md"
        )
    if (root / ".gemini/settings.json").is_file() and not _gemini_loads_agents(root, report):
        report.add(
            "WARN",
            ".gemini/settings.json",
            "GEMINI_CONTEXT",
            "context.fileName does not include AGENTS.md",
        )

    llms = present.get("llms.txt")
    if llms:
        first = next(
            (line for line in llms.read_text(encoding="utf-8").splitlines() if line.strip()), ""
        )
        if not first.startswith("# "):
            report.add("ERROR", "llms.txt", "LLMS_TITLE", "first non-empty line must be an H1")

    nested = sorted(
        str(path.relative_to(root))
        for path in root.rglob("AGENTS.md")
        if path != root / "AGENTS.md" and not SKIP_PARTS.intersection(path.parts)
    )
    if nested:
        report.add("INFO", "AGENTS.md", "NESTED_SCOPES", ", ".join(nested))
    _check_frontmatter(root, report)
    if check_remote:
        _check_remote_links(root, remote_links, timeout, report)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--check", action="store_true", help="run the read-only check (default)")
    parser.add_argument("--diff", action="store_true", help="show advisory duplicate-removal diffs")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    parser.add_argument("--quiet", action="store_true", help="print only the summary")
    parser.add_argument("--check-remote", action="store_true", help="verify HTTP(S) links")
    parser.add_argument("--remote-timeout", type=float, default=5.0)
    parser.add_argument("--duplication-threshold", type=int, default=88, metavar="PERCENT")
    parser.add_argument(
        "--secret-allowlist", action="append", default=[], type=Path, metavar="FILE"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}")
        return 2
    if not 0 <= args.duplication_threshold <= 100:
        print("ERROR: --duplication-threshold must be between 0 and 100")
        return 2
    if args.remote_timeout <= 0:
        print("ERROR: --remote-timeout must be positive")
        return 2

    report = Report()
    allowlist = _load_allowlist(args.secret_allowlist, root, report)
    check(
        root,
        report,
        duplication_threshold=args.duplication_threshold,
        allowlist=allowlist,
        check_remote=args.check_remote,
        timeout=args.remote_timeout,
    )
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    if not args.quiet:
        for item in sorted(
            report.findings,
            key=lambda finding: (order[finding.severity], finding.path, finding.code),
        ):
            print(f"[{item.severity}] {item.path}: {item.code}: {item.message}")
        if args.diff:
            for diff in report.diffs:
                print(diff, end="" if diff.endswith("\n") else "\n")
    errors, warnings = report.count("ERROR"), report.count("WARN")
    print(f"summary: {errors} error(s), {warnings} warning(s), {report.count('INFO')} info")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
