"""
super_ai.messaging
──────────────────
Telegram Bot — 100% free.

Features:
  - send_text()  → plain text message
  - send_voice() → voice note (WAV file)
  - notify()     → quick notification (har task ke baad)
"""

import asyncio
from pathlib import Path

from .config import cfg

# ═══════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════

def _is_configured() -> bool:
    """Check if Telegram is set up."""
    token = cfg.telegram_bot_token
    chat_id = cfg.telegram_chat_id
    return (
        bool(token) and token != "your_token_here"
        and bool(chat_id) and chat_id != "your_chat_id_here"
    )


def _get_bot():
    """Create a Bot instance."""
    from telegram import Bot
    return Bot(token=cfg.telegram_bot_token)


def _resolve_chat_id(to: str) -> str:
    """Fall back to default chat_id if 'to' is empty."""
    if to and to not in ("", "chat_id", "default"):
        return to
    return cfg.telegram_chat_id


def _run_async(coro):
    """Run async coroutine from sync code."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


# ═══════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════

def send_text(chat_id: str, text: str) -> str:
    """Send a plain text message via Telegram."""
    if not _is_configured():
        return "Telegram not configured. Please add your Bot Token and Chat ID in ~/.superai/config.json"

    chat_id = _resolve_chat_id(chat_id)
    bot = _get_bot()

    async def _send():
        await bot.send_message(chat_id=chat_id, text=text)

    try:
        _run_async(_send())
        msg = f"Message sent: {text[:50]}"
        print(f"[telegram] ✓ {msg}")
        return msg
    except Exception as exc:
        err = f"Telegram error: {exc}"
        print(f"[telegram] ✗ {err}")
        return err


def send_voice(chat_id: str, audio_path: str) -> str:
    """Send a voice note via Telegram."""
    if not _is_configured():
        return "Telegram not configured. Please add your Bot Token and Chat ID in ~/.superai/config.json"

    chat_id = _resolve_chat_id(chat_id)
    bot = _get_bot()
    path = Path(audio_path)

    if not path.is_file():
        return f"Audio file not found: {path}"

    async def _send():
        with open(path, "rb") as f:
            await bot.send_voice(chat_id=chat_id, voice=f)

    try:
        _run_async(_send())
        msg = f"Voice note sent"
        print(f"[telegram] ✓ {msg}")
        return msg
    except Exception as exc:
        err = f"Telegram error: {exc}"
        print(f"[telegram] ✗ {err}")
        return err


def notify(message: str) -> bool:
    """
    Send a quick notification to default Telegram chat.
    Called automatically after every task completes.
    Returns True if sent, False if Telegram not configured (silent fail).
    """
    if not _is_configured():
        # Telegram not set up — silently skip, don't bother user
        return False

    try:
        notification = f"🤖 Super-AI Notification:\n{message}"
        send_text(cfg.telegram_chat_id, notification)
        return True
    except Exception:
        return False
