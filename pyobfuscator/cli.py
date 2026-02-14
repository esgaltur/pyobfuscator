# -*- coding: utf-8 -*-
"""
Command-line interface for PyObfuscator.
Supports multiple commands:
- obfuscate: Obfuscate Python source code
- analyze: Analyze a project and generate configuration
- init: Initialize a pyobfuscator.json config file
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from .obfuscator import Obfuscator


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from a JSON or TOML file."""
    if not config_path.exists():
        return {}

    content = config_path.read_text(encoding='utf-8')

    if config_path.suffix == '.json':
        return json.loads(content)
    elif config_path.suffix == '.toml':
        # Try to use tomllib (Python 3.11+) or tomli
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
    return {}


def find_config() -> Optional[Path]:
    """Find configuration file in current directory."""
    for name in ['pyobfuscator.json', 'pyobfuscator.toml', '.pyobfuscator.json', '.pyobfuscator.toml']:
        path = Path(name)
        if path.exists():
            return path
    return None


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog='pyobfuscator',
        description='Python code obfuscation tool with auto-detection and framework support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Commands:
  obfuscate   Obfuscate Python source code (default if -i/-o provided)
  analyze     Analyze a project and show detected frameworks/entry points
  init        Generate a pyobfuscator.json config file for a project

Examples:
  # Analyze a project and generate config
  pyobfuscator init ./my_project
  
  # Or analyze without saving
  pyobfuscator analyze ./my_project

  # Obfuscate using auto-detected config
  pyobfuscator obfuscate -i ./my_project -o ./dist

  # Single file (short form)
  pyobfuscator -i script.py -o obfuscated.py

  # PySide6 app with framework preset
  pyobfuscator -i my_app/ -o dist/ --frameworks pyside6
        '''
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    # For backwards compatibility: allow pyobfuscator -i src -o dist
    parser.add_argument('-i', '--input', help='Input file or directory (shortcut for obfuscate)')
    parser.add_argument('-o', '--output', help='Output file or directory (shortcut for obfuscate)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # ===== ANALYZE command =====
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze a project and show detected frameworks, entry points, and public API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  pyobfuscator analyze ./my_project
  pyobfuscator analyze ./my_project --format json
  pyobfuscator analyze . --verbose
        '''
    )
    analyze_parser.add_argument(
        'project_path',
        nargs='?',
        default='.',
        help='Path to the project directory (default: current directory)'
    )
    analyze_parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    analyze_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed analysis'
    )

    # ===== INIT command =====
    init_parser = subparsers.add_parser(
        'init',
        help='Analyze a project and generate a pyobfuscator.json config file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  pyobfuscator init ./my_project
  pyobfuscator init . --output pyobfuscator.toml --format toml
  pyobfuscator init ./my_app --verbose
        '''
    )
    init_parser.add_argument(
        'project_path',
        nargs='?',
        default='.',
        help='Path to the project directory (default: current directory)'
    )
    init_parser.add_argument(
        '-o', '--output',
        help='Output config file path (default: pyobfuscator.json in project root)'
    )
    init_parser.add_argument(
        '--format',
        choices=['json', 'toml'],
        default='json',
        help='Config file format (default: json)'
    )
    init_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show analysis summary'
    )
    init_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing config file'
    )

    # ===== OBFUSCATE command =====
    obfuscate_parser = subparsers.add_parser(
        'obfuscate',
        help='Obfuscate Python source code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  pyobfuscator obfuscate -i script.py -o obfuscated.py
  pyobfuscator obfuscate -i src/ -o dist/ --frameworks pyside6
  pyobfuscator obfuscate -i app/ -o dist/ --config pyobfuscator.json
        '''
    )
    _add_obfuscate_arguments(obfuscate_parser)

    # ===== PROTECT command (PYD encryption) =====
    protect_parser = subparsers.add_parser(
        'protect',
        help='Protect code with PYD runtime encryption (AES-256-GCM)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
PYD Protection creates encrypted bytecode with a compiled native runtime.
This provides the strongest protection level.

Examples:
  # Protect entire project with PYD encryption
  pyobfuscator protect -i ./my_project -o ./dist

  # Protect with expiration date (365 days)
  pyobfuscator protect -i ./src -o ./dist --expire-days 365

  # Protect with machine binding
  pyobfuscator protect -i ./src -o ./dist --bind-machine

  # Get machine ID for binding
  pyobfuscator protect --machine-id
        '''
    )
    protect_parser.add_argument(
        '-i', '--input',
        help='Input file or directory to protect'
    )
    protect_parser.add_argument(
        '-o', '--output',
        help='Output directory for protected files'
    )
    protect_parser.add_argument(
        '--license-info',
        default='PyObfuscator Protected',
        help='License/author info to embed (default: PyObfuscator Protected)'
    )
    protect_parser.add_argument(
        '--expire-days',
        type=int,
        default=None,
        help='Expiration in days from now (optional)'
    )
    protect_parser.add_argument(
        '--bind-machine',
        action='store_true',
        help='Bind to current machine (hardware lock)'
    )
    protect_parser.add_argument(
        '--machine-id',
        action='store_true',
        help='Print current machine ID and exit'
    )
    protect_parser.add_argument(
        '--no-anti-debug',
        action='store_true',
        help='Disable anti-debugging protection'
    )
    protect_parser.add_argument(
        '--no-build-pyd',
        action='store_true',
        help='Skip PYD compilation (generate .pyx only)'
    )
    protect_parser.add_argument(
        '--exclude-patterns',
        nargs='+',
        default=['__pycache__', '*.pyc', 'test_*', '*_test.py', 'tests/'],
        help='File patterns to exclude'
    )
    protect_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    return parser


def _add_obfuscate_arguments(parser: argparse.ArgumentParser) -> None:
    """Add obfuscation arguments to a parser."""
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input file or directory to obfuscate'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output file or directory for obfuscated code'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=True,
        help='Process directories recursively (default: True)'
    )

    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not process directories recursively'
    )

    parser.add_argument(
        '--no-rename-vars',
        action='store_true',
        help='Do not rename variables'
    )

    parser.add_argument(
        '--no-rename-funcs',
        action='store_true',
        help='Do not rename functions'
    )

    parser.add_argument(
        '--no-rename-classes',
        action='store_true',
        help='Do not rename classes'
    )

    parser.add_argument(
        '--no-string-obfuscation',
        action='store_true',
        help='Do not obfuscate strings'
    )

    parser.add_argument(
        '--compress',
        action='store_true',
        help='Compress the output code (wraps in exec statement)'
    )

    parser.add_argument(
        '--keep-docstrings',
        action='store_true',
        help='Keep docstrings in the output'
    )

    parser.add_argument(
        '--name-style',
        choices=['random', 'hex', 'hash'],
        default='random',
        help='Style for generated names (default: random)'
    )

    parser.add_argument(
        '--string-method',
        choices=['xor', 'hex', 'base64'],
        default='xor',
        help='Method for string obfuscation (default: xor). Note: base64/hex are encoding only, xor provides actual obfuscation'
    )

    parser.add_argument(
        '--exclude',
        nargs='+',
        default=[],
        help='Names to exclude from renaming'
    )

    parser.add_argument(
        '--exclude-patterns',
        nargs='+',
        default=['__pycache__', '*.pyc', 'test_*', '*_test.py'],
        help='File patterns to exclude (for directory processing)'
    )

    parser.add_argument(
        '--frameworks',
        nargs='+',
        default=[],
        choices=['pyside6', 'pyqt6', 'flask', 'django', 'fastapi', 'asyncio', 'click', 'sqlalchemy'],
        help='Framework presets - preserves framework-specific names (e.g., --frameworks pyside6 sqlalchemy)'
    )

    parser.add_argument(
        '--entry-points',
        nargs='+',
        default=[],
        help='Function/class names to preserve (e.g., --entry-points main App MainWindow)'
    )

    parser.add_argument(
        '--preserve-public',
        action='store_true',
        help='Preserve names listed in __all__ and public names (without underscore prefix)'
    )

    # Advanced obfuscation arguments
    parser.add_argument(
        '--control-flow',
        action='store_true',
        help='Enable control flow obfuscation (opaque predicates, dead code)'
    )

    parser.add_argument(
        '--control-flow-flatten',
        action='store_true',
        help='Enable control flow flattening (CFF) - transforms functions into state machines'
    )

    parser.add_argument(
        '--numbers',
        action='store_true',
        help='Enable numeric literal obfuscation'
    )

    parser.add_argument(
        '--builtins',
        action='store_true',
        help='Enable builtin function call obfuscation'
    )

    parser.add_argument(
        '--integrity-check',
        action='store_true',
        help='Enable integrity verification checks in functions'
    )

    parser.add_argument(
        '--all-advanced',
        action='store_true',
        help='Enable all advanced obfuscation features (control-flow, cff, numbers, builtins, integrity)'
    )

    parser.add_argument(
        '--intensity',
        type=int,
        choices=[1, 2, 3],
        default=1,
        help='Intensity level for advanced obfuscation (1-3, default: 1)'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel processing for directory obfuscation'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of worker threads for parallel processing (default: CPU count)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to config file (JSON or TOML). Auto-detects pyobfuscator.json/toml in current directory'
    )

    # Encryption/Protection options
    parser.add_argument(
        '--no-encrypt',
        action='store_true',
        help='Disable encryption (only apply name obfuscation). By default, code is encrypted with AES-256-GCM'
    )

    parser.add_argument(
        '--no-anti-debug',
        action='store_true',
        help='Disable anti-debugging protection'
    )

    parser.add_argument(
        '--license-info',
        type=str,
        default='Protected by PyObfuscator',
        help='License/author information embedded in protected files'
    )

    parser.add_argument(
        '--expire-days',
        type=int,
        default=None,
        help='Expiration in days from now (optional)'
    )

    parser.add_argument(
        '--bind-machine',
        action='store_true',
        help='Bind to current machine (hardware lock)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )



def _create_obfuscator(parsed: argparse.Namespace) -> Obfuscator:
    """Create an Obfuscator instance from parsed arguments."""
    from datetime import datetime, timedelta
    from .crypto import get_machine_id

    # Handle --all-advanced flag
    all_advanced = getattr(parsed, 'all_advanced', False)

    control_flow = getattr(parsed, 'control_flow', False) or all_advanced
    control_flow_flatten = getattr(parsed, 'control_flow_flatten', False) or all_advanced
    numbers = getattr(parsed, 'numbers', False) or all_advanced
    builtins = getattr(parsed, 'builtins', False) or all_advanced
    integrity_check = getattr(parsed, 'integrity_check', False) or all_advanced

    # Encryption options
    encrypt_code = not getattr(parsed, 'no_encrypt', False)
    anti_debug = not getattr(parsed, 'no_anti_debug', False)
    license_info = getattr(parsed, 'license_info', 'Protected by PyObfuscator')

    # Handle expiration
    expiration_date = None
    expire_days = getattr(parsed, 'expire_days', None)
    if expire_days:
        expiration_date = datetime.now() + timedelta(days=expire_days)

    # Handle machine binding
    allowed_machines = None
    if getattr(parsed, 'bind_machine', False):
        allowed_machines = [get_machine_id()]

    return Obfuscator(
        # Core protection
        encrypt_code=encrypt_code,
        anti_debug=anti_debug,
        license_info=license_info,
        expiration_date=expiration_date,
        allowed_machines=allowed_machines,
        # Name obfuscation
        rename_variables=not parsed.no_rename_vars,
        rename_functions=not parsed.no_rename_funcs,
        rename_classes=not parsed.no_rename_classes,
        obfuscate_strings=not parsed.no_string_obfuscation,
        compress_code=parsed.compress,
        remove_docstrings=not parsed.keep_docstrings,
        name_style=parsed.name_style,
        string_method=parsed.string_method,
        exclude_names=set(parsed.exclude),
        frameworks=parsed.frameworks if parsed.frameworks else None,
        entry_points=parsed.entry_points if parsed.entry_points else None,
        preserve_public_api=parsed.preserve_public,
        control_flow=control_flow,
        number_obfuscation=numbers,
        builtin_obfuscation=builtins,
        control_flow_flatten=control_flow_flatten,
        integrity_check=integrity_check,
        obfuscation_intensity=getattr(parsed, 'intensity', 1)
    )


def _obfuscate_single_file(
    obfuscator: Obfuscator,
    input_path: Path,
    output_path: Path,
    verbose: bool
) -> int:
    """Obfuscate a single file. Returns exit code."""
    # If output_path is an existing directory, put the file inside it
    if output_path.is_dir():
        output_path = output_path / input_path.name
    # If output_path doesn't exist but looks like a directory (no extension), create it
    elif not output_path.suffix and not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        output_path = output_path / input_path.name
    # Ensure parent directory exists
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file has local imports - warn user
    try:
        content = input_path.read_text(encoding='utf-8')
        if 'from .' in content or 'from app' in content or 'import app' in content:
            print("Warning: This file appears to have local imports.", file=sys.stderr)
            print("         For multi-file projects, obfuscate the entire directory:", file=sys.stderr)
            print(f"         pyobfuscator obfuscate -i {input_path.parent} -o {output_path.parent}", file=sys.stderr)
            print("", file=sys.stderr)
    except Exception:
        pass

    if verbose:
        if obfuscator.encrypt_code:
            print(f"Protecting (obfuscate + encrypt) {input_path}...")
        else:
            print(f"Obfuscating {input_path}...")

    # Read source
    with open(input_path, 'r', encoding='utf-8') as f:
        source = f.read()

    if obfuscator.encrypt_code:
        # Apply full protection: obfuscation + encryption
        protected, runtime = obfuscator.protect_source(source, str(input_path.name))

        # Write protected file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(protected)

        # Write runtime module in the same directory
        runtime_name = f"pyobfuscator_runtime_{obfuscator._runtime_protector.runtime_id}"
        runtime_path = output_path.parent / f"{runtime_name}.py"
        with open(runtime_path, 'w', encoding='utf-8') as f:
            f.write(runtime)

        if verbose:
            print(f"Output written to {output_path}")
            print(f"Runtime module: {runtime_path}")
        print("Protection complete! (Code is encrypted with AES-256-GCM)")
    else:
        # Just obfuscation
        obfuscator.obfuscate_file(input_path, output_path)
        if verbose:
            print(f"Output written to {output_path}")
        print("Obfuscation complete!")

    return 0


def _obfuscate_directory(
    obfuscator: Obfuscator,
    input_path: Path,
    output_path: Path,
    parsed: argparse.Namespace
) -> int:
    """Obfuscate a directory. Returns exit code."""
    verbose = getattr(parsed, 'verbose', False)

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        if obfuscator.encrypt_code:
            print(f"Protecting directory (obfuscate + encrypt): {input_path}")
        else:
            print(f"Obfuscating directory: {input_path}")
        print(f"Output directory: {output_path}")
        print("")

    recursive = getattr(parsed, 'recursive', True) and not getattr(parsed, 'no_recursive', False)
    exclude_patterns = getattr(parsed, 'exclude_patterns', ['__pycache__', '*.pyc', 'test_*', '*_test.py'])
    parallel = getattr(parsed, 'parallel', False)
    max_workers = getattr(parsed, 'workers', None)

    if verbose and parallel:
        print(f"Parallel processing enabled (workers: {max_workers or 'auto'})")
        print("")

    if obfuscator.encrypt_code:
        # Use protect_directory for full protection
        results, runtime = obfuscator.protect_directory(
            input_path,
            output_path,
            recursive=recursive,
            exclude_patterns=exclude_patterns
        )

        success_count = sum(1 for v in results.values() if v == "success")
        error_count = len(results) - success_count

        if verbose:
            print("\nResults:")
            for file_path, result in sorted(results.items()):
                status = "[OK]" if result == "success" else "[FAIL]"
                print(f"  {status} {file_path}")
                if result != "success":
                    print(f"        Error: {result}")

        print("\nProtection complete! (Code is encrypted with AES-256-GCM)")
        print(f"  - Files processed: {success_count}")
        print(f"  - Errors: {error_count}")
        print(f"  - Output: {output_path}")
        print(f"  - Runtime module: pyobfuscator_runtime_{obfuscator._runtime_protector.runtime_id}.py")
    else:
        # Just obfuscation
        results = obfuscator.obfuscate_directory(
            input_path,
            output_path,
            recursive=recursive,
            exclude_patterns=exclude_patterns,
            parallel=parallel,
            max_workers=max_workers
        )

        success_count = sum(1 for v in results.values() if v == "success")
        error_count = len(results) - success_count

        if verbose:
            print("\nResults:")
            for file_path, result in sorted(results.items()):
                status = "[OK]" if result == "success" else "[FAIL]"
                print(f"  {status} {file_path}")
                if result != "success":
                    print(f"        Error: {result}")

        print("\nObfuscation complete!")
        print(f"  - Files processed: {success_count}")
        print(f"  - Errors: {error_count}")
        print(f"  - Output: {output_path}")
    print(f"  - Output: {output_path}")

    return 1 if error_count > 0 else 0


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
    }

    for config_key, attr_name in config_mapping.items():
        if config_key in config:
            current_value = getattr(parsed, attr_name, None)
            config_value = config[config_key]

            # For lists, merge them (CLI values + config values)
            if isinstance(config_value, list) and isinstance(current_value, list):
                merged = list(set(current_value + config_value))
                setattr(parsed, attr_name, merged)
            # For booleans/strings, only use config if CLI didn't set it
            elif current_value in (None, False, [], 'random', 'xor'):
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
        # Output as JSON
        output = {
            'project_path': str(project_path),
            'frameworks': sorted(result.detected_frameworks),
            'entry_points': sorted(result.entry_points),
            'public_api': sorted(result.public_api),
            'packages': sorted(set(m.package.split('.')[0] for m in result.modules.values() if m.package)),
            'total_files': len(result.modules),
            'warnings': result.warnings,
            'recommendations': result.recommendations,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # Print human-readable summary
        analyzer.print_summary()

    return 0


def _handle_init(parsed: argparse.Namespace) -> int:
    """Handle the init command - generate config file."""
    from .analyzer import ProjectAnalyzer

    project_path = Path(parsed.project_path).resolve()

    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}", file=sys.stderr)
        return 1

    # Determine output path
    if parsed.output:
        output_path = Path(parsed.output)
    else:
        output_path = project_path / f'pyobfuscator.{parsed.format}'

    # Check if file exists
    if output_path.exists() and not parsed.force:
        print(f"Error: Config file already exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    # Analyze project
    print(f"Analyzing project: {project_path}")
    analyzer = ProjectAnalyzer(str(project_path))
    result = analyzer.analyze()

    # Print summary if verbose
    if parsed.verbose:
        analyzer.print_summary()

    # Save config
    analyzer.save_config(output_path, format=parsed.format)

    print(f"\nConfiguration saved to: {output_path}")
    print(f"  - Frameworks detected: {', '.join(sorted(result.detected_frameworks)) or 'none'}")
    print(f"  - Entry points: {len(result.entry_points)}")
    print(f"  - Public API names: {len(result.public_api)}")

    if result.recommendations:
        print(f"\nRecommendations:")
        for rec in result.recommendations[:3]:
            print(f"  * {rec}")

    print(f"\nNext steps:")
    print(f"  1. Review and edit {output_path}")
    print(f"  2. Run: pyobfuscator obfuscate -i {project_path} -o ./dist")

    return 0


def _handle_obfuscate(parsed: argparse.Namespace) -> int:
    """Handle the obfuscate command."""
    # Load config file if specified or auto-detect
    config: Dict[str, Any] = {}
    if hasattr(parsed, 'config') and parsed.config:
        config_path = Path(parsed.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}", file=sys.stderr)
            return 1
        config = load_config(config_path)
        if parsed.verbose:
            print(f"Loaded config from {config_path}")
    else:
        # Auto-detect config file in input directory
        input_path = Path(parsed.input)
        if input_path.is_dir():
            for name in ['pyobfuscator.json', 'pyobfuscator.toml']:
                config_file = input_path / name
                if config_file.exists():
                    config = load_config(config_file)
                    if parsed.verbose:
                        print(f"Auto-detected config from {config_file}")
                    break

        # Also check current directory
        if not config:
            auto_config = find_config()
            if auto_config:
                config = load_config(auto_config)
                if parsed.verbose:
                    print(f"Auto-detected config from {auto_config}")

    # Merge config with CLI arguments
    if config:
        parsed = _merge_config(parsed, config)

    input_path = Path(parsed.input)
    output_path = Path(parsed.output)

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    obfuscator = _create_obfuscator(parsed)

    # Print summary if verbose
    if parsed.verbose:
        print(f"Frameworks: {parsed.frameworks or 'none'}")
        print(f"Entry points: {parsed.entry_points or 'none'}")
        print(f"Excluded names: {len(parsed.exclude)} custom exclusions")

    try:
        if input_path.is_file():
            return _obfuscate_single_file(
                obfuscator, input_path, output_path, parsed.verbose
            )
        elif input_path.is_dir():
            return _obfuscate_directory(
                obfuscator, input_path, output_path, parsed
            )
        else:
            print(f"Error: Input path is neither a file nor directory: {input_path}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _handle_protect(parsed: argparse.Namespace) -> int:
    """Handle the protect command - PYD runtime encryption."""
    from .pyd_protection import PydRuntimeProtector
    from datetime import datetime, timedelta

    verbose = getattr(parsed, 'verbose', False)

    # Handle --machine-id flag
    if getattr(parsed, 'machine_id', False):
        machine_id = PydRuntimeProtector.get_machine_id()
        print(f"Machine ID: {machine_id}")
        print(f"\nUse this in your config or with --allowed-machines to bind code to this machine.")
        return 0

    # Validate input/output
    if not parsed.input or not parsed.output:
        print("Error: -i/--input and -o/--output are required for protection", file=sys.stderr)
        print("Use --machine-id to get the current machine ID", file=sys.stderr)
        return 1

    input_path = Path(parsed.input).resolve()
    output_path = Path(parsed.output).resolve()

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    # Build protector options
    expiration_date = None
    if parsed.expire_days:
        expiration_date = datetime.now() + timedelta(days=parsed.expire_days)

    allowed_machines = []
    if parsed.bind_machine:
        machine_id = PydRuntimeProtector.get_machine_id()
        allowed_machines = [machine_id]
        if verbose:
            print(f"Binding to machine: {machine_id}")

    # Create protector
    protector = PydRuntimeProtector(
        license_info=parsed.license_info,
        expiration_date=expiration_date,
        allowed_machines=allowed_machines,
        anti_debug=not parsed.no_anti_debug,
    )

    build_pyd = not parsed.no_build_pyd

    if verbose:
        print(f"PYD Protection Settings:")
        print(f"  - License: {parsed.license_info}")
        print(f"  - Expiration: {expiration_date or 'None'}")
        print(f"  - Machine binding: {'Yes' if allowed_machines else 'No'}")
        print(f"  - Anti-debug: {'Yes' if not parsed.no_anti_debug else 'No'}")
        print(f"  - Build PYD: {'Yes' if build_pyd else 'No (pyx only)'}")
        print("")

    try:
        if input_path.is_file():
            # Single file protection
            print(f"Protecting file: {input_path}")
            result = protector.protect_file(
                input_path,
                output_path,
                build_pyd=build_pyd
            )

            print(f"\nProtection complete!")
            print(f"  - Protected file: {result['protected']}")
            if result.get('pyd'):
                print(f"  - PYD runtime: {result['pyd']}")
            elif result.get('pyx'):
                print(f"  - Cython source: {result['pyx']}")
                print(f"  - Build with: cd {output_path} && python setup.py build_ext --inplace")

        elif input_path.is_dir():
            # Directory protection
            print(f"Protecting directory: {input_path}")
            print(f"Output directory: {output_path}")

            result = protector.protect_directory(
                input_path,
                output_path,
                recursive=True,
                exclude_patterns=parsed.exclude_patterns,
                build_pyd=build_pyd
            )

            file_count = len(result.get('files', []))

            if verbose:
                print(f"\nProtected files:")
                for f in result.get('files', []):
                    print(f"  - {f}")

            print(f"\nProtection complete!")
            print(f"  - Files protected: {file_count}")
            print(f"  - Output: {output_path}")
            if result.get('pyd'):
                print(f"  - PYD runtime: {result['pyd']}")
            elif result.get('pyx'):
                print(f"  - Cython source: {result['pyx']}")
                print(f"  - Build with: cd {output_path} && python setup.py build_ext --inplace")
        else:
            print(f"Error: Input is neither a file nor directory: {input_path}", file=sys.stderr)
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    # Create main parser with subcommands
    parser = create_main_parser()

    # Parse args
    parsed = parser.parse_args(args)

    # Determine which command to run
    if parsed.command == 'analyze':
        return _handle_analyze(parsed)

    elif parsed.command == 'init':
        return _handle_init(parsed)

    elif parsed.command == 'obfuscate':
        return _handle_obfuscate(parsed)

    elif parsed.command == 'protect':
        return _handle_protect(parsed)

    elif hasattr(parsed, 'input') and parsed.input and hasattr(parsed, 'output') and parsed.output:
        # Backwards compatibility: -i/-o without subcommand
        # Re-parse with obfuscate subcommand
        new_args = ['obfuscate', '-i', parsed.input, '-o', parsed.output]
        if parsed.verbose:
            new_args.append('-v')
        # Add any remaining args
        if args:
            for arg in args:
                if arg not in ['-i', '--input', '-o', '--output', '-v', '--verbose',
                               parsed.input, parsed.output]:
                    new_args.append(arg)
        return main(new_args)

    else:
        # No command specified, show help
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
