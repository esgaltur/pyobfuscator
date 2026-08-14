"""Tests for the reproducible adversarial security evaluation."""

from pathlib import Path

from benchmarks.security_evaluation import (
    DEFAULT_FIXTURES,
    DEFAULT_PROFILES,
    aggregate_results,
    evaluate_trial,
)


def test_aggregate_results_reports_observed_attack_rates() -> None:
    fixture = DEFAULT_FIXTURES[0]
    results = [
        {
            "fixture": fixture.name,
            "normal_execution": {"passed": True},
            "static_attack": {
                "recovered_canaries": [],
                "recovered_identifiers": [],
            },
            "dynamic_attack": {
                "code_object_captured": True,
                "recovered_canaries": list(fixture.canaries),
                "recovered_identifiers": [],
            },
        }
    ]

    aggregate = aggregate_results(results, [fixture])

    assert aggregate["normal_execution_passed"]["rate"] == 1.0
    assert aggregate["static_canary_recovery"]["rate"] == 0.0
    assert aggregate["static_identifier_recovery"]["rate"] == 0.0
    assert aggregate["dynamic_code_object_capture"]["rate"] == 1.0
    assert aggregate["dynamic_canary_recovery"]["rate"] == 1.0
    assert aggregate["dynamic_identifier_recovery"]["rate"] == 0.0


def test_default_artifact_is_measured_by_real_dynamic_attack(tmp_path: Path) -> None:
    fixture = DEFAULT_FIXTURES[0]

    result = evaluate_trial(
        fixture=fixture,
        profile=DEFAULT_PROFILES[0],
        trial_number=1,
        workspace=tmp_path,
    )

    assert result["normal_execution"]["passed"] is True
    assert result["static_attack"]["recovered_canaries"] == []
    assert result["dynamic_attack"]["anti_debug_policy_bypassed"] is True
    assert result["dynamic_attack"]["code_object_captured"] is True
    assert result["dynamic_attack"]["recovered_canaries"] == list(fixture.canaries)
