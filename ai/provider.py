"""AI integration module for JARVIS.

Supports multiple LLM providers: Google Gemini, OpenAI, and local Ollama.
Provides unified /api/chat endpoint with RAG persistent memory integration
and function calling for JARVIS actions and system controls.
Gracefully falls back to mock mode if packages aren't available or configured.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from core.jarvis_core import JarvisCore
from memory.store import MemoryStore


def _load_settings_keys() -> Dict[str, str]:
    """Load API keys from settings.json if not present in environment."""
    config_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "gemini": data.get("geminiKey", ""),
                "openai": data.get("secretKey", ""),
            }
    except Exception:
        return {}


class AIProvider:
    """Unified AI provider supporting multiple LLM backends with RAG memory."""

    PROVIDER_GEMINI = "gemini"
    PROVIDER_OPENAI = "openai"
    PROVIDER_OLLAMA = "ollama"

    def __init__(self, provider: str | None = None, model: str | None = None, memory: MemoryStore | None = None):
        self.provider = provider or os.environ.get("AI_PROVIDER", "mock")
        self.model = model or os.environ.get("AI_MODEL", "gemini-1.5-flash")
        self.core = JarvisCore()
        self.memory = memory or MemoryStore()
        self._chat_history: List[Dict[str, Any]] = []
        self._available = False
        self._configure_provider()

    def _configure_provider(self) -> None:
        """Set up provider-specific settings. Gracefully falls back to mock."""
        settings_keys = _load_settings_keys()
        try:
            if self.provider == self.PROVIDER_GEMINI:
                import google.generativeai as genai

                api_key = os.environ.get("GEMINI_API_KEY") or settings_keys.get("gemini", "")
                if api_key and "•" not in api_key:
                    genai.configure(api_key=api_key)
                    self._model = genai.GenerativeModel(self.model)
                    self._available = True
                else:
                    self._available = False
            elif self.provider == self.PROVIDER_OPENAI:
                import openai

                api_key = os.environ.get("OPENAI_API_KEY") or settings_keys.get("openai", "")
                if api_key and "•" not in api_key:
                    openai.api_key = api_key
                    self._client = openai.OpenAI(api_key=api_key)
                    self._model_name = self.model
                    self._available = True
                else:
                    self._available = False
            elif self.provider == self.PROVIDER_OLLAMA:
                import requests

                ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
                try:
                    resp = requests.get(f"{ollama_url}/api/tags", timeout=2)
                    self._ollama_url = ollama_url
                    self._available = resp.status_code == 200
                except Exception:
                    self._available = False
            else:
                self._available = False
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        """Check if the AI provider is properly configured and available."""
        return self._available

    def _get_memory_context(self, query: str) -> str:
        """Retrieve relevant memories for RAG prompt augmentation."""
        try:
            # Query-specific search first, fall back to recent entries
            matched = self.memory.list(limit=4, query=query) if query else []
            if not matched:
                matched = self.memory.list(limit=4)
            if not matched:
                return ""
            lines = [f"- [{m['title']}]: {m['content']} (Tags: {', '.join(m.get('tags', []))})" for m in matched]
            return "Stored User Memories:\n" + "\n".join(lines)
        except Exception:
            return ""

    def _build_system_prompt(self, query: str) -> str:
        """Create rich system prompt containing capabilities and memory context."""
        mem_ctx = self._get_memory_context(query)
        base = (
            "You are JARVIS, an advanced personal AI desktop assistant.\n"
            "You are capable, intelligent, polite, concise, and proactive.\n"
            "You can control the user's PC by returning a JSON object in this format:\n"
            '{"action": "<action_name>", "parameters": { ... }}\n'
            "Supported actions:\n"
            "- scan, status, time, settings, apps, gesture, help\n"
            "- volume_up, volume_down, volume_mute\n"
            "- media_play_pause, media_next, media_prev\n"
            "- lock_workstation, show_desktop, power_status\n"
            "- screenshot, search_web, open_url\n"
            "- save_memory: {\"title\": \"...\", \"content\": \"...\", \"tags\": [...]}\n"
            "- list_memories: {\"query\": \"...\"}\n"
        )
        if mem_ctx:
            base += f"\n{mem_ctx}\n"
        return base

    def chat(self, message: str, history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """Send a message to the LLM and get a response with RAG and action handling."""
        # 1. Quick intent check for local commands or memory management
        direct_resp = self._check_direct_intents(message)
        if direct_resp:
            return direct_resp

        # 2. If no cloud/local LLM configured, use the enriched mock engine
        if not self.available:
            return self._chat_mock(message)

        self._chat_history.append({"role": "user", "content": message})

        try:
            if self.provider == self.PROVIDER_GEMINI:
                return self._chat_gemini(message, history)
            elif self.provider == self.PROVIDER_OPENAI:
                return self._chat_openai(message, history)
            elif self.provider == self.PROVIDER_OLLAMA:
                return self._chat_ollama(message, history)
            else:
                return self._chat_mock(message)
        except Exception:
            return self._chat_mock(message)

    def _check_direct_intents(self, message: str) -> Dict[str, Any] | None:
        """Check for explicit memory creation or system control intents."""
        normalized = message.strip().lower()

        # Save memory intent
        if normalized.startswith(("remember that ", "remember ", "take a note: ", "note that ", "save memory: ")):
            for prefix in ("remember that ", "remember ", "take a note: ", "note that ", "save memory: "):
                if normalized.startswith(prefix):
                    content = message.strip()[len(prefix):].strip()
                    break
            else:
                content = message.strip()

            title = content[:32] + ("..." if len(content) > 32 else "")
            mem = self.memory.add(title=title, content=content, tags=["note", "user_prompt"])
            return {
                "ok": True,
                "message": f"I have saved that to my memory core: '{title}'",
                "action": "memory_saved",
                "data": {"memory": mem},
                "source": "ai_direct",
            }

        # Recall memories intent
        if any(k in normalized for k in ("what are my memories", "do you remember", "list my memories", "show notes", "what did i note")):
            query = ""
            for trigger in ("about ", "regarding ", "for "):
                if trigger in normalized:
                    query = normalized.split(trigger, 1)[1].strip().rstrip("?!.,;")
                    break
            mems = self.memory.list(limit=5, query=query if query else None)
            if not mems:
                return {
                    "ok": True,
                    "message": "I checked my memory core, but I don't have any matching records.",
                    "action": "memory_list",
                    "data": {"memories": []},
                    "source": "ai_direct",
                }
            items = "\n".join([f"• {m['title']}: {m['content']}" for m in mems])
            return {
                "ok": True,
                "message": f"Here is what I found in my memory core:\n{items}",
                "action": "memory_list",
                "data": {"memories": mems},
                "source": "ai_direct",
            }

        return None

    def _chat_gemini(self, message: str, history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """Chat using Google Gemini with RAG memory context."""
        try:
            model = self._model
            sys_prompt = self._build_system_prompt(message)

            contents = [{"role": "user", "parts": [sys_prompt]}]
            if not history:
                history = self._chat_history[-8:]

            for msg in history[-4:]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [msg["content"]]})

            contents.append({"role": "user", "parts": [message]})

            response = model.generate_content(contents)
            text = response.text or ""

            parsed = self._try_parse_function_call(text, message)
            if parsed:
                return parsed

            return {"ok": True, "message": text, "action": None}
        except Exception as e:
            return {"ok": False, "message": f"Gemini error: {str(e)[:100]}", "action": None}

    def _chat_openai(self, message: str, history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """Chat using OpenAI with RAG memory context."""
        try:
            sys_prompt = self._build_system_prompt(message)
            messages = [{"role": "system", "content": sys_prompt}]
            for msg in self._chat_history[-6:]:
                messages.append(msg)
            messages.append({"role": "user", "content": message})

            response = self._client.chat.completions.create(
                model=self._model_name, messages=messages, temperature=0.7
            )
            text = response.choices[0].message.content or ""

            parsed = self._try_parse_function_call(text, message)
            if parsed:
                return parsed

            return {"ok": True, "message": text, "action": None}
        except Exception as e:
            return {"ok": False, "message": f"OpenAI error: {str(e)[:100]}", "action": None}

    def _chat_ollama(self, message: str, history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """Chat using local Ollama."""
        try:
            import requests

            sys_prompt = self._build_system_prompt(message)
            messages = [{"role": "system", "content": sys_prompt}] + self._chat_history[-6:]
            messages.append({"role": "user", "content": message})

            response = requests.post(
                f"{self._ollama_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                text = result.get("message", {}).get("content", "")
            else:
                text = f"Ollama error: {response.status_code}"

            parsed = self._try_parse_function_call(text, message)
            if parsed:
                return parsed

            return {"ok": True, "message": text, "action": None}
        except Exception as e:
            return {"ok": False, "message": f"Ollama error: {str(e)[:100]}", "action": None}

    def _chat_mock(self, message: str) -> Dict[str, Any]:
        """Smart local fallback handler covering all commands, actions, and memories."""
        text = message.lower().strip()

        # System telemetry and controls
        if any(k in text for k in ("scan", "diagnostic", "analyze")):
            return self.core.execute_command("scan", source="ai")
        elif any(k in text for k in ("status", "health", "how are you")):
            return self.core.execute_command("status", source="ai")
        elif "time" in text or "date" in text:
            from datetime import datetime
            return {"ok": True, "message": f"Local time: {datetime.now().strftime('%H:%M:%S')}. Date: {datetime.now().strftime('%Y-%m-%d')}.", "action": "time"}
        elif "screenshot" in text:
            return self.core.execute_command("screenshot", source="ai")
        elif "volume up" in text or "louder" in text:
            return self.core.execute_command("volume up", source="ai")
        elif "volume down" in text or "quieter" in text:
            return self.core.execute_command("volume down", source="ai")
        elif "mute" in text:
            return self.core.execute_command("mute", source="ai")
        elif any(k in text for k in ("lock pc", "lock computer", "lock screen")):
            return self.core.execute_command("lock pc", source="ai")
        elif "show desktop" in text or "minimize" in text:
            return self.core.execute_command("show desktop", source="ai")
        elif any(k in text for k in ("battery", "power")):
            return self.core.execute_command("battery", source="ai")
        elif "focus mode" in text:
            return self.core.execute_command("focus mode", source="ai")
        elif "dev mode" in text:
            return self.core.execute_command("dev mode", source="ai")
        elif "settings" in text:
            return {"ok": True, "message": "Opening system configuration.", "action": "settings"}
        elif "apps" in text or "menu" in text:
            return {"ok": True, "message": "Launching application grid.", "action": "apps"}
        elif "gesture" in text:
            return {"ok": True, "message": "Gesture controls active in panel.", "action": "gesture"}
        elif "help" in text:
            return self.core.execute_command("help", source="ai")
        else:
            return {
                "ok": True,
                "message": f"I received: \"{message}\". How can I assist you with your system today, sir?",
                "action": None,
            }

    def _try_parse_function_call(self, text: str, original_message: str) -> Dict[str, Any] | None:
        """Parse LLM response as a structured JARVIS action or memory function."""
        try:
            text_stripped = text.strip()
            start = text_stripped.find("{")
            end = text_stripped.rfind("}")

            if start >= 0 and end > start:
                json_str = text_stripped[start : end + 1]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and "action" in parsed:
                    action = parsed["action"]
                    params = parsed.get("parameters", {})

                    if action == "save_memory":
                        title = params.get("title") or original_message[:30]
                        content = params.get("content", original_message)
                        tags = params.get("tags", ["ai_saved"])
                        mem = self.memory.add(title=title, content=content, tags=tags)
                        return {
                            "ok": True,
                            "message": f"Memory saved: '{title}'",
                            "action": "memory_saved",
                            "data": {"memory": mem},
                            "source": "ai_llm",
                        }

                    if action == "list_memories":
                        query = params.get("query", "")
                        mems = self.memory.list(limit=5, query=query if query else None)
                        return {
                            "ok": True,
                            "message": f"Retrieved {len(mems)} memories.",
                            "action": "memory_list",
                            "data": {"memories": mems},
                            "source": "ai_llm",
                        }

                    result = self.core.execute_command(action, source="ai")
                    return {
                        "ok": result["ok"],
                        "message": result.get("message", text),
                        "action": result.get("action"),
                        "data": result.get("data"),
                        "source": "ai_llm",
                    }
            return None
        except Exception:
            return None


_ai_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """Get or create the global AI provider instance."""
    global _ai_provider
    if _ai_provider is None:
        _ai_provider = AIProvider()
    return _ai_provider


def set_ai_provider(provider: str, model: str | None = None) -> None:
    """Set the AI provider and model."""
    global _ai_provider
    _ai_provider = AIProvider(provider=provider, model=model)


def chat(message: str, history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Convenience function to chat with the AI."""
    return get_ai_provider().chat(message, history)