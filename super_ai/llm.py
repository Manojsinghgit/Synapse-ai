"""
super_ai.llm
────────────
Local LLM via Ollama (auto-managed, user ko pata bhi nahi chalta).
"""

import json
import re
from typing import Any

import ollama as _ollama

from .config import cfg
from .actions import _DYNAMIC_TOOL_SCHEMAS

# ═══════════════════════════════════════════════════
#  System prompt — tool‑call contract
# ═══════════════════════════════════════════════════

from thefuzz import fuzz

def contains_wake_word(text: str) -> bool:
    wake = cfg.wake_word.lower().strip()
    words = re.findall(r'\b\w+\b', text.lower())
    if wake in words:
        return True
        
    # Use fuzzy string matching to dynamically catch misspellings/phonetic errors
    # regardless of what the wake word is changed to in the future
    for w in words:
        if fuzz.ratio(wake, w) >= 75:  # 75% similarity threshold
            return True
            
    # Fallback for known weird Whisper hallucinations specifically for "tom"
    if wake == "tom":
        weird_hallucinations = {"town", "ton", "dom", "tam", "thom", "time", "dumb", "tod"}
        if any(w in weird_hallucinations for w in words):
            return True
            
    return False


def check_intent_via_llm(text: str) -> bool:
    """Uses a lightning-fast zero-shot LLM prompt to detect command/query intent without hardcoding keywords."""
    prompt = f"""\
You are an intent classifier for a voice assistant named {cfg.wake_word}.
Analyze the following transcribed text.
Does this text contain a clear command, a question, or a greeting directed at the assistant?
Consider Hinglish (Hindi-English mix) as well.
Reply with ONLY the word "YES" if it is a command/question/greeting.
Reply with ONLY the word "NO" if it is ambient background noise or unrelated chatter.

Text: "{text}"
"""
    try:
        res = _ollama.chat(
            model=cfg.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0, "num_predict": 2}
        )
        ans = res["message"]["content"].strip().upper()
        return "YES" in ans
    except Exception as e:
        print(f"[llm] Intent check error: {e}")
        return False


def clean_translations(text: str) -> str:
    # Remove bracketed translations like (How are you?) or [I am fine.]
    text = re.sub(r'\s*\([^)]*\)', '', text)
    text = re.sub(r'\s*\[[^\]]*\]', '', text)
    return text.strip()


def get_system_prompt(expect_followup: bool = False, force_respond: bool = False) -> str:
    wake = cfg.wake_word.capitalize()

    base_prompt = f"""\
You are {wake}, an advanced ambient AI assistant (like Jarvis from Iron Man) running on the user's macOS computer.
You are ALWAYS listening to the user's microphone.
"""

    if force_respond:
        base_prompt += f"""
═══ DIRECT RESPONSE MODE ═══
The user is speaking directly to you. Do NOT reply with "IGNORE". You MUST process the command, answer the question, or perform the requested action.
• If the user's request is incomplete (e.g., they say "send a whatsapp" but not to whom, or what to say), do NOT make a tool call with placeholder/fake values. Instead, ASK the user for the missing details.
"""
    else:
        base_prompt += f"""
═══ AMBIENT LISTENING RULES ═══
Because the mic is always on, you will hear background chatter, TV audio, and random noise.
• If the input is NOT addressed to you → reply with the single word: IGNORE
• If the input is garbled noise or meaningless fragments (e.g. "Ah", "Um", "Pico", "questioned") → reply: IGNORE
• You MUST reply to the user when they give a clear command/question directed at a computer (e.g. "open YouTube", "what time is it", "send a message")
"""

    base_prompt += f"""
═══ HOW TO TALK ═══
• Be natural. Talk like a human friend, not a robot.
• Match the user's language. If they speak Hindi/Hinglish, reply in Hindi/Hinglish. If English, reply in English.
• NEVER put translations in brackets like "Kaise ho? (How are you?)". Pick ONE language.
• Keep replies SHORT — 1-2 sentences max for conversation, just the JSON for tool calls.

═══ SPEECH-TO-TEXT QUIRKS ═══
The speech engine is English-based. Hindi words often get mangled:
  "casey" → kaise, "him way" → Hindi, "whats up" → WhatsApp, "some age" → samajh
Sound out garbled text phonetically — it's probably Hindi.

═══ TOOL CALLS ═══
When you need to perform an action, reply with ONLY this JSON (no other text before or after):
{{"action": "<tool_name>", "args": {{"<key>": "<value>"}}}}

CRITICAL TOOL RULES:
• NEVER invent fake phone numbers, file paths, or contact names. If you don't know, ASK.
• If the user says "send WhatsApp message" but doesn't say to whom, ASK: "Kisko bhejna hai?".
• NEVER invent the `message` content. If the user doesn't say WHAT to send, ASK: "Kya message bhejna hai?". NEVER guess or send "Hello!".
• If the transcribed name or message looks weird, CONFIRM it first before sending (e.g. "Should I send this to [Name]?").
• Your saved WhatsApp contacts are: {", ".join(cfg.whatsapp_contacts.keys()) if cfg.whatsapp_contacts else "None"}. If a name sounds similar to these (e.g. "Onyth" -> "Ronit"), assume it's the saved contact.
• If the user gives incomplete info, ASK for it. Do NOT guess.

Available tools:
- open_url      → {{"action":"open_url","args":{{"url":"https://..."}}}}
- launch_app    → {{"action":"launch_app","args":{{"name":"AppName"}}}}
- send_whatsapp → {{"action":"send_whatsapp","args":{{"phone":"name_or_number","message":"text"}}}}
- send_message  → {{"action":"send_message","args":{{"to":"name","body":"text"}}}} (Telegram)
- search_web    → {{"action":"search_web","args":{{"query":"..."}}}}
- get_time      → {{"action":"get_time","args":{{}}}}
- set_reminder  → {{"action":"set_reminder","args":{{"text":"what","seconds":60}}}}
- read_clipboard→ {{"action":"read_clipboard","args":{{}}}}
- read_screen   → {{"action":"read_screen","args":{{}}}}
- play_media    → {{"action":"play_media","args":{{"path":"/path/to/file"}}}}
- play_youtube  → {{"action":"play_youtube","args":{{"query":"..."}}}}
- get_wikipedia_summary → {{"action":"get_wikipedia_summary","args":{{"query":"..."}}}}
- get_weather   → {{"action":"get_weather","args":{{"location":"city name"}}}}
- tell_joke     → {{"action":"tell_joke","args":{{}}}}
"""

    if expect_followup:
        base_prompt += f"\n⚡ CONTEXT: You just asked the user a question. Their next message is almost certainly a direct reply to YOU. Do NOT reply IGNORE unless it is absolute garbage noise.\n"

    if _DYNAMIC_TOOL_SCHEMAS:
        base_prompt += "\nAdditional tools:\n" + "\n".join(_DYNAMIC_TOOL_SCHEMAS) + "\n"

    base_prompt += "\nIf the user asks a factual question you don't know the answer to, use search_web.\n"
    return base_prompt


_warmed_up = False
_conversation_history = []
MAX_HISTORY = 10  # keep last 10 messages (5 turns) for better multi-turn context


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


def _is_ignore(text: str) -> bool:
    """Robustly detect IGNORE responses from the LLM regardless of formatting quirks."""
    cleaned = text.strip().strip(".,!;:'\"").strip().upper()
    # Accept: "IGNORE", "Ignore", "ignore.", "IGNORE!", etc.
    if cleaned == "IGNORE":
        return True
    # Also catch things like "It seems like... IGNORE" — if it ends with IGNORE
    if cleaned.endswith("IGNORE") and len(cleaned) < 80:
        return True
    return False


def ask(user_input: str, expect_followup: bool = False) -> dict | str:
    """
    Send user_input to local LLM.
    Returns dict (tool-call), str (plain answer), or "IGNORE".
    """
    _ensure_llm()

    global _conversation_history

    # Determine if we should force response based on wake word, LLM intent check, or active follow-up
    has_wake = contains_wake_word(user_input)
    
    if has_wake or expect_followup:
        force_respond = True
    else:
        # Run zero-shot intent classifier only if no wake word and no active conversation
        force_respond = check_intent_via_llm(user_input)

    messages = [{"role": "system", "content": get_system_prompt(expect_followup, force_respond)}]
    messages.extend(_conversation_history)
    messages.append({"role": "user", "content": user_input})

    try:
        response = _ollama.chat(
            model=cfg.ollama_model,
            messages=messages,
            options={
                "temperature": 0.3,
                "num_predict": 250,
            },
        )
        text = response["message"]["content"].strip()
    except Exception as exc:
        print(f"[llm] Error: {exc}")
        return f"Sorry, my brain had an error: {exc}"

    # ── Check for IGNORE ──
    if not force_respond and _is_ignore(text):
        print(f"[llm] → IGNORE (background noise)")
        return "IGNORE"

    # Clean any bracket translations first
    text = clean_translations(text)

    # If the response became empty after cleaning, return IGNORE
    if not text:
        return "IGNORE"

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
                # Save the tool-call context in history so follow-ups work
                _conversation_history.append({"role": "user", "content": user_input})
                _conversation_history.append({"role": "assistant", "content": text})
                if len(_conversation_history) > MAX_HISTORY:
                    _conversation_history = _conversation_history[-MAX_HISTORY:]
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    # Update history for plain text responses (NOT for IGNORE)
    _conversation_history.append({"role": "user", "content": user_input})
    _conversation_history.append({"role": "assistant", "content": text})
    if len(_conversation_history) > MAX_HISTORY:
        _conversation_history = _conversation_history[-MAX_HISTORY:]

    return text
