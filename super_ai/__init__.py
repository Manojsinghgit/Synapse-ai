"""
super_ai
════════
Free, offline, voice‑controlled AI assistant.

Install:  pip install .
Run:      superai

That's it. Models auto‑download. Telegram notifications auto‑send.
"""

__version__ = "0.1.0"

from .speech import listen, speak, check_wake_word, text_to_wav
from .llm import ask
from .actions import run_action


def start_loop():
    """
    The WHOLE assistant. One function. Called by `superai` CLI.
    """
    from .config import cfg
    from .messaging import notify

    # ── Banner ──
    print()
    print("╔══════════════════════════════════════════╗")
    print("║     🤖  S U P E R - A I   v0.1.0        ║")
    print("║     Free · Offline · Voice-Controlled    ║")
    print("╚══════════════════════════════════════════╝")
    print()

    # ── Auto‑download models (first run only) ──
    print("⏳ Checking models...")
    from .model_manager import ensure_all_models
    ensure_all_models()

    # ── Warm up engines ──
    print("⏳ Starting speech engine...")
    from .speech import _ensure_vosk, _ensure_tts
    _ensure_vosk()
    _ensure_tts()

    print("⏳ Starting AI brain...")
    from .llm import _ensure_llm
    _ensure_llm()

    # ── Ready ──
    print()
    print("═" * 44)
    print(f"  ✅ READY! Say \"{cfg.wake_word}\" + command")
    print(f"  Example: \"{cfg.wake_word} open youtube\"")
    print(f"  Press Ctrl+C to quit")
    print("═" * 44)
    print()

    speak(f"Super AI is ready. Say {cfg.wake_word} followed by your command.")

    # Notify on Telegram that AI is online
    notify("🟢 Super-AI is now online and listening!")

    # ── Main loop — runs forever until Ctrl+C ──
    while True:
        try:
            # 1. Listen
            text = listen(timeout=15)
            if not text:
                continue

            # 2. Wake word?
            command = check_wake_word(text)
            if command is None:
                continue  # not for us

            print(f"\n🎯 Command: \"{command}\"")

            # 3. Ask LLM
            response = ask(command)

            # 4. Execute or speak
            if isinstance(response, dict):
                # Tool‑call → run action → speak result → Telegram notify (auto)
                result = run_action(response)
                speak(result)
            else:
                # Plain answer → speak it
                speak(response)

            print()

        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
            speak("Goodbye!")
            notify("🔴 Super-AI is now offline.")
            break
        except Exception as exc:
            print(f"[error] {exc}")
            speak("Sorry, something went wrong.")
            notify(f"⚠️ Error: {exc}")
