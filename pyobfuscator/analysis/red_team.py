# -*- coding: utf-8 -*-
"""
Red Team Security Metrics for Skjol.

Provides development heuristics for comparing transformed source files.

These measurements are not a cryptographic strength estimate, an adversarial
success probability, or an independently validated security score.
"""

import ast
import builtins
import math
import re
from typing import Dict, Any, List, Set
from collections import Counter

class RedTeamAnalyzer:
    """
    Automated adversary that attempts to extract information from obfuscated source.
    """

    def __init__(self, original_source: str, obfuscated_source: str):
        self.original_source = original_source
        self.obfuscated_source = obfuscated_source
        self.original_tree = ast.parse(original_source)
        self.obfuscated_tree = ast.parse(obfuscated_source)

    @staticmethod
    def calculate_entropy(data: str) -> float:
        """Calculates Shannon Entropy of a string."""
        if not data:
            return 0.0
        entropy = 0
        for count in Counter(data).values():
            p = count / len(data)
            entropy -= p * math.log2(p)
        return entropy

    def analyze_identifier_recovery(self) -> Dict[str, Any]:
        """Measure how many renameable original identifiers remain visible."""
        original_names = {node.id for node in ast.walk(self.original_tree) if isinstance(node, ast.Name)}
        obfuscated_names = {node.id for node in ast.walk(self.obfuscated_tree) if isinstance(node, ast.Name)}

        builtin_names = set(dir(builtins))
        candidate_names = {
            name for name in original_names
            if len(name) > 3 and name not in builtin_names
        }
        recovered_names = candidate_names.intersection(obfuscated_names)
        recovery_rate = len(recovered_names) / len(candidate_names) if candidate_names else 0.0
        
        return {
            "recovery_rate": recovery_rate,
            "recovered_identifiers": sorted(recovered_names),
            "candidate_identifiers": len(candidate_names),
        }

    def analyze_string_visibility(self) -> Dict[str, Any]:
        """Checks if original sensitive strings are visible in plain text."""
        original_strings = {
            node.value for node in ast.walk(self.original_tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and len(node.value) > 5
        }
        
        found_strings = sorted(
            value for value in original_strings if value in self.obfuscated_source
        )

        leak_ratio = len(found_strings) / len(original_strings) if original_strings else 0.0
        
        return {
            "plain_text_leaks": found_strings,
            "leak_ratio": leak_ratio,
            "candidate_strings": len(original_strings),
        }

    def analyze_structural_complexity(self) -> Dict[str, Any]:
        """Measures the increase in control flow complexity."""
        def get_complexity(tree):
            # Simple cyclomatic complexity proxy: count of branches
            branches = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)):
                    branches += 1
            return branches

        orig_comp = get_complexity(self.original_tree)
        obf_comp = get_complexity(self.obfuscated_tree)
        
        dispersion = obf_comp / orig_comp if orig_comp > 0 else 1.0
        
        return {
            "original_complexity": orig_comp,
            "obfuscated_complexity": obf_comp,
            "dispersion_factor": dispersion,
        }

    def get_heuristic_report(self) -> Dict[str, Any]:
        """Generate source-level measurements with explicit limitations."""
        id_metrics = self.analyze_identifier_recovery()
        str_metrics = self.analyze_string_visibility()
        flow_metrics = self.analyze_structural_complexity()
        
        return {
            "report_type": "development_heuristics",
            "warning": (
                "These source-level heuristics do not measure security strength "
                "or resistance to a capable attacker."
            ),
            "identifier_protection": id_metrics,
            "string_protection": str_metrics,
            "control_flow_protection": flow_metrics,
            "entropy": self.calculate_entropy(self.obfuscated_source)
        }

    def get_resistance_report(self) -> Dict[str, Any]:
        """Compatibility alias for :meth:`get_heuristic_report`."""
        return self.get_heuristic_report()
