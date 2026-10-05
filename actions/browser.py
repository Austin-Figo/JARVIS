"""Browser and web search actions for JARVIS."""

from __future__ import annotations

import urllib.parse
import webbrowser
from typing import Any, Dict


def open_url(url: str) -> Dict[str, Any]:
    """Open a URL in the user's default browser."""
    clean = url.strip()
    if not clean.startswith(("http://", "https://")):
        clean = "https://" + clean

    try:
        webbrowser.open(clean)
        return {"ok": True, "message": f"Opened {clean} in browser.", "action": "open_url", "data": {"url": clean}}
    except Exception as e:
        return {"ok": False, "message": f"Could not open browser: {e}", "action": "open_url"}


def search_web(query: str, engine: str = "google") -> Dict[str, Any]:
    """Search the web using Google, YouTube, or GitHub."""
    clean_query = query.strip()
    if not clean_query:
        return {"ok": False, "message": "Search query cannot be empty.", "action": "search_web"}

    encoded = urllib.parse.quote_plus(clean_query)
    engines = {
        "google": f"https://www.google.com/search?q={encoded}",
        "youtube": f"https://www.youtube.com/results?search_query={encoded}",
        "github": f"https://github.com/search?q={encoded}",
    }

    url = engines.get(engine.lower(), engines["google"])
    try:
        webbrowser.open(url)
        return {
            "ok": True,
            "message": f"Searching {engine.title()} for '{clean_query}'.",
            "action": "search_web",
            "data": {"query": clean_query, "url": url},
        }
    except Exception as e:
        return {"ok": False, "message": f"Could not open search: {e}", "action": "search_web"}
