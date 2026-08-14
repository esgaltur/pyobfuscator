# -*- coding: utf-8 -*-
"""
Project analyzer for automatic obfuscation configuration generation.

Scans a Python project directory and:
- Detects frameworks (PySide6, Flask, Django, FastAPI, etc.)
- Identifies entry points (main functions, app factories)
- Finds public APIs from __all__ exports
- Analyzes module structure
- Generates optimal obfuscation configuration
"""

import ast
import importlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: Path
    package: str
    imports: Set[str] = field(default_factory=set)
    from_imports: Dict[str, Set[str]] = field(default_factory=dict)
    exports: Set[str] = field(default_factory=set)  # Names in __all__
    public_names: Set[str] = field(default_factory=set)  # Public functions/classes
    entry_points: Set[str] = field(default_factory=set)  # main, app, etc.
    has_init: bool = False
    is_package: bool = False


@dataclass
class ProjectAnalysis:
    """Complete analysis of a Python project."""
    root_path: Path
    detected_frameworks: Set[str] = field(default_factory=set)
    entry_points: Set[str] = field(default_factory=set)
    public_api: Set[str] = field(default_factory=set)
    exclude_names: Set[str] = field(default_factory=set)
    exclude_patterns: List[str] = field(default_factory=list)
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class TomlDocumentLoader:
    """Load TOML without coupling analysis to one parser package."""

    PARSER_MODULES = ('tomllib', 'tomli')

    @classmethod
    def load(cls, content: str) -> Optional[Mapping[str, Any]]:
        """Return parsed TOML, or ``None`` when no parser is installed."""
        for module_name in cls.PARSER_MODULES:
            try:
                parser = importlib.import_module(module_name)
            except ImportError:
                continue
            return parser.loads(content)
        return None


class PyProjectDependencyExtractor:
    """Extract dependency specifications from supported pyproject layouts."""

    @classmethod
    def extract(cls, document: Mapping[str, Any]) -> List[str]:
        """Collect PEP 621 and Poetry dependency declarations."""
        dependencies: List[str] = []
        project = cls._mapping(document.get('project'))
        dependencies.extend(cls._sequence(project.get('dependencies')))

        optional_groups = cls._mapping(project.get('optional-dependencies'))
        for group in optional_groups.values():
            dependencies.extend(cls._sequence(group))

        tool = cls._mapping(document.get('tool'))
        poetry = cls._mapping(tool.get('poetry'))
        dependencies.extend(cls._mapping(poetry.get('dependencies')).keys())
        dependencies.extend(cls._mapping(poetry.get('dev-dependencies')).keys())
        return [str(dependency) for dependency in dependencies]

    @staticmethod
    def _mapping(value: Any) -> Mapping[str, Any]:
        return value if isinstance(value, Mapping) else {}

    @staticmethod
    def _sequence(value: Any) -> Sequence[Any]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return value
        return ()


class MainGuardEntryPointFinder(ast.NodeVisitor):
    """Find calls to public functions inside real ``__main__`` guards."""

    def __init__(self, public_names: Iterable[str]):
        self._public_names = set(public_names)
        self.entry_points: Set[str] = set()

    @classmethod
    def find(cls, tree: ast.AST, public_names: Iterable[str]) -> Set[str]:
        finder = cls(public_names)
        finder.visit(tree)
        return finder.entry_points

    def visit_If(self, node: ast.If) -> None:  # noqa: N802 - ast visitor API
        if not self._is_main_guard(node.test):
            self.generic_visit(node)
            return

        for statement in node.body:
            self._collect_calls(statement)

    def _collect_calls(self, statement: ast.AST) -> None:
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in self._public_names:
                    self.entry_points.add(node.func.id)

    @classmethod
    def _is_main_guard(cls, test: ast.AST) -> bool:
        if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
            return False
        if not isinstance(test.ops[0], ast.Eq):
            return False

        left, right = test.left, test.comparators[0]
        return (
                cls._is_name(left, '__name__') and cls._is_string(right, '__main__')
        ) or (
                cls._is_string(left, '__main__') and cls._is_name(right, '__name__')
        )

    @staticmethod
    def _is_name(node: ast.AST, value: str) -> bool:
        return isinstance(node, ast.Name) and node.id == value

    @staticmethod
    def _is_string(node: ast.AST, value: str) -> bool:
        return isinstance(node, ast.Constant) and node.value == value


class TomlConfigFormatter:
    """Serialize the flat Skjol configuration and its comment metadata."""

    _BARE_KEY = re.compile(r'^[A-Za-z0-9_-]+$')

    def format(self, config: Mapping[str, Any], prefix: str = '') -> str:
        lines = self._format_settings(config, prefix)
        metadata = config.get('_metadata')
        if isinstance(metadata, Mapping):
            lines.extend(self._format_metadata(metadata))
        return '\n'.join(lines) + '\n'

    def _format_settings(self, config: Mapping[str, Any], prefix: str) -> List[str]:
        lines: List[str] = []
        for key, value in config.items():
            if key.startswith('_') or isinstance(value, Mapping):
                continue
            formatted = self._format_value(value)
            if formatted is not None:
                lines.append(f'{self._qualified_key(prefix, key)} = {formatted}')
        return lines

    def _format_value(self, value: Any) -> Optional[str]:
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, list):
            items = [self._format_value(item) for item in value]
            if all(item is not None for item in items):
                return f"[{', '.join(item for item in items if item is not None)}]"
        return None

    def _qualified_key(self, prefix: str, key: str) -> str:
        formatted_key = self._format_key(key)
        return f'{prefix}.{formatted_key}' if prefix else formatted_key

    def _format_key(self, key: str) -> str:
        return key if self._BARE_KEY.fullmatch(key) else json.dumps(key, ensure_ascii=False)

    def _format_metadata(self, metadata: Mapping[str, Any]) -> List[str]:
        lines = ['', '# Generated configuration metadata']
        for key, value in metadata.items():
            values = value if isinstance(value, list) else [value]
            for item in values:
                lines.extend(self._comment_lines(str(key), item))
        return lines

    @staticmethod
    def _comment_lines(key: str, value: Any) -> List[str]:
        text_lines = str(value).splitlines() or ['']
        return [f'# {key}: {line}' for line in text_lines]


class ProjectSummaryFormatter:
    """Render project analysis separately from console output."""

    SEPARATOR = '=' * 60
    PREVIEW_LIMIT = 10

    def format(self, analysis: ProjectAnalysis, project_name: str) -> str:
        lines = [
            '',
            self.SEPARATOR,
            f'Project Analysis: {project_name}',
            self.SEPARATOR,
            '',
            f'Total Python files: {len(analysis.modules)}',
        ]
        self._append_frameworks(lines, analysis.detected_frameworks)
        self._append_preview(lines, 'Entry points', analysis.entry_points)
        self._append_preview(lines, 'Public API names', analysis.public_api)
        self._append_all(lines, 'Warnings', analysis.warnings, '!')
        self._append_all(lines, 'Recommendations', analysis.recommendations, '*')
        lines.extend(['', self.SEPARATOR, ''])
        return '\n'.join(lines)

    @staticmethod
    def _append_frameworks(lines: List[str], frameworks: Iterable[str]) -> None:
        sorted_frameworks = sorted(frameworks)
        if not sorted_frameworks:
            lines.extend(['', 'No specific frameworks detected.'])
            return
        lines.extend(['', 'Detected frameworks:'])
        lines.extend(f'  - {framework}' for framework in sorted_frameworks)

    def _append_preview(self, lines: List[str], title: str, values: Iterable[str]) -> None:
        sorted_values = sorted(values)
        if not sorted_values:
            return
        lines.extend(['', f'{title} ({len(sorted_values)}):'])
        lines.extend(f'  - {value}' for value in sorted_values[:self.PREVIEW_LIMIT])
        remaining = len(sorted_values) - self.PREVIEW_LIMIT
        if remaining > 0:
            lines.append(f'  ... and {remaining} more')

    @staticmethod
    def _append_all(lines: List[str], title: str, values: Iterable[str], marker: str) -> None:
        values = list(values)
        if not values:
            return
        lines.extend(['', f'{title}:'])
        lines.extend(f'  {marker} {value}' for value in values)


class ProjectAnalyzer:
    """
    Analyzes a Python project and generates obfuscation configuration.

    Usage:
        analyzer = ProjectAnalyzer("./my_project")
        config = analyzer.analyze()
        analyzer.save_config("skjol.json")
    """

    # Framework detection patterns: import name -> framework preset
    FRAMEWORK_IMPORTS = {
        # Qt frameworks
        'PySide6': 'pyside6',
        'PySide2': 'pyside6',  # Similar API
        'PyQt6': 'pyqt6',
        'PyQt5': 'pyqt6',  # Similar API
        'shiboken6': 'pyside6',
        'shiboken2': 'pyside6',
        # Web frameworks
        'flask': 'flask',
        'Flask': 'flask',
        'django': 'django',
        'fastapi': 'fastapi',
        'FastAPI': 'fastapi',
        'starlette': 'fastapi',
        # CLI frameworks
        'click': 'click',
        'typer': 'click',  # Built on click
        # Database
        'sqlalchemy': 'sqlalchemy',
        'SQLAlchemy': 'sqlalchemy',
        # Async
        'asyncio': 'asyncio',
        'aiohttp': 'asyncio',
        'httpx': 'asyncio',
    }

    # Package names in requirements.txt/pyproject.toml -> framework preset
    REQUIREMENTS_FRAMEWORK_MAP = {
        # Qt frameworks
        'pyside6': 'pyside6',
        'pyside2': 'pyside6',
        'pyqt6': 'pyqt6',
        'pyqt5': 'pyqt6',
        'shiboken6': 'pyside6',
        # Web frameworks
        'flask': 'flask',
        'flask-restful': 'flask',
        'flask-sqlalchemy': 'flask',
        'flask-login': 'flask',
        'flask-wtf': 'flask',
        'django': 'django',
        'djangorestframework': 'django',
        'django-rest-framework': 'django',
        'fastapi': 'fastapi',
        'starlette': 'fastapi',
        'uvicorn': 'fastapi',
        # CLI frameworks
        'click': 'click',
        'typer': 'click',
        'argparse': 'click',
        # Database
        'sqlalchemy': 'sqlalchemy',
        'alembic': 'sqlalchemy',
        'flask-migrate': 'sqlalchemy',
        'psycopg2': 'sqlalchemy',
        'psycopg2-binary': 'sqlalchemy',
        'pymysql': 'sqlalchemy',
        'asyncpg': 'sqlalchemy',
        # Async
        'aiohttp': 'asyncio',
        'httpx': 'asyncio',
        'aiofiles': 'asyncio',
        'aiomysql': 'asyncio',
        'aiopg': 'asyncio',
    }

    # Common entry point patterns
    ENTRY_POINT_PATTERNS = {
        'main',
        'app',
        'application',
        'create_app',
        'make_app',
        'get_app',
        'run',
        'start',
        'cli',
        'main_window',
        'MainWindow',
        'App',
        'Application',
        'GUI',
        'Window',
    }

    FRAMEWORK_ENTRY_POINTS = {
        'click': {'cli', 'main', 'app'},
        'flask': {'create_app', 'app', 'application'},
        'fastapi': {'app', 'create_app', 'get_app'},
        'django': {'urlpatterns', 'application', 'wsgi', 'asgi'},
    }

    TOP_LEVEL_HANDLERS = {
        ast.Assign: '_process_export_assignment',
        ast.FunctionDef: '_process_top_level_function',
        ast.AsyncFunctionDef: '_process_top_level_function',
        ast.ClassDef: '_process_top_level_class',
    }

    ENTRY_CLASS_MARKERS = ('window', 'app', 'application', 'gui', 'dialog')

    # Files that typically shouldn't be obfuscated
    DEFAULT_EXCLUDE_PATTERNS = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        'test_*.py',
        '*_test.py',
        'tests/',
        'test/',
        'conftest.py',
        'setup.py',
        'setup.cfg',
        'pyproject.toml',
        '*.egg-info',
        'dist/',
        'build/',
        '.git/',
        '.venv/',
        'venv/',
        'env/',
        '.env',
        '*.md',
        '*.txt',
        '*.rst',
    ]

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()
        self.analysis = ProjectAnalysis(root_path=self.project_path)
        self._processed_files: Set[Path] = set()
        self._entry_point_names = {name.casefold() for name in self.ENTRY_POINT_PATTERNS}
        self._toml_formatter = TomlConfigFormatter()
        self._summary_formatter = ProjectSummaryFormatter()

    def analyze(self) -> ProjectAnalysis:
        """
        Perform complete project analysis.

        Returns:
            ProjectAnalysis with detected frameworks, entry points, etc.
        """
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")

        # Initialize default exclude patterns
        self.analysis.exclude_patterns = list(self.DEFAULT_EXCLUDE_PATTERNS)

        # Analyze dependency files first (requirements.txt, pyproject.toml, setup.py)
        self._analyze_dependencies()

        # Find all Python files
        py_files = self._collect_python_files()

        # Analyze each file
        for py_file in py_files:
            self._analyze_file(py_file)

        # Post-processing
        self._detect_package_structure()
        self._identify_additional_entry_points()
        self._generate_recommendations()

        return self.analysis

    def _analyze_dependencies(self) -> None:
        """Analyze dependency files to detect frameworks."""
        # Check requirements.txt
        self._analyze_requirements_txt()

        # Check pyproject.toml
        self._analyze_pyproject_toml()

        # Check setup.py
        self._analyze_setup_py()

    def _parse_requirement_line(self, line: str) -> Optional[str]:
        """Parse a single requirement line and return the package name."""
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#') or line.startswith('-'):
            return None

        # Handle various requirement formats:
        # package==1.0.0, package>=1.0, package[extra], package @ url
        match = re.match(r'^([a-zA-Z0-9_-]+)', line)
        if match:
            return match.group(1).lower()
        return None

    def _analyze_requirements_txt(self) -> None:
        """Analyze requirements.txt files for framework detection."""
        req_files = [
            self.project_path / 'requirements.txt',
            self.project_path / 'requirements' / 'base.txt',
            self.project_path / 'requirements' / 'prod.txt',
            self.project_path / 'requirements' / 'production.txt',
            self.project_path / 'requirements-dev.txt',
            self.project_path / 'requirements-prod.txt',
        ]

        for req_file in req_files:
            if req_file.exists():
                try:
                    content = req_file.read_text(encoding='utf-8')
                    for line in content.splitlines():
                        package_name = self._parse_requirement_line(line)
                        if package_name:
                            self._record_dependency_framework(package_name)
                except Exception:
                    self.analysis.warnings.append(f"Could not parse {req_file.name}")

    def _analyze_pyproject_toml(self) -> None:
        """Analyze pyproject.toml for dependencies and framework detection."""
        pyproject_path = self.project_path / 'pyproject.toml'
        if not pyproject_path.exists():
            return

        try:
            content = pyproject_path.read_text(encoding='utf-8')
            document = TomlDocumentLoader.load(content)
            if document is None:
                self._analyze_pyproject_toml_regex(content)
                return
            self._record_dependency_frameworks(PyProjectDependencyExtractor.extract(document))
        except Exception as e:
            self.analysis.warnings.append(f"Could not fully parse pyproject.toml: {e}")

    def _record_dependency_frameworks(self, dependencies: Iterable[str]) -> None:
        """Add frameworks represented by dependency specifications."""
        for dependency in dependencies:
            package_name = self._parse_requirement_line(str(dependency))
            if package_name:
                self._record_dependency_framework(package_name)

    def _record_dependency_framework(self, package_name: str) -> None:
        framework = self.REQUIREMENTS_FRAMEWORK_MAP.get(package_name)
        if framework:
            self.analysis.detected_frameworks.add(framework)

    def _analyze_pyproject_toml_regex(self, content: str) -> None:
        """Fallback regex parsing for pyproject.toml when toml library unavailable."""
        # Simple pattern to find dependencies
        for package_name in self.REQUIREMENTS_FRAMEWORK_MAP.keys():
            pattern = rf'["\']?{re.escape(package_name)}["\']?\s*[=><\[]'
            if re.search(pattern, content, re.IGNORECASE):
                framework = self.REQUIREMENTS_FRAMEWORK_MAP[package_name]
                self.analysis.detected_frameworks.add(framework)

    def _analyze_setup_py(self) -> None:
        """Analyze setup.py for dependencies."""
        setup_path = self.project_path / 'setup.py'
        if not setup_path.exists():
            return

        try:
            content = setup_path.read_text(encoding='utf-8')

            # Look for install_requires patterns
            # Match install_requires=[...] or install_requires=["..."]
            for package_name in self.REQUIREMENTS_FRAMEWORK_MAP.keys():
                pattern = rf'["\']({re.escape(package_name)})["\'\s,\]]'
                if re.search(pattern, content, re.IGNORECASE):
                    framework = self.REQUIREMENTS_FRAMEWORK_MAP[package_name]
                    self.analysis.detected_frameworks.add(framework)

        except Exception:
            pass  # setup.py parsing is best-effort

    def _collect_python_files(self) -> List[Path]:
        """Collect all Python files in the project."""
        py_files = []

        for pattern in ['**/*.py']:
            for path in self.project_path.glob(pattern):
                # Skip excluded patterns
                relative = path.relative_to(self.project_path)
                relative_str = str(relative)

                skip = False
                for exclude in ['__pycache__', '.git', '.venv', 'venv', 'env', 'dist', 'build', '.egg-info']:
                    if exclude in relative_str:
                        skip = True
                        break

                if not skip:
                    py_files.append(path)

        return sorted(py_files)

    def _analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """Analyze a single Python file."""
        if file_path in self._processed_files:
            return self.analysis.modules.get(str(file_path))

        self._processed_files.add(file_path)

        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
            self.analysis.warnings.append(f"Could not parse {file_path}: {e}")
            return None

        relative_path = file_path.relative_to(self.project_path)
        package = self._path_to_package(relative_path)

        module_info = ModuleInfo(
            path=file_path,
            package=package,
            has_init=file_path.name == '__init__.py',
            is_package=file_path.name == '__init__.py'
        )

        # Analyze AST
        for node in ast.walk(tree):
            self._process_node(node, module_info)

        # Check for top-level definitions
        for node in tree.body:
            self._process_top_level(node, module_info)

        self.analysis.modules[str(file_path)] = module_info
        return module_info

    def _process_node(self, node: ast.AST, module_info: ModuleInfo) -> None:
        """Process an AST node for imports and framework detection."""
        if isinstance(node, ast.Import):
            self._process_import(node, module_info)
        elif isinstance(node, ast.ImportFrom):
            self._process_from_import(node, module_info)

    def _process_import(self, node: ast.Import, module_info: ModuleInfo) -> None:
        for alias in node.names:
            self._record_module_import(alias.name, module_info)

    def _process_from_import(self, node: ast.ImportFrom, module_info: ModuleInfo) -> None:
        if not node.module:
            return
        module_name = self._record_module_import(node.module, module_info)
        imported_names = {alias.name for alias in node.names if alias.name != '*'}
        module_info.from_imports.setdefault(module_name, set()).update(imported_names)
        for imported_name in imported_names:
            self._check_framework(imported_name)

    def _record_module_import(self, imported_path: str, module_info: ModuleInfo) -> str:
        module_name = imported_path.split('.')[0]
        module_info.imports.add(module_name)
        self._check_framework(module_name)
        return module_name

    def _process_top_level(self, node: ast.AST, module_info: ModuleInfo) -> None:
        """Process top-level definitions."""
        handler_name = self.TOP_LEVEL_HANDLERS.get(type(node))
        if handler_name:
            getattr(self, handler_name)(node, module_info)

    def _process_export_assignment(self, node: ast.Assign, module_info: ModuleInfo) -> None:
        if not self._assigns_to_all(node):
            return
        exports = self._string_sequence(node.value)
        module_info.exports.update(exports)
        self.analysis.public_api.update(exports)

    @staticmethod
    def _assigns_to_all(node: ast.Assign) -> bool:
        return any(isinstance(target, ast.Name) and target.id == '__all__' for target in node.targets)

    @staticmethod
    def _string_sequence(node: ast.AST) -> Set[str]:
        if not isinstance(node, (ast.List, ast.Tuple)):
            return set()
        return {
            element.value
            for element in node.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        }

    def _process_top_level_function(
            self,
            node: ast.FunctionDef | ast.AsyncFunctionDef,
            module_info: ModuleInfo,
    ) -> None:
        if node.name.startswith(('test_', '_')):
            return
        module_info.public_names.add(node.name)
        if node.name.casefold() in self._entry_point_names:
            self._record_entry_point(node.name, module_info)

    def _process_top_level_class(self, node: ast.ClassDef, module_info: ModuleInfo) -> None:
        if node.name.startswith(('Test', '_')):
            return
        module_info.public_names.add(node.name)
        name = node.name.casefold()
        if name in self._entry_point_names or any(marker in name for marker in self.ENTRY_CLASS_MARKERS):
            self._record_entry_point(node.name, module_info)

    def _record_entry_point(self, name: str, module_info: ModuleInfo) -> None:
        module_info.entry_points.add(name)
        self.analysis.entry_points.add(name)

    def _check_framework(self, name: str) -> None:
        """Check if a name indicates a framework."""
        if name in self.FRAMEWORK_IMPORTS:
            framework = self.FRAMEWORK_IMPORTS[name]
            self.analysis.detected_frameworks.add(framework)

    def _path_to_package(self, path: Path) -> str:
        """Convert a file path to a Python package name."""
        parts = list(path.parts)
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        elif parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        return '.'.join(parts)

    def _detect_package_structure(self) -> None:
        """Detect package structure and identify root packages."""
        packages: Set[str] = set()

        for module_info in self.analysis.modules.values():
            if module_info.is_package:
                # This is a package __init__.py
                package = module_info.package
                packages.add(package)

                # Exports from __init__.py are important
                self.analysis.public_api.update(module_info.exports)
                self.analysis.entry_points.update(module_info.entry_points)

        # Add package names to exclude (they shouldn't be renamed)
        for package in packages:
            root_package = package.split('.')[0]
            self.analysis.exclude_names.add(root_package)

    def _identify_additional_entry_points(self) -> None:
        """Identify additional entry points based on common patterns."""
        for module_info in self.analysis.modules.values():
            self.analysis.entry_points.update(self._find_guarded_entry_points(module_info))
        self._add_framework_entry_points()

    @staticmethod
    def _find_guarded_entry_points(module_info: ModuleInfo) -> Set[str]:
        try:
            content = module_info.path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (OSError, SyntaxError, UnicodeError):
            return set()
        return MainGuardEntryPointFinder.find(tree, module_info.public_names)

    def _add_framework_entry_points(self) -> None:
        for framework in self.analysis.detected_frameworks:
            self.analysis.entry_points.update(self.FRAMEWORK_ENTRY_POINTS.get(framework, set()))

    def _generate_recommendations(self) -> None:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Framework-specific recommendations
        if 'pyside6' in self.analysis.detected_frameworks or 'pyqt6' in self.analysis.detected_frameworks:
            recommendations.append(
                "Qt app detected: Signal/Slot connections and event handlers will be preserved automatically."
            )
            # Qt apps often use dynamic property access
            recommendations.append(
                "Consider using --preserve-public if you use dynamic attribute access (getattr/setattr)."
            )

        if 'flask' in self.analysis.detected_frameworks:
            recommendations.append(
                "Flask app detected: Route decorators and view functions will work correctly."
            )
            recommendations.append(
                "Ensure your Jinja2 templates reference the correct function names if using url_for()."
            )

        if 'django' in self.analysis.detected_frameworks:
            recommendations.append(
                "Django app detected: Model field names and view names should be preserved."
            )
            recommendations.append(
                "Add model field names to exclude list if using dynamic queries."
            )

        if 'fastapi' in self.analysis.detected_frameworks:
            recommendations.append(
                "FastAPI app detected: Pydantic models and dependency injection will work correctly."
            )

        # General recommendations
        if len(self.analysis.public_api) > 20:
            recommendations.append(
                f"Large public API detected ({len(self.analysis.public_api)} names). "
                "Consider enabling --preserve-public to maintain API compatibility."
            )

        if not self.analysis.detected_frameworks:
            recommendations.append(
                "No specific framework detected. Default obfuscation settings should work well."
            )

        self.analysis.recommendations = recommendations

    def generate_config(self) -> Dict[str, Any]:
        """Generate a configuration dictionary from the analysis."""
        config: Dict[str, Any] = {}

        # Frameworks
        if self.analysis.detected_frameworks:
            config['frameworks'] = sorted(self.analysis.detected_frameworks)

        # Filter entry points - remove test functions and empty strings
        entry_points = {
            ep for ep in self.analysis.entry_points
            if ep and not ep.startswith('test_') and not ep.startswith('Test')
        }

        # Entry points - these are the main app entry points that MUST be preserved
        if entry_points:
            config['entry_points'] = sorted(entry_points)

        # Exclude names (public API + detected excludes)
        # Remove empty strings and filter out names already in entry_points
        exclude_names = (self.analysis.exclude_names | self.analysis.public_api) - entry_points
        exclude_names = {name for name in exclude_names if name}  # Remove empty strings

        # Also filter out common test-related names
        exclude_names = {
            name for name in exclude_names
            if not name.startswith('test_') and not name.startswith('Test')
        }

        if exclude_names:
            config['exclude'] = sorted(exclude_names)

        # Exclude patterns
        config['exclude_patterns'] = self.analysis.exclude_patterns

        # Default settings
        config['string_method'] = 'xor'
        config['name_style'] = 'random'
        config['compress'] = False
        config['keep_docstrings'] = False
        config['preserve_public'] = len(self.analysis.public_api) > 10

        # Add metadata
        config['_metadata'] = {
            'generated_by': 'skjol analyzer',
            'project_path': str(self.project_path),
            'detected_frameworks': sorted(self.analysis.detected_frameworks),
            'total_modules': len(self.analysis.modules),
            'recommendations': self.analysis.recommendations,
            'warnings': self.analysis.warnings,
        }

        return config

    def save_config(
            self,
            output_path: Optional[str | Path] = None,
            format: str = 'json'
    ) -> Path:
        """
        Save the generated configuration to a file.

        Args:
            output_path: Path to save the config (default: skjol.json in project root)
            format: 'json' or 'toml'

        Returns:
            Path to the saved config file
        """
        config = self.generate_config()

        if output_path is None:
            output_path = self.project_path / f'skjol.{format}'
        else:
            output_path = Path(output_path)

        if format == 'json':
            content = json.dumps(config, indent=2, ensure_ascii=False)
        elif format == 'toml':
            content = self._dict_to_toml(config)
        else:
            raise ValueError(f"Unknown format: {format}")

        output_path.write_text(content, encoding='utf-8')
        return output_path

    def _dict_to_toml(self, config: Dict[str, Any], prefix: str = '') -> str:
        """Convert a dictionary to TOML format."""
        return self._toml_formatter.format(config, prefix)

    def print_summary(self) -> None:
        """Print a summary of the analysis to stdout."""
        summary = self._summary_formatter.format(self.analysis, self.project_path.name)
        print(summary)


def analyze_project(project_path: str | Path) -> ProjectAnalysis:
    """
    Convenience function to analyze a project.

    Args:
        project_path: Path to the project directory

    Returns:
        ProjectAnalysis object with all detected information
    """
    analyzer = ProjectAnalyzer(project_path)
    return analyzer.analyze()


def generate_config(
        project_path: str | Path,
        output_path: Optional[str | Path] = None,
        format: str = 'json',
        verbose: bool = False
) -> Path:
    """
    Analyze a project and generate an obfuscation config file.

    Args:
        project_path: Path to the project directory
        output_path: Path for the config file (optional)
        format: 'json' or 'toml'
        verbose: Print analysis summary

    Returns:
        Path to the generated config file
    """
    analyzer = ProjectAnalyzer(project_path)
    analyzer.analyze()

    if verbose:
        analyzer.print_summary()

    return analyzer.save_config(output_path, format)
