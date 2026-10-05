"""Automated build script for packaging JARVIS into a standalone Windows application."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = PROJECT_ROOT / "dist"
INSTALLER_DIR = PROJECT_ROOT / "installer"


def step(message: str) -> None:
    print(f"\n[+] {message}")


def run_cmd(cmd: list[str], cwd: Path | None = None) -> bool:
    print(f"    Running: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)
        return res.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"    [!] Error running command: {e}")
        return False
    except FileNotFoundError:
        print(f"    [!] Executable not found: {cmd[0]}")
        return False


def build_frontend() -> bool:
    step("Building React Frontend with Vite...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    return run_cmd([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)


def build_executable() -> bool:
    step("Packaging Python application with PyInstaller...")
    python_exe = sys.executable

    # Check if pyinstaller is installed
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        step("PyInstaller not found in environment. Installing PyInstaller...")
        if not run_cmd([python_exe, "-m", "pip", "install", "pyinstaller"]):
            print("    [!] Failed to install PyInstaller. Please run: pip install pyinstaller")
            return False

    spec_file = INSTALLER_DIR / "jarvis.spec"
    return run_cmd([
        python_exe,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(spec_file),
    ], cwd=PROJECT_ROOT)


def main() -> int:
    print("=" * 60)
    print("JARVIS - STANDALONE BUILD SCRIPT")
    print("=" * 60)

    # 1. Compile frontend
    if not build_frontend():
        print("[!] Frontend compilation failed.")
        return 1

    # 2. Package with PyInstaller
    if not build_executable():
        print("[!] PyInstaller build failed.")
        return 1

    target = PROJECT_ROOT / "dist" / "JARVIS" / "JARVIS.exe"
    print("\n" + "=" * 60)
    if target.exists():
        print(f"SUCCESS! Standalone application built successfully:")
        print(f"Executable: {target}")
    else:
        print(f"Build complete. Look inside: {PROJECT_ROOT / 'dist' / 'JARVIS'}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
