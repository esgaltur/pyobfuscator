# -*- coding: utf-8 -*-
"""
Core obfuscation module with various transformation techniques.

Features:
- Single file and directory obfuscation
- Cross-file obfuscation with shared name mapping (for multi-file projects)
- Method and class variable renaming (with attribute tracking)
- Variable, function, and class renaming
- String obfuscation (XOR, hex, base64)
- Code compression
"""

import ast
import base64
import random
import string
import zlib
import hashlib
from typing import Dict, Set, Optional, List, Tuple
from pathlib import Path

from .constants import ReservedNames, FrameworkPresets, DEFAULT_EXCLUDE_PATTERNS
from .transformers import (
    ControlFlowObfuscator,
    NumberObfuscator,
    BuiltinObfuscator,
    CommentRemover,
    ControlFlowFlattener,
    IntegrityTransformer
)
from .runtime_protection import RuntimeProtector


class NameGenerator:
    """
    Generates obfuscated names for variables, functions, and classes.

    Can be shared across multiple files to ensure consistent renaming
    for cross-file obfuscation.
    """

    def __init__(self, prefix: str = "_", style: str = "random"):
        self.prefix = prefix
        self.style = style
        self.counter = 0
        self.name_map: Dict[str, str] = {}
        self._used_names: Set[str] = set()
        # Track which names are methods/attributes for cross-reference
        self.method_names: Set[str] = set()
        self.class_attributes: Set[str] = set()

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

    def register_method(self, name: str) -> None:
        """Register a name as a method for attribute renaming."""
        self.method_names.add(name)

    def register_class_attribute(self, name: str) -> None:
        """Register a name as a class attribute for attribute renaming."""
        self.class_attributes.add(name)

    def is_known_member(self, name: str) -> bool:
        """Check if a name is a known method or class attribute."""
        return name in self.method_names or name in self.class_attributes

    def export_mapping(self) -> Dict[str, str]:
        """Export the name mapping for use in other files or debugging."""
        return dict(self.name_map)

    def import_mapping(self, mapping: Dict[str, str]) -> None:
        """Import a name mapping from another obfuscation session."""
        self.name_map.update(mapping)
        self._used_names.update(mapping.values())

    def pre_register_name(self, original: str) -> str:
        """
        Pre-register a name to ensure consistent mapping across files.

        This is used in the two-phase obfuscation approach:
        Phase 1: Collect all definitions and pre-register them
        Phase 2: Apply transformations using the complete mapping
        """
        return self.get_name(original)


class DefinitionCollector(ast.NodeVisitor):
    """
    AST visitor that collects all definitions (classes, functions, variables)
    without transforming the code.

    Used in Phase 1 of two-phase obfuscation to build the complete name mapping
    before any transformations are applied.
    """

    # Use reserved names from constants module
    RESERVED = ReservedNames.CORE_RESERVED | ReservedNames.BUILTINS
    BUILTINS = set(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))

    def __init__(self, name_generator: 'NameGenerator', exclude_names: Optional[Set[str]] = None):
        self.name_gen = name_generator
        self.exclude = self.RESERVED | self.BUILTINS | (exclude_names or set())
        self._in_class = False

    def _should_collect(self, name: str) -> bool:
        """Check if a name should be collected for obfuscation."""
        if name.startswith('__') and name.endswith('__'):
            return False
        if name in self.exclude:
            return False
        return True

    def _register(self, name: str) -> None:
        """Pre-register a name in the name generator."""
        if self._should_collect(name):
            self.name_gen.pre_register_name(name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Collect function/method definitions."""
        self._register(node.name)
        if self._in_class:
            self.name_gen.register_method(node.name)
        # Collect argument names
        for arg in node.args.args:
            if arg.arg not in ('self', 'cls'):
                self._register(arg.arg)
        for arg in node.args.posonlyargs:
            if arg.arg not in ('self', 'cls'):
                self._register(arg.arg)
        for arg in node.args.kwonlyargs:
            self._register(arg.arg)
        if node.args.vararg:
            self._register(node.args.vararg.arg)
        if node.args.kwarg:
            self._register(node.args.kwarg.arg)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Collect async function/method definitions."""
        self._register(node.name)
        if self._in_class:
            self.name_gen.register_method(node.name)
        # Collect argument names
        for arg in node.args.args:
            if arg.arg not in ('self', 'cls'):
                self._register(arg.arg)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Collect class definitions and enter class context."""
        self._register(node.name)

        prev_in_class = self._in_class
        self._in_class = True

        # Collect class-level attribute assignments
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        self._register(target.id)
                        self.name_gen.register_class_attribute(target.id)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                self._register(stmt.target.id)
                self.name_gen.register_class_attribute(stmt.target.id)

        self.generic_visit(node)
        self._in_class = prev_in_class

    def visit_Assign(self, node: ast.Assign) -> None:
        """Collect variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._register(target.id)
            elif isinstance(target, ast.Attribute):
                # self.x or cls.x
                if (isinstance(target.value, ast.Name) and
                    target.value.id in ('self', 'cls')):
                    self._register(target.attr)
                    self.name_gen.register_class_attribute(target.attr)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Collect annotated assignments."""
        if isinstance(node.target, ast.Name):
            self._register(node.target.id)
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        """Collect walrus operator assignments."""
        if isinstance(node.target, ast.Name):
            self._register(node.target.id)
        self.generic_visit(node)


class NameObfuscator(ast.NodeTransformer):
    """
    AST transformer that renames variables, functions, classes, methods,
    and class attributes.

    Features:
    - Tracks method definitions for safe attribute renaming
    - Tracks class attributes for consistent renaming
    - Preserves external API calls (module.function)
    - Handles self.attr and cls.attr patterns
    """

    # Use reserved names from constants module
    BUILTINS = set(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))
    RESERVED = ReservedNames.get_all_reserved()

    # Framework presets from constants module
    FRAMEWORK_PRESETS = {
        'pyside6': FrameworkPresets.PYSIDE6,
        'pyqt6': FrameworkPresets.PYQT6,
        'flask': FrameworkPresets.FLASK,
        'django': FrameworkPresets.DJANGO,
        'fastapi': FrameworkPresets.FASTAPI,
        'asyncio': FrameworkPresets.ASYNCIO,
        'click': FrameworkPresets.CLICK,
        'sqlalchemy': FrameworkPresets.SQLALCHEMY,
    }

    @classmethod
    def get_framework_excludes(cls, frameworks: List[str]) -> Set[str]:
        """Get all names to exclude for specified frameworks."""
        return FrameworkPresets.get_framework_excludes(frameworks)

    def __init__(self, name_generator: 'NameGenerator', exclude_names: Optional[Set[str]] = None,
                 rename_methods: bool = True, rename_attributes: bool = True):
        self.name_gen = name_generator
        self.exclude = self.RESERVED | self.BUILTINS | (exclude_names or set())
        self.local_scopes: List[Set[str]] = []
        self.global_names: Set[str] = set()
        self.import_names: Set[str] = set()
        self.rename_methods = rename_methods
        self.rename_attributes = rename_attributes
        # Track current class context for method/attribute detection
        self._in_class: bool = False
        self._current_class_name: Optional[str] = None
        # Track local variables defined with self.x = ... or cls.x = ...
        self._instance_attributes: Set[str] = set()

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
        """Track and optionally rename imported names for cross-file consistency."""
        for alias in node.names:
            original_name = alias.name
            if original_name == '*':
                continue

            # Check if this name was already obfuscated in a previous file
            # (exists in name_gen.name_map from cross-file processing)
            if original_name in self.name_gen.name_map:
                # Rename the import to match the obfuscated name
                obfuscated_name = self.name_gen.name_map[original_name]
                alias.name = obfuscated_name
                # If there's an asname, rename it too; otherwise don't set asname
                # so that the obfuscated name is used directly in local scope
                if alias.asname:
                    alias.asname = self._rename(alias.asname)
                # Don't add to import_names - the name in local scope is already
                # in name_gen.name_map and will be handled by visit_Name
            else:
                # Track as imported name to prevent renaming (external module)
                name = alias.asname if alias.asname else alias.name
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
        """Rename function/method definitions."""
        # Check if this is a method (inside a class)
        is_method = self._in_class

        if is_method and self.rename_methods:
            # Register as method for attribute renaming
            self.name_gen.register_method(node.name)
            node.name = self._rename(node.name)
        elif not is_method:
            # Regular function
            node.name = self._rename(node.name)

        # Rename arguments
        self._rename_arguments(node.args)
        # Visit child nodes
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Rename async function/method definitions."""
        is_method = self._in_class

        if is_method and self.rename_methods:
            self.name_gen.register_method(node.name)
            node.name = self._rename(node.name)
        elif not is_method:
            node.name = self._rename(node.name)

        self._rename_arguments(node.args)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Rename class definitions and track class context."""
        # Rename the class
        original_name = node.name
        node.name = self._rename(node.name)

        # Enter class context
        prev_in_class = self._in_class
        prev_class_name = self._current_class_name
        self._in_class = True
        self._current_class_name = original_name

        # First pass: collect class-level attribute assignments
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # Class variable like: my_var = value
                        self.name_gen.register_class_attribute(target.id)
                        self._instance_attributes.add(target.id)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                # Annotated class variable like: my_var: int = value
                self.name_gen.register_class_attribute(stmt.target.id)
                self._instance_attributes.add(stmt.target.id)

        # Visit child nodes
        self.generic_visit(node)

        # Exit class context
        self._in_class = prev_in_class
        self._current_class_name = prev_class_name

        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Rename variable references."""
        node.id = self._rename(node.id)
        return node

    def _is_dunder_attribute(self, name: str) -> bool:
        """Check if attribute is a dunder (double underscore) name."""
        return name.startswith('__') and name.endswith('__')

    def _is_self_or_cls_access(self, node: ast.Attribute) -> bool:
        """Check if this is a self.x or cls.x access pattern."""
        return (
            isinstance(node.value, ast.Name) and
            node.value.id in ('self', 'cls')
        )

    def _handle_self_cls_attribute(self, node: ast.Attribute, attr_name: str) -> None:
        """Handle attribute access on self or cls."""
        if not self._in_class:
            return

        # Track instance attribute assignments: self.x = ...
        if isinstance(node.ctx, ast.Store):
            self._instance_attributes.add(attr_name)
            self.name_gen.register_class_attribute(attr_name)

        # Rename if it's a known member or we're in the same class
        should_rename = (
            attr_name in self._instance_attributes or
            self.name_gen.is_known_member(attr_name)
        )
        if should_rename:
            node.attr = self._rename(attr_name)

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        """Rename attributes (methods and class variables) when safe."""
        # First, visit the value (the object being accessed)
        self.generic_visit(node)

        if not self.rename_attributes:
            return node

        attr_name = node.attr

        # Don't rename dunder attributes or excluded names
        if self._is_dunder_attribute(attr_name) or attr_name in self.exclude:
            return node

        if self._is_self_or_cls_access(node):
            self._handle_self_cls_attribute(node, attr_name)
        elif self.name_gen.is_known_member(attr_name):
            # obj.attr where attr is a known method/attribute we defined
            node.attr = self._rename(attr_name)

        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        """Track attribute assignments for later renaming."""
        # Check for self.x = ... pattern to track instance attributes
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if (isinstance(target.value, ast.Name) and
                    target.value.id in ('self', 'cls')):
                    self._instance_attributes.add(target.attr)
                    self.name_gen.register_class_attribute(target.attr)

        self.generic_visit(node)
        return node


class StringObfuscator(ast.NodeTransformer):
    """AST transformer that obfuscates string literals."""

    def __init__(self, method: str = "xor"):
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
    """
    Main obfuscator class that combines all obfuscation techniques.

    Features:
    - Variable, function, class, method, and attribute renaming
    - Cross-file obfuscation (share name_generator for multiple files)
    - String obfuscation (XOR, hex, base64)
    - Code compression
    - Docstring removal

    For cross-file obfuscation (multi-file projects):
        obfuscator = Obfuscator()
        obfuscator.obfuscate_file("file1.py", "out/file1.py")
        obfuscator.obfuscate_file("file2.py", "out/file2.py")  # Uses same name mapping
        # Or use obfuscate_directory() for automatic handling
    """

    # Available framework presets for easy configuration
    FRAMEWORK_PRESETS = NameObfuscator.FRAMEWORK_PRESETS

    def __init__(
        self,
        # Core protection - encryption (recommended)
        encrypt_code: bool = True,
        anti_debug: bool = True,
        # Name obfuscation options
        rename_variables: bool = True,
        rename_functions: bool = True,
        rename_classes: bool = True,
        rename_methods: bool = True,
        rename_attributes: bool = True,
        obfuscate_strings: bool = True,
        compress_code: bool = False,
        remove_comments: bool = True,
        remove_docstrings: bool = True,
        name_style: str = "random",
        string_method: str = "xor",
        exclude_names: Optional[Set[str]] = None,
        name_generator: Optional[NameGenerator] = None,
        frameworks: Optional[List[str]] = None,
        preserve_public_api: bool = False,
        entry_points: Optional[List[str]] = None,
        control_flow: bool = False,
        number_obfuscation: bool = False,
        builtin_obfuscation: bool = False,
        control_flow_flatten: bool = False,
        integrity_check: bool = False,
        obfuscation_intensity: int = 1,
        # Encryption/Protection options
        license_info: str = "Protected by PyObfuscator",
        encryption_key: Optional[bytes] = None,
        expiration_date: Optional['datetime'] = None,
        allowed_machines: Optional[List[str]] = None
    ):
        """
        Initialize the obfuscator.

        CORE PROTECTION (Recommended - enabled by default):
            encrypt_code: Encrypt the code with AES-256-GCM (hides real code)
            anti_debug: Enable anti-debugging protection

        Name Obfuscation (supplementary):
            rename_variables: Rename local variables
            rename_functions: Rename function definitions
            rename_classes: Rename class definitions
            rename_methods: Rename method definitions (inside classes)
            rename_attributes: Rename class attributes and self.x patterns
            obfuscate_strings: Apply string obfuscation
            compress_code: Compress output with zlib (only if encrypt_code=False)
            remove_comments: Remove comments (automatic via AST)
            remove_docstrings: Remove docstrings
            name_style: Name generation style ("random", "hex", "hash")
            string_method: String obfuscation method ("xor", "hex", "base64")
            exclude_names: Names to never obfuscate
            name_generator: Shared NameGenerator for cross-file obfuscation
            frameworks: List of framework presets to use (e.g., ['pyside6', 'sqlalchemy'])
                       Available: pyside6, pyqt6, flask, django, fastapi, asyncio, click, sqlalchemy
            preserve_public_api: If True, don't rename names in __all__ or public names
            entry_points: List of function/class names that should never be renamed

        Advanced Obfuscation:
            control_flow: Enable control flow obfuscation (opaque predicates, dead code)
            number_obfuscation: Enable numeric literal obfuscation
            builtin_obfuscation: Enable builtin function call obfuscation
            control_flow_flatten: Enable control flow flattening (CFF)
            integrity_check: Enable integrity verification checks in functions
            obfuscation_intensity: Intensity of advanced obfuscation (1-3)

        Encryption/Protection Options:
            license_info: License/author information embedded in protected files
            encryption_key: Custom encryption key (32 bytes), or auto-generated
            expiration_date: Optional expiration date for the protected code
            allowed_machines: List of allowed machine IDs for hardware binding
        """
        # Core protection settings
        self.encrypt_code = encrypt_code
        self.anti_debug = anti_debug
        self.license_info = license_info
        self.encryption_key = encryption_key
        self.expiration_date = expiration_date
        self.allowed_machines = allowed_machines or []

        # Name obfuscation settings
        self.rename_variables = rename_variables
        self.rename_functions = rename_functions
        self.rename_classes = rename_classes
        self.rename_methods = rename_methods
        self.rename_attributes = rename_attributes
        self.obfuscate_strings = obfuscate_strings
        self.compress_code = compress_code
        self.remove_comments = remove_comments
        self.remove_docstrings = remove_docstrings
        self.name_style = name_style
        self.string_method = string_method
        self.preserve_public_api = preserve_public_api
        self.control_flow = control_flow
        self.number_obfuscation = number_obfuscation
        self.builtin_obfuscation = builtin_obfuscation
        self.control_flow_flatten = control_flow_flatten
        self.integrity_check = integrity_check
        self.obfuscation_intensity = obfuscation_intensity

        # Create RuntimeProtector if encryption is enabled
        self._runtime_protector: Optional[RuntimeProtector] = None
        if self.encrypt_code:
            self._runtime_protector = RuntimeProtector(
                license_info=license_info,
                encryption_key=encryption_key,
                expiration_date=expiration_date,
                allowed_machines=allowed_machines,
                anti_debug=anti_debug
            )

        # Build exclude names from multiple sources
        combined_excludes: Set[str] = set(exclude_names or set())

        # Add framework-specific exclusions
        if frameworks:
            combined_excludes.update(NameObfuscator.get_framework_excludes(frameworks))

        # Add entry points
        if entry_points:
            combined_excludes.update(entry_points)

        self.exclude_names = combined_excludes

        # Use provided name_generator or create new one
        # Sharing name_generator enables cross-file obfuscation
        self.name_generator = name_generator or NameGenerator(style=name_style)

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
                exclude_names=self.exclude_names,
                rename_methods=self.rename_methods,
                rename_attributes=self.rename_attributes
            )
            tree = name_obfuscator.visit(tree)

        # Fix missing line numbers
        ast.fix_missing_locations(tree)

        # Apply string obfuscation
        if self.obfuscate_strings:
            string_obfuscator = StringObfuscator(method=self.string_method)
            tree = string_obfuscator.visit(tree)
            ast.fix_missing_locations(tree)

        # Apply advanced transformations
        if self.control_flow:
            cf_obfuscator = ControlFlowObfuscator(intensity=self.obfuscation_intensity)
            tree = cf_obfuscator.visit(tree)
            ast.fix_missing_locations(tree)

        if self.control_flow_flatten:
            cff_obfuscator = ControlFlowFlattener(intensity=self.obfuscation_intensity)
            tree = cff_obfuscator.visit(tree)
            ast.fix_missing_locations(tree)

        if self.number_obfuscation:
            num_obfuscator = NumberObfuscator(intensity=self.obfuscation_intensity)
            tree = num_obfuscator.visit(tree)
            ast.fix_missing_locations(tree)

        if self.builtin_obfuscation:
            builtin_obfuscator = BuiltinObfuscator()
            tree = builtin_obfuscator.visit(tree)
            ast.fix_missing_locations(tree)

        if self.integrity_check:
            integrity_obfuscator = IntegrityTransformer(intensity=self.obfuscation_intensity)
            tree = integrity_obfuscator.visit(tree)
            ast.fix_missing_locations(tree)

        # Convert AST back to source
        try:
            obfuscated = ast.unparse(tree)
        except Exception as e:
            raise ValueError(f"Failed to generate obfuscated code: {e}")

        # Compress if requested (only when not encrypting)
        if self.compress_code and not self.encrypt_code:
            encoded = CodeCompressor.compress_code(obfuscated)
            obfuscated = CodeCompressor.create_loader(encoded)

        return obfuscated

    def protect_source(self, source: str, filename: str = "<protected>") -> Tuple[str, str]:
        """
        Apply full protection: obfuscation + encryption.

        This is the recommended method for maximum protection.
        The code is first obfuscated (names, strings, control flow) then
        encrypted with AES-256-GCM.

        Args:
            source: Python source code
            filename: Filename for error messages

        Returns:
            Tuple of (protected_code, runtime_module_code)
            - protected_code: The encrypted loader code
            - runtime_module_code: The runtime module that must be deployed with your code
        """
        if not self._runtime_protector:
            raise ValueError("Encryption is not enabled. Set encrypt_code=True")

        # First apply obfuscation
        obfuscated = self.obfuscate_source(source)

        # Then encrypt with runtime protection
        protected, runtime = self._runtime_protector.protect_source(obfuscated, filename)

        return protected, runtime

    def obfuscate_file(self, input_path: Path, output_path: Optional[Path] = None) -> str:
        """
        Obfuscate a Python file.

        When obfuscating multiple files, use the same Obfuscator instance
        to ensure consistent name mapping across files.

        If encrypt_code=True (default), this will produce encrypted output
        that requires the runtime module to execute.

        Args:
            input_path: Path to input file
            output_path: Path to output file (optional)

        Returns:
            Obfuscated/protected source code
        """
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

    def _should_exclude_file(
        self,
        relative_path: Path,
        filename: str,
        exclude_patterns: List[str]
    ) -> bool:
        """Check if a file should be excluded based on patterns."""
        import fnmatch
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(str(relative_path), pattern):
                return True
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _collect_python_files(
        self,
        input_dir: Path,
        pattern: str,
        exclude_patterns: List[str]
    ) -> List[Tuple[Path, Path]]:
        """Collect Python files to process, excluding matched patterns."""
        py_files = []
        for py_file in input_dir.glob(pattern):
            relative_path = py_file.relative_to(input_dir)
            if not self._should_exclude_file(relative_path, py_file.name, exclude_patterns):
                py_files.append((py_file, relative_path))
        return py_files

    def _collect_definitions_from_source(self, source: str) -> None:
        """
        Phase 1: Collect all definitions from source code without transforming.

        This populates the name_generator with all names that will be obfuscated,
        ensuring consistent mapping across all files in a multi-file project.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return  # Skip files that can't be parsed

        collector = DefinitionCollector(
            self.name_generator,
            exclude_names=self.exclude_names
        )
        collector.visit(tree)

    def obfuscate_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Obfuscate all Python files in a directory with cross-file consistency.

        This method uses a two-phase approach to ensure names are consistently
        obfuscated across all files:

        Phase 1: Collect all definitions from all files (build complete name mapping)
        Phase 2: Transform all files using the complete mapping

        This ensures that imports between files continue to work correctly,
        treating the entire directory as ONE unified application.

        Args:
            input_dir: Input directory containing Python files
            output_dir: Output directory for obfuscated files
            recursive: Process subdirectories recursively
            exclude_patterns: File patterns to exclude
            parallel: Enable parallel processing for Phase 2
            max_workers: Maximum number of worker processes (None = CPU count)

        Returns:
            Dict mapping relative file paths to result status
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS

        results: Dict[str, str] = {}
        pattern = '**/*.py' if recursive else '*.py'

        # Collect all files to process
        py_files = self._collect_python_files(input_dir, pattern, exclude_patterns)

        # PHASE 1: Collect all definitions from all files (SEQUENTIAL)
        # This builds the complete name mapping before any transformations
        # Must be sequential to ensure consistent name mapping
        for py_file, relative_path in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                self._collect_definitions_from_source(source)
            except Exception:
                pass  # Skip files that can't be read; will be handled in Phase 2

        # PHASE 2: Transform all files using the complete mapping
        if parallel and len(py_files) > 1:
            results = self._obfuscate_files_parallel(
                py_files, output_dir, max_workers
            )
        else:
            # Sequential processing
            for py_file, relative_path in py_files:
                output_path = output_dir / relative_path
                try:
                    self.obfuscate_file(py_file, output_path)
                    results[str(relative_path)] = "success"
                except Exception as e:
                    results[str(relative_path)] = f"error: {e}"

        return results

    def protect_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ) -> Tuple[Dict[str, str], str]:
        """
        Protect all Python files in a directory with encryption.

        This is the recommended method for maximum protection of multi-file projects.
        All files are first obfuscated, then encrypted with AES-256-GCM.

        Args:
            input_dir: Input directory containing Python files
            output_dir: Output directory for protected files
            recursive: Process subdirectories recursively
            exclude_patterns: File patterns to exclude

        Returns:
            Tuple of (results_dict, runtime_module_code)
            - results_dict: Dict mapping relative file paths to result status
            - runtime_module_code: The runtime module that must be deployed
        """
        if not self._runtime_protector:
            raise ValueError("Encryption is not enabled. Set encrypt_code=True")

        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS

        results: Dict[str, str] = {}
        pattern = '**/*.py' if recursive else '*.py'
        runtime_code = None

        # Collect all files to process
        py_files = self._collect_python_files(input_dir, pattern, exclude_patterns)

        # PHASE 1: Collect all definitions from all files
        for py_file, relative_path in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                self._collect_definitions_from_source(source)
            except Exception:
                pass

        # PHASE 2: Transform and encrypt all files
        for py_file, relative_path in py_files:
            output_path = output_dir / relative_path
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()

                # Apply obfuscation first
                obfuscated = self.obfuscate_source(source)

                # Then encrypt with runtime protection
                protected, runtime = self._runtime_protector.protect_source(
                    obfuscated, str(relative_path)
                )

                # Save runtime code (same for all files)
                if runtime_code is None:
                    runtime_code = runtime

                # Write protected file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(protected)

                results[str(relative_path)] = "success"
            except Exception as e:
                results[str(relative_path)] = f"error: {e}"

        # Write runtime module
        if runtime_code:
            runtime_name = f"pyobfuscator_runtime_{self._runtime_protector.runtime_id}"
            runtime_path = output_dir / f"{runtime_name}.py"
            with open(runtime_path, 'w', encoding='utf-8') as f:
                f.write(runtime_code)

        return results, runtime_code or ""

    def _obfuscate_files_parallel(
        self,
        py_files: List[Tuple[Path, Path]],
        output_dir: Path,
        max_workers: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Process files in parallel using ProcessPoolExecutor.

        Note: This creates a copy of the name mapping for each worker to ensure
        thread safety. All workers use the same pre-computed name mapping from Phase 1.
        """
        import concurrent.futures
        import os

        results: Dict[str, str] = {}


        # Default to number of CPUs
        if max_workers is None:
            max_workers = os.cpu_count() or 4

        # Limit workers to number of files
        max_workers = min(max_workers, len(py_files))

        # Use ThreadPoolExecutor instead of ProcessPoolExecutor to share state
        # This is simpler and avoids serialization issues with the name generator
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {}
            for py_file, relative_path in py_files:
                output_path = output_dir / relative_path
                future = executor.submit(
                    self._obfuscate_single_file_worker,
                    py_file,
                    output_path
                )
                future_to_file[future] = relative_path

            for future in concurrent.futures.as_completed(future_to_file):
                relative_path = future_to_file[future]
                try:
                    result = future.result()
                    results[str(relative_path)] = result
                except Exception as e:
                    results[str(relative_path)] = f"error: {e}"

        return results

    def _obfuscate_single_file_worker(self, input_path: Path, output_path: Path) -> str:
        """Worker function for parallel file obfuscation."""
        try:
            self.obfuscate_file(input_path, output_path)
            return "success"
        except Exception as e:
            return f"error: {e}"


    def export_name_mapping(self) -> Dict[str, str]:
        """
        Export the current name mapping for debugging or cross-session use.

        Returns:
            Dict mapping original names to obfuscated names

        Example:
            obfuscator = Obfuscator()
            obfuscator.obfuscate_file("file1.py", "out/file1.py")
            mapping = obfuscator.export_name_mapping()
            # Save mapping for later or for debugging
            import json
            with open("mapping.json", "w") as f:
                json.dump(mapping, f)
        """
        return self.name_generator.export_mapping()

    def import_name_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Import a name mapping from a previous session.

        This is useful for:
        - Continuing obfuscation across multiple runs
        - Ensuring consistency when adding new files to an obfuscated project

        Args:
            mapping: Dict mapping original names to obfuscated names
        """
        self.name_generator.import_mapping(mapping)

    def get_obfuscated_name(self, original: str) -> Optional[str]:
        """
        Get the obfuscated version of a name, if it exists.

        Args:
            original: Original name

        Returns:
            Obfuscated name or None if not yet mapped
        """
        return self.name_generator.name_map.get(original)

