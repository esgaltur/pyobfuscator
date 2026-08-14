"""Tests for source-level evaluation heuristics."""

from pyobfuscator.analysis.red_team import RedTeamAnalyzer


def test_identifier_recovery_excludes_builtins_from_denominator() -> None:
    analyzer = RedTeamAnalyzer(
        "secret_name = 1\nprint(secret_name)\n",
        "renamed_value = 1\nprint(renamed_value)\n",
    )

    result = analyzer.analyze_identifier_recovery()

    assert result == {
        "recovery_rate": 0.0,
        "recovered_identifiers": [],
        "candidate_identifiers": 1,
    }


def test_identifier_recovery_reports_preserved_candidate() -> None:
    source = "public_result = 1\nprint(public_result)\n"
    analyzer = RedTeamAnalyzer(source, source)

    result = analyzer.analyze_identifier_recovery()

    assert result["recovery_rate"] == 1.0
    assert result["recovered_identifiers"] == ["public_result"]


def test_string_visibility_only_counts_strings_it_checks() -> None:
    analyzer = RedTeamAnalyzer(
        'print("tiny", "long secret value")\n',
        'print("tiny", decode_payload())\n',
    )

    result = analyzer.analyze_string_visibility()

    assert result["candidate_strings"] == 1
    assert result["leak_ratio"] == 0.0
    assert result["plain_text_leaks"] == []


def test_report_explicitly_rejects_security_score_interpretation() -> None:
    analyzer = RedTeamAnalyzer("value = 1\n", "renamed = 1\n")

    report = analyzer.get_heuristic_report()

    assert report["report_type"] == "development_heuristics"
    assert "do not measure security strength" in report["warning"]
    assert "overall_resistance_score" not in report
