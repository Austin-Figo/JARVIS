"""Convenience script to trigger the full JARVIS build."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "installer"))

from build_executable import main

if __name__ == "__main__":
    sys.exit(main())
