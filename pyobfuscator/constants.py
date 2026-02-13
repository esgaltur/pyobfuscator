# -*- coding: utf-8 -*-
"""
Constants module for PyObfuscator.

Centralizes all magic values, configuration constants, and default settings.
"""

from typing import Set, Dict, List


class RuntimeConstants:
    """Constants used by the runtime protection module."""

    MAGIC = b'PYO00004'  # Magic header (v4 = advanced protection)
    VERSION = b'\x00\x04'
    DEFAULT_FILENAME = '<protected>'

    # Key wiping configuration
    KEY_WIPE_PASSES = 5

    # Anti-debug timing thresholds (milliseconds)
    DEBUG_TIMING_THRESHOLD_MS = 100


class CryptoConstants:
    """Constants used by the cryptography module."""

    SALT_SIZE = 16
    NONCE_SIZE = 12
    KEY_SIZE = 32
    PBKDF2_ITERATIONS = 100_000

    # Tag sizes for authentication
    AUTH_TAG_SIZE = 16


class ObfuscatorConstants:
    """Constants used by the obfuscation module."""

    # Default name generation settings
    DEFAULT_NAME_PREFIX = "_"
    DEFAULT_NAME_LENGTH = 8

    # Available obfuscation styles
    NAME_STYLES = frozenset({"random", "hex", "hash"})

    # Available string obfuscation methods
    STRING_METHODS = frozenset({"xor", "hex", "base64"})


class ReservedNames:
    """
    Reserved names that should never be obfuscated.

    These include Python builtins, dunder methods, and common imports.
    """

    # Core Python reserved names
    CORE_RESERVED: Set[str] = {
        'self', 'cls', 'super', '__init__', '__new__', '__del__', '__repr__',
        '__str__', '__bytes__', '__format__', '__lt__', '__le__', '__eq__',
        '__ne__', '__gt__', '__ge__', '__hash__', '__bool__', '__getattr__',
        'True', 'False', 'None', 'Exception', 'BaseException',
    }

    # Python built-in functions
    BUILTINS: Set[str] = {
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
    }

    # Dunder (double underscore) method names
    DUNDER_METHODS: Set[str] = {
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
    }

    # Common module names
    COMMON_MODULES: Set[str] = {
        'os', 'sys', 'typing', 'pathlib', 'json', 'logging', 're',
        'collections', 'functools', 'itertools', 'datetime', 'time',
        'threading', 'multiprocessing', 'subprocess', 'asyncio',
    }

    # Testing-related names
    TESTING_NAMES: Set[str] = {
        'pytest', 'unittest', 'test', 'setup', 'teardown',
    }

    @classmethod
    def get_all_reserved(cls) -> Set[str]:
        """Return all reserved names combined."""
        return (
            cls.CORE_RESERVED |
            cls.BUILTINS |
            cls.DUNDER_METHODS |
            cls.COMMON_MODULES |
            cls.TESTING_NAMES |
            set(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))
        )


class FrameworkPresets:
    """
    Framework-specific names that should be preserved.

    These are commonly used method and attribute names from popular frameworks.
    """

    PYSIDE6: Set[str] = {
        # PySide6/Qt signal-slot system
        'Signal', 'Slot', 'Property', 'QObject', 'QWidget', 'QMainWindow',
        'QApplication', 'QDialog', 'QThread', 'QTimer', 'QEvent',
        'emit', 'connect', 'disconnect', 'sender', 'receivers',
        'blockSignals', 'signalsBlocked', 'moveToThread', 'thread',
        # Common Qt methods
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
        'setContextProperty', 'rootContext', 'rootObject', 'load', 'setSource',
        'property', 'setProperty', 'dynamicPropertyNames',
    }

    PYQT6: Set[str] = {
        'pyqtSignal', 'pyqtSlot', 'pyqtProperty', 'QObject', 'QWidget',
        'QMainWindow', 'QApplication', 'QDialog', 'QThread', 'QTimer',
        'emit', 'connect', 'disconnect', 'sender', 'receivers',
        'show', 'hide', 'close', 'exec', 'exec_', 'accept', 'reject',
        'setWindowTitle', 'setGeometry', 'resize', 'move',
        'setLayout', 'layout', 'update', 'repaint', 'setStyleSheet',
        'paintEvent', 'resizeEvent', 'closeEvent', 'showEvent', 'hideEvent',
        'keyPressEvent', 'keyReleaseEvent', 'mousePressEvent', 'mouseReleaseEvent',
    }

    FLASK: Set[str] = {
        'Flask', 'Blueprint', 'request', 'Response', 'make_response',
        'redirect', 'url_for', 'render_template', 'jsonify', 'abort',
        'session', 'g', 'current_app', 'flash', 'get_flashed_messages',
        'route', 'before_request', 'after_request', 'teardown_request',
        'before_first_request', 'errorhandler', 'context_processor',
        'app_context', 'request_context', 'test_client', 'test_request_context',
        'db', 'Model', 'Column', 'Integer', 'String', 'Text', 'Boolean',
        'DateTime', 'ForeignKey', 'relationship', 'backref',
    }

    DJANGO: Set[str] = {
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
    }

    FASTAPI: Set[str] = {
        'FastAPI', 'APIRouter', 'Depends', 'HTTPException', 'Request',
        'Response', 'Body', 'Query', 'Path', 'Header', 'Cookie', 'Form',
        'File', 'UploadFile', 'BackgroundTasks', 'WebSocket',
        'get', 'post', 'put', 'delete', 'patch', 'options', 'head',
        'status_code', 'response_model', 'dependencies', 'tags',
        'startup', 'shutdown', 'on_event', 'middleware',
        'BaseModel', 'Field', 'validator', 'root_validator', 'Config',
    }

    ASYNCIO: Set[str] = {
        'async', 'await', 'asyncio', 'coroutine', 'Task', 'Future',
        'gather', 'wait', 'wait_for', 'create_task', 'ensure_future',
        'run', 'sleep', 'Event', 'Lock', 'Semaphore', 'Queue',
        'StreamReader', 'StreamWriter', 'start_server', 'open_connection',
    }

    CLICK: Set[str] = {
        'click', 'command', 'group', 'option', 'argument', 'pass_context',
        'Context', 'echo', 'secho', 'prompt', 'confirm', 'Choice',
    }

    SQLALCHEMY: Set[str] = {
        'Base', 'Session', 'engine', 'create_engine', 'sessionmaker',
        'Column', 'Integer', 'String', 'Text', 'Boolean', 'DateTime',
        'ForeignKey', 'relationship', 'backref', 'query', 'add', 'commit',
        'rollback', 'flush', 'expire', 'refresh', 'delete', 'merge',
    }

    # Registry mapping framework names to their presets
    REGISTRY: Dict[str, Set[str]] = {
        'pyside6': PYSIDE6,
        'pyqt6': PYQT6,
        'flask': FLASK,
        'django': DJANGO,
        'fastapi': FASTAPI,
        'asyncio': ASYNCIO,
        'click': CLICK,
        'sqlalchemy': SQLALCHEMY,
    }

    @classmethod
    def get_framework_excludes(cls, frameworks: List[str]) -> Set[str]:
        """Get all names to exclude for specified frameworks."""
        excludes: Set[str] = set()
        for framework in frameworks:
            framework_lower = framework.lower()
            if framework_lower in cls.REGISTRY:
                excludes.update(cls.REGISTRY[framework_lower])
        return excludes

    @classmethod
    def get_available_frameworks(cls) -> List[str]:
        """Get list of available framework presets."""
        return list(cls.REGISTRY.keys())


# Default exclude patterns for directory obfuscation
DEFAULT_EXCLUDE_PATTERNS: List[str] = [
    '__pycache__',
    '*.pyc',
    'test_*',
    '*_test.py',
]

