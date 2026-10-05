# JARVIS Installer & Packaging Guide

This directory contains configuration and tools to compile JARVIS into a standalone Windows desktop executable (`JARVIS.exe`).

## Build Requirements

1. **Python 3.10+** (with `.venv` containing `PySide6`, etc.)
2. **Node.js 18+ & npm** (for Vite frontend build)
3. **PyInstaller** (`pip install pyinstaller`)

---

## One-Click Build

Run the automated build script from the project root:

```powershell
# Using the active virtual environment:
.\.venv\Scripts\python.exe installer\build_executable.py
```

Or via scripts convenience wrapper:

```powershell
.\.venv\Scripts\python.exe scripts\build.py
```

### What this does:
1. Runs `npm run build` inside `frontend/` to generate production web bundles in `frontend/dist`.
2. Packages `main.py`, the PySide6 Qt WebEngine shell, `config/settings.json`, and backend modules into `dist/JARVIS/`.
3. Creates a standalone windowed Windows desktop executable at:
   `dist\JARVIS\JARVIS.exe`

---

## Running the Standalone Executable

Once built, you can run JARVIS directly:

```powershell
.\dist\JARVIS\JARVIS.exe
```

No external server or terminal prompt is required. The splash screen will initialize, start the local backend services, and launch the holographic JARVIS interface.
