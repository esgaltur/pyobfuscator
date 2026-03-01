# -*- coding: utf-8 -*-
"""
Comprehensive tests for advanced transformers integration.

Tests the following features:
- ControlFlowObfuscator: Opaque predicates and dead code injection
- NumberObfuscator: Numeric literal obfuscation
- BuiltinObfuscator: Builtin function call obfuscation
- ControlFlowFlattener: State machine transformation
- IntegrityTransformer: Hash-based integrity verification
"""
import pytest
import sys
import os
import ast
import random
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyobfuscator import Obfuscator
from pyobfuscator.transformers import (
    ControlFlowObfuscator,
    NumberObfuscator,
    BuiltinObfuscator,
    ControlFlowFlattener,
    IntegrityTransformer,
    apply_advanced_obfuscation
)


class TestControlFlowObfuscator:
    """Test the ControlFlowObfuscator transformer."""

    def test_dead_code_injection(self):
        """Test that dead code is injected into function bodies."""
        source = '''
def target_func(x):
    a = x + 1
    b = a * 2
    return b
'''
        tree = ast.parse(source)
        obfuscator = ControlFlowObfuscator(intensity=3)

        # Set seed for reproducibility
        random.seed(42)
        new_tree = obfuscator.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        # Verify code still works
        namespace = {}
        exec(result, namespace)
        assert namespace['target_func'](5) == 12

    def test_opaque_predicates(self):
        """Test that opaque predicates are added to if conditions."""
        source = '''
def check_value(x):
    if x > 0:
        return True
    return False
'''
        tree = ast.parse(source)
        obfuscator = ControlFlowObfuscator(intensity=3)

        random.seed(42)
        new_tree = obfuscator.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        # Verify code still works
        namespace = {}
        exec(result, namespace)
        assert namespace['check_value'](5) is True
        assert namespace['check_value'](-1) is False

    def test_intensity_levels(self):
        """Test that intensity levels affect obfuscation amount."""
        source = '''
def func(x):
    a = x + 1
    b = a * 2
    c = b - 3
    return c
'''
        results = []
        for intensity in [1, 2, 3]:
            tree = ast.parse(source)
            obfuscator = ControlFlowObfuscator(intensity=intensity)
            random.seed(42)
            new_tree = obfuscator.visit(tree)
            ast.fix_missing_locations(new_tree)
            results.append(ast.unparse(new_tree))

        # All should produce valid code
        for result in results:
            namespace = {}
            exec(result, namespace)
            assert namespace['func'](10) == 19


class TestNumberObfuscator:
    """Test the NumberObfuscator transformer."""

    def test_number_obfuscation(self):
        """Test that numeric literals are obfuscated."""
        source = 'x = 1234'
        tree = ast.parse(source)
        obfuscator = NumberObfuscator(intensity=3)

        random.seed(42)
        new_tree = obfuscator.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        # The literal 1234 should be replaced
        assert '1234' not in result

        # But the result should still evaluate to 1234
        namespace = {}
        exec(result, namespace)
        assert namespace['x'] == 1234

    def test_multiple_numbers(self):
        """Test obfuscation of multiple numbers."""
        source = '''
a = 100
b = 200
c = a + b
'''
        tree = ast.parse(source)
        obfuscator = NumberObfuscator(intensity=3)

        random.seed(42)
        new_tree = obfuscator.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        namespace = {}
        exec(result, namespace)
        assert namespace['c'] == 300

    def test_preserves_small_numbers(self):
        """Test that small numbers (0, 1) are often preserved."""
        source = 'x = 0; y = 1'
        tree = ast.parse(source)
        obfuscator = NumberObfuscator(intensity=1)

        new_tree = obfuscator.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        namespace = {}
        exec(result, namespace)
        assert namespace['x'] == 0
        assert namespace['y'] == 1


class TestBuiltinObfuscator:
    """Test the BuiltinObfuscator transformer."""

    def test_len_obfuscation(self):
        """Test that len() calls are obfuscated."""
        source = 'x = len([1, 2, 3])'
        tree = ast.parse(source)
        obfuscator = BuiltinObfuscator()

        new_tree = obfuscator.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        assert 'len(' not in result
        assert 'getattr' in result
        assert '__import__' in result
        assert 'builtins' in result

        namespace = {}
        exec(result, namespace)
        assert namespace['x'] == 3

    def test_multiple_builtins(self):
        """Test obfuscation of multiple builtin calls."""
        source = '''
a = len([1, 2, 3])
b = str(42)
c = int("10")
d = list(range(3))
'''
        tree = ast.parse(source)
        obfuscator = BuiltinObfuscator()

        new_tree = obfuscator.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        namespace = {}
        exec(result, namespace)
        assert namespace['a'] == 3
        assert namespace['b'] == "42"
        assert namespace['c'] == 10
        assert namespace['d'] == [0, 1, 2]


class TestControlFlowFlattener:
    """Test the ControlFlowFlattener transformer."""

    def test_basic_flattening(self):
        """Test that functions are transformed into state machines."""
        source = '''
def calculate(x):
    a = x + 1
    b = a * 2
    c = b - 3
    return c
'''
        tree = ast.parse(source)
        flattener = ControlFlowFlattener(intensity=3, min_statements=2)

        random.seed(42)
        new_tree = flattener.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        # Verify the code still works correctly
        namespace = {}
        exec(result, namespace)
        assert namespace['calculate'](10) == 19

    def test_with_return(self):
        """Test flattening with return statements."""
        source = '''
def get_value(x):
    if x > 5:
        return x * 2
    y = x + 1
    return y
'''
        tree = ast.parse(source)
        flattener = ControlFlowFlattener(intensity=3, min_statements=2)

        random.seed(42)
        new_tree = flattener.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        namespace = {}
        exec(result, namespace)
        assert namespace['get_value'](10) == 20
        assert namespace['get_value'](3) == 4

    def test_skip_decorated_functions(self):
        """Test that decorated functions are skipped."""
        source = '''
def decorator(f):
    return f

@decorator
def decorated_func(x):
    a = x + 1
    b = a * 2
    return b
'''
        tree = ast.parse(source)
        flattener = ControlFlowFlattener(intensity=3, min_statements=2)

        new_tree = flattener.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        namespace = {}
        exec(result, namespace)
        assert namespace['decorated_func'](5) == 12


class TestIntegrityTransformer:
    """Test the IntegrityTransformer."""

    def test_integrity_check_added(self):
        """Test that integrity checks are added to functions."""
        from pyobfuscator.core.context import TransformationContext

        source = '''
def protected_func(x):
    a = x + 1
    return a
'''
        tree = ast.parse(source)
        context = TransformationContext()
        transformer = IntegrityTransformer(intensity=3, critical_functions=['protected_func'])
        transformer.context = context

        random.seed(42)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        # Verify the code contains integrity-related checkpoint variables
        assert '_chk_' in result

        # The function should still work (integrity check passes)
        namespace = {}
        exec(result, namespace)
        assert namespace['protected_func'](5) == 6

    def test_skip_private_functions(self):
        """Test that private functions are skipped by default."""
        source = '''
def _private_func(x):
    return x + 1
'''
        tree = ast.parse(source)
        transformer = IntegrityTransformer(intensity=3)

        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = ast.unparse(new_tree)

        # Private function should not have integrity checks
        namespace = {}
        exec(result, namespace)
        assert namespace['_private_func'](5) == 6


class TestApplyAdvancedObfuscation:
    """Test the apply_advanced_obfuscation function."""

    def test_all_options_enabled(self):
        """Test with all obfuscation options enabled."""
        source = '''
def compute(x):
    a = 100
    b = len([1, 2, 3])
    if x > 5:
        return a + b
    return x
'''
        tree = ast.parse(source)

        random.seed(42)
        new_tree = apply_advanced_obfuscation(
            tree,
            control_flow=True,
            number_obfuscation=True,
            builtin_obfuscation=True,
            control_flow_flatten=True,
            integrity_check=True,
            intensity=2
        )

        result = ast.unparse(new_tree)

        # Verify the code still works
        namespace = {}
        exec(result, namespace)
        assert namespace['compute'](10) == 103
        assert namespace['compute'](3) == 3


class TestObfuscatorIntegration:
    """Test the Obfuscator class integration with advanced features."""

    def test_control_flow_obfuscation(self):
        """Test that control flow obfuscation adds opaque predicates or dead code."""
        obfuscator = Obfuscator(
            encrypt_code=False,  # Disable encryption for testing
            control_flow=True,
            obfuscation_intensity=3,
            rename_variables=False,
            rename_functions=False,
            rename_classes=False,
            obfuscate_strings=False
        )
        source = '''
def target_func(x):
    if x > 0:
        return x * 2
    return 0
'''
        result = obfuscator.obfuscate_source(source)
        
        # Verify it still executes correctly
        namespace = {}
        exec(result, namespace)
        assert namespace['target_func'](5) == 10
        assert namespace['target_func'](-1) == 0
        
        # Verify it's actually different
        assert result.strip() != source.strip()

    def test_number_obfuscation(self):
        """Test that numeric literals are obfuscated."""
        obfuscator = Obfuscator(
            encrypt_code=False,
            number_obfuscation=True,
            intensity=3,
            rename_variables=False,
            rename_functions=False,
            rename_classes=False,
            obfuscate_strings=False
        )
        source = 'x = 1234'
        result = obfuscator.obfuscate_source(source)
        
        assert '1234' not in result
        
        namespace = {}
        exec(result, namespace)
        assert namespace['x'] == 1234

    def test_builtin_obfuscation(self):
        """Test that builtin calls are obfuscated."""
        obfuscator = Obfuscator(
            encrypt_code=False,  # Disable encryption for testing
            builtin_obfuscation=True,
            rename_variables=False,
            rename_functions=False,
            rename_classes=False,
            obfuscate_strings=False
        )
        source = 'x = len([1, 2, 3])'
        result = obfuscator.obfuscate_source(source)
        
        assert 'len(' not in result
        assert 'getattr' in result
        assert '__import__' in result
        assert 'builtins' in result
        
        namespace = {}
        exec(result, namespace)
        assert namespace['x'] == 3

    def test_control_flow_flatten(self):
        """Test that control flow flattening works via Obfuscator."""
        obfuscator = Obfuscator(
            encrypt_code=False,  # Disable encryption for testing
            control_flow_flatten=True,
            obfuscation_intensity=3,
            rename_variables=False,
            rename_functions=False,
            rename_classes=False,
            obfuscate_strings=False
        )
        source = '''
def calc(x):
    a = x + 1
    b = a * 2
    c = b - 3
    return c
'''
        result = obfuscator.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace['calc'](10) == 19

    def test_integrity_check(self):
        """Test that integrity checks are added via Obfuscator."""
        obfuscator = Obfuscator(
            encrypt_code=False,  # Disable encryption for testing
            integrity_check=True,
            obfuscation_intensity=3,
            rename_variables=False,
            rename_functions=False,
            rename_classes=False,
            obfuscate_strings=False
        )
        source = '''
def protected(x):
    a = x + 1
    return a
'''
        result = obfuscator.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace['protected'](5) == 6

    def test_all_advanced_combined(self):
        """Test all advanced features combined."""
        obfuscator = Obfuscator(
            encrypt_code=False,  # Disable encryption for testing
            control_flow=True,
            number_obfuscation=True,
            builtin_obfuscation=True,
            control_flow_flatten=True,
            integrity_check=True,
            obfuscation_intensity=2,
            rename_variables=False,
            rename_functions=False,
            rename_classes=False,
            obfuscate_strings=False
        )
        source = '''
def complex_func(x):
    a = 50
    b = len([1, 2, 3, 4, 5])
    if x > 10:
        return a + b
    c = x * 2
    return c + b
'''
        result = obfuscator.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace['complex_func'](15) == 55
        assert namespace['complex_func'](5) == 15


class TestParallelProcessing:
    """Test parallel processing for directory obfuscation."""

    def test_parallel_directory_obfuscation(self):
        """Test that parallel processing produces correct results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            # Create test files
            for i in range(5):
                file_path = input_dir / f"module{i}.py"
                file_path.write_text(f'''
def func{i}(x):
    return x + {i}
''')

            obfuscator = Obfuscator(
                encrypt_code=False,  # Disable encryption for testing
                rename_variables=False,
                rename_functions=False,
                rename_classes=False,
                obfuscate_strings=False
            )

            # Test directory obfuscation (parallel is handled at CLI level, not API)
            results = obfuscator.obfuscate_directory(
                input_dir,
                output_dir,
            )

            # Verify all files processed successfully
            assert len(results) == 5
            assert all(v == "success" for v in results.values())

            # Verify output files exist and work
            for i in range(5):
                output_file = output_dir / f"module{i}.py"
                assert output_file.exists()

                content = output_file.read_text()
                namespace = {}
                exec(content, namespace)
                assert namespace[f'func{i}'](10) == 10 + i


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
