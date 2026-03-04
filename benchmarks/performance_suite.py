# -*- coding: utf-8 -*-
"""
PyObfuscator Performance & Security Benchmarking Suite.

Measures the overhead of various obfuscation layers on different workloads.
"""

import time
import timeit
import ast
import tracemalloc
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Callable
import statistics

from pyobfuscator import Obfuscator

# Define Standard Workloads
WORKLOADS = {
    "computational": """
def workload(n=1000):
    res = 0
    for i in range(n):
        for j in range(n):
            res += (i * j) // 2
    return res
result = workload()
""",
    "string_intensive": """
def workload(n=5000):
    s = ""
    for i in range(n):
        s += f"secret_key_{i}"
        if i % 100 == 0:
            s = s[10:] # Keep memory manageable
    return len(s)
result = workload()
""",
    "recursive": """
def workload(n=20):
    def fib(i):
        if i <= 1: return i
        return fib(i-1) + fib(i-2)
    return fib(n)
result = workload()
""",
    "object_oriented": """
class Processor:
    def __init__(self, val): self.val = val
    def process(self): return self.val * 2
def workload(n=10000):
    total = 0
    for i in range(n):
        p = Processor(i)
        total += p.process()
    return total
result = workload()
"""
}

class BenchmarkRunner:
    def __init__(self):
        self.results = {}

    def run_benchmark(self, name: str, source: str, config: Dict[str, Any], iterations: int = 5):
        """Runs a benchmark for a specific workload and config."""
        # 1. Obfuscate
        obfuscator = Obfuscator(**config, exclude_names={'result'})
        
        start_obf = time.perf_counter()
        try:
            obfuscated_source = obfuscator.obfuscate_source(source)
        except Exception as e:
            print(f"Obfuscation failed for {name}: {e}")
            return None
        end_obf = time.perf_counter()
        
        # 2. Measure Execution Time
        exec_times = []
        for _ in range(iterations):
            ns = {}
            t = timeit.timeit(lambda: exec(obfuscated_source, ns), number=1)
            exec_times.append(t)
            
        # 3. Measure Memory
        tracemalloc.start()
        ns = {}
        exec(obfuscated_source, ns)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 4. Measure Size
        original_size = len(source)
        obfuscated_size = len(obfuscated_source)
        
        return {
            "obfuscation_time": end_obf - start_obf,
            "exec_time_avg": statistics.mean(exec_times),
            "exec_time_std": statistics.stdev(exec_times) if len(exec_times) > 1 else 0,
            "peak_memory_kb": peak / 1024,
            "size_overhead_ratio": obfuscated_size / original_size
        }

    def execute_all(self):
        configs = {
            "Baseline (None)": {},
            "Basic (Rename)": {"rename_variables": True, "rename_functions": True, "obfuscate_strings": False},
            "Advanced (Polymorphic Strings)": {"rename_variables": True, "obfuscate_strings": True, "string_method": "polymorphic"},
            "Hardened (CFF + Strings)": {"rename_variables": True, "obfuscate_strings": True, "control_flow_flatten": True, "intensity": 3},
            "Maximum (All features)": {
                "rename_variables": True, "obfuscate_strings": True, "control_flow_flatten": True, 
                "number_obfuscation": True, "intensity": 3, "integrity_checks": True
            }
        }
        
        report = {}
        for workload_name, source in WORKLOADS.items():
            print(f"Benchmarking Workload: {workload_name}...")
            report[workload_name] = {}
            
            # Baseline (No obfuscation)
            t_baseline = timeit.timeit(lambda: exec(source, {}), number=10) / 10
            report[workload_name]["unprotected_avg_time"] = t_baseline
            
            for config_name, config in configs.items():
                print(f"  Testing Config: {config_name}...")
                res = self.run_benchmark(workload_name, source, config)
                if res:
                    res["slowdown_factor"] = res["exec_time_avg"] / t_baseline
                    report[workload_name][config_name] = res
                    
        self.results = report
        self.save_report()

    def save_report(self):
        with open("benchmarks/results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\nBenchmark results saved to benchmarks/results.json")

if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.execute_all()
