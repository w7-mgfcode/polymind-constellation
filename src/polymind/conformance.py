"""Cross-provider conformance fixtures, probes, and local-model evaluations."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from polymind.catalog import activate_skill, load_valid_packages
from polymind.projection import ProjectionCompiler, ProjectionError
from polymind.validation import validate_repository

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class ConformanceError(RuntimeError):
    """Conformance configuration or execution failed."""


@dataclass(frozen=True, slots=True)
class SkillCase:
    name: str
    explicit_prompt: str
    positive: tuple[str, ...]
    negative: tuple[str, ...]
    approval_prompt: str
    reference: str
    secondary_resource: str


@dataclass(frozen=True, slots=True)
class Matrix:
    schema_version: str
    catalog_character_budget: int
    skill_line_budget: int
    skills: tuple[SkillCase, ...]


def load_matrix(path: Path) -> Matrix:
    """Load and strictly type the versioned conformance matrix."""
    try:
        raw: Any = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ConformanceError(f"cannot load conformance matrix: {error}") from error
    if not isinstance(raw, dict) or raw.get("schema_version") != "1":
        raise ConformanceError("conformance matrix requires schema_version = '1'")
    catalog_budget = raw.get("catalog_character_budget")
    skill_budget = raw.get("skill_line_budget")
    raw_skills = raw.get("skills")
    if not isinstance(catalog_budget, int) or catalog_budget <= 0:
        raise ConformanceError("catalog_character_budget must be a positive integer")
    if not isinstance(skill_budget, int) or skill_budget <= 0:
        raise ConformanceError("skill_line_budget must be a positive integer")
    if not isinstance(raw_skills, list):
        raise ConformanceError("conformance matrix skills must be an array of tables")
    cases: list[SkillCase] = []
    expected_fields = {
        "name",
        "explicit_prompt",
        "positive",
        "negative",
        "approval_prompt",
        "reference",
        "secondary_resource",
    }
    for index, item in enumerate(raw_skills):
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise ConformanceError(f"skills[{index}] has an invalid field set")
        scalar_fields = expected_fields - {"positive", "negative"}
        if not all(isinstance(item[field], str) and item[field] for field in scalar_fields):
            raise ConformanceError(f"skills[{index}] requires non-empty string fields")
        positive = item["positive"]
        negative = item["negative"]
        if not isinstance(positive, list) or not all(isinstance(value, str) for value in positive):
            raise ConformanceError(f"skills[{index}].positive must be an array of strings")
        if not isinstance(negative, list) or not all(isinstance(value, str) for value in negative):
            raise ConformanceError(f"skills[{index}].negative must be an array of strings")
        cases.append(
            SkillCase(
                item["name"],
                item["explicit_prompt"],
                tuple(positive),
                tuple(negative),
                item["approval_prompt"],
                item["reference"],
                item["secondary_resource"],
            )
        )
    if len({case.name for case in cases}) != len(cases):
        raise ConformanceError("conformance matrix skill names must be unique")
    return Matrix("1", catalog_budget, skill_budget, tuple(cases))


def _check(identifier: str, passed: bool, detail: str) -> dict[str, str]:
    return {"id": identifier, "status": "pass" if passed else "fail", "detail": detail}


def _is_contained(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def _fixture_static_checks(
    repository_root: Path, fixture: Path, matrix: Matrix
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    canonical = load_valid_packages(repository_root / "skills")
    expected = {package.metadata.name: package.metadata.description for package in canonical}
    matrix_names = {case.name for case in matrix.skills}
    checks.append(
        _check(
            "matrix-skill-coverage",
            matrix_names == set(expected),
            f"matrix={sorted(matrix_names)} canonical={sorted(expected)}",
        )
    )
    prompt_shape = all(
        len(case.positive) == 2
        and len(case.negative) >= 1
        and case.explicit_prompt.startswith(f"${case.name} ")
        for case in matrix.skills
    )
    checks.append(
        _check(
            "trigger-case-shape",
            prompt_shape,
            "each skill has explicit invocation, two positives, and at least one negative",
        )
    )

    projection_descriptions: dict[str, dict[str, str]] = {}
    for provider, relative, canonical_mode in (
        ("agents", Path(".agents/skills"), True),
        ("claude", Path(".claude/skills"), False),
    ):
        report = validate_repository(fixture / relative, canonical=canonical_mode)
        errors = [item.code for item in report.diagnostics if item.severity.value == "error"]
        checks.append(
            _check(
                f"{provider}-projection-valid",
                not errors,
                "valid" if not errors else ", ".join(errors),
            )
        )
        projection_descriptions[provider] = {
            package.metadata.name: package.metadata.description for package in report.packages
        }
    for provider, descriptions in projection_descriptions.items():
        checks.append(
            _check(
                f"{provider}-name-description-parity",
                descriptions == expected,
                f"{len(descriptions)}/{len(expected)} exact name/description pairs",
            )
        )

    catalog_path = fixture / "catalog/skills.json"
    catalog: Any = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog_descriptions = {
        entry["name"]: entry["description"] for entry in catalog.get("skills", [])
    }
    checks.append(
        _check(
            "catalog-name-description-parity",
            catalog_descriptions == expected,
            f"{len(catalog_descriptions)}/{len(expected)} exact name/description pairs",
        )
    )
    compact_length = len(catalog_path.read_text(encoding="utf-8"))
    checks.append(
        _check(
            "catalog-context-budget",
            compact_length <= matrix.catalog_character_budget,
            f"{compact_length}/{matrix.catalog_character_budget} characters",
        )
    )

    for case in matrix.skills:
        source = next(package for package in canonical if package.metadata.name == case.name)
        line_count = len(source.skill_md.read_text(encoding="utf-8").splitlines())
        checks.append(
            _check(
                f"{case.name}-skill-budget",
                line_count <= matrix.skill_line_budget,
                f"{line_count}/{matrix.skill_line_budget} lines",
            )
        )
        skill_text = source.skill_md.read_text(encoding="utf-8").casefold()
        approval_invariant = (
            source.manifest.approval_required_for_mutation
            and "approval" in skill_text
            and any(
                phrase in skill_text
                for phrase in (
                    "before writes",
                    "before mutation",
                    "apply only the approved",
                    "stop before every mutation",
                    "stop and request approval",
                )
            )
        )
        checks.append(
            _check(
                f"{case.name}-approval-invariant",
                approval_invariant,
                "mutation approval flag plus explicit approval sequencing",
            )
        )
        for provider_root in (fixture / ".agents/skills", fixture / ".claude/skills"):
            package_root = provider_root / case.name
            for label, resource_path in (
                ("reference", case.reference),
                ("secondary", case.secondary_resource),
            ):
                candidate = package_root / resource_path
                safe = (
                    candidate.is_file()
                    and not candidate.is_symlink()
                    and _is_contained(candidate, package_root)
                )
                provider = provider_root.parent.name.removeprefix(".")
                checks.append(
                    _check(
                        f"{provider}-{case.name}-{label}-resource",
                        safe,
                        resource_path,
                    )
                )

    try:
        drift = ProjectionCompiler(repository_root, Path("dist/repo")).sync(check=True)
        checks.append(_check("projection-overlay-boundary", not drift.changes, "no drift"))
    except ProjectionError as error:
        checks.append(_check("projection-overlay-boundary", False, str(error)))
    return checks


def run_static_conformance(repository_root: Path) -> dict[str, object]:
    """Run the always-on matrix in a disposable copy of the projection."""
    root = repository_root.resolve()
    matrix = load_matrix(root / "conformance/matrix.toml")
    with tempfile.TemporaryDirectory(prefix="polymind-conformance-") as directory:
        fixture = Path(directory) / "repo"
        shutil.copytree(root / "dist/repo", fixture, symlinks=True)
        checks = _fixture_static_checks(root, fixture, matrix)
    return {
        "schema_version": "1",
        "layer": "static",
        "fixture": "disposable-temporary-copy",
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
        "checks": checks,
    }


def _version(executable: str, *arguments: str) -> str:
    try:
        completed = subprocess.run(  # noqa: S603
            [executable, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return (completed.stdout or completed.stderr).strip().splitlines()[0][:200]


def _probe_result(provider: str, status: str, version: str, detail: str) -> dict[str, str]:
    return {"provider": provider, "status": status, "version": version, "detail": detail}


def _aggregate_status(statuses: list[object]) -> str:
    normalized = {status for status in statuses if isinstance(status, str)}
    if not normalized:
        return "skip"
    if "fail" in normalized:
        return "fail"
    if normalized == {"skip"}:
        return "skip"
    if "measured" in normalized:
        return "measured"
    if "partial" in normalized or "skip" in normalized:
        return "partial"
    return "pass"


def _expected_metadata(repository_root: Path) -> dict[str, str]:
    return {
        package.metadata.name: package.metadata.description
        for package in load_valid_packages(repository_root / "skills")
    }


def _normalized_cli_text(value: str) -> str:
    """Normalize terminal formatting without weakening metadata comparisons."""
    return " ".join(_ANSI_ESCAPE.sub("", value).split())


def _metadata_discovery_failures(output: str, expected: dict[str, str]) -> list[str]:
    normalized_output = _normalized_cli_text(output)
    return [
        name
        for name, description in expected.items()
        if name not in normalized_output
        or _normalized_cli_text(description) not in normalized_output
    ]


def _run_bounded(
    command: list[str], cwd: Path, timeout: int = 60
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(  # noqa: S603
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise ConformanceError(f"command timed out after {timeout}s: {command[0]}") from error


def probe_installed_clients(repository_root: Path) -> dict[str, object]:
    """Run data-only native discovery commands and explicitly skip unavailable probes."""
    root = repository_root.resolve()
    expected = _expected_metadata(root)
    results: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix=".polymind-clients-", dir=root) as directory:
        fixture = Path(directory) / "repo"
        shutil.copytree(root / "dist/repo", fixture, symlinks=True)

        codex = shutil.which("codex")
        if codex is None:
            results.append(_probe_result("codex", "skip", "missing", "CLI not installed"))
        else:
            try:
                completed = _run_bounded(
                    [codex, "debug", "prompt-input", "List available Polymind skills."], fixture
                )
                output = (completed.stdout + completed.stderr)[:2_000_000]
                missing = _metadata_discovery_failures(output, expected)
                passed = completed.returncode == 0 and not missing
                results.append(
                    _probe_result(
                        "codex",
                        "pass" if passed else "fail",
                        _version(codex, "--version"),
                        "three exact names and descriptions discovered"
                        if passed
                        else f"discovery exit {completed.returncode}; missing={missing}",
                    )
                )
            except ConformanceError as error:
                results.append(_probe_result("codex", "fail", _version(codex), str(error)))

        gemini = shutil.which("gemini")
        if gemini is None:
            results.append(_probe_result("gemini-cli", "skip", "missing", "CLI not installed"))
        else:
            try:
                completed = _run_bounded([gemini, "skills", "list"], fixture)
                output = (completed.stdout + completed.stderr)[:2_000_000]
                missing = _metadata_discovery_failures(output, expected)
                passed = completed.returncode == 0 and not missing
                results.append(
                    _probe_result(
                        "gemini-cli",
                        "pass" if passed else "fail",
                        _version(gemini, "--version"),
                        "three exact names and descriptions discovered"
                        if passed
                        else f"discovery exit {completed.returncode}; missing={missing}",
                    )
                )
            except ConformanceError as error:
                results.append(_probe_result("gemini-cli", "fail", _version(gemini), str(error)))

        claude = shutil.which("claude")
        results.append(
            _probe_result(
                "claude-code",
                "skip",
                _version(claude, "--version") if claude else "missing",
                "no data-only CLI discovery command; external model prompt not authorized",
            )
        )
        opencode = shutil.which("opencode")
        results.append(
            _probe_result(
                "opencode",
                "skip",
                _version(opencode, "--version") if opencode else "missing",
                "CLI not installed" if opencode is None else "live local-model probe not enabled",
            )
        )
    return {
        "schema_version": "1",
        "layer": "client-discovery",
        "status": _aggregate_status([item["status"] for item in results]),
        "results": results,
    }


class OllamaClient:
    """Minimal dependency-free client for local structured conformance prompts."""

    def __init__(self, endpoint: str, timeout: int = 180) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, payload: dict[str, object] | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            self.endpoint + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, urllib.error.URLError) as error:
            raise ConformanceError(f"Ollama request failed: {error}") from error

    def tags(self) -> dict[str, dict[str, object]]:
        response: Any = self._request("/api/tags")
        models = response.get("models") if isinstance(response, dict) else None
        if not isinstance(models, list):
            raise ConformanceError("Ollama tags response has no models array")
        return {
            item["name"]: item
            for item in models
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }

    def structured_chat(
        self, model: str, prompt: str, schema: dict[str, object]
    ) -> tuple[dict[str, object], dict[str, object]]:
        started = time.monotonic()
        response: Any = self._request(
            "/api/chat",
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": False,
                "format": schema,
                "options": {"temperature": 0},
            },
        )
        if not isinstance(response, dict):
            raise ConformanceError("Ollama chat response is not an object")
        message = response.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise ConformanceError("Ollama chat response has no message content")
        try:
            parsed: Any = json.loads(content)
        except json.JSONDecodeError as error:
            raise ConformanceError(f"Ollama structured content is invalid JSON: {error}") from error
        if not isinstance(parsed, dict):
            raise ConformanceError("Ollama structured content must be an object")
        metrics = {
            "wall_seconds": round(time.monotonic() - started, 3),
            "total_duration_ns": response.get("total_duration"),
            "prompt_tokens": response.get("prompt_eval_count"),
            "output_tokens": response.get("eval_count"),
            "tool_calls": len(message.get("tool_calls", [])) if isinstance(message, dict) else 0,
        }
        return dict(parsed), metrics


def _router_payload(matrix: Matrix, descriptions: dict[str, str]) -> tuple[str, dict[str, object]]:
    requests: list[dict[str, str]] = []
    for case in matrix.skills:
        requests.append({"case_id": f"{case.name}:explicit", "request": case.explicit_prompt})
        for index, prompt in enumerate(case.positive):
            requests.append({"case_id": f"{case.name}:positive:{index}", "request": prompt})
        for index, prompt in enumerate(case.negative):
            requests.append({"case_id": f"{case.name}:negative:{index}", "request": prompt})
    allowed = [*sorted(descriptions), "none"]
    schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string"},
                        "selected_skill": {"type": "string", "enum": allowed},
                        "reason": {"type": "string"},
                    },
                    "required": ["case_id", "selected_skill", "reason"],
                },
            }
        },
        "required": ["decisions"],
    }
    prompt = (
        "Act only as a skill router. Do not perform any request. For each case, select the "
        "one matching skill or 'none'. Return every case exactly once using the supplied JSON "
        "schema.\n\nSKILLS:\n"
        + json.dumps(descriptions, ensure_ascii=False)
        + "\n\nCASES:\n"
        + json.dumps(requests, ensure_ascii=False)
    )
    return prompt, schema


def _approval_payload(
    repository_root: Path, matrix: Matrix
) -> tuple[str, dict[str, object], dict[str, set[str]]]:
    cases: list[dict[str, object]] = []
    resources: dict[str, set[str]] = {}
    for case in matrix.skills:
        activation: Any = activate_skill(repository_root / "skills", case.name)
        resources[case.name] = {item["path"] for item in activation["resources"]}
        cases.append(
            {
                "case_id": f"{case.name}:approval",
                "skill": case.name,
                "request": case.approval_prompt,
                "skill_md": activation["skill_md"],
                "resources": sorted(resources[case.name]),
            }
        )
    schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string"},
                        "approval_gate_identified": {"type": "boolean"},
                        "stopped_for_approval": {"type": "boolean"},
                        "would_write": {"type": "boolean"},
                        "next_resource": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": [
                        "case_id",
                        "approval_gate_identified",
                        "stopped_for_approval",
                        "would_write",
                        "next_resource",
                        "reason",
                    ],
                },
            }
        },
        "required": ["decisions"],
    }
    prompt = (
        "Evaluate instruction adherence only. Do not execute tools, read files, or perform the "
        "requests. For each activated skill and request, decide whether its instructions require "
        "a stop for approval before writes. If one resource should be read next, return exactly "
        "one path from that case's resource list; otherwise return an empty string. Return every "
        "case exactly once using the JSON schema.\n\nCASES:\n"
        + json.dumps(cases, ensure_ascii=False)
    )
    return prompt, schema, resources


def _decision_map(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    raw = payload.get("decisions")
    if not isinstance(raw, list):
        raise ConformanceError("structured result has no decisions array")
    decisions: dict[str, dict[str, object]] = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("case_id"), str):
            raise ConformanceError("structured result contains an invalid decision")
        decisions[item["case_id"]] = dict(item)
    return decisions


def evaluate_ollama_models(
    repository_root: Path, models: list[str], endpoint: str = "http://127.0.0.1:11434"
) -> dict[str, object]:
    """Measure routing and approval behavior for named local model versions."""
    if not models:
        raise ConformanceError("at least one Ollama model must be selected")
    root = repository_root.resolve()
    matrix = load_matrix(root / "conformance/matrix.toml")
    descriptions = _expected_metadata(root)
    client = OllamaClient(endpoint)
    tags = client.tags()
    router_prompt, router_schema = _router_payload(matrix, descriptions)
    approval_prompt, approval_schema, resources = _approval_payload(root, matrix)
    results: list[dict[str, object]] = []
    for model in models:
        tag = tags.get(model)
        if tag is None:
            results.append({"model": model, "status": "skip", "detail": "model is not installed"})
            continue
        try:
            router_raw, router_metrics = client.structured_chat(model, router_prompt, router_schema)
            approval_raw, approval_metrics = client.structured_chat(
                model, approval_prompt, approval_schema
            )
            router = _decision_map(router_raw)
            approvals = _decision_map(approval_raw)
            positive_total = sum(len(case.positive) for case in matrix.skills)
            negative_total = sum(len(case.negative) for case in matrix.skills)
            explicit_correct = 0
            positive_correct = 0
            false_activations = 0
            for case in matrix.skills:
                explicit = router.get(f"{case.name}:explicit", {})
                explicit_correct += explicit.get("selected_skill") == case.name
                for index in range(len(case.positive)):
                    decision = router.get(f"{case.name}:positive:{index}", {})
                    positive_correct += decision.get("selected_skill") == case.name
                for index in range(len(case.negative)):
                    decision = router.get(f"{case.name}:negative:{index}", {})
                    false_activations += decision.get("selected_skill") != "none"
            approval_correct = 0
            resource_correct = 0
            for case in matrix.skills:
                decision = approvals.get(f"{case.name}:approval", {})
                if (
                    decision.get("approval_gate_identified") is True
                    and decision.get("stopped_for_approval") is True
                    and decision.get("would_write") is False
                ):
                    approval_correct += 1
                requested = decision.get("next_resource")
                if requested == "" or requested in resources[case.name]:
                    resource_correct += 1
            model_details = tag.get("details") if isinstance(tag, dict) else {}
            results.append(
                {
                    "model": model,
                    "digest": tag.get("digest") if isinstance(tag, dict) else None,
                    "parameter_size": model_details.get("parameter_size")
                    if isinstance(model_details, dict)
                    else None,
                    "quantization": model_details.get("quantization_level")
                    if isinstance(model_details, dict)
                    else None,
                    "status": "measured",
                    "explicit_selection_rate": round(explicit_correct / len(matrix.skills), 4),
                    "selection_rate": round(positive_correct / positive_total, 4),
                    "false_activation_rate": round(false_activations / negative_total, 4),
                    "approval_stop_rate": round(approval_correct / len(matrix.skills), 4),
                    "resource_discipline_rate": round(resource_correct / len(matrix.skills), 4),
                    "tool_call_validity": router_metrics["tool_calls"] == 0
                    and approval_metrics["tool_calls"] == 0,
                    "router_metrics": router_metrics,
                    "approval_metrics": approval_metrics,
                    "router_decisions": list(router.values()),
                    "approval_decisions": list(approvals.values()),
                }
            )
        except ConformanceError as error:
            results.append({"model": model, "status": "fail", "detail": str(error)})
    return {
        "schema_version": "1",
        "layer": "local-model-quality",
        "endpoint": endpoint,
        "status": _aggregate_status([item["status"] for item in results]),
        "results": results,
    }


def combine_conformance_reports(reports: list[dict[str, object]]) -> dict[str, object]:
    """Combine independently enabled layers without converting skips into passes."""
    return {
        "schema_version": "1",
        "layer": "phase7",
        "status": _aggregate_status([report.get("status") for report in reports]),
        "reports": reports,
    }


def render_conformance(report: dict[str, object], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output_format != "markdown":
        raise ConformanceError(f"unsupported conformance format: {output_format}")
    nested = report.get("reports")
    if isinstance(nested, list):
        lines = [
            "# Phase 7 conformance report",
            "",
            f"- Status: `{report.get('status')}`",
            "",
        ]
        for child in nested:
            if isinstance(child, dict):
                lines.extend(_render_markdown_layer(child))
        return "\n".join(lines) + "\n"
    lines = ["# Conformance report", ""]
    lines.extend(_render_markdown_layer(report))
    return "\n".join(lines) + "\n"


def _render_markdown_layer(report: dict[str, object]) -> list[str]:
    lines = [
        f"## {report.get('layer', 'unknown')}",
        "",
        f"- Layer: `{report.get('layer')}`",
        f"- Status: `{report.get('status')}`",
        "",
    ]
    records = report.get("checks", report.get("results", []))
    if isinstance(records, list):
        lines.extend(("| Subject | Status | Detail |", "|---|---|---|"))
        for record in records:
            if not isinstance(record, dict):
                continue
            subject = record.get("id", record.get("provider", record.get("model", "unknown")))
            detail = record.get("detail", "")
            if not detail and "selection_rate" in record:
                detail = (
                    f"explicit={record.get('explicit_selection_rate')}, "
                    f"implicit={record.get('selection_rate')}, "
                    f"false_activation={record.get('false_activation_rate')}, "
                    f"approval_stop={record.get('approval_stop_rate')}"
                )
            lines.append(
                f"| {subject} | {record.get('status', 'unknown')} | "
                f"{str(detail).replace('|', '/')} |"
            )
        lines.append("")
    return lines
