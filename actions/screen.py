"""Screen capture utility for JARVIS.

Captures primary display using Windows native .NET Drawing libraries via PowerShell.
Saves to logs/screenshots/ without requiring external Python packages.
"""

from __future__ import annotations

import base64
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict


def capture_screenshot(dest_folder: Path | str | None = None) -> Dict[str, Any]:
    """Capture a screenshot and save it to disk."""
    if dest_folder is None:
        dest_folder = Path(__file__).resolve().parents[1] / "logs" / "screenshots"
    else:
        dest_folder = Path(dest_folder)

    dest_folder.mkdir(parents=True, exist_ok=True)
    filename = f"screenshot_{int(time.time())}.png"
    target_path = dest_folder / filename

    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save('{str(target_path).replace('\\', '\\\\')}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
"""

    encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = startupinfo

    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
            capture_output=True,
            timeout=10,
            **kwargs,
        )
        if target_path.exists() and target_path.stat().st_size > 0:
            return {
                "ok": True,
                "message": f"Screenshot captured: {filename}",
                "action": "screenshot",
                "data": {
                    "path": str(target_path),
                    "filename": filename,
                    "size_bytes": target_path.stat().st_size,
                },
            }
        else:
            return {
                "ok": False,
                "message": f"Screenshot failed: {proc.stderr.decode('utf-8', errors='ignore')[:100]}",
                "action": "screenshot",
            }
    except Exception as e:
        return {"ok": False, "message": f"Screenshot error: {e}", "action": "screenshot"}
