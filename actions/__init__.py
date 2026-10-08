"""Windows Actions package for JARVIS."""

from actions.system_controls import (
    volume_up,
    volume_down,
    volume_mute,
    media_play_pause,
    media_next,
    media_prev,
    lock_workstation,
    show_desktop,
    get_power_status,
)
from actions.screen import capture_screenshot
from actions.browser import open_url, search_web
from actions.app_launcher import launch_application, resolve_application, get_available_system_apps
from actions.weather import get_weather

__all__ = [
    "volume_up",
    "volume_down",
    "volume_mute",
    "media_play_pause",
    "media_next",
    "media_prev",
    "lock_workstation",
    "show_desktop",
    "get_power_status",
    "capture_screenshot",
    "open_url",
    "search_web",
    "launch_application",
    "resolve_application",
    "get_available_system_apps",
    "get_weather",
]

