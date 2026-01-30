"""
Demo of PyArmor-style runtime protection with advanced security features.

Features demonstrated:
- AES-256-GCM encryption
- Anti-debugging detection
- Time-based license expiration
- Hardware/machine binding
- Domain lock
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscate.runtime_protection import RuntimeProtector, protect


def main():
    # Sample code to protect
    sample_code = '''
def greet(name):
    """Greet someone by name."""
    return f"Hello, {name}!"

def calculate(a, b, operation="add"):
    """Perform a calculation."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b if b != 0 else None
    return None

class Calculator:
    """A simple calculator class."""
    
    def __init__(self, initial_value=0):
        self.value = initial_value
    
    def add(self, x):
        self.value += x
        return self
    
    def subtract(self, x):
        self.value -= x
        return self
    
    def result(self):
        return self.value

# Main execution
if __name__ == "__main__":
    print(greet("World"))
    print(f"10 + 5 = {calculate(10, 5)}")
    print(f"10 * 5 = {calculate(10, 5, 'multiply')}")
    
    calc = Calculator(100)
    result = calc.add(50).subtract(30).result()
    print(f"Calculator result: {result}")
'''

    print("=" * 70)
    print("PyArmor-Style Runtime Protection Demo (v3 - Advanced)")
    print("=" * 70)

    # Get current machine ID for demonstration
    current_machine_id = RuntimeProtector.get_machine_id()
    print(f"\n[MACHINE INFO]")
    print(f"Current Machine ID: {current_machine_id}")

    print("\n[ORIGINAL CODE]")
    print("-" * 70)
    print(sample_code[:500] + "..." if len(sample_code) > 500 else sample_code)

    # === Demo 1: Basic Protection ===
    print("\n" + "=" * 70)
    print("Demo 1: Basic Protection (no restrictions)")
    print("=" * 70)

    protector = RuntimeProtector(
        license_info="demo-license",
        anti_debug=False  # Disable for demo execution
    )
    protected, runtime = protector.protect_source(sample_code, "demo.py")

    print("\n[PROTECTED CODE]")
    print(protected)

    # === Demo 2: Protection with Expiration ===
    print("\n" + "=" * 70)
    print("Demo 2: Protection with 30-day Expiration")
    print("=" * 70)

    protector_exp = RuntimeProtector(
        license_info="time-limited-license",
        expiration_date=datetime.now() + timedelta(days=30),
        anti_debug=False
    )
    protected_exp, _ = protector_exp.protect_source(sample_code, "demo_exp.py")
    print(f"Expires: {protector_exp.expiration_date}")
    print(protected_exp)

    # === Demo 3: Machine-Bound Protection ===
    print("\n" + "=" * 70)
    print("Demo 3: Machine-Bound Protection")
    print("=" * 70)

    protector_machine = RuntimeProtector(
        license_info="machine-bound-license",
        allowed_machines=[current_machine_id],  # Bind to current machine
        anti_debug=False
    )
    protected_machine, _ = protector_machine.protect_source(sample_code, "demo_machine.py")
    print(f"Allowed machines: {protector_machine.allowed_machines}")
    print(protected_machine)

    # === Demo 4: Full Protection (all features) ===
    print("\n" + "=" * 70)
    print("Demo 4: Full Protection (all features enabled)")
    print("=" * 70)

    protector_full = RuntimeProtector(
        license_info="full-protection-license",
        expiration_date=datetime.now() + timedelta(days=365),
        allowed_machines=[current_machine_id],
        anti_debug=True,  # Enable anti-debugging
        domain_lock=["localhost", "mycompany.com"]
    )
    protected_full, runtime_full = protector_full.protect_source(sample_code, "demo_full.py")
    print(f"Expires: {protector_full.expiration_date}")
    print(f"Allowed machines: {protector_full.allowed_machines}")
    print(f"Anti-debug: {protector_full.anti_debug}")
    print(f"Domain lock: {protector_full.domain_lock}")
    print(protected_full)

    # === Test Execution ===
    print("\n" + "=" * 70)
    print("[TESTING PROTECTED CODE EXECUTION]")
    print("=" * 70)

    # Write files to temp location
    output_dir = Path(__file__).parent.parent / "build" / "runtime_protected_demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write protected file (using basic protection for demo)
    protected_file = output_dir / "demo.py"
    with open(protected_file, 'w') as f:
        f.write(protected)

    # Write runtime module
    runtime_file = output_dir / f"pyobfuscate_runtime_{protector.runtime_id}.py"
    with open(runtime_file, 'w') as f:
        f.write(runtime)

    # Execute the protected code
    print(f"Files written to: {output_dir}")
    print("\nExecuting protected code...\n")

    # Add output dir to path and execute
    sys.path.insert(0, str(output_dir))
    try:
        exec(open(protected_file).read(), {'__name__': '__main__', '__file__': str(protected_file)})
    except Exception as e:
        print(f"Execution error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sys.path.remove(str(output_dir))

    print("\n" + "=" * 70)
    print("Protection complete!")
    print(f"Runtime ID: {protector.runtime_id}")
    print(f"Output directory: {output_dir}")
    print("\nNew Features in v3:")
    print("  - Anti-debugging detection")
    print("  - Time-based license expiration")
    print("  - Hardware/machine binding")
    print("  - Domain lock for web apps")
    print("  - Memory protection (sensitive data clearing)")


if __name__ == "__main__":
    main()
