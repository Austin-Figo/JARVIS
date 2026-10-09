"""AI integration module for JARVIS.

Supports multiple LLM providers: Google Gemini, OpenAI, and local Ollama.
Provides unified /api/chat endpoint with RAG persistent memory integration
and function calling for JARVIS actions and system controls.
Includes capable local reasoning and calculation engine for offline tasks.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
import random
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
                "model": data.get("ai_model", ""),
            }
    except Exception:
        return {}


class AIProvider:
    """Unified AI provider supporting multiple LLM backends with RAG memory."""

    PROVIDER_GEMINI = "gemini"
    PROVIDER_OPENAI = "openai"
    PROVIDER_OLLAMA = "ollama"

    def __init__(self, provider: str | None = None, model: str | None = None, memory: MemoryStore | None = None):
        settings_keys = _load_settings_keys()
        
        # Auto-detect provider if not explicitly given
        if provider:
            self.provider = provider
        elif os.environ.get("AI_PROVIDER"):
            self.provider = os.environ["AI_PROVIDER"]
        elif (os.environ.get("GEMINI_API_KEY") or settings_keys.get("gemini")) and "•" not in (os.environ.get("GEMINI_API_KEY") or settings_keys.get("gemini", "")):
            self.provider = self.PROVIDER_GEMINI
        elif (os.environ.get("OPENAI_API_KEY") or settings_keys.get("openai")) and "•" not in (os.environ.get("OPENAI_API_KEY") or settings_keys.get("openai", "")):
            self.provider = self.PROVIDER_OPENAI
        else:
            self.provider = "mock"

        self.model = model or os.environ.get("AI_MODEL") or settings_keys.get("model") or "gemini-3.8-flash"
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
                    self.model = self.model or "gemini-3.1-flash-lite"
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
            "You are JARVIS, an advanced personal conversational AI assistant (inspired by the Marvel JARVIS).\n"
            "You possess extensive intellect, general knowledge, reasoning, and conversational skill like ChatGPT/GPT.\n"
            "When the user asks you questions, seeks information, explanations, facts, advice, or general conversation, ANSWER DIRECTLY AND CONCISELY with your own vast knowledge.\n"
            "CRITICAL INSTRUCTION: NEVER return a search_web action or try to open a browser to answer questions! Answer all questions directly yourself in clear, dignified, articulate spoken sentences (1-3 sentences).\n"
            "Only return PC control actions when the user explicitly commands you to control their Windows PC or launch an app.\n"
            "When executing an explicit PC control command, return ONLY a JSON object in this format:\n"
            '{"action": "<action_name>", "parameters": { ... }}\n'
            "Supported actions:\n"
            "- open_app: {\"target\": \"<app_name>\"} (e.g. calculator, notepad, paint, chrome, settings, taskmgr, code)\n"
            "- scan, status, time, settings, apps, gesture, help\n"
            "- volume_up, volume_down, volume_mute\n"
            "- media_play_pause, media_next, media_prev\n"
            "- lock_workstation, show_desktop, power_status\n"
            "- screenshot\n"
            "- save_memory: {\"title\": \"...\", \"content\": \"...\", \"tags\": [...]}\n"
            "- list_memories: {\"query\": \"...\"}\n"
        )
        if mem_ctx:
            base += f"\n{mem_ctx}\n"
        return base

    def chat(self, message: str, history: List[Dict[str, Any]] | None = None, source: str = "console") -> Dict[str, Any]:
        # Strip conversational wake prefix if user spoke "Hey Jarvis, ..."
        clean_msg = message.strip()
        clean_lower = clean_msg.lower()
        for pfx in ("hey jarvis,", "hey jarvis", "he jarvis,", "he jarvis", "hi jarvis,", "hi jarvis", "jarvis,", "jarvis"):
            if clean_lower.startswith(pfx):
                stripped = clean_msg[len(pfx):].strip().lstrip(",").strip()
                if stripped:
                    message = stripped
                else:
                    return {"ok": True, "message": "At your service, sir. What can I help you with?", "action": None, "source": source}
                break

        # 1. Quick intent check for local commands or memory management
        direct_resp = self._check_direct_intents(message)
        if direct_resp:
            direct_resp["source"] = source
            return direct_resp

        # 2. If no cloud/local LLM configured, use the enriched local intelligence engine
        if not self.available:
            res = self._chat_mock(message)
            res["source"] = source
            return res

        self._chat_history.append({"role": "user", "content": message})

        try:
            if self.provider == self.PROVIDER_GEMINI:
                res = self._chat_gemini(message, history)
            elif self.provider == self.PROVIDER_OPENAI:
                res = self._chat_openai(message, history)
            elif self.provider == self.PROVIDER_OLLAMA:
                res = self._chat_ollama(message, history)
            else:
                res = self._chat_mock(message)
        except Exception:
            res = self._chat_mock(message)
        res["source"] = source
        return res

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

        # 3. Direct system controls & telemetry (execute locally instantly)
        if any(k in normalized for k in ("system scan", "scan system", "run diagnostic", "diagnostic scan", "analyze system")) or normalized in ("scan", "diagnostic"):
            return self.core.execute_command("scan", source="ai")
        elif any(k in normalized for k in ("system status", "system health", "how are systems", "hardware status")) or normalized in ("status", "health"):
            return self.core.execute_command("status", source="ai")
        elif any(k in normalized for k in ("what time", "current time", "tell me the time", "what's the time", "time is it", "current date", "what date", "today's date")) or normalized in ("time", "date", "clock"):
            from datetime import datetime
            return {"ok": True, "message": f"Local time is {datetime.now().strftime('%H:%M:%S')} on {datetime.now().strftime('%A, %B %d, %Y')}.", "action": "time"}
        elif any(k in normalized for k in ("take screenshot", "take a screenshot", "capture screen", "screen capture")) or normalized in ("screenshot",):
            return self.core.execute_command("screenshot", source="ai")
        elif any(k in normalized for k in ("volume up", "increase volume", "raise volume", "louder")):
            return self.core.execute_command("volume up", source="ai")
        elif any(k in normalized for k in ("volume down", "decrease volume", "lower volume", "quieter")):
            return self.core.execute_command("volume down", source="ai")
        elif any(k in normalized for k in ("mute volume", "mute sound", "mute audio", "unmute volume", "unmute sound")) or normalized in ("mute", "unmute"):
            return self.core.execute_command("mute", source="ai")
        elif any(k in normalized for k in ("lock pc", "lock computer", "lock screen", "lock workstation")):
            return self.core.execute_command("lock pc", source="ai")
        elif any(k in normalized for k in ("show desktop", "minimize all windows", "minimize windows", "show the desktop")):
            return self.core.execute_command("show desktop", source="ai")
        elif any(k in normalized for k in ("battery status", "power status", "battery percentage", "battery level", "power level")) or normalized in ("battery",):
            return self.core.execute_command("battery", source="ai")
        elif any(k in normalized for k in ("enable focus mode", "turn on focus mode", "focus mode on")) or normalized in ("focus mode",):
            return self.core.execute_command("focus mode", source="ai")
        elif any(k in normalized for k in ("enable dev mode", "turn on dev mode", "dev mode on")) or normalized in ("dev mode",):
            return self.core.execute_command("dev mode", source="ai")
        elif normalized in ("settings", "open settings", "system settings", "config"):
            return {"ok": True, "message": "Opening system configuration.", "action": "settings"}
        elif normalized in ("apps", "app grid", "open apps", "open app grid", "all apps"):
            return {"ok": True, "message": "Launching application grid.", "action": "apps"}
        elif normalized in ("gesture", "gestures", "open gesture", "open gestures"):
            return {"ok": True, "message": "Gesture controls active in panel.", "action": "gesture"}
        elif any(k in normalized for k in ("help me", "show commands", "list commands", "what can you do")) or normalized in ("help", "commands"):
            return self.core.execute_command("help", source="ai")

        # 4. Natural application launching
        for prefix in (
            "can you please open ", "can you open ", "please open ", "open the ", "open up ", "open ",
            "can you please launch ", "can you launch ", "please launch ", "launch the ", "launch up ", "launch ",
            "start the ", "start ", "run the ", "run "
        ):
            if normalized.startswith(prefix):
                app_target = normalized[len(prefix):].strip().rstrip(".?!")
                from actions.app_launcher import resolve_application, launch_application
                if resolve_application(app_target):
                    return launch_application(app_target)

        direct_system_apps = {
            "calculator", "calc", "notepad", "paint", "mspaint", "task manager", "taskmgr",
            "cmd", "powershell", "terminal", "snipping tool", "control panel"
        }
        if normalized in direct_system_apps:
            from actions.app_launcher import launch_application
            return launch_application(normalized)

        # 5. Math & arithmetic calculations
        math_match = re.search(r"(?:what is|calculate|evaluate)?\s*([\d\.\s\+\-\*\/\(\)\%]+)", normalized)
        if math_match:
            expr = math_match.group(1).strip()
            if any(op in expr for op in ("+", "-", "*", "/", "%")) and any(c.isdigit() for c in expr):
                try:
                    if re.match(r"^[\d\.\s\+\-\*\/\(\)\%]+$", expr):
                        val = eval(expr, {"__builtins__": None}, {})
                        formatted = f"{val:,.4f}".rstrip("0").rstrip(".") if isinstance(val, float) else f"{val:,}"
                        return {
                            "ok": True,
                            "message": f"{expr} = {formatted}",
                            "action": "calculate",
                            "data": {"expression": expr, "result": val},
                        }
                except Exception:
                    pass

        # 6. Explicit browser search requests
        for search_pfx in ("open google and search ", "open chrome and search ", "search google for "):
            if normalized.startswith(search_pfx):
                query = message.strip()[len(search_pfx):].strip().rstrip(".?!")
                from actions.browser import search_web
                return search_web(query)

        return None

    def _chat_gemini(self, message: str, history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """Chat using Google Gemini with RAG memory context and multi-model fallback."""
        try:
            import google.generativeai as genai

            sys_prompt = self._build_system_prompt(message)

            # Build strictly alternating conversation history
            raw_history = history if history else self._chat_history[:-1]
            contents = []
            last_role = None

            for msg in raw_history[-6:]:
                role = "user" if msg.get("role") == "user" else "model"
                text_content = msg.get("content", "").strip()
                if not text_content:
                    continue
                # Enforce alternating turns
                if role != last_role:
                    contents.append({"role": role, "parts": [text_content]})
                    last_role = role

            # Ensure the final turn is the current user message
            if last_role == "user" and contents:
                contents.append({"role": "model", "parts": ["Understood, standing by."]})
            contents.append({"role": "user", "parts": [message]})

            models_to_try = [self.model, "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
            seen: set[str] = set()
            candidates = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

            last_error = ""
            for m_name in candidates:
                try:
                    try:
                        m = genai.GenerativeModel(m_name, system_instruction=sys_prompt)
                        response = m.generate_content(contents, request_options={"timeout": 15})
                    except (TypeError, Exception):
                        m = genai.GenerativeModel(m_name)
                        first_content = contents[0]["parts"][0] if contents and contents[0].get("parts") else message
                        fallback_contents = [{"role": "user", "parts": [f"{sys_prompt}\n\n{first_content}"]}] + contents[1:]
                        response = m.generate_content(fallback_contents, request_options={"timeout": 15})

                    text = response.text or ""
                    if text:
                        # Record model response to history so subsequent questions don't get repeated!
                        self._chat_history.append({"role": "model", "content": text})
                        parsed = self._try_parse_function_call(text, message)
                        if parsed:
                            return parsed
                        return {"ok": True, "message": text, "action": None}
                except Exception as e:
                    last_error = str(e)
                    continue

            return {"ok": False, "message": f"Gemini error: {last_error[:120]}", "action": None}
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
        """Intelligent local reasoning engine for tasks, conversation, and calculations."""
        text = message.lower().strip()

        # 1. System controls and telemetry
        if any(k in text for k in ("scan", "diagnostic", "analyze")):
            return self.core.execute_command("scan", source="ai")
        elif any(k in text for k in ("status", "health", "how are systems")):
            return self.core.execute_command("status", source="ai")
        elif "time" in text or "what time" in text or "current date" in text:
            from datetime import datetime
            return {"ok": True, "message": f"Local time is {datetime.now().strftime('%H:%M:%S')} on {datetime.now().strftime('%A, %B %d, %Y')}.", "action": "time"}
        elif "screenshot" in text or "capture screen" in text:
            return self.core.execute_command("screenshot", source="ai")
        elif "volume up" in text or "louder" in text or "increase volume" in text:
            return self.core.execute_command("volume up", source="ai")
        elif "volume down" in text or "quieter" in text or "decrease volume" in text:
            return self.core.execute_command("volume down", source="ai")
        elif "mute" in text or "unmute" in text:
            return self.core.execute_command("mute", source="ai")
        elif any(k in text for k in ("lock pc", "lock computer", "lock screen")):
            return self.core.execute_command("lock pc", source="ai")
        elif "show desktop" in text or "minimize all" in text or "minimize windows" in text:
            return self.core.execute_command("show desktop", source="ai")
        elif any(k in text for k in ("battery", "power status", "charging")):
            return self.core.execute_command("battery", source="ai")
        elif "focus mode" in text:
            return self.core.execute_command("focus mode", source="ai")
        elif "dev mode" in text:
            return self.core.execute_command("dev mode", source="ai")
        elif "settings" in text:
            return {"ok": True, "message": "Opening system configuration.", "action": "settings"}
        elif "apps" in text or "app grid" in text:
            return {"ok": True, "message": "Launching application grid.", "action": "apps"}
        elif "gesture" in text:
            return {"ok": True, "message": "Gesture controls active in panel.", "action": "gesture"}
        elif "help" in text or "commands" in text:
            return self.core.execute_command("help", source="ai")

        # 2. Natural Language Application Launching
        # Handles: "open calculator", "please launch paint", "start notepad", "can you open chrome", etc.
        for prefix in (
            "can you please open ", "can you open ", "please open ", "open the ", "open up ", "open ",
            "can you please launch ", "can you launch ", "please launch ", "launch the ", "launch up ", "launch ",
            "start the ", "start ", "run the ", "run "
        ):
            if text.startswith(prefix):
                app_target = text[len(prefix):].strip().rstrip(".?!")
                from actions.app_launcher import resolve_application, launch_application
                if resolve_application(app_target):
                    return launch_application(app_target)

        direct_system_apps = {
            "calculator", "calc", "notepad", "paint", "mspaint", "task manager", "taskmgr",
            "cmd", "powershell", "terminal", "snipping tool", "control panel"
        }
        if text in direct_system_apps:
            from actions.app_launcher import launch_application
            return launch_application(text)

        # 3. Math & Arithmetic Calculation Engine
        # Handles: "what is 25 * 40", "calculate 1500 / 3", "25 + 75", etc.
        math_match = re.search(r"(?:what is|calculate|evaluate)?\s*([\d\.\s\+\-\*\/\(\)\%]+)", text)
        if math_match:
            expr = math_match.group(1).strip()
            # Only evaluate if it contains operators and digits
            if any(op in expr for op in ("+", "-", "*", "/", "%")) and any(c.isdigit() for c in expr):
                try:
                    # Sanitize: allow only numbers, whitespace, and basic math operators
                    if re.match(r"^[\d\.\s\+\-\*\/\(\)\%]+$", expr):
                        val = eval(expr, {"__builtins__": None}, {})
                        formatted = f"{val:,.4f}".rstrip("0").rstrip(".") if isinstance(val, float) else f"{val:,}"
                        return {
                            "ok": True,
                            "message": f"{expr} = {formatted}",
                            "action": "calculate",
                            "data": {"expression": expr, "result": val},
                        }
                except Exception:
                    pass

        # 4. Web Search queries
        # Handles: "search for quantum computing", "google latest news", "look up python tutorials"
        for search_pfx in ("search for ", "search ", "google for ", "google ", "look up "):
            if text.startswith(search_pfx):
                query = message.strip()[len(search_pfx):].strip().rstrip(".?!")
                from actions.browser import search_web
                return search_web(query)

        # 5. Natural Conversations & Personality
        greetings = ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "daddy's home", "greetings"]
        if any(text == g or text.startswith(f"{g} ") for g in greetings):
            return {
                "ok": True,
                "message": "Hello! JARVIS is fully operational and standing by. All neural pathways online. How can I assist you today, sir?",
                "action": None,
            }

        if any(k in text for k in ("who are you", "what are you", "what is your name", "who made you", "introduce yourself")):
            return {
                "ok": True,
                "message": (
                    "I am JARVIS (Just A Rather Very Intelligent System), your personal AI assistant. "
                    "I monitor your hardware, automate Windows tasks, launch applications, store personal memories, "
                    "and assist you via voice and holographic interfaces."
                ),
                "action": None,
            }

        if any(k in text for k in ("what can you do", "your capabilities", "how can you help")):
            return {
                "ok": True,
                "message": (
                    "I can perform a wide range of tasks:\n"
                    "• Open any Windows app ('open calculator', 'open chrome', 'open task manager')\n"
                    "• Control audio & media ('volume up', 'mute', 'play', 'pause')\n"
                    "• Capture screenshots ('take a screenshot')\n"
                    "• Search the web ('search quantum computing', 'google AI news')\n"
                    "• Store & recall personal memories ('remember that...', 'what are my notes?')\n"
                    "• Check hardware telemetry, CPU, RAM, battery, and diagnostics\n"
                    "• Calculate math expressions and execute custom workflows"
                ),
                "action": None,
            }

        if any(k in text for k in ("tell me a joke", "make me laugh", "say something funny")):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
                "Why did the neural network cross the road? To optimize the loss function on the other side.",
                "An SQL statement walks into a bar, approaches two tables and asks: 'May I join you?'",
                "I asked my computer for a joke. It told me Windows was searching for a solution to the problem.",
            ]
            return {"ok": True, "message": random.choice(jokes), "action": None}

        if any(k in text for k in ("thank you", "thanks", "good job", "well done")):
            return {"ok": True, "message": "Always at your service, sir. Let me know if you need anything else.", "action": None}

        # 6. Default helpful assistant response
        return {
            "ok": True,
            "message": (
                f'I understand: "{message}". I am standing by to execute actions, '
                'search the web, store memories, or control your system. How would you like me to proceed?'
            ),
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

                    if action == "open_app":
                        target = params.get("target") or params.get("app") or original_message
                        return self.core.execute_command(f"open {target}", source="ai")

                    if action == "search_web":
                        query = params.get("query", original_message)
                        if any(k in original_message.lower() for k in ("open chrome", "open browser", "open google")):
                            return self.core.execute_command(f"search {query}", source="ai")
                        return self._chat_gemini(f"Please answer this question directly without opening a browser: {query}")

                    if action == "open_url":
                        url = params.get("url", "")
                        return self.core.execute_command(f"open url {url}", source="ai")

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


def chat(message: str, history: List[Dict[str, Any]] | None = None, source: str = "console") -> Dict[str, Any]:
    """Convenience function to chat with the AI."""
    return get_ai_provider().chat(message, history, source=source)