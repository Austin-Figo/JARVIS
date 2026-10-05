"""Windows system controls (volume, media, window management, power telemetry).

Uses Windows API via ctypes with zero external dependencies.
"""

from __future__ import annotations

import ctypes
import time
from typing import Any, Dict


# Virtual Key Codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_LWIN = 0x5B
KEYEVENTF_KEYUP = 0x0002


def _send_key(vk_code: int) -> None:
    """Send keydown and keyup for a virtual key code."""
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.02)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def volume_up(steps: int = 5) -> Dict[str, Any]:
    """Increase system volume by sending key events."""
    count = max(1, min(steps, 25))
    for _ in range(count):
        _send_key(VK_VOLUME_UP)
    return {"ok": True, "message": f"Volume increased by {count * 2}%.", "action": "volume_up"}


def volume_down(steps: int = 5) -> Dict[str, Any]:
    """Decrease system volume by sending key events."""
    count = max(1, min(steps, 25))
    for _ in range(count):
        _send_key(VK_VOLUME_DOWN)
    return {"ok": True, "message": f"Volume decreased by {count * 2}%.", "action": "volume_down"}


def volume_mute() -> Dict[str, Any]:
    """Toggle system mute state."""
    _send_key(VK_VOLUME_MUTE)
    return {"ok": True, "message": "Volume mute toggled.", "action": "volume_mute"}


def media_play_pause() -> Dict[str, Any]:
    """Toggle media play/pause."""
    _send_key(VK_MEDIA_PLAY_PAUSE)
    return {"ok": True, "message": "Media play/pause toggled.", "action": "media_play_pause"}


def media_next() -> Dict[str, Any]:
    """Skip to next media track."""
    _send_key(VK_MEDIA_NEXT_TRACK)
    return {"ok": True, "message": "Skipped to next track.", "action": "media_next"}


def media_prev() -> Dict[str, Any]:
    """Return to previous media track."""
    _send_key(VK_MEDIA_PREV_TRACK)
    return {"ok": True, "message": "Returned to previous track.", "action": "media_prev"}


def lock_workstation() -> Dict[str, Any]:
    """Lock the Windows workstation."""
    success = bool(ctypes.windll.user32.LockWorkStation())
    return {
        "ok": success,
        "message": "Workstation locked." if success else "Failed to lock workstation.",
        "action": "lock_workstation",
    }


def show_desktop() -> Dict[str, Any]:
    """Toggle show desktop (minimize all windows) using Win+D."""
    ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)  # 'D' key
    time.sleep(0.02)
    ctypes.windll.user32.keybd_event(0x44, 0, KEYEVENTF_KEYUP, 0)
    ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
    return {"ok": True, "message": "Toggled desktop display.", "action": "show_desktop"}


class _SystemPowerStatus(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("SystemStatusFlag", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


def get_power_status() -> Dict[str, Any]:
    """Get system power and battery status using GetSystemPowerStatus."""
    status = _SystemPowerStatus()
    success = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
    if not success:
        return {"ok": False, "message": "Could not query power status.", "action": "power_status"}

    ac_line = {
        0: "Offline (Battery)",
        1: "Online (Plugged In)",
        255: "Unknown",
    }.get(status.ACLineStatus, "Unknown")

    battery_percent = status.BatteryLifePercent if status.BatteryLifePercent <= 100 else None

    return {
        "ok": True,
        "message": f"Power: {ac_line}, Battery: {battery_percent if battery_percent is not None else 'N/A'}%",
        "action": "power_status",
        "data": {
            "ac_line_status": ac_line,
            "battery_percent": battery_percent,
            "is_charging": bool(status.BatteryFlag & 8),
            "battery_life_seconds": status.BatteryLifeTime if status.BatteryLifeTime != 0xFFFFFFFF else None,
        },
    }
