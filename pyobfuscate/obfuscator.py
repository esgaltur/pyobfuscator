"""
Core obfuscation module with various transformation techniques.
"""

import ast
import base64
import random
import string
import zlib
import hashlib
from typing import Dict, Set, Optional, List
from pathlib import Path


class NameGenerator:
    """Generates obfuscated names for variables, functions, and classes."""

    def __init__(self, prefix: str = "_", style: str = "random"):
        self.prefix = prefix
        self.style = style
        self.counter = 0
        self.name_map: Dict[str, str] = {}
        self._used_names: Set[str] = set()

    def _generate_random_name(self, length: int = 8) -> str:
        """Generate a random alphanumeric name."""
        chars = string.ascii_letters + string.digits
        while True:
            # First char must be letter or underscore
            name = self.prefix + random.choice(string.ascii_letters)
            name += ''.join(random.choices(chars, k=length - 1))
            if name not in self._used_names:
                self._used_names.add(name)
                return name

    def _generate_hex_name(self) -> str:
        """Generate a hex-based name."""
        self.counter += 1
        name = f"{self.prefix}x{hex(self.counter)[2:]}"
        self._used_names.add(name)
        return name

    def _generate_hash_name(self, original: str) -> str:
        """Generate a hash-based name from the original."""
        h = hashlib.md5(original.encode()).hexdigest()[:8]
        name = f"{self.prefix}{h}"
        if name in self._used_names:
            name = f"{name}_{self.counter}"
            self.counter += 1
        self._used_names.add(name)
        return name

    def get_name(self, original: str) -> str:
        """Get or create an obfuscated name for the original identifier."""
        if original in self.name_map:
            return self.name_map[original]

        if self.style == "random":
            new_name = self._generate_random_name()
        elif self.style == "hex":
            new_name = self._generate_hex_name()
        elif self.style == "hash":
            new_name = self._generate_hash_name(original)
        else:
            new_name = self._generate_random_name()

        self.name_map[original] = new_name
        return new_name


class NameObfuscator(ast.NodeTransformer):
    """AST transformer that renames variables, functions, and classes."""

    # Names that should never be obfuscated
    BUILTINS = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
    RESERVED = {
        # Python keywords and special names
        'self', 'cls', 'super', '__init__', '__new__', '__del__', '__repr__',
        '__str__', '__bytes__', '__format__', '__lt__', '__le__', '__eq__',
        '__ne__', '__gt__', '__ge__', '__hash__', '__bool__', '__getattr__',
        '__getattribute__', '__setattr__', '__delattr__', '__dir__', '__get__',
        '__set__', '__delete__', '__slots__', '__init_subclass__', '__set_name__',
        '__instancecheck__', '__subclasscheck__', '__class_getitem__', '__call__',
        '__len__', '__length_hint__', '__getitem__', '__setitem__', '__delitem__',
        '__missing__', '__iter__', '__reversed__', '__contains__', '__add__',
        '__sub__', '__mul__', '__matmul__', '__truediv__', '__floordiv__',
        '__mod__', '__divmod__', '__pow__', '__lshift__', '__rshift__', '__and__',
        '__xor__', '__or__', '__neg__', '__pos__', '__abs__', '__invert__',
        '__complex__', '__int__', '__float__', '__index__', '__round__',
        '__trunc__', '__floor__', '__ceil__', '__enter__', '__exit__',
        '__await__', '__aiter__', '__anext__', '__aenter__', '__aexit__',
        '__name__', '__doc__', '__qualname__', '__module__', '__defaults__',
        '__code__', '__globals__', '__dict__', '__closure__', '__annotations__',
        '__kwdefaults__', '__builtins__', '__file__', '__cached__', '__loader__',
        '__package__', '__spec__', '__path__', '__all__', '__version__',
        'True', 'False', 'None', 'Exception', 'BaseException',
        # Built-in functions that must be preserved
        'print', 'range', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict',
        'tuple', 'set', 'frozenset', 'bytes', 'bytearray', 'type', 'object',
        'open', 'input', 'abs', 'all', 'any', 'ascii', 'bin', 'callable',
        'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dir', 'divmod',
        'enumerate', 'eval', 'exec', 'filter', 'format', 'getattr', 'globals',
        'hasattr', 'hash', 'help', 'hex', 'id', 'isinstance', 'issubclass',
        'iter', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'oct',
        'ord', 'pow', 'property', 'repr', 'reversed', 'round', 'setattr',
        'slice', 'sorted', 'staticmethod', 'sum', 'super', 'vars', 'zip',
        '__import__', 'breakpoint',
        # Common module names
        'os', 'sys', 'typing', 'pathlib', 'json', 'logging', 're',
        'collections', 'functools', 'itertools', 'datetime', 'time',
        'threading', 'multiprocessing', 'subprocess', 'asyncio',
        # pytest and common test names
        'pytest', 'unittest', 'test', 'setup', 'teardown',
    }

    def __init__(self, name_generator: NameGenerator, exclude_names: Optional[Set[str]] = None):
        self.name_gen = name_generator
        self.exclude = self.RESERVED | self.BUILTINS | (exclude_names or set())
        self.local_scopes: List[Set[str]] = []
        self.global_names: Set[str] = set()
        self.import_names: Set[str] = set()

    def _should_rename(self, name: str) -> bool:
        """Check if a name should be obfuscated."""
        if name.startswith('__') and name.endswith('__'):
            return False
        if name in self.exclude:
            return False
        if name in self.import_names:
            return False
        return True

    def _rename(self, name: str) -> str:
        """Get the obfuscated version of a name."""
        if self._should_rename(name):
            return self.name_gen.get_name(name)
        return name

    def visit_Import(self, node: ast.Import) -> ast.Import:
        """Track imported names."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            self.import_names.add(name)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """Track imported names."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name != '*':
                self.import_names.add(name)
        return node

    def _rename_arguments(self, args: ast.arguments) -> None:
        """Rename all function arguments."""
        for arg in args.args:
            if arg.arg not in ('self', 'cls'):
                arg.arg = self._rename(arg.arg)
        for arg in args.posonlyargs:
            if arg.arg not in ('self', 'cls'):
                arg.arg = self._rename(arg.arg)
        for arg in args.kwonlyargs:
            arg.arg = self._rename(arg.arg)
        if args.vararg:
            args.vararg.arg = self._rename(args.vararg.arg)
        if args.kwarg:
            args.kwarg.arg = self._rename(args.kwarg.arg)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Rename function definitions."""
        # Rename the function name
        node.name = self._rename(node.name)
        # Rename arguments
        self._rename_arguments(node.args)
        # Visit child nodes
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Rename async function definitions."""
        node.name = self._rename(node.name)
        self._rename_arguments(node.args)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Rename class definitions."""
        node.name = self._rename(node.name)
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Rename variable references."""
        node.id = self._rename(node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        """Visit attributes but don't rename them (could be external API)."""
        self.generic_visit(node)
        return node


class StringObfuscator(ast.NodeTransformer):
    """AST transformer that obfuscates string literals."""

    def __init__(self, method: str = "base64"):
        self.method = method
        self._in_fstring = False  # Track if we're inside an f-string

    def _encode_string(self, s: str) -> ast.Call:
        """Create an AST node that decodes the obfuscated string at runtime."""
        if self.method == "base64":
            encoded = base64.b64encode(s.encode('utf-8')).decode('ascii')
            # __import__('base64').b64decode('...').decode('utf-8')
            return ast.Call(
                func=ast.Attribute(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Call(
                                func=ast.Name(id='__import__', ctx=ast.Load()),
                                args=[ast.Constant(value='base64')],
                                keywords=[]
                            ),
                            attr='b64decode',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=encoded)],
                        keywords=[]
                    ),
                    attr='decode',
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value='utf-8')],
                keywords=[]
            )
        elif self.method == "hex":
            encoded = s.encode('utf-8').hex()
            # bytes.fromhex('...').decode('utf-8')
            return ast.Call(
                func=ast.Attribute(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='bytes', ctx=ast.Load()),
                            attr='fromhex',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=encoded)],
                        keywords=[]
                    ),
                    attr='decode',
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value='utf-8')],
                keywords=[]
            )
        elif self.method == "xor":
            key = random.randint(1, 255)
            encoded = bytes([b ^ key for b in s.encode('utf-8')])
            # bytes([b ^ key for b in encoded]).decode('utf-8')
            return ast.Call(
                func=ast.Attribute(
                    value=ast.Call(
                        func=ast.Name(id='bytes', ctx=ast.Load()),
                        args=[
                            ast.ListComp(
                                elt=ast.BinOp(
                                    left=ast.Name(id='b', ctx=ast.Load()),
                                    op=ast.BitXor(),
                                    right=ast.Constant(value=key)
                                ),
                                generators=[
                                    ast.comprehension(
                                        target=ast.Name(id='b', ctx=ast.Store()),
                                        iter=ast.Constant(value=encoded),
                                        ifs=[],
                                        is_async=0
                                    )
                                ]
                            )
                        ],
                        keywords=[]
                    ),
                    attr='decode',
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value='utf-8')],
                keywords=[]
            )
        return ast.Constant(value=s)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:
        """Don't modify f-strings - they have special handling requirements."""
        # Skip f-strings entirely to avoid AST issues
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Obfuscate string constants."""
        if isinstance(node.value, str) and len(node.value) > 2:
            # Don't obfuscate very short strings
            return self._encode_string(node.value)
        return node


class CodeCompressor:
    """Compresses and encodes Python code for obfuscation."""

    @staticmethod
    def compress_code(code: str) -> str:
        """Compress code using zlib and base64 encode it."""
        compressed = zlib.compress(code.encode('utf-8'), level=9)
        encoded = base64.b64encode(compressed).decode('ascii')
        return encoded

    @staticmethod
    def create_loader(encoded_code: str) -> str:
        """Create a loader script that decompresses and executes the code."""
        return f'''# -*- coding: utf-8 -*-
import zlib as _z
import base64 as _b
exec(_z.decompress(_b.b64decode({repr(encoded_code)})).decode('utf-8'))
'''


class Obfuscator:
    """Main obfuscator class that combines all obfuscation techniques."""

    def __init__(
        self,
        rename_variables: bool = True,
        rename_functions: bool = True,
        rename_classes: bool = True,
        obfuscate_strings: bool = True,
        compress_code: bool = False,
        remove_comments: bool = True,
        remove_docstrings: bool = True,
        name_style: str = "random",
        string_method: str = "base64",
        exclude_names: Optional[Set[str]] = None
    ):
        self.rename_variables = rename_variables
        self.rename_functions = rename_functions
        self.rename_classes = rename_classes
        self.obfuscate_strings = obfuscate_strings
        self.compress_code = compress_code
        self.remove_comments = remove_comments
        self.remove_docstrings = remove_docstrings
        self.name_style = name_style
        self.string_method = string_method
        self.exclude_names = exclude_names or set()

        self.name_generator = NameGenerator(style=name_style)

    def _remove_docstrings(self, tree: ast.AST) -> ast.AST:
        """Remove docstrings from the AST."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    node.body = node.body[1:] or [ast.Pass()]
        return tree

    def obfuscate_source(self, source: str) -> str:
        """Obfuscate Python source code."""
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Failed to parse source code: {e}")

        # Remove docstrings first
        if self.remove_docstrings:
            tree = self._remove_docstrings(tree)

        # Apply name obfuscation
        if self.rename_variables or self.rename_functions or self.rename_classes:
            name_obfuscator = NameObfuscator(
                self.name_generator,
                exclude_names=self.exclude_names
            )
            tree = name_obfuscator.visit(tree)

        # Fix missing line numbers
        ast.fix_missing_locations(tree)

        # Apply string obfuscation
        if self.obfuscate_strings:
            string_obfuscator = StringObfuscator(method=self.string_method)
            tree = string_obfuscator.visit(tree)
            ast.fix_missing_locations(tree)

        # Convert AST back to source
        try:
            obfuscated = ast.unparse(tree)
        except Exception as e:
            raise ValueError(f"Failed to generate obfuscated code: {e}")

        # Compress if requested
        if self.compress_code:
            encoded = CodeCompressor.compress_code(obfuscated)
            obfuscated = CodeCompressor.create_loader(encoded)

        return obfuscated

    def obfuscate_file(self, input_path: Path, output_path: Optional[Path] = None) -> str:
        """Obfuscate a Python file."""
        input_path = Path(input_path)

        with open(input_path, 'r', encoding='utf-8') as f:
            source = f.read()

        obfuscated = self.obfuscate_source(source)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(obfuscated)

        return obfuscated

    def obfuscate_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Obfuscate all Python files in a directory."""
        import fnmatch

        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', 'test_*', '*_test.py']

        results = {}
        pattern = '**/*.py' if recursive else '*.py'

        for py_file in input_dir.glob(pattern):
            # Check exclusions
            relative_path = py_file.relative_to(input_dir)
            skip = False
            for pattern_str in exclude_patterns:
                if fnmatch.fnmatch(str(relative_path), pattern_str):
                    skip = True
                    break
                if fnmatch.fnmatch(py_file.name, pattern_str):
                    skip = True
                    break

            if skip:
                continue

            output_path = output_dir / relative_path

            try:
                self.obfuscate_file(py_file, output_path)
                results[str(relative_path)] = "success"
            except Exception as e:
                results[str(relative_path)] = f"error: {e}"

        return results
