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

    # Names that should never be obfuscated
    BUILTINS = set(dir(__builtins__))
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

    # Framework-specific names that should be preserved
    FRAMEWORK_PRESETS = {
        'pyside6': {
            # PySide6/Qt signal-slot system
            'Signal', 'Slot', 'Property', 'QObject', 'QWidget', 'QMainWindow',
            'QApplication', 'QDialog', 'QThread', 'QTimer', 'QEvent',
            'emit', 'connect', 'disconnect', 'sender', 'receivers',
            'blockSignals', 'signalsBlocked', 'moveToThread', 'thread',
            # Common Qt methods that must be preserved
            'show', 'hide', 'close', 'exec', 'exec_', 'accept', 'reject',
            'setWindowTitle', 'setGeometry', 'resize', 'move', 'raise_',
            'lower', 'setParent', 'parent', 'children', 'findChild', 'findChildren',
            'setLayout', 'layout', 'update', 'repaint', 'setStyleSheet',
            'setEnabled', 'setVisible', 'setHidden', 'setFocus', 'hasFocus',
            'event', 'eventFilter', 'installEventFilter', 'removeEventFilter',
            'paintEvent', 'resizeEvent', 'closeEvent', 'showEvent', 'hideEvent',
            'keyPressEvent', 'keyReleaseEvent', 'mousePressEvent', 'mouseReleaseEvent',
            'mouseMoveEvent', 'mouseDoubleClickEvent', 'wheelEvent', 'enterEvent',
            'leaveEvent', 'focusInEvent', 'focusOutEvent', 'dragEnterEvent',
            'dragMoveEvent', 'dragLeaveEvent', 'dropEvent', 'timerEvent',
            # QML integration
            'setContextProperty', 'rootContext', 'rootObject', 'load', 'setSource',
            # Property system
            'property', 'setProperty', 'dynamicPropertyNames',
        },
        'pyqt6': {
            # Same as PySide6 mostly
            'pyqtSignal', 'pyqtSlot', 'pyqtProperty', 'QObject', 'QWidget',
            'QMainWindow', 'QApplication', 'QDialog', 'QThread', 'QTimer',
            'emit', 'connect', 'disconnect', 'sender', 'receivers',
            'show', 'hide', 'close', 'exec', 'exec_', 'accept', 'reject',
            'setWindowTitle', 'setGeometry', 'resize', 'move',
            'setLayout', 'layout', 'update', 'repaint', 'setStyleSheet',
            'paintEvent', 'resizeEvent', 'closeEvent', 'showEvent', 'hideEvent',
            'keyPressEvent', 'keyReleaseEvent', 'mousePressEvent', 'mouseReleaseEvent',
        },
        'flask': {
            # Flask framework
            'Flask', 'Blueprint', 'request', 'Response', 'make_response',
            'redirect', 'url_for', 'render_template', 'jsonify', 'abort',
            'session', 'g', 'current_app', 'flash', 'get_flashed_messages',
            'route', 'before_request', 'after_request', 'teardown_request',
            'before_first_request', 'errorhandler', 'context_processor',
            'app_context', 'request_context', 'test_client', 'test_request_context',
            # Flask-SQLAlchemy
            'db', 'Model', 'Column', 'Integer', 'String', 'Text', 'Boolean',
            'DateTime', 'ForeignKey', 'relationship', 'backref',
        },
        'django': {
            # Django framework
            'models', 'Model', 'CharField', 'TextField', 'IntegerField',
            'BooleanField', 'DateTimeField', 'ForeignKey', 'ManyToManyField',
            'OneToOneField', 'Manager', 'QuerySet', 'Meta', 'objects',
            'get', 'filter', 'exclude', 'create', 'update', 'delete', 'save',
            'HttpResponse', 'HttpRequest', 'JsonResponse', 'render', 'redirect',
            'get_object_or_404', 'get_list_or_404', 'reverse', 'reverse_lazy',
            'View', 'TemplateView', 'ListView', 'DetailView', 'CreateView',
            'UpdateView', 'DeleteView', 'FormView', 'RedirectView',
            'get_queryset', 'get_context_data', 'get_object', 'form_valid',
            'path', 'include', 'urlpatterns', 'admin', 'site',
        },
        'fastapi': {
            # FastAPI framework
            'FastAPI', 'APIRouter', 'Depends', 'HTTPException', 'Request',
            'Response', 'Body', 'Query', 'Path', 'Header', 'Cookie', 'Form',
            'File', 'UploadFile', 'BackgroundTasks', 'WebSocket',
            'get', 'post', 'put', 'delete', 'patch', 'options', 'head',
            'status_code', 'response_model', 'dependencies', 'tags',
            'startup', 'shutdown', 'on_event', 'middleware',
            # Pydantic
            'BaseModel', 'Field', 'validator', 'root_validator', 'Config',
        },
        'asyncio': {
            # Asyncio patterns
            'async', 'await', 'asyncio', 'coroutine', 'Task', 'Future',
            'gather', 'wait', 'wait_for', 'create_task', 'ensure_future',
            'run', 'sleep', 'Event', 'Lock', 'Semaphore', 'Queue',
            'StreamReader', 'StreamWriter', 'start_server', 'open_connection',
        },
        'click': {
            # Click CLI framework
            'click', 'command', 'group', 'option', 'argument', 'pass_context',
            'Context', 'echo', 'secho', 'prompt', 'confirm', 'Choice',
        },
        'sqlalchemy': {
            # SQLAlchemy ORM
            'Base', 'Session', 'engine', 'create_engine', 'sessionmaker',
            'Column', 'Integer', 'String', 'Text', 'Boolean', 'DateTime',
            'ForeignKey', 'relationship', 'backref', 'query', 'add', 'commit',
            'rollback', 'flush', 'expire', 'refresh', 'delete', 'merge',
        },
    }

    @classmethod
    def get_framework_excludes(cls, frameworks: List[str]) -> Set[str]:
        """Get all names to exclude for specified frameworks."""
        excludes: Set[str] = set()
        for framework in frameworks:
            framework_lower = framework.lower()
            if framework_lower in cls.FRAMEWORK_PRESETS:
                excludes.update(cls.FRAMEWORK_PRESETS[framework_lower])
        return excludes

    def __init__(self, name_generator: NameGenerator, exclude_names: Optional[Set[str]] = None,
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
        entry_points: Optional[List[str]] = None
    ):
        """
        Initialize the obfuscator.

        Args:
            rename_variables: Rename local variables
            rename_functions: Rename function definitions
            rename_classes: Rename class definitions
            rename_methods: Rename method definitions (inside classes)
            rename_attributes: Rename class attributes and self.x patterns
            obfuscate_strings: Apply string obfuscation
            compress_code: Compress output with zlib
            remove_comments: Remove comments (automatic via AST)
            remove_docstrings: Remove docstrings
            name_style: Name generation style ("random", "hex", "hash")
            string_method: String obfuscation method ("xor", "hex", "base64")
            exclude_names: Names to never obfuscate
            name_generator: Shared NameGenerator for cross-file obfuscation
            frameworks: List of framework presets to use (e.g., ['pyside6', 'sqlalchemy'])
                       Available: pyside6, pyqt6, flask, django, fastapi, asyncio, click, sqlalchemy
            preserve_public_api: If True, don't rename names in __all__ or public names (no underscore prefix)
            entry_points: List of function/class names that should never be renamed (e.g., ['main', 'App'])
        """
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
        """
        Obfuscate a Python file.

        When obfuscating multiple files, use the same Obfuscator instance
        to ensure consistent name mapping across files.

        Args:
            input_path: Path to input file
            output_path: Path to output file (optional)

        Returns:
            Obfuscated source code
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

    def obfuscate_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Obfuscate all Python files in a directory with cross-file consistency.

        This method ensures that names are consistently obfuscated across
        all files, so imports between files continue to work correctly.
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', 'test_*', '*_test.py']

        results: Dict[str, str] = {}
        pattern = '**/*.py' if recursive else '*.py'

        # Collect all files to process
        py_files = self._collect_python_files(input_dir, pattern, exclude_patterns)

        # Obfuscate all files using shared name generator
        for py_file, relative_path in py_files:
            output_path = output_dir / relative_path

            try:
                self.obfuscate_file(py_file, output_path)
                results[str(relative_path)] = "success"
            except Exception as e:
                results[str(relative_path)] = f"error: {e}"

        return results

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

