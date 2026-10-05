"""The small, dependency-free command core used by the local API."""

from __future__ import annotations

import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class _FileTime(ctypes.Structure):
    _fields_ = (("dwLowDateTime", ctypes.c_ulong), ("dwHighDateTime", ctypes.c_ulong))


class _MemoryStatus(ctypes.Structure):
    _fields_ = (
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    )


def _filetime_value(value: _FileTime) -> int:
    return (value.dwHighDateTime << 32) + value.dwLowDateTime


def _get_cpu_percent(previous: tuple[int, int] | None = None) -> tuple[float, tuple[int, int]]:
    """Get CPU percentage using Windows API. Returns (cpu_percent, (idle, total)) for next call."""
    idle, kernel, user = _FileTime(), _FileTime(), _FileTime()
    ctypes.windll.kernel32.GetSystemTimes(
        ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
    )
    idle_value = _filetime_value(idle)
    total_value = _filetime_value(kernel) + _filetime_value(user)

    cpu_percent = 0.0
    if previous:
        previous_idle, previous_total = previous
        total_delta = total_value - previous_total
        if total_delta:
            cpu_percent = round(100 * (1 - (idle_value - previous_idle) / total_delta), 1)

    return max(0.0, min(100.0, cpu_percent)), (idle_value, total_value)


def _get_memory_info() -> dict[str, Any]:
    """Get memory info using Windows API."""
    memory = _MemoryStatus()
    memory.dwLength = ctypes.sizeof(_MemoryStatus)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
    return {
        "percent": float(memory.dwMemoryLoad),
        "used_bytes": memory.ullTotalPhys - memory.ullAvailPhys,
        "total_bytes": memory.ullTotalPhys,
        "available_bytes": memory.ullAvailPhys,
    }


def _get_disk_info() -> list[dict[str, Any]]:
    """Get disk usage for all drives."""
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            try:
                total, used, free = shutil.disk_usage(drive)
                drives.append({
                    "device": drive,
                    "total_bytes": total,
                    "used_bytes": used,
                    "free_bytes": free,
                    "percent_used": round(100 * used / total, 1) if total > 0 else 0,
                })
            except Exception:
                pass
    return drives


def _get_top_processes(limit: int = 10) -> list[dict[str, Any]]:
    """Get top processes by memory using tasklist."""
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        processes = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split('","')
            if len(parts) >= 5:
                name = parts[0].strip('"')
                pid = parts[1].strip('"')
                mem_str = parts[4].strip('"').replace(",", "").replace(" K", "")
                try:
                    mem_kb = int(mem_str)
                except ValueError:
                    mem_kb = 0
                processes.append({
                    "name": name,
                    "pid": int(pid) if pid.isdigit() else 0,
                    "memory_kb": mem_kb,
                })
        processes.sort(key=lambda p: p["memory_kb"], reverse=True)
        return processes[:limit]
    except Exception:
        return []


def _get_network_info() -> dict[str, Any]:
    """Get basic network info."""
    try:
        # Get active interfaces
        result = subprocess.run(
            ["powershell", "-Command", "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, LinkSpeed | ConvertTo-Json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip():
            adapters = json.loads(result.stdout)
            if not isinstance(adapters, list):
                adapters = [adapters]
            return {"adapters": adapters}
    except Exception:
        pass
    return {"adapters": []}


def _run_system_scan() -> dict[str, Any]:
    """Run a comprehensive system scan and return structured results."""
    # CPU utilization needs two samples; a first sample alone is only a baseline.
    _, cpu_baseline = _get_cpu_percent()
    time.sleep(0.2)
    cpu_percent, _ = _get_cpu_percent(cpu_baseline)
    mem = _get_memory_info()
    disks = _get_disk_info()
    processes = _get_top_processes(5)
    net = _get_network_info()

    scan_results = [
        {
            "category": "CPU",
            "value": f"{cpu_percent:.1f}% utilization",
            "status": "optimal" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "critical",
        },
        {
            "category": "MEMORY",
            "value": f"{mem['used_bytes'] // (1024**3)} GB / {mem['total_bytes'] // (1024**3)} GB ({mem['percent']:.1f}%)",
            "status": "optimal" if mem['percent'] < 70 else "warning" if mem['percent'] < 90 else "critical",
        },
        {
            "category": "DISK",
            "value": ", ".join(f"{d['device']}: {d['free_bytes'] // (1024**3)} GB free ({100-d['percent_used']:.0f}%)" for d in disks[:3]),
            "status": "optimal",
        },
        {
            "category": "TOP PROCESSES",
            "value": ", ".join(f"{p['name']} ({p['memory_kb'] // 1024} MB)" for p in processes[:3]),
            "status": "info",
        },
        {
            "category": "NETWORK",
            "value": f"{len(net.get('adapters', []))} active interface(s)",
            "status": "optimal" if net.get('adapters') else "warning",
        },
        {
            "category": "OS",
            "value": f"{platform.system()} {platform.release()} ({platform.version()})",
            "status": "info",
        },
        {
            "category": "PYTHON",
            "value": f"{sys.version.split()[0]} ({platform.architecture()[0]})",
            "status": "info",
        },
    ]

    return {
        "ok": True,
        "message": "System scan complete. Results available in scanner panel.",
        "action": "scan",
        "scan_results": scan_results,
        "timestamp": datetime.now().isoformat(),
    }


class JarvisCore:
    _APP_ACTIONS = {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "explorer": ["explorer.exe"],
    }
    def __init__(self):
        self.name = "JARVIS"
        self.status = "ONLINE"
        self._cpu_previous: tuple[int, int] | None = None

    def start(self) -> None:
        print(f"{self.name} core started.")
        print(f"Status: {self.status}")
        # Prime CPU measurement
        _ = _get_cpu_percent()
        self._cpu_previous = _get_cpu_percent()[1]

    def execute_command(self, command: str, source: str = "console") -> dict[str, Any]:
        """Execute a command and return structured result."""
        text = command.strip()
        normalized = text.lower()

        if not text:
            return {"ok": False, "message": "Please enter a command.", "action": None}

        # Built-in commands with real implementations
        if any(k in normalized for k in ("scan", "diagnostic", "analyze system")):
            return _run_system_scan()

        if any(k in normalized for k in ("status", "system status", "health")):
            cpu_percent, self._cpu_previous = _get_cpu_percent(self._cpu_previous)
            mem = _get_memory_info()
            disks = _get_disk_info()
            uptime = int(ctypes.windll.kernel32.GetTickCount64() / 1000)
            return {
                "ok": True,
                "message": f"CPU: {cpu_percent:.1f}% | RAM: {mem['percent']:.1f}% | Uptime: {uptime//3600}h {(uptime%3600)//60}m",
                "action": "status",
                "data": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": mem["percent"],
                    "uptime_seconds": uptime,
                    "disks": disks,
                },
                "source": source,
            }

        if "time" in normalized:
            return {
                "ok": True,
                "message": f"Local time: {datetime.now().strftime('%H:%M:%S')}. Date: {datetime.now().strftime('%Y-%m-%d')}.",
                "action": "time",
                "source": source,
            }

        if "settings" in normalized or "config" in normalized:
            return {
                "ok": True,
                "message": "Opening system configuration panel.",
                "action": "settings",
                "source": source,
            }

        if "app" in normalized and ("grid" in normalized or "launch" in normalized or "list" in normalized):
            return {
                "ok": True,
                "message": "Launching application grid.",
                "action": "apps",
                "source": source,
            }

        if "gesture" in normalized:
            return {
                "ok": True,
                "message": "Gesture recognition module not yet connected to camera.",
                "action": "gesture",
                "source": source,
            }

        if normalized.startswith("open "):
            target = normalized.removeprefix("open ").strip()
            if target not in self._APP_ACTIONS:
                return {"ok": False, "message": "Only Notepad, Calculator, and Explorer are available for opening.", "action": None, "source": source}
            return {
                "ok": True,
                "action": "open_app",
                "requires_confirmation": True,
                "confirmation": {"title": f"Open {target.title()}?", "message": "JARVIS will launch this local Windows application.", "action": "open_app", "target": target},
                "message": f"Confirmation required before opening {target.title()}.",
                "source": source,
            }

        if "process" in normalized or "task" in normalized:
            procs = _get_top_processes(10)
            return {
                "ok": True,
                "message": f"Top {len(procs)} processes by memory usage.",
                "action": "processes",
                "data": {"processes": procs},
                "source": source,
            }

        if "disk" in normalized or "storage" in normalized:
            disks = _get_disk_info()
            return {
                "ok": True,
                "message": f"Found {len(disks)} drives.",
                "action": "disk",
                "data": {"disks": disks},
                "source": source,
            }

        if "network" in normalized or "net" in normalized:
            net = _get_network_info()
            return {
                "ok": True,
                "message": f"Network: {len(net.get('adapters', []))} active adapter(s).",
                "action": "network",
                "data": net,
                "source": source,
            }

        # System controls & Media actions
        if normalized in ("mute", "unmute", "volume mute", "toggle mute"):
            from actions.system_controls import volume_mute
            res = volume_mute()
            res["source"] = source
            return res

        if "volume up" in normalized or "louder" in normalized:
            from actions.system_controls import volume_up
            res = volume_up()
            res["source"] = source
            return res

        if "volume down" in normalized or "quieter" in normalized:
            from actions.system_controls import volume_down
            res = volume_down()
            res["source"] = source
            return res

        if normalized in ("play", "pause", "play pause", "media pause", "toggle playback"):
            from actions.system_controls import media_play_pause
            res = media_play_pause()
            res["source"] = source
            return res

        if any(k in normalized for k in ("next track", "next song", "skip track")):
            from actions.system_controls import media_next
            res = media_next()
            res["source"] = source
            return res

        if any(k in normalized for k in ("prev track", "previous track", "previous song")):
            from actions.system_controls import media_prev
            res = media_prev()
            res["source"] = source
            return res

        if any(k in normalized for k in ("lock workstation", "lock pc", "lock screen", "lock computer")):
            from actions.system_controls import lock_workstation
            res = lock_workstation()
            res["source"] = source
            return res

        if any(k in normalized for k in ("show desktop", "minimize all", "minimize windows")):
            from actions.system_controls import show_desktop
            res = show_desktop()
            res["source"] = source
            return res

        if any(k in normalized for k in ("battery", "power status", "charging")):
            from actions.system_controls import get_power_status
            res = get_power_status()
            res["source"] = source
            return res

        # Screenshot action
        if any(k in normalized for k in ("screenshot", "capture screen", "take screenshot", "screen capture")):
            from actions.screen import capture_screenshot
            res = capture_screenshot()
            res["source"] = source
            return res

        # Browser & Search actions
        if normalized.startswith("google ") or normalized.startswith("search "):
            query = text.split(" ", 1)[1].strip()
            from actions.browser import search_web
            res = search_web(query, engine="google")
            res["source"] = source
            return res

        if normalized.startswith("youtube "):
            query = text.split(" ", 1)[1].strip()
            from actions.browser import search_web
            res = search_web(query, engine="youtube")
            res["source"] = source
            return res

        if normalized.startswith("github "):
            query = text.split(" ", 1)[1].strip()
            from actions.browser import search_web
            res = search_web(query, engine="github")
            res["source"] = source
            return res

        if normalized.startswith("open url ") or normalized.startswith("browse "):
            url = text.split(" ", 2)[-1].strip()
            from actions.browser import open_url
            res = open_url(url)
            res["source"] = source
            return res

        # Workflows
        if "focus mode" in normalized:
            from automation.workflows import run_workflow
            res = run_workflow("focus_mode")
            res["source"] = source
            return res

        if "dev mode" in normalized or "developer mode" in normalized:
            from automation.workflows import run_workflow
            res = run_workflow("dev_mode")
            res["source"] = source
            return res

        if "diagnostics mode" in normalized:
            from automation.workflows import run_workflow
            res = run_workflow("diagnostics_mode")
            res["source"] = source
            return res

        # Memory commands
        if normalized.startswith("remember ") or normalized.startswith("note "):
            content = text.split(" ", 1)[1].strip()
            from memory.store import MemoryStore
            store = MemoryStore()
            title = content[:30] + ("..." if len(content) > 30 else "")
            mem = store.add(title=title, content=content, tags=["quick_note"])
            return {
                "ok": True,
                "message": f"Saved to memory: '{title}'",
                "action": "memory_saved",
                "data": {"memory": mem},
                "source": source,
            }

        if normalized in ("memories", "memory list", "list memories"):
            from memory.store import MemoryStore
            store = MemoryStore()
            mems = store.list(limit=5)
            titles = [f"• {m['title']}" for m in mems]
            msg = f"Stored memories ({len(mems)}):\n" + "\n".join(titles) if titles else "No memories found."
            return {
                "ok": True,
                "message": msg,
                "action": "memory_list",
                "data": {"memories": mems},
                "source": source,
            }

        if "help" in normalized:
            return {
                "ok": True,
                "message": (
                    "Available commands:\n"
                    "• scan / diagnostic — Full system scan\n"
                    "• status / health — Quick system status\n"
                    "• volume up / volume down / mute — Audio control\n"
                    "• play / pause / next track / prev track — Media control\n"
                    "• screenshot — Capture display to logs/screenshots/\n"
                    "• lock pc / show desktop — Window & system lock\n"
                    "• search <query> / youtube <query> — Web search\n"
                    "• battery / power — Battery & power status\n"
                    "• focus mode / dev mode / diagnostics mode — Workflows\n"
                    "• remember <note> / memories — Quick memory notes\n"
                    "• time — Current time\n"
                    "• settings / apps / gesture — Open interface panels\n"
                    "• help — This list"
                ),
                "action": "help",
                "source": source,
            }

        if normalized.startswith(("run ", "exec ", "execute ")):
            return {"ok": False, "message": "Arbitrary shell commands are disabled. Use a supported read-only command or 'open notepad', 'open calculator', or 'open explorer'.", "action": None, "source": source}

        return {
            "ok": True,
            "message": f'I received "{text}". This action is not implemented yet. Say "help" for available commands.',
            "action": None,
            "source": source,
        }

    def confirm_action(self, action: str, target: str, source: str = "console") -> dict[str, Any]:
        """Execute only a pre-approved action after an explicit UI confirmation."""
        if action != "open_app" or target not in self._APP_ACTIONS:
            return {"ok": False, "message": "This confirmation request is not allowed.", "action": None, "source": source}
        try:
            subprocess.Popen(self._APP_ACTIONS[target])
            return {"ok": True, "message": f"Opened {target.title()}.", "action": "open_app", "source": source}
        except OSError as error:
            return {"ok": False, "message": f"Unable to open {target.title()}: {error}", "action": None, "source": source}
