# -*- coding: utf-8 -*-
"""
Red Team Security Resistance Evaluation.
"""

import json
from pyobfuscator import Obfuscator
from pyobfuscator.analysis.red_team import RedTeamAnalyzer

SOURCE = '''
SECRET_KEY = "SUPER_SECURE_API_KEY_2026"
DATABASE_URL = "postgresql://admin:password@localhost:5432/production"

def process_payment(amount, user_id):
    if amount > 1000:
        log_audit("high_value_transaction", user_id)
        apply_discount = True
    else:
        apply_discount = False
    
    final_amount = amount * 0.9 if apply_discount else amount
    return final_amount

def log_audit(event, user):
    print(f"Audit: {event} for {user}")

result = process_payment(1500, "user_99")
'''

def run_red_team_benchmark():
    tiers = {
        "Basic (Rename)": {"rename_variables": True, "rename_functions": True},
        "Advanced (Polymorphic Strings)": {"rename_variables": True, "obfuscate_strings": True, "string_method": "polymorphic"},
        "Hardened (CFF + Virtualization)": {
            "rename_variables": True, 
            "obfuscate_strings": True, 
            "control_flow_flatten": True, 
            "code_virtualization": True,
            "intensity": 3
        }
    }

    report = {}
    
    for tier_name, config in tiers.items():
        print(f"Red Teaming Tier: {tier_name}...")
        obf = Obfuscator(**config, exclude_names={'result'})
        obfuscated = obf.obfuscate_source(SOURCE)
        
        analyzer = RedTeamAnalyzer(SOURCE, obfuscated)
        report[tier_name] = analyzer.get_resistance_report()

    with open("benchmarks/security_resistance.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\nSecurity Resistance Report saved to benchmarks/security_resistance.json")

if __name__ == "__main__":
    run_red_team_benchmark()
