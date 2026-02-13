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
import json
from pathlib import Path
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field


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


class ProjectAnalyzer:
    """
    Analyzes a Python project and generates obfuscation configuration.

    Usage:
        analyzer = ProjectAnalyzer("./my_project")
        config = analyzer.analyze()
        analyzer.save_config("pyobfuscator.json")
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
        import re
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
                        if package_name and package_name in self.REQUIREMENTS_FRAMEWORK_MAP:
                            framework = self.REQUIREMENTS_FRAMEWORK_MAP[package_name]
                            self.analysis.detected_frameworks.add(framework)
                except Exception:
                    self.analysis.warnings.append(f"Could not parse {req_file.name}")

    def _analyze_pyproject_toml(self) -> None:
        """Analyze pyproject.toml for dependencies and framework detection."""
        pyproject_path = self.project_path / 'pyproject.toml'
        if not pyproject_path.exists():
            return

        try:
            content = pyproject_path.read_text(encoding='utf-8')

            # Try to parse with tomllib (Python 3.11+) or tomli
            try:
                import tomllib
                data = tomllib.loads(content)
            except ImportError:
                try:
                    import tomli
                    data = tomli.loads(content)
                except ImportError:
                    # Fall back to regex parsing
                    self._analyze_pyproject_toml_regex(content)
                    return

            # Extract dependencies from various locations
            dependencies = []

            # [project.dependencies]
            if 'project' in data and 'dependencies' in data['project']:
                dependencies.extend(data['project']['dependencies'])

            # [project.optional-dependencies]
            if 'project' in data and 'optional-dependencies' in data['project']:
                for deps in data['project']['optional-dependencies'].values():
                    dependencies.extend(deps)

            # [tool.poetry.dependencies]
            if 'tool' in data and 'poetry' in data['tool']:
                poetry = data['tool']['poetry']
                if 'dependencies' in poetry:
                    dependencies.extend(poetry['dependencies'].keys())
                if 'dev-dependencies' in poetry:
                    dependencies.extend(poetry['dev-dependencies'].keys())

            # Detect frameworks from dependencies
            for dep in dependencies:
                package_name = self._parse_requirement_line(str(dep))
                if package_name and package_name in self.REQUIREMENTS_FRAMEWORK_MAP:
                    framework = self.REQUIREMENTS_FRAMEWORK_MAP[package_name]
                    self.analysis.detected_frameworks.add(framework)

        except Exception as e:
            self.analysis.warnings.append(f"Could not fully parse pyproject.toml: {e}")

    def _analyze_pyproject_toml_regex(self, content: str) -> None:
        """Fallback regex parsing for pyproject.toml when toml library unavailable."""
        import re

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
            import re

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
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                module_info.imports.add(module_name)
                self._check_framework(module_name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                module_info.imports.add(module_name)
                self._check_framework(module_name)

                # Track specific imports
                imported_names = set()
                for alias in node.names:
                    if alias.name != '*':
                        imported_names.add(alias.name)
                        self._check_framework(alias.name)

                if module_name not in module_info.from_imports:
                    module_info.from_imports[module_name] = set()
                module_info.from_imports[module_name].update(imported_names)

    def _process_top_level(self, node: ast.AST, module_info: ModuleInfo) -> None:
        """Process top-level definitions."""
        # Check for __all__ definition
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                module_info.exports.add(elt.value)
                                self.analysis.public_api.add(elt.value)

        # Check for function definitions
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            name = node.name

            # Skip test functions
            if name.startswith('test_') or name.startswith('_'):
                return

            module_info.public_names.add(name)

            # Check for entry points
            if name.lower() in {ep.lower() for ep in self.ENTRY_POINT_PATTERNS}:
                module_info.entry_points.add(name)
                self.analysis.entry_points.add(name)

        # Check for class definitions
        elif isinstance(node, ast.ClassDef):
            name = node.name

            # Skip test classes
            if name.startswith('Test') or name.startswith('_'):
                return

            module_info.public_names.add(name)

            # Check for entry point classes
            if name in self.ENTRY_POINT_PATTERNS or any(
                ep.lower() in name.lower() for ep in ['Window', 'App', 'Application', 'GUI', 'Dialog']
            ):
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
        # Check for if __name__ == '__main__' blocks
        for module_info in self.analysis.modules.values():
            try:
                content = module_info.path.read_text(encoding='utf-8')
                if "if __name__ ==" in content or 'if __name__==' in content:
                    # This file has a main block, check for main() call
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.If):
                            # Look for main() calls in the if block
                            for stmt in ast.walk(node):
                                if isinstance(stmt, ast.Call):
                                    if isinstance(stmt.func, ast.Name):
                                        func_name = stmt.func.id
                                        if func_name in module_info.public_names:
                                            self.analysis.entry_points.add(func_name)
            except Exception:
                pass

        # Add common CLI entry points if click is detected
        if 'click' in self.analysis.detected_frameworks:
            self.analysis.entry_points.update({'cli', 'main', 'app'})

        # Add common web entry points
        if 'flask' in self.analysis.detected_frameworks:
            self.analysis.entry_points.update({'create_app', 'app', 'application'})
        if 'fastapi' in self.analysis.detected_frameworks:
            self.analysis.entry_points.update({'app', 'create_app', 'get_app'})
        if 'django' in self.analysis.detected_frameworks:
            self.analysis.entry_points.update({'urlpatterns', 'application', 'wsgi', 'asgi'})

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
            'generated_by': 'pyobfuscator analyzer',
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
            output_path: Path to save the config (default: pyobfuscator.json in project root)
            format: 'json' or 'toml'

        Returns:
            Path to the saved config file
        """
        config = self.generate_config()

        if output_path is None:
            output_path = self.project_path / f'pyobfuscator.{format}'
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
        lines = []

        # Process simple values first
        for key, value in config.items():
            if key.startswith('_'):
                continue  # Skip metadata for TOML

            if isinstance(value, dict):
                continue  # Handle nested dicts later
            elif isinstance(value, list):
                if all(isinstance(v, str) for v in value):
                    items = ', '.join(f'"{v}"' for v in value)
                    lines.append(f'{key} = [{items}]')
                else:
                    items = ', '.join(str(v) for v in value)
                    lines.append(f'{key} = [{items}]')
            elif isinstance(value, bool):
                lines.append(f'{key} = {str(value).lower()}')
            elif isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, (int, float)):
                lines.append(f'{key} = {value}')

        # Add metadata as comments
        if '_metadata' in config:
            lines.append('')
            lines.append('# Generated configuration metadata')
            metadata = config['_metadata']
            for key, value in metadata.items():
                if isinstance(value, list):
                    for item in value:
                        lines.append(f'# {key}: {item}')
                else:
                    lines.append(f'# {key}: {value}')

        return '\n'.join(lines) + '\n'

    def print_summary(self) -> None:
        """Print a summary of the analysis to stdout."""
        print(f"\n{'='*60}")
        print(f"Project Analysis: {self.project_path.name}")
        print(f"{'='*60}\n")

        print(f"Total Python files: {len(self.analysis.modules)}")

        if self.analysis.detected_frameworks:
            print(f"\nDetected frameworks:")
            for fw in sorted(self.analysis.detected_frameworks):
                print(f"  - {fw}")
        else:
            print("\nNo specific frameworks detected.")

        if self.analysis.entry_points:
            print(f"\nEntry points ({len(self.analysis.entry_points)}):")
            for ep in sorted(self.analysis.entry_points)[:10]:
                print(f"  - {ep}")
            if len(self.analysis.entry_points) > 10:
                print(f"  ... and {len(self.analysis.entry_points) - 10} more")

        if self.analysis.public_api:
            print(f"\nPublic API names ({len(self.analysis.public_api)}):")
            for name in sorted(self.analysis.public_api)[:10]:
                print(f"  - {name}")
            if len(self.analysis.public_api) > 10:
                print(f"  ... and {len(self.analysis.public_api) - 10} more")

        if self.analysis.warnings:
            print(f"\nWarnings:")
            for warning in self.analysis.warnings:
                print(f"  ! {warning}")

        if self.analysis.recommendations:
            print(f"\nRecommendations:")
            for rec in self.analysis.recommendations:
                print(f"  * {rec}")

        print(f"\n{'='*60}\n")


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

