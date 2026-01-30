#!/usr/bin/env python
"""
Script to obfuscate the github_pr_dashboard project using PyObfuscate.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscate import Obfuscator


def main():
    """Obfuscate the github_pr_dashboard project."""
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "github_pr_dashboard"
    output_dir = project_root / "build" / "obfuscated" / "github_pr_dashboard"

    print(f"PyObfuscate - Python Code Obfuscation")
    print(f"=" * 50)
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print()

    # Create obfuscator with settings optimized for a PyQt application
    obfuscator = Obfuscator(
        rename_variables=True,
        rename_functions=True,
        rename_classes=True,
        obfuscate_strings=True,
        compress_code=False,  # Don't compress for better debugging
        remove_docstrings=True,
        name_style="random",
        string_method="base64",
        exclude_names={
            # Qt-specific names that shouldn't be renamed
            'QApplication', 'QMainWindow', 'QWidget', 'QDialog',
            'QPushButton', 'QLabel', 'QLineEdit', 'QTextEdit',
            'QTableWidget', 'QTableWidgetItem', 'QVBoxLayout', 'QHBoxLayout',
            'QGridLayout', 'QFormLayout', 'QGroupBox', 'QFrame',
            'QMenuBar', 'QMenu', 'QAction', 'QToolBar', 'QStatusBar',
            'QMessageBox', 'QFileDialog', 'QInputDialog', 'QColorDialog',
            'QTimer', 'QThread', 'QRunnable', 'QThreadPool',
            'pyqtSignal', 'pyqtSlot', 'Signal', 'Slot',
            'QSettings', 'QIcon', 'QPixmap', 'QFont', 'QColor',
            'Qt', 'QSize', 'QPoint', 'QRect',
            'clicked', 'triggered', 'textChanged', 'valueChanged',
            'currentIndexChanged', 'itemSelectionChanged', 'finished',
            'started', 'timeout', 'error', 'result',
            'setupUi', 'retranslateUi', 'show', 'exec', 'exec_',
            'close', 'hide', 'setWindowTitle', 'setGeometry',
            'connect', 'disconnect', 'emit', 'sender',
            # Keep public API names
            'main', 'run', 'start', 'stop', 'quit', 'exit',
        }
    )

    # Exclude patterns
    exclude_patterns = [
        '__pycache__',
        '*.pyc',
        'test_*.py',
        '*_test.py',
        'tests/*',
        'tools/*',
        'docs/*',
    ]

    print("Processing files...")
    results = obfuscator.obfuscate_directory(
        input_dir,
        output_dir,
        recursive=True,
        exclude_patterns=exclude_patterns
    )

    # Print results
    success_count = 0
    error_count = 0

    for file_path, result in sorted(results.items()):
        if result == "success":
            print(f"  ✓ {file_path}")
            success_count += 1
        else:
            print(f"  ✗ {file_path}: {result}")
            error_count += 1

    print()
    print(f"Obfuscation complete!")
    print(f"  Files processed: {success_count}")
    print(f"  Errors: {error_count}")

    if error_count > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
