"""Create Windows Desktop and Start Menu shortcuts for JARVIS."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def create_shortcuts() -> bool:
    project_root = Path(__file__).resolve().parents[1]
    exe_target = project_root / "dist" / "JARVIS" / "JARVIS.exe"

    if not exe_target.exists():
        print(f"[!] Executable not found at {exe_target}. Run build_executable.py first.")
        return False

    user_profile = Path(os.environ.get("USERPROFILE", ""))
    desktop_dir = user_profile / "Desktop"
    start_menu_dir = user_profile / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    targets = [
        ("Desktop", desktop_dir / "JARVIS.lnk"),
        ("Start Menu", start_menu_dir / "JARVIS.lnk"),
    ]

    success = True
    for name, lnk_path in targets:
        try:
            ps_script = (
                f"$WshShell = New-Object -ComObject WScript.Shell; "
                f"$Shortcut = $WshShell.CreateShortcut('{str(lnk_path)}'); "
                f"$Shortcut.TargetPath = '{str(exe_target)}'; "
                f"$Shortcut.WorkingDirectory = '{str(exe_target.parent)}'; "
                f"$Shortcut.Description = 'JARVIS - Advanced Desktop AI Assistant'; "
                f"$Shortcut.IconLocation = '{str(exe_target)},0'; "
                f"$Shortcut.Save();"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"[+] Created {name} shortcut: {lnk_path}")
        except Exception as e:
            print(f"[!] Failed to create {name} shortcut: {e}")
            success = False

    return success


if __name__ == "__main__":
    create_shortcuts()

