from __future__ import annotations

from pathlib import Path
from typing import Any

from polymind.conformance import (
    OllamaClient,
    _metadata_discovery_failures,
    combine_conformance_reports,
    evaluate_ollama_models,
    load_matrix,
    probe_installed_clients,
    render_conformance,
    run_static_conformance,
)

ROOT = Path(__file__).parents[1]


def test_native_discovery_parser_normalizes_terminal_layout() -> None:
    expected = {"example-skill": "A long\n description."}
    output = "\x1b[32mexample-skill\x1b[0m\n  Description: A long description.\n"

    assert _metadata_discovery_failures(output, expected) == []


def test_matrix_covers_the_three_canonical_skills() -> None:
    matrix = load_matrix(ROOT / "conformance/matrix.toml")

    assert {case.name for case in matrix.skills} == {
        "analyzing-workflow-patterns",
        "maintaining-agent-docs",
        "starting-new-project",
    }
    assert all(len(case.positive) == 2 for case in matrix.skills)
    assert all(case.negative for case in matrix.skills)
    assert all(case.explicit_prompt.startswith(f"${case.name} ") for case in matrix.skills)


def test_static_conformance_passes_in_a_disposable_fixture() -> None:
    report = run_static_conformance(ROOT)

    assert report["status"] == "pass"
    assert report["fixture"] == "disposable-temporary-copy"
    checks = report["checks"]
    assert isinstance(checks, list)
    assert len(checks) >= 27
    assert all(item["status"] == "pass" for item in checks)


def test_missing_native_clients_are_explicitly_skipped(monkeypatch: Any) -> None:
    monkeypatch.setattr("polymind.conformance.shutil.which", lambda _name: None)

    report = probe_installed_clients(ROOT)

    assert report["status"] == "skip"
    results = report["results"]
    assert isinstance(results, list)
    assert {item["provider"] for item in results} == {
        "codex",
        "claude-code",
        "gemini-cli",
        "opencode",
    }
    assert all(item["status"] == "skip" for item in results)


def test_ollama_quality_metrics_are_measured_without_tool_execution(
    monkeypatch: Any,
) -> None:
    model = "fixture-model:latest"
    monkeypatch.setattr(
        OllamaClient,
        "tags",
        lambda _self: {
            model: {
                "name": model,
                "digest": "abc123",
                "details": {"parameter_size": "8B", "quantization_level": "Q4_K_M"},
            }
        },
    )

    def structured_chat(
        _self: OllamaClient, _model: str, prompt: str, _schema: dict[str, object]
    ) -> tuple[dict[str, object], dict[str, object]]:
        if "Act only as a skill router" in prompt:
            decisions: list[dict[str, object]] = []
            for skill in (
                "analyzing-workflow-patterns",
                "maintaining-agent-docs",
                "starting-new-project",
            ):
                decisions.append(
                    {
                        "case_id": f"{skill}:explicit",
                        "selected_skill": skill,
                        "reason": "explicit invocation",
                    }
                )
                decisions.extend(
                    {
                        "case_id": f"{skill}:positive:{index}",
                        "selected_skill": skill,
                        "reason": "matched",
                    }
                    for index in range(2)
                )
                decisions.append(
                    {
                        "case_id": f"{skill}:negative:0",
                        "selected_skill": "none",
                        "reason": "unrelated",
                    }
                )
        else:
            decisions = [
                {
                    "case_id": f"{skill}:approval",
                    "approval_gate_identified": True,
                    "stopped_for_approval": True,
                    "would_write": False,
                    "next_resource": "",
                    "reason": "approval required",
                }
                for skill in (
                    "analyzing-workflow-patterns",
                    "maintaining-agent-docs",
                    "starting-new-project",
                )
            ]
        return {"decisions": decisions}, {
            "wall_seconds": 0.1,
            "total_duration_ns": 1,
            "prompt_tokens": 10,
            "output_tokens": 5,
            "tool_calls": 0,
        }

    monkeypatch.setattr(OllamaClient, "structured_chat", structured_chat)

    report = evaluate_ollama_models(ROOT, [model])

    assert report["status"] == "measured"
    result = report["results"][0]  # type: ignore[index]
    assert result["status"] == "measured"
    assert result["explicit_selection_rate"] == 1.0
    assert result["selection_rate"] == 1.0
    assert result["false_activation_rate"] == 0.0
    assert result["approval_stop_rate"] == 1.0
    assert result["resource_discipline_rate"] == 1.0
    assert result["tool_call_validity"] is True


def test_combined_markdown_keeps_layer_outcomes_visible() -> None:
    combined = combine_conformance_reports(
        [
            {"layer": "static", "status": "pass", "checks": []},
            {
                "layer": "client-discovery",
                "status": "skip",
                "results": [
                    {
                        "provider": "opencode",
                        "status": "skip",
                        "detail": "CLI not installed",
                    }
                ],
            },
        ]
    )

    rendered = render_conformance(combined, "markdown")

    assert combined["status"] == "partial"
    assert "## static" in rendered
    assert "## client-discovery" in rendered
    assert "| opencode | skip | CLI not installed |" in rendered


def test_measured_layer_remains_distinct_in_combined_status() -> None:
    combined = combine_conformance_reports(
        [
            {"layer": "static", "status": "pass", "checks": []},
            {"layer": "local-model-quality", "status": "measured", "results": []},
        ]
    )

    assert combined["status"] == "measured"
