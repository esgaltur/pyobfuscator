# -*- coding: utf-8 -*-
"""
Red Team Security Metrics for PyObfuscator.

Quantifies the resistance of obfuscated code against automated static analysis.
"""

import ast
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
        """Checks how many original identifiers still exist in the output."""
        original_names = {node.id for node in ast.walk(self.original_tree) if isinstance(node, ast.Name)}
        obfuscated_names = {node.id for node in ast.walk(self.obfuscated_tree) if isinstance(node, ast.Name)}
        
        leaked_names = original_names.intersection(obfuscated_names)
        # Filter out builtins/common names that shouldn't be renamed
        real_leaks = {n for n in leaked_names if len(n) > 3}
        
        recovery_rate = len(real_leaks) / len(original_names) if original_names else 0
        
        return {
            "recovery_rate": recovery_rate,
            "leaked_identifiers": list(real_leaks),
            "score": 1.0 - recovery_rate
        }

    def analyze_string_visibility(self) -> Dict[str, Any]:
        """Checks if original sensitive strings are visible in plain text."""
        original_strings = {node.value for node in ast.walk(self.original_tree) 
                           if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        
        found_strings = []
        for s in original_strings:
            if len(s) > 5 and s in self.obfuscated_source:
                found_strings.append(s)
                
        leak_ratio = len(found_strings) / len(original_strings) if original_strings else 0
        
        return {
            "plain_text_leaks": found_strings,
            "leak_ratio": leak_ratio,
            "score": 1.0 - leak_ratio
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
            "score": min(1.0, dispersion / 5.0) # Normalized score (5x complexity is "perfect")
        }

    def get_resistance_report(self) -> Dict[str, Any]:
        """Generates a full Red Team Resistance Report."""
        id_metrics = self.analyze_identifier_recovery()
        str_metrics = self.analyze_string_visibility()
        flow_metrics = self.analyze_structural_complexity()
        
        # Weighted Security Score
        total_score = (
            id_metrics["score"] * 0.4 +
            str_metrics["score"] * 0.4 +
            flow_metrics["score"] * 0.2
        )
        
        return {
            "overall_resistance_score": total_score,
            "identifier_protection": id_metrics,
            "string_protection": str_metrics,
            "control_flow_protection": flow_metrics,
            "entropy": self.calculate_entropy(self.obfuscated_source)
        }
