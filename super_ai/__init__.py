"""
super_ai
════════
Free, offline, voice‑controlled AI assistant.

Install:  pip install .
Run:      superai

That's it. Models auto‑download. Telegram notifications auto‑send.
"""

import importlib.metadata
try:
    __version__ = importlib.metadata.version("synapse-assistant-ai")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.3.1"

from .speech import listen, speak, check_wake_word, text_to_wav
from .llm import ask
from .actions import run_action


def start_loop():
    """
    The WHOLE assistant. One function. Called by `superai` CLI.
    """
    from .config import interactive_setup, cfg
    from .messaging import notify

    # ── Interactive Setup (if first run) ──
    interactive_setup()

    # ── Banner ──
    print()
    ai_name = cfg.wake_word.upper()
    title_line = f"🤖  {ai_name}   v{__version__}"
    print("╔══════════════════════════════════════════╗")
    print(f"║{title_line.center(42)}║")
    print("║     Free · Offline · Voice-Controlled    ║".center(44))
    print("╚══════════════════════════════════════════╝")
    print()

    # ── Auto‑download models (first run only) ──
    print("⏳ Checking models...")
    from .model_manager import ensure_all_models
    ensure_all_models()

    # ── Warm up engines ──
    print("⏳ Starting speech engine...")
    from .speech import _ensure_whisper, _ensure_tts
    _ensure_whisper()
    _ensure_tts()

    print("⏳ Starting AI brain...")
    from .llm import _ensure_llm
    _ensure_llm()

    # ── Ready ──
    print()
    print("═" * 44)
    print(f"  ✅ READY! Jarvis Mode (Always Listening)")
    print(f'  Say "{cfg.wake_word}" to talk, or just chat')
    print(f"  Press Ctrl+C to quit")
    print("═" * 44)
    print()

    speak(f"{cfg.wake_word.capitalize()} is online. I'm listening.")

    # Notify on Telegram that AI is online
    notify(f"🟢 {cfg.wake_word.capitalize()} is now online and listening!")

    # ── Main loop — Jarvis mode ──
    expect_followup = False
    consecutive_ignores = 0

    while True:
        try:
            # 1. Listen ambiently
            #    When expecting a follow-up, use shorter timeout so user feels responsiveness
            t = 10 if expect_followup else 15
            text = listen(timeout=t)

            if not text:
                # Silence timeout
                if expect_followup:
                    # User didn't reply after AI asked a question — reset
                    expect_followup = False
                continue

            # 2. Send to LLM — it decides whether to IGNORE or respond
            response = ask(text, expect_followup=expect_followup)

            # 3. Handle IGNORE
            if isinstance(response, str) and response.strip().upper() == "IGNORE":
                consecutive_ignores += 1
                # Don't flood the terminal with IGNORE logs
                if consecutive_ignores <= 3:
                    print(f"   ↳ (ignored background noise)")
                continue

            consecutive_ignores = 0
            print(f"\n🎯 Responding to: \"{text}\"")

            # 4. Execute tool or speak response
            if isinstance(response, dict):
                # Tool call → execute → speak result
                result = run_action(response)
                speak(result)
                # After a completed action, don't expect immediate follow-up
                expect_followup = False
            else:
                # Conversational reply → speak it
                speak(response)

                # Detect if AI asked a follow-up question
                resp_lower = response.strip().lower()
                if (response.strip().endswith("?")
                    or "kisko" in resp_lower
                    or "kya " in resp_lower
                    or "kaun" in resp_lower
                    or "which" in resp_lower
                    or "what " in resp_lower
                    or "who " in resp_lower):
                    expect_followup = True
                else:
                    expect_followup = False

            print()

        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
            speak("Goodbye!")
            notify(f"🔴 {cfg.wake_word.capitalize()} is now offline.")
            break
        except Exception as exc:
            print(f"[error] {exc}")
            import traceback
            traceback.print_exc()
            # Don't crash the whole loop for one error
            expect_followup = False
