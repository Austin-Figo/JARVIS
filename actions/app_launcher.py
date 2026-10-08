"""Windows application discovery and launcher for JARVIS.

Supports built-in Windows system tools, UWP protocol apps, and dynamically
discovers installed desktop applications via PATH, Windows Registry App Paths,
and Start Menu shortcuts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import winreg
from pathlib import Path
from typing import Any, Dict, List, Optional


# Canonical system applications and protocols
SYSTEM_APPS: Dict[str, str] = {
    # System Utilities
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "notepad": "notepad.exe",
    "editor": "notepad.exe",
    "text editor": "notepad.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "files": "explorer.exe",
    "my computer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "control panel": "control.exe",
    "control": "control.exe",
    "snipping tool": "snippingtool.exe",
    "snip": "snippingtool.exe",
    "registry editor": "regedit.exe",
    "regedit": "regedit.exe",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "resource monitor": "resmon.exe",
    "resmon": "resmon.exe",
    "event viewer": "eventvwr.msc",
    "services": "services.msc",
    "volume mixer": "sndvol.exe",
    "sound settings": "sndvol.exe",
    # Windows UWP Apps / Protocols
    "settings": "ms-settings:",
    "windows settings": "ms-settings:",
    "camera": "microsoft.windows.camera:",
    "clock": "ms-clock:",
    "alarm": "ms-clock:",
    "alarms": "ms-clock:",
    "timer": "ms-clock:",
    "calendar": "outlookcal:",
    "weather": "bingweather:",
    "maps": "bingmaps:",
    "photos": "ms-photos:",
    "calculator uwp": "calculator:",
    "store": "ms-windows-store:",
    "windows store": "ms-windows-store:",
    # Common Browsers and Desktop Software
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": "brave.exe",
    "firefox": "firefox.exe",
    "spotify": "spotify.exe",
    "vs code": "code.cmd",
    "vscode": "code.cmd",
    "code": "code.cmd",
    "visual studio code": "code.cmd",
    "discord": "discord.exe",
    "steam": "steam.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "vlc": "vlc.exe",
    "obs": "obs64.exe",
}


def find_app_in_registry(name: str) -> Optional[str]:
    """Look up executable path in Windows Registry App Paths."""
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for ext in ("", ".exe"):
            try:
                key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{name}{ext}"
                with winreg.OpenKey(root, key_path) as key:
                    val, _ = winreg.QueryValueEx(key, "")
                    if val and (os.path.exists(val) or val.endswith(".exe")):
                        return val
            except Exception:
                pass
    return None


def find_app_in_start_menu(name: str) -> Optional[str]:
    """Search Start Menu shortcuts for the application."""
    clean_name = name.lower()
    start_folders = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]

    for folder in start_folders:
        if not folder.exists():
            continue
        try:
            for shortcut in folder.rglob("*.lnk"):
                stem = shortcut.stem.lower()
                if clean_name == stem or clean_name in stem.split() or stem.startswith(f"{clean_name} "):
                    return str(shortcut)
        except Exception:
            pass
    return None


def resolve_application(name: str) -> Optional[str]:
    """Resolve an application name to an executable path or protocol."""
    clean = name.strip().lower()
    if not clean:
        return None

    # 1. Check known system apps and protocols
    if clean in SYSTEM_APPS:
        return SYSTEM_APPS[clean]

    # 2. Check PATH
    path_found = shutil.which(clean) or shutil.which(f"{clean}.exe")
    if path_found:
        return path_found

    # 3. Check Windows Registry App Paths
    reg_found = find_app_in_registry(clean)
    if reg_found:
        return reg_found

    # 4. Check Start Menu shortcuts
    lnk_found = find_app_in_start_menu(clean)
    if lnk_found:
        return lnk_found

    return None


def launch_application(name: str) -> Dict[str, Any]:
    """Launch a Windows application by name."""
    target = resolve_application(name)
    if not target:
        return {
            "ok": False,
            "message": f"Could not find application '{name}' on your Windows system.",
            "action": "open_app",
            "target": name,
        }

    try:
        # Protocol URI (e.g. ms-settings:, calc:, etc.) or shortcut (.lnk)
        if ":" in target or target.endswith(".lnk"):
            os.startfile(target)
            return {
                "ok": True,
                "message": f"Opened {name.title()}.",
                "action": "open_app",
                "target": target,
            }

        # Executable file or command
        if os.path.exists(target):
            os.startfile(target)
        else:
            # Fall back to startfile or Popen
            try:
                os.startfile(target)
            except Exception:
                kwargs = {}
                if os.name == "nt":
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    kwargs["startupinfo"] = startupinfo
                subprocess.Popen([target], shell=True, **kwargs)

        return {
            "ok": True,
            "message": f"Opened {name.title()}.",
            "action": "open_app",
            "target": target,
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Unable to open {name.title()}: {e}",
            "action": "open_app",
            "target": target,
        }


def get_available_system_apps() -> List[str]:
    """Return a list of popular available system apps."""
    return sorted(list(set(SYSTEM_APPS.keys())))

