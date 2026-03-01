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
    candidates = ['pyobfuscator.json', 'pyobfuscator.toml', '.pyobfuscator.json', '.pyobfuscator.toml']
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
DEFAULT_LICENSE = 'Protected by PyObfuscator'


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog='pyobfuscator',
        description='Python code obfuscation tool with auto-detection and framework support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_get_cli_epilog()
    )

    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
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
  init        Generate a pyobfuscator.json config file for a project

Examples:
  pyobfuscator init ./my_project
  pyobfuscator obfuscate -i ./my_project -o ./dist
  pyobfuscator -i script.py -o obfuscated.py
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
    parser.add_argument('--numbers', action='store_true')
    parser.add_argument('--builtins', action='store_true')
    parser.add_argument('--integrity-check', action='store_true')
    parser.add_argument('--pyd', action='store_true')
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

    return Obfuscator(
        config={
            'encrypt_code': not getattr(parsed, 'no_encrypt', False),
            'use_pyd_compilation': getattr(parsed, 'pyd', False),
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


def _obfuscate_single_file(
    obfuscator: Obfuscator,
    input_path: Path,
    output_path: Path,
    verbose: bool
) -> int:
    """Obfuscate a single file. Returns exit code."""
    # If output_path is an existing directory, put the file inside it
    if output_path.is_dir():
        target_path = output_path / input_path.name
    # If output_path doesn't exist but looks like a directory (no extension), create it
    elif not output_path.suffix and not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        target_path = output_path / input_path.name
    # Ensure parent directory exists
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        target_path = output_path

    _warn_if_local_imports(input_path)

    if verbose:
        msg = "Protecting (obfuscate + encrypt)" if obfuscator.config.get('encrypt_code') else "Obfuscating"
        print(f"{msg} {input_path}...")

    if obfuscator.config.get('encrypt_code'):
        # Apply full protection: obfuscation + encryption
        source = input_path.read_text(encoding='utf-8')
        protected, runtime = obfuscator.protect_source(source, str(input_path.name))

        target_path.write_text(protected, encoding='utf-8')

        # Write runtime module in the same directory
        runtime_id = obfuscator.runtime_protector.runtime_id
        runtime_path = target_path.parent / f"pyobfuscator_runtime_{runtime_id}.py"
        runtime_path.write_text(runtime, encoding='utf-8')

        if verbose:
            print(f"Output written to {target_path}")
            print(f"Runtime module: {runtime_path}")
        print("Protection complete! (Code is encrypted with AES-256-GCM)")
    else:
        # Just obfuscation
        obfuscator.obfuscate_file(input_path, target_path)
        if verbose:
            print(f"Output written to {target_path}")
        print("Obfuscation complete!")

    return 0


def _warn_if_local_imports(input_path: Path):
    """Warn user if file has local imports."""
    try:
        content = input_path.read_text(encoding='utf-8')
        if any(x in content for x in ['from .', 'from app', 'import app']):
            print("Warning: This file appears to have local imports.", file=sys.stderr)
            print("         For multi-file projects, obfuscate the entire directory.", file=sys.stderr)
            print("", file=sys.stderr)
    except Exception:
        pass


def _obfuscate_directory(
    obfuscator: Obfuscator,
    input_path: Path,
    output_path: Path,
    parsed: argparse.Namespace
) -> int:
    """Obfuscate a directory. Returns exit code."""
    verbose = getattr(parsed, 'verbose', False)
    use_parallel = getattr(parsed, 'parallel', False)
    workers = getattr(parsed, 'workers', None)
    output_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        msg = "Protecting" if obfuscator.config.get('encrypt_code') else "Obfuscating"
        parallel_msg = f" (parallel, {workers or 'auto'} workers)" if use_parallel else ""
        print(f"{msg} directory: {input_path}{parallel_msg}")
        print(f"Output directory: {output_path}\n")

    recursive = getattr(parsed, 'recursive', True) and not getattr(parsed, 'no_recursive', False)
    exclude_patterns = getattr(parsed, 'exclude_patterns', DEFAULT_EXCLUDES)

    if obfuscator.config.get('encrypt_code'):
        # Use protect_directory for full protection
        results, _ = obfuscator.runtime_protector.protect_directory(
            input_path,
            output_path,
            recursive=recursive,
            exclude_patterns=exclude_patterns
        )
        msg_suffix = "(Code is encrypted with AES-256-GCM)"
    else:
        # Just obfuscation
        results = obfuscator.obfuscate_directory(
            input_path,
            output_path,
            recursive=recursive,
            exclude_patterns=exclude_patterns
        )
        msg_suffix = ""

    success_count = sum(1 for v in results.values() if v == "success")
    error_count = len(results) - success_count

    if verbose:
        print("\nResults:")
        for file_path, result in sorted(results.items()):
            status = "[OK]" if result == "success" else "[FAIL]"
            print(f"  {status} {file_path}")
            if result != "success":
                print(f"        Error: {result}")

    print(f"\nProcessing complete! {msg_suffix}")
    print(f"  - Files processed: {success_count}")
    print(f"  - Errors: {error_count}")
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

    output_path = Path(parsed.output) if parsed.output else project_path / f'pyobfuscator.{parsed.format}'

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
    config: Dict[str, Any] = _get_merged_config(parsed)
    if config:
        parsed = _merge_config(parsed, config)

    input_path = Path(parsed.input)
    output_path = Path(parsed.output)

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    obfuscator = _create_obfuscator(parsed)

    try:
        if input_path.is_file():
            return _obfuscate_single_file(obfuscator, input_path, output_path, parsed.verbose)
        if input_path.is_dir():
            return _obfuscate_directory(obfuscator, input_path, output_path, parsed)
        print(f"Error: Input path is neither file nor directory: {input_path}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _get_merged_config(parsed: argparse.Namespace) -> Dict[str, Any]:
    """Auto-detect and load config file."""
    if hasattr(parsed, 'config') and parsed.config:
        config_path = Path(parsed.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}", file=sys.stderr)
            return {}
        return load_config(config_path)
    
    input_path = Path(parsed.input)
    if input_path.is_dir():
        for name in ['pyobfuscator.json', 'pyobfuscator.toml']:
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
