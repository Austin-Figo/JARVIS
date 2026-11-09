# JARVIS

Personal AI desktop assistant for Windows.

## Vision & Capabilities

JARVIS is a secure, offline-capable personal AI assistant featuring:

- **Offline Speech Recognition (STT)**: Built with Windows native `System.Speech.Recognition`.
- **Offline Voice Feedback (TTS)**: Built with Windows native `System.Speech.Synthesis`.
- **Wake Phrase & Clap Activation**: Background wake word detection ("Daddy's home", "Jarvis") and double-clap acoustic peak trigger.
- **Multi-Provider AI Intelligence**: Unified LLM engine supporting Google Gemini, OpenAI, local Ollama, and local fallback.
- **RAG & Persistent Memory Core**: SQLite-backed local memory engine automatically indexing and injecting notes, preferences, and context into conversations.
- **Windows Actions & System Controls**: Zero-dependency Win32 controls for audio volume, media playback, workstation locking, power telemetry, and screen capture.
- **Automated Workflows**: Multi-step composite routines for focus mode, developer setup, and diagnostics.
- **Holographic Cyberpunk HUD**: React + Vite + Tailwind UI featuring live hardware telemetry charts, central Arc Reactor AI core, terminal console, and settings.
- **Secure Sandboxing & Permissions**: Append-only activity audit logging and human-in-the-loop confirmation before launching external applications.
- **Standalone Windows Application**: PySide6 Qt WebEngine desktop shell with custom animated splash screen and one-click PyInstaller packager.

## Wake Phrase

Default wake phrase: **"Daddy's home"** (configurable in `config/settings.json`), plus **"Jarvis"** and acoustic **double-clap** detection.

---

## Project Structure

- `actions/` — Windows native system controls (volume, media, screen capture, browser, power).
- `automation/` — Automated multi-step workflow routines (focus mode, dev mode, diagnostics).
- `ai/` — Unified LLM provider (Gemini, OpenAI, Ollama) with RAG memory context and tool calling.
- `app/` — Desktop PySide6 shell, animated splash screen, and standard-library HTTP + SSE API server.
- `core/` — Core Win32 hardware telemetry and safe command dispatch engine.
- `frontend/` — Futuristic React HUD interface with live streaming monitors, audio visualizer, and dock.
- `installer/` — Packaging configuration (`jarvis.spec`), automated builder (`build_executable.py`), and documentation.
- `logs/` — Append-only audit logs (`activity.jsonl`) and captured screenshots.
- `memory/` — Thread-safe SQLite persistent memory database (`jarvis_memory.db`).
- `scripts/` — Convenience build and automation scripts.
- `security/` — Action validation, permission checks, and activity audit logging.
- `tests/` — Automated test suite covering core, memory, AI, actions, voice, wake detection, and API.
- `voice/` — Offline Windows speech recognition and speech synthesis engines.
- `wake/` — Background wake phrase and acoustic double-clap detector.

---

## Getting Started

### 1. Running in Development Mode
```powershell
# In virtual environment:
.\.venv\Scripts\python.exe main.py
```

### 2. Running Test Suite
```powershell
.\.venv\Scripts\python.exe tests\run_all_tests.py
```

### 3. Packaging into Standalone Executable
```powershell
.\.venv\Scripts\python.exe installer\build_executable.py
```
Outputs the standalone windowed executable at: `dist\JARVIS\JARVIS.exe`.


## Configuration and security

JARVIS reads provider credentials from process environment variables (`GEMINI_API_KEY` or `OPENAI_API_KEY`). Set `AI_PROVIDER` and optionally `AI_MODEL` to select a provider and model. The included `.env.example` is documentation only: the current application does not automatically load `.env` files. Set variables in the PowerShell session that launches JARVIS. Never place real credentials in `config/settings.json` or commit populated local settings.

A provider credential was found in earlier Git history. It has been removed from the current audit branch, but history cleanup and credential rotation are still required before this repository can safely be made public. See [SECURITY.md](SECURITY.md).
