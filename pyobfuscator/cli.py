# -*- coding: utf-8 -*-
"""
Command-line interface for Skjol.
Supports multiple commands:
- obfuscate: Obfuscate Python source code
- analyze: Analyze a project and generate configuration
- init: Initialize a skjol.json config file
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from ._version import __version__
from .constants import (
    CLI_NAME,
    CONFIG_BASENAME,
    LEGACY_CONFIG_BASENAME,
    PRODUCT_NAME,
    RUNTIME_MODULE_PREFIX,
)
from .obfuscator import Obfuscator


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from a JSON or TOML file."""
    if not config_path.exists():
        return {}

    content = config_path.read_text(encoding='utf-8')

    if config_path.suffix == '.json':
        return json.loads(content)
    if config_path.suffix == '.toml':
        return _load_toml(content)
    return {}


def _load_toml(content: str) -> Dict[str, Any]:
    """Helper to load TOML content with appropriate library."""
    try:
        import tomllib
        return tomllib.loads(content)
    except ImportError:
        try:
            import tomli
            return tomli.loads(content)
        except ImportError:
            print("Warning: TOML config requires Python 3.11+ or 'tomli' package", file=sys.stderr)
            return {}


def find_config() -> Optional[Path]:
    """Find configuration file in current directory."""
    candidates = [
        f'{CONFIG_BASENAME}.json',
        f'{CONFIG_BASENAME}.toml',
        f'.{CONFIG_BASENAME}.json',
        f'.{CONFIG_BASENAME}.toml',
        f'{LEGACY_CONFIG_BASENAME}.json',
        f'{LEGACY_CONFIG_BASENAME}.toml',
        f'.{LEGACY_CONFIG_BASENAME}.json',
        f'.{LEGACY_CONFIG_BASENAME}.toml',
    ]
    for name in candidates:
        path = Path(name)
        if path.exists():
            return path
    return None


# Constants for repeated CLI strings
HELP_VERBOSE = 'Verbose output'
HELP_INPUT = 'Input file or directory'
HELP_OUTPUT = 'Output file or directory'
DEFAULT_EXCLUDES = ['__pycache__', '*.pyc', 'test_*', '*_test.py']
DEFAULT_LICENSE = f'Protected by {PRODUCT_NAME}'
LOCAL_IMPORT_MARKERS = ('from .', 'from app', 'import app')
LOCAL_IMPORT_WARNING = (
    "Warning: This file appears to have local imports.\n"
    "         For multi-file projects, obfuscate the entire directory.\n"
)


@dataclass(frozen=True)
class DirectoryObfuscationOptions:
    """Normalized CLI options for one directory-processing command."""

    verbose: bool
    use_parallel: bool
    workers: Optional[int]
    recursive: bool
    exclude_patterns: Optional[List[str]]

    @classmethod
    def from_namespace(cls, parsed: argparse.Namespace) -> 'DirectoryObfuscationOptions':
        patterns = getattr(parsed, 'exclude_patterns', DEFAULT_EXCLUDES)
        return cls(
            verbose=getattr(parsed, 'verbose', False),
            use_parallel=getattr(parsed, 'parallel', False),
            workers=getattr(parsed, 'workers', None),
            recursive=(
                getattr(parsed, 'recursive', True)
                and not getattr(parsed, 'no_recursive', False)
            ),
            exclude_patterns=list(patterns) if patterns is not None else None,
        )


@dataclass(frozen=True)
class DirectoryProcessingResult:
    """Directory outcomes and the exit-code policy derived from them."""

    files: Mapping[str, str]
    output_path: Path
    encrypted: bool

    @property
    def success_count(self) -> int:
        return sum(result == 'success' for result in self.files.values())

    @property
    def error_count(self) -> int:
        return len(self.files) - self.success_count

    @property
    def exit_code(self) -> int:
        return int(self.error_count > 0)

    @property
    def message_suffix(self) -> str:
        return '(Code is encrypted with AES-256-GCM)' if self.encrypted else ''


class DirectoryResultReporter:
    """Render directory progress independently from processing decisions."""

    @staticmethod
    def print_start(
        input_path: Path,
        output_path: Path,
        encrypted: bool,
        options: DirectoryObfuscationOptions,
    ) -> None:
        if not options.verbose:
            return
        action = 'Protecting' if encrypted else 'Obfuscating'
        parallel = DirectoryResultReporter._parallel_description(options)
        print(f'{action} directory: {input_path}{parallel}')
        print(f'Output directory: {output_path}\n')

    @staticmethod
    def _parallel_description(options: DirectoryObfuscationOptions) -> str:
        if not options.use_parallel:
            return ''
        return f" (parallel, {options.workers or 'auto'} workers)"

    def print_result(self, result: DirectoryProcessingResult, verbose: bool) -> None:
        if verbose:
            self._print_file_results(result.files)
        self._print_summary(result)

    @staticmethod
    def _print_file_results(results: Mapping[str, str]) -> None:
        print('\nResults:')
        for file_path, outcome in sorted(results.items()):
            DirectoryResultReporter._print_file_result(file_path, outcome)

    @staticmethod
    def _print_file_result(file_path: str, outcome: str) -> None:
        status = '[OK]' if outcome == 'success' else '[FAIL]'
        print(f'  {status} {file_path}')
        if outcome != 'success':
            print(f'        Error: {outcome}')

    @staticmethod
    def _print_summary(result: DirectoryProcessingResult) -> None:
        print(f'\nProcessing complete! {result.message_suffix}')
        print(f'  - Files processed: {result.success_count}')
        print(f'  - Errors: {result.error_count}')
        print(f'  - Output: {result.output_path}')


class DirectoryObfuscationWorkflow:
    """Coordinate directory processing through the selected backend."""

    def __init__(
        self,
        obfuscator: Obfuscator,
        input_path: Path,
        output_path: Path,
        options: DirectoryObfuscationOptions,
        reporter: Optional[DirectoryResultReporter] = None,
    ):
        self._obfuscator = obfuscator
        self._input_path = input_path
        self._output_path = output_path
        self._options = options
        self._reporter = reporter or DirectoryResultReporter()

    def run(self) -> int:
        self._output_path.mkdir(parents=True, exist_ok=True)
        encrypted = bool(self._obfuscator.config.get('encrypt_code'))
        self._reporter.print_start(
            self._input_path,
            self._output_path,
            encrypted,
            self._options,
        )
        result = self._process(encrypted)
        self._reporter.print_result(result, self._options.verbose)
        return result.exit_code

    def _process(self, encrypted: bool) -> DirectoryProcessingResult:
        files = self._protect_directory() if encrypted else self._obfuscate_directory()
        return DirectoryProcessingResult(files, self._output_path, encrypted)

    def _protect_directory(self) -> Mapping[str, str]:
        if self._uses_rust_backend():
            from .runtime_backends import RustRuntimeBackend

            return RustRuntimeBackend(self._obfuscator).protect_directory(
                self._input_path,
                self._output_path,
                recursive=self._options.recursive,
                exclude_patterns=self._options.exclude_patterns,
            )["files"]
        backend = self._native_backend() if self._uses_pyd_backend() else self._obfuscator
        result = backend.protect_directory(
            self._input_path,
            self._output_path,
            recursive=self._options.recursive,
            exclude_patterns=self._options.exclude_patterns,
        )
        return result['files']

    def _obfuscate_directory(self) -> Mapping[str, str]:
        return self._obfuscator.obfuscate_directory(
            self._input_path,
            self._output_path,
            recursive=self._options.recursive,
            exclude_patterns=self._options.exclude_patterns,
        )

    def _uses_pyd_backend(self) -> bool:
        return bool(self._obfuscator.config.get('use_pyd_compilation'))

    def _uses_rust_backend(self) -> bool:
        return self._obfuscator.config.get('runtime_backend') == 'rust'

    def _native_backend(self) -> Any:
        return self._obfuscator.runtime_protector


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description='Python code obfuscation tool with auto-detection and framework support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_get_cli_epilog()
    )

    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-i', '--input', help=f'{HELP_INPUT} (shortcut for obfuscate)')
    parser.add_argument('-o', '--output', help=f'{HELP_OUTPUT} (shortcut for obfuscate)')
    parser.add_argument('-v', '--verbose', action='store_true', help=HELP_VERBOSE)

    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    _setup_analyze_parser(subparsers)
    _setup_init_parser(subparsers)
    _setup_obfuscate_parser(subparsers)
    _setup_protect_parser(subparsers)

    return parser


def _get_cli_epilog() -> str:
    return '''
Commands:
  obfuscate   Obfuscate Python source code (default if -i/-o provided)
  analyze     Analyze a project and show detected frameworks/entry points
  init        Generate a skjol.json config file for a project

Examples:
  skjol init ./my_project
  skjol obfuscate -i ./my_project -o ./dist
  skjol -i script.py -o protected.py
        '''


def _setup_analyze_parser(subparsers):
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a project')
    analyze_parser.add_argument('project_path', nargs='?', default='.', help='Path to project')
    analyze_parser.add_argument('--format', choices=['text', 'json'], default='text')
    analyze_parser.add_argument('-v', '--verbose', action='store_true', help=HELP_VERBOSE)


def _setup_init_parser(subparsers):
    init_parser = subparsers.add_parser('init', help='Generate config file')
    init_parser.add_argument('project_path', nargs='?', default='.', help='Path to project')
    init_parser.add_argument('-o', '--output', help='Output config path')
    init_parser.add_argument('--format', choices=['json', 'toml'], default='json')
    init_parser.add_argument('-v', '--verbose', action='store_true', help=HELP_VERBOSE)
    init_parser.add_argument('--force', action='store_true', help='Overwrite existing')


def _setup_obfuscate_parser(subparsers):
    obfuscate_parser = subparsers.add_parser('obfuscate', help='Obfuscate source code')
    _add_obfuscate_arguments(obfuscate_parser)


def _setup_protect_parser(subparsers):
    protect_parser = subparsers.add_parser('protect', help='Protect code with PYD encryption')
    protect_parser.add_argument('-i', '--input', help=HELP_INPUT)
    protect_parser.add_argument('-o', '--output', help=HELP_OUTPUT)
    protect_parser.add_argument('--license-info', default=DEFAULT_LICENSE)
    protect_parser.add_argument('--expire-days', type=int)
    protect_parser.add_argument('--bind-machine', action='store_true')
    protect_parser.add_argument('--machine-id', action='store_true')
    protect_parser.add_argument('--no-anti-debug', action='store_true')
    protect_parser.add_argument('--no-build-pyd', action='store_true')
    protect_parser.add_argument('--exclude-patterns', nargs='+', default=DEFAULT_EXCLUDES)
    protect_parser.add_argument('-v', '--verbose', action='store_true', help=HELP_VERBOSE)


def _add_obfuscate_arguments(parser: argparse.ArgumentParser) -> None:
    """Add obfuscation arguments to a parser."""
    parser.add_argument('-i', '--input', required=True, help=HELP_INPUT)
    parser.add_argument('-o', '--output', required=True, help=HELP_OUTPUT)
    parser.add_argument('-r', '--recursive', action='store_true', default=True)
    parser.add_argument('--no-recursive', action='store_true')
    parser.add_argument('--no-rename-vars', action='store_true')
    parser.add_argument('--no-rename-funcs', action='store_true')
    parser.add_argument('--no-rename-classes', action='store_true')
    parser.add_argument('--no-string-obfuscation', action='store_true')
    parser.add_argument('--compress', action='store_true')
    parser.add_argument('--keep-docstrings', action='store_true')
    parser.add_argument('--name-style', choices=['random', 'hex', 'hash'], default='random')
    parser.add_argument('--string-method', choices=['polymorphic', 'xor', 'hex', 'base64'], default='polymorphic')
    parser.add_argument('--exclude', nargs='+', default=[])
    parser.add_argument('--exclude-patterns', nargs='+', default=DEFAULT_EXCLUDES)
    parser.add_argument('--frameworks', nargs='+', default=[],
                        choices=['pyside6', 'pyqt6', 'flask', 'django', 'fastapi', 'asyncio', 'click', 'sqlalchemy'])
    parser.add_argument('--entry-points', nargs='+', default=[])
    parser.add_argument('--preserve-public', action='store_true')
    parser.add_argument('--control-flow', action='store_true')
    parser.add_argument('--control-flow-flatten', action='store_true')
    parser.add_argument('--code-virtualization', action='store_true')
    parser.add_argument('--whitebox', action='store_true')
    parser.add_argument('--numbers', action='store_true')
    parser.add_argument('--builtins', action='store_true')
    parser.add_argument('--integrity-check', action='store_true')
    parser.add_argument(
        '--pyd',
        action='store_true',
        help='Deprecated alias for --runtime cython',
    )
    parser.add_argument(
        '--runtime',
        choices=['python', 'cython', 'rust'],
        help='Runtime backend (default: python; rust requires the rust extra and toolchain)',
    )
    parser.add_argument('--all-advanced', action='store_true')
    parser.add_argument('--intensity', type=int, choices=[1, 2, 3], default=1)
    parser.add_argument('--config', type=str)
    parser.add_argument('--no-encrypt', action='store_true')
    parser.add_argument('--no-anti-debug', action='store_true')
    parser.add_argument('--license-info', type=str, default=DEFAULT_LICENSE)
    parser.add_argument('--expire-days', type=int)
    parser.add_argument('--bind-machine', action='store_true')
    parser.add_argument('--parallel', action='store_true', help='Enable parallel file processing')
    parser.add_argument('--workers', type=int, default=None, help='Number of parallel workers')
    parser.add_argument('-v', '--verbose', action='store_true', help=HELP_VERBOSE)


def _create_obfuscator(parsed: argparse.Namespace) -> Obfuscator:
    """Create an Obfuscator instance from parsed arguments."""
    from datetime import datetime, timedelta
    from .crypto import get_machine_id

    # Handle advanced flags
    all_adv = getattr(parsed, 'all_advanced', False)
    adv_config = {
        'control_flow': getattr(parsed, 'control_flow', False) or all_adv,
        'control_flow_flatten': getattr(parsed, 'control_flow_flatten', False) or all_adv,
        'code_virtualization': getattr(parsed, 'code_virtualization', False) or all_adv,
        'use_whitebox': getattr(parsed, 'whitebox', False) or all_adv,
        'number_obfuscation': getattr(parsed, 'numbers', False) or all_adv,
        'builtin_obfuscation': getattr(parsed, 'builtins', False) or all_adv,
        'integrity_checks': getattr(parsed, 'integrity_check', False) or all_adv,
    }

    # Handle expiration
    expiration_date = None
    expire_days = getattr(parsed, 'expire_days', None)
    if expire_days:
        expiration_date = datetime.now() + timedelta(days=expire_days)

    # Handle machine binding
    allowed_machines = [get_machine_id()] if getattr(parsed, 'bind_machine', False) else None

    runtime_backend = _resolve_runtime_backend(parsed)
    return Obfuscator(
        config={
            'encrypt_code': not getattr(parsed, 'no_encrypt', False),
            'runtime_backend': runtime_backend,
            'use_pyd_compilation': runtime_backend == 'cython',
            'anti_debug': not getattr(parsed, 'no_anti_debug', False),
            'license_info': getattr(parsed, 'license_info', DEFAULT_LICENSE),
            'expiration_date': expiration_date,
            'allowed_machines': allowed_machines,
            'rename_variables': not parsed.no_rename_vars,
            'rename_functions': not parsed.no_rename_funcs,
            'rename_classes': not parsed.no_rename_classes,
            'obfuscate_strings': not parsed.no_string_obfuscation,
            'compress_code': parsed.compress,
            'remove_docstrings': not parsed.keep_docstrings,
            'name_style': parsed.name_style,
            'string_method': parsed.string_method,
            'exclude_names': set(parsed.exclude),
            'frameworks': parsed.frameworks if parsed.frameworks else None,
            'entry_points': parsed.entry_points if parsed.entry_points else None,
            'preserve_public_api': parsed.preserve_public,
            'intensity': getattr(parsed, 'intensity', 1),
            **adv_config
        }
    )


class SingleFileObfuscationWorkflow:
    """Coordinate one input file without mixing backend and reporting logic."""

    def __init__(
        self,
        obfuscator: Obfuscator,
        input_path: Path,
        output_path: Path,
        verbose: bool,
    ):
        self._obfuscator = obfuscator
        self._input_path = input_path
        self._output_path = output_path
        self._verbose = verbose

    def run(self) -> int:
        target_path = self._resolve_target_path()
        _warn_if_local_imports(self._input_path)
        self._print_start()
        if self._is_encrypted():
            self._protect(target_path)
        else:
            self._obfuscate(target_path)
        return 0

    def _resolve_target_path(self) -> Path:
        if self._output_path.is_dir():
            return self._output_path / self._input_path.name
        if not self._output_path.suffix and not self._output_path.exists():
            self._output_path.mkdir(parents=True, exist_ok=True)
            return self._output_path / self._input_path.name
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        return self._output_path

    def _protect(self, target_path: Path) -> None:
        if self._uses_rust_runtime():
            self._protect_with_rust(target_path)
            return
        self._protect_with_python(target_path)

    def _protect_with_rust(self, target_path: Path) -> None:
        from .runtime_backends import RustRuntimeBackend

        build = RustRuntimeBackend(self._obfuscator).protect_file(
            self._input_path,
            target_path,
        )
        self._print_output(target_path, build.extension_path)
        print("Protection complete! (Rust native runtime, AES-256-GCM)")

    def _protect_with_python(self, target_path: Path) -> None:
        source = self._input_path.read_text(encoding='utf-8')
        protected, runtime = self._obfuscator.protect_source(
            source,
            self._input_path.name,
        )
        target_path.write_text(protected, encoding='utf-8')
        runtime_path = self._python_runtime_path(target_path)
        runtime_path.write_text(runtime, encoding='utf-8')
        self._print_output(target_path, runtime_path)
        print("Protection complete! (Code is encrypted with AES-256-GCM)")

    def _python_runtime_path(self, target_path: Path) -> Path:
        runtime_id = self._obfuscator.runtime_protector.runtime_id
        return target_path.parent / f"{RUNTIME_MODULE_PREFIX}{runtime_id}.py"

    def _obfuscate(self, target_path: Path) -> None:
        self._obfuscator.obfuscate_file(self._input_path, target_path)
        self._print_output(target_path)
        print("Obfuscation complete!")

    def _print_start(self) -> None:
        if not self._verbose:
            return
        action = "Protecting (obfuscate + encrypt)" if self._is_encrypted() else "Obfuscating"
        print(f"{action} {self._input_path}...")

    def _print_output(
        self,
        target_path: Path,
        runtime_path: Optional[Path] = None,
    ) -> None:
        if not self._verbose:
            return
        print(f"Output written to {target_path}")
        if runtime_path is not None:
            print(f"Runtime module: {runtime_path}")

    def _is_encrypted(self) -> bool:
        return bool(self._obfuscator.config.get('encrypt_code'))

    def _uses_rust_runtime(self) -> bool:
        return self._obfuscator.config.get('runtime_backend') == 'rust'


def _obfuscate_single_file(
    obfuscator: Obfuscator,
    input_path: Path,
    output_path: Path,
    verbose: bool,
) -> int:
    """Run the single-file workflow and return its CLI exit code."""
    return SingleFileObfuscationWorkflow(
        obfuscator,
        input_path,
        output_path,
        verbose,
    ).run()


def _warn_if_local_imports(input_path: Path) -> None:
    """Warn user if file has local imports."""
    try:
        content = input_path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return
    if any(marker in content for marker in LOCAL_IMPORT_MARKERS):
        print(LOCAL_IMPORT_WARNING, file=sys.stderr)


def _obfuscate_directory(
    obfuscator: Obfuscator,
    input_path: Path,
    output_path: Path,
    parsed: argparse.Namespace
) -> int:
    """Obfuscate a directory. Returns exit code."""
    options = DirectoryObfuscationOptions.from_namespace(parsed)
    return DirectoryObfuscationWorkflow(
        obfuscator,
        input_path,
        output_path,
        options,
    ).run()


def _merge_config(parsed: argparse.Namespace, config: Dict[str, Any]) -> argparse.Namespace:
    """Merge config file settings with CLI arguments (CLI takes precedence)."""
    # Map config keys to argparse attributes
    config_mapping = {
        'frameworks': 'frameworks',
        'entry_points': 'entry_points',
        'exclude': 'exclude',
        'exclude_patterns': 'exclude_patterns',
        'string_method': 'string_method',
        'name_style': 'name_style',
        'compress': 'compress',
        'keep_docstrings': 'keep_docstrings',
        'preserve_public': 'preserve_public',
        'no_rename_vars': 'no_rename_vars',
        'no_rename_funcs': 'no_rename_funcs',
        'no_rename_classes': 'no_rename_classes',
        'no_string_obfuscation': 'no_string_obfuscation',
        'verbose': 'verbose',
        'runtime': 'runtime',
    }

    for config_key, attr_name in config_mapping.items():
        if config_key not in config:
            continue
            
        current_value = getattr(parsed, attr_name, None)
        config_value = config[config_key]

        if isinstance(config_value, list) and isinstance(current_value, list):
            # Merge and keep unique items using set comprehension
            merged = list({item for item in (current_value + config_value)})
            setattr(parsed, attr_name, merged)
        elif current_value in (None, False, [], 'random', 'xor', 'polymorphic'):
            setattr(parsed, attr_name, config_value)

    return parsed


def _handle_analyze(parsed: argparse.Namespace) -> int:
    """Handle the analyze command."""
    from .analyzer import ProjectAnalyzer

    project_path = Path(parsed.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}", file=sys.stderr)
        return 1

    analyzer = ProjectAnalyzer(str(project_path))
    result = analyzer.analyze()

    if parsed.format == 'json':
        output = {
            'project_path': str(project_path),
            'frameworks': sorted(result.detected_frameworks),
            'entry_points': sorted(result.entry_points),
            'public_api': sorted(result.public_api),
            'packages': sorted({m.package.split('.')[0] for m in result.modules.values() if m.package}),
            'total_files': len(result.modules),
            'warnings': result.warnings,
            'recommendations': result.recommendations,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        analyzer.print_summary()

    return 0


def _handle_init(parsed: argparse.Namespace) -> int:
    """Handle the init command - generate config file."""
    from .analyzer import ProjectAnalyzer

    project_path = Path(parsed.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}", file=sys.stderr)
        return 1

    output_path = Path(parsed.output) if parsed.output else project_path / f'{CONFIG_BASENAME}.{parsed.format}'

    if output_path.exists() and not parsed.force:
        print(f"Error: Config file already exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    print(f"Analyzing project: {project_path}")
    analyzer = ProjectAnalyzer(str(project_path))
    result = analyzer.analyze()

    if parsed.verbose:
        analyzer.print_summary()

    analyzer.save_config(output_path, format=parsed.format)

    print(f"\nConfiguration saved to: {output_path}")
    print(f"  - Frameworks detected: {', '.join(sorted(result.detected_frameworks)) or 'none'}")
    print(f"  - Entry points: {len(result.entry_points)}")
    print(f"  - Public API names: {len(result.public_api)}")

    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations[:3]:
            print(f"  * {rec}")

    return 0


def _handle_obfuscate(parsed: argparse.Namespace) -> int:
    """Handle the obfuscate command."""
    config = _get_merged_config(parsed)
    if config is None:
        return 1
    if config:
        parsed = _merge_config(parsed, config)

    input_path = Path(parsed.input)
    output_path = Path(parsed.output)

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        _validate_runtime_selection(parsed)
        obfuscator = _create_obfuscator(parsed)
        if input_path.is_file():
            return _obfuscate_single_file(obfuscator, input_path, output_path, parsed.verbose)
        if input_path.is_dir():
            return _obfuscate_directory(obfuscator, input_path, output_path, parsed)
        print(f"Error: Input path is neither file nor directory: {input_path}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _resolve_runtime_backend(parsed: argparse.Namespace) -> str:
    runtime = getattr(parsed, 'runtime', None)
    if getattr(parsed, 'pyd', False):
        if runtime not in (None, 'cython'):
            raise ValueError("--pyd cannot be combined with a conflicting --runtime value")
        return 'cython'
    return runtime or 'python'


def _validate_runtime_selection(parsed: argparse.Namespace) -> None:
    runtime = _resolve_runtime_backend(parsed)
    if getattr(parsed, 'no_encrypt', False) and runtime != 'python':
        raise ValueError(f"--runtime {runtime} cannot be combined with --no-encrypt")
    if runtime != 'rust':
        return
    unsupported = []
    if getattr(parsed, 'expire_days', None):
        unsupported.append('--expire-days')
    if getattr(parsed, 'bind_machine', False):
        unsupported.append('--bind-machine')
    if unsupported:
        raise ValueError(
            "Rust runtime does not yet support " + ", ".join(unsupported)
        )


def _get_merged_config(parsed: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """Auto-detect and load config file."""
    if hasattr(parsed, 'config') and parsed.config:
        config_path = Path(parsed.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}", file=sys.stderr)
            return None
        return load_config(config_path)
    
    input_path = Path(parsed.input)
    if input_path.is_dir():
        for name in [
            f'{CONFIG_BASENAME}.json',
            f'{CONFIG_BASENAME}.toml',
            f'{LEGACY_CONFIG_BASENAME}.json',
            f'{LEGACY_CONFIG_BASENAME}.toml',
        ]:
            config_file = input_path / name
            if config_file.exists():
                return load_config(config_file)
    
    auto_config = find_config()
    return load_config(auto_config) if auto_config else {}


def _handle_protect(parsed: argparse.Namespace) -> int:
    """Handle the protect command - PYD runtime encryption."""
    from .pyd_protection import PydRuntimeProtector
    from datetime import datetime, timedelta

    if getattr(parsed, 'machine_id', False):
        print(f"Machine ID: {PydRuntimeProtector.get_machine_id()}")
        return 0

    if not parsed.input or not parsed.output:
        print("Error: -i/--input and -o/--output are required for protection", file=sys.stderr)
        return 1

    input_path = Path(parsed.input).resolve()
    output_path = Path(parsed.output).resolve()

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    expire_date = datetime.now() + timedelta(days=parsed.expire_days) if parsed.expire_days else None
    allowed = [PydRuntimeProtector.get_machine_id()] if parsed.bind_machine else []

    protector = PydRuntimeProtector(
        license_info=parsed.license_info,
        expiration_date=expire_date,
        allowed_machines=allowed,
        anti_debug=not parsed.no_anti_debug,
    )

    try:
        if input_path.is_file():
            protector.protect_file(input_path, output_path, build_pyd=not parsed.no_build_pyd)
        elif input_path.is_dir():
            protector.protect_directory(input_path, output_path, build_pyd=not parsed.no_build_pyd)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_main_parser()
    parsed = parser.parse_args(args)

    handlers = {
        'analyze': _handle_analyze,
        'init': _handle_init,
        'obfuscate': _handle_obfuscate,
        'protect': _handle_protect
    }

    if parsed.command in handlers:
        return handlers[parsed.command](parsed)

    if hasattr(parsed, 'input') and parsed.input and hasattr(parsed, 'output') and parsed.output:
        new_args = ['obfuscate', '-i', parsed.input, '-o', parsed.output]
        if parsed.verbose:
            new_args.append('-v')
        return main(new_args)

    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
