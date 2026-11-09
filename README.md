# JARVIS — Personal AI Desktop Assistant

A Windows desktop assistant combining voice interaction, multi-provider LLM integration, local memory, and controlled operating-system actions.

> **Project status:** Personal engineering project. Windows-focused. Review the security notes before running or exposing any local service.

## Core capabilities

- **AI providers:** Google Gemini, OpenAI, and local Ollama through a unified provider interface.
- **Voice interaction:** Windows speech recognition and speech synthesis, wake-phrase handling, and acoustic activation.
- **Local memory:** SQLite-backed notes and retrieval-augmented context.
- **Desktop automation:** Application launching, volume and media controls, screenshots, workstation locking, and system telemetry.
- **Workflow routines:** Multi-step focus, developer, and diagnostic routines.
- **Desktop interface:** React, Vite, and Tailwind frontend hosted inside a PySide6 desktop shell.
- **Packaging:** PyInstaller-based Windows executable build workflow.

## Architecture

| Component | Responsibility |
|---|---|
| frontend/ | React-based desktop dashboard |
| app/ | PySide6 shell and local application server |
| ai/ | LLM provider integration, prompt handling, and tool dispatch |
| voice/ and wake/ | Speech input/output and activation |
| memory/ | Persistent local memory and retrieval |
| actions/ and core/ | Windows actions, telemetry, and command execution |
| automation/ | Multi-step local workflows |
| security/ | Permission checks and activity logging |
| tests/ | Automated test sources |
| installer/ | Windows packaging scripts |

## Technology

Python, PySide6, React, Vite, Tailwind CSS, SQLite, Windows speech APIs, Win32 integration, PyInstaller, and integrations for Gemini, OpenAI, and Ollama.

## Run locally

The project is intended for Windows. Create and activate a virtual environment, install the dependencies listed in the repository, then run from the project root:

```powershell
python main.py
```

Run the test runner:

```powershell
python tests\run_all_tests.py
```

Build the Windows executable:

```powershell
python installer\build_executable.py
```

## Configure an AI provider

JARVIS reads credentials from process environment variables. The included .env.example documents variable names; it is not automatically loaded by the application.

Example PowerShell session:

```powershell
$env:AI_PROVIDER = "gemini"
$env:AI_MODEL = "your-supported-model"
$env:GEMINI_API_KEY = "your-key"
python main.py
```

For OpenAI, set AI_PROVIDER to openai and provide OPENAI_API_KEY. For Ollama, set AI_PROVIDER to ollama and optionally set OLLAMA_URL.

**Never commit real credentials.** Keep local configuration and database files out of Git.

## Security and limitations

- JARVIS can execute local Windows actions. Run it only on a trusted machine and review confirmation and permission behavior before enabling actions.
- Do not expose its local API or desktop services to an untrusted network.
- A provider API credential was previously committed to Git history. The owner reports that the key has been revoked. The audit branch removes credentials from the current settings file and changes provider loading to environment variables, but the historical Git object still requires cleanup before public release.
- See [SECURITY.md](SECURITY.md) for the current security boundary and cleanup requirement.

## Project goals

JARVIS explores practical integration of desktop automation, voice interfaces, local context retrieval, and multi-provider AI systems. It is a personal engineering project, not a claim of production-grade security or reliability.
