# -*- coding: utf-8 -*-
"""
Command-line interface for PyObfuscate.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List

from .obfuscator import Obfuscator


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='pyobfuscator',
        description='Obfuscate Python source code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  pyobfuscate -i script.py -o obfuscated.py
  pyobfuscate -i src/ -o dist/ --recursive
  pyobfuscate -i module/ -o dist/ --compress --string-method xor
        '''
    )

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
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    return parser.parse_args(args)


def _create_obfuscator(parsed: argparse.Namespace) -> Obfuscator:
    """Create an Obfuscator instance from parsed arguments."""
    return Obfuscator(
        rename_variables=not parsed.no_rename_vars,
        rename_functions=not parsed.no_rename_funcs,
        rename_classes=not parsed.no_rename_classes,
        obfuscate_strings=not parsed.no_string_obfuscation,
        compress_code=parsed.compress,
        remove_docstrings=not parsed.keep_docstrings,
        name_style=parsed.name_style,
        string_method=parsed.string_method,
        exclude_names=set(parsed.exclude)
    )


def _obfuscate_single_file(
    obfuscator: Obfuscator,
    input_path: Path,
    output_path: Path,
    verbose: bool
) -> int:
    """Obfuscate a single file. Returns exit code."""
    if verbose:
        print(f"Obfuscating {input_path}...")

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
    if parsed.verbose:
        print(f"Obfuscating directory {input_path}...")

    recursive = parsed.recursive and not parsed.no_recursive
    results = obfuscator.obfuscate_directory(
        input_path,
        output_path,
        recursive=recursive,
        exclude_patterns=parsed.exclude_patterns
    )

    success_count = sum(1 for v in results.values() if v == "success")
    error_count = len(results) - success_count

    if parsed.verbose:
        for file_path, result in results.items():
            status = "✓" if result == "success" else "✗"
            print(f"  {status} {file_path}: {result}")

    print(f"Obfuscation complete! {success_count} files processed, {error_count} errors")
    return 1 if error_count > 0 else 0


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parsed = parse_args(args)

    input_path = Path(parsed.input)
    output_path = Path(parsed.output)

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    obfuscator = _create_obfuscator(parsed)

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



if __name__ == '__main__':
    sys.exit(main())
