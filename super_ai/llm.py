"""
super_ai.llm
────────────
Local LLM via Ollama (auto-managed, user ko pata bhi nahi chalta).
"""

import json
from typing import Any

import ollama as _ollama

from .config import cfg

# ═══════════════════════════════════════════════════
#  System prompt — tool‑call contract
# ═══════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are Super-AI, a helpful voice assistant on the user's computer.
The user speaks in Hindi-English mix. Reply in simple English. Keep answers SHORT (1-2 sentences).

IMPORTANT: When the user asks you to DO something, reply with ONLY this JSON (no other text):
{"action": "<tool>", "args": {<arguments>}}

Available tools:
- open_url: {"url": "https://..."} — opens a website
- launch_app: {"name": "AppName"} — opens a desktop app
- play_media: {"path": "/path/to/file"} — plays audio/video
- send_message: {"to": "", "body": "text"} — sends Telegram message
- send_voice_note: {"to": "", "text": "words"} — sends voice note
- analyse_video: {"path": "/path/to/video"} — analyses video content
- set_reminder: {"text": "what", "seconds": 60} — sets a reminder
- send_whatsapp: {"phone": "+919876543210", "message": "hello"} — sends a WhatsApp message (use exact phone number with country code, or a saved contact name)
- search_web: {"query": "weather in Delhi"} — searches the internet for real-time information

If the user is just asking a question and you don't know the answer, use the search_web tool instead of making it up. Be brief.\
"""

_warmed_up = False


def _ensure_llm():
    """Verify LLM is reachable by sending a tiny test prompt."""
    global _warmed_up
    if _warmed_up:
        return

    print("[llm] Warming up AI brain...")
    try:
        _ollama.chat(
            model=cfg.ollama_model,
            messages=[{"role": "user", "content": "hi"}],
            options={"num_predict": 1},
        )
        _warmed_up = True
        print("[llm] ✓ AI brain ready")
    except Exception as exc:
        raise RuntimeError(
            f"Cannot reach AI brain: {exc}\n"
            "This should not happen — model_manager should have started it."
        ) from exc


def ask(user_input: str) -> dict | str:
    """
    Send user_input to local LLM.
    Returns dict (tool-call) or str (plain answer).
    """
    _ensure_llm()

    try:
        response = _ollama.chat(
            model=cfg.ollama_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            options={
                "temperature": 0.3,
                "num_predict": 200,
            },
        )
        text = response["message"]["content"].strip()
    except Exception as exc:
        print(f"[llm] Error: {exc}")
        return f"Sorry, my brain had an error: {exc}"

    print(f"[llm] Response: {text}")

    # ── Try parsing as JSON tool‑call ──
    cleaned = text
    if "```" in cleaned:
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            parsed = json.loads(cleaned[start:end])
            if isinstance(parsed, dict) and "action" in parsed:
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    return text
