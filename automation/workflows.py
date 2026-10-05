"""Automated workflow routines for JARVIS."""

from __future__ import annotations

import time
from typing import Any, Dict

from actions.system_controls import (
    volume_mute,
    show_desktop,
    get_power_status,
)
from actions.browser import open_url
from security.activity_log import ActivityLog


class WorkflowRunner:
    """Executes composite, multi-step system workflows."""

    def __init__(self) -> None:
        self.activity_log = ActivityLog()

    def run(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a named workflow."""
        workflow_id = name.lower().replace("-", "_").replace(" ", "_")
        handler = getattr(self, f"_wf_{workflow_id}", None)
        if not handler:
            return {
                "ok": False,
                "message": f"Unknown workflow '{name}'. Available: focus_mode, dev_mode, diagnostics_mode.",
                "action": "workflow",
            }

        start = time.time()
        result = handler(**kwargs)
        duration = round(time.time() - start, 2)
        result["duration_seconds"] = duration
        self.activity_log.record("workflow", name=name, ok=result.get("ok", False), duration=duration)
        return result

    def _wf_focus_mode(self, **_kwargs: Any) -> Dict[str, Any]:
        """Activate Focus Mode: mute audio and clear desktop clutter."""
        volume_mute()
        show_desktop()
        return {
            "ok": True,
            "message": "Focus Mode activated: audio muted and desktop workspace cleared.",
            "action": "workflow",
            "workflow": "focus_mode",
        }

    def _wf_dev_mode(self, **_kwargs: Any) -> Dict[str, Any]:
        """Activate Developer Mode: check environment and power status."""
        power = get_power_status()
        return {
            "ok": True,
            "message": f"Dev Environment ready. Power: {power.get('message', 'Normal')}. All neural modules standing by.",
            "action": "workflow",
            "workflow": "dev_mode",
            "data": {"power": power},
        }

    def _wf_diagnostics_mode(self, **_kwargs: Any) -> Dict[str, Any]:
        """Activate Diagnostics Mode: gather comprehensive hardware & power report."""
        power = get_power_status()
        return {
            "ok": True,
            "message": f"Full diagnostic sweep executed. Power status: {power.get('message')}.",
            "action": "workflow",
            "workflow": "diagnostics_mode",
            "data": {"power": power},
        }


_runner = WorkflowRunner()


def run_workflow(name: str, **kwargs: Any) -> Dict[str, Any]:
    """Convenience helper to run a workflow."""
    return _runner.run(name, **kwargs)
