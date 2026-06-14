"""
super_ai.llm
────────────
Local LLM via Ollama (auto-managed, user ko pata bhi nahi chalta).
"""

import json
from typing import Any

import ollama as _ollama

from .config import cfg
from .actions import _DYNAMIC_TOOL_SCHEMAS

# ═══════════════════════════════════════════════════
#  System prompt — tool‑call contract
# ═══════════════════════════════════════════════════

def get_system_prompt() -> str:
    base_prompt = """\
You are Super-AI, a helpful voice assistant on the user's computer.
You can understand English and Hindi perfectly. Reply in simple conversational English or Hindi. Keep answers SHORT (1-2 sentences).

CRITICAL CONTEXT ABOUT USER'S VOICE INPUT:
The speech-to-text engine is English-only. When the user speaks Hindi, it will phonetically butcher the words into random English words!
Examples:
- "casey" -> "kaise ho"
- "him way" -> "hindi"
- "can you understand him way" -> "kya tum hindi samajh sakte ho"
If the user's input looks like weird, non-sensical English words, SOUND IT OUT phonetically. It is almost certainly Hindi. DO NOT assume they are asking about random actors like "Tom Casey". Reply contextually.

You have access to tools. Follow these RULES strictly:
1. If you have all the information needed to perform a task, you MUST reply with ONLY this JSON format (no other text):
{"action": "<tool_name>", "args": {"<arg_name>": "<value>"}}
2. If the user asks you to perform a task but DOES NOT provide necessary details (e.g., says "play music" but no song name, or "send message" but no name), DO NOT use JSON. You MUST reply in plain text asking: "What exactly do you want me to play/open/send?"
3. NEVER invent fake URLs, fake paths, or fake numbers. If you don't know the exact detail, just ask the user!

If the user is just chatting (like "how are you?"), DO NOT use JSON. Just reply normally in plain text.
ONLY use JSON if you need to trigger a specific tool from the list below.
If the user asks for the current time or date, you MUST use the get_time JSON tool.

Available tools:
- open_url: {"action": "open_url", "args": {"url": "https://..."}} — opens a website
- launch_app: {"action": "launch_app", "args": {"name": "AppName"}} — opens a desktop app
- play_media: {"action": "play_media", "args": {"path": "/path/to/file"}} — plays audio/video
- send_message: {"action": "send_message", "args": {"to": "", "body": "text"}} — sends Telegram message
- send_voice_note: {"action": "send_voice_note", "args": {"to": "", "text": "words"}} — sends voice note
- analyse_video: {"action": "analyse_video", "args": {"path": "/path/to/video"}} — analyses video content
- set_reminder: {"action": "set_reminder", "args": {"text": "what", "seconds": 60}} — sets a reminder
- send_whatsapp: {"action": "send_whatsapp", "args": {"phone": "+919876543210", "message": "hello"}} — sends a WhatsApp message
- search_web: {"action": "search_web", "args": {"query": "weather in Delhi"}} — searches the internet
- get_time: {"action": "get_time", "args": {}} — tells the current local time and date
- read_clipboard: {"action": "read_clipboard", "args": {}} — reads clipboard
- read_screen: {"action": "read_screen", "args": {}} — uses OCR to read screen"""
    
    if _DYNAMIC_TOOL_SCHEMAS:
        base_prompt += "\n" + "\n".join(_DYNAMIC_TOOL_SCHEMAS)
        
    base_prompt += """\n
If the user asks a factual question and you don't know the answer, use the search_web tool. Be brief.\
"""
    return base_prompt

_warmed_up = False
_conversation_history = []
MAX_HISTORY = 6  # keep last 6 messages (3 turns)


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

    global _conversation_history
    
    messages = [{"role": "system", "content": get_system_prompt()}]
    for msg in _conversation_history:
        messages.append(msg)
        
    messages.append({"role": "user", "content": user_input})

    try:
        response = _ollama.chat(
            model=cfg.ollama_model,
            messages=messages,
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
    
    is_action = False
    if start >= 0 and end > start:
        try:
            parsed = json.loads(cleaned[start:end])
            if isinstance(parsed, dict) and "action" in parsed:
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    # Update history for plain text responses
    _conversation_history.append({"role": "user", "content": user_input})
    _conversation_history.append({"role": "assistant", "content": text})
    if len(_conversation_history) > MAX_HISTORY:
        _conversation_history = _conversation_history[-MAX_HISTORY:]

    return text
