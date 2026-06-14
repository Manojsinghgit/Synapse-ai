"""
super_ai.actions
────────────────
OS‑level action dispatcher.

LLM returns JSON → this module executes it → sends Telegram notification.
"""

import os
import sys
import webbrowser
import subprocess
import platform
import urllib.parse
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from .config import cfg

# ═══════════════════════════════════════════════════
#  Scheduler (reminders)
# ═══════════════════════════════════════════════════

_scheduler = BackgroundScheduler()
_scheduler.start()


# ═══════════════════════════════════════════════════
#  Action functions
# ═══════════════════════════════════════════════════

def open_url(url: str) -> str:
    """Open a URL in the default browser."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def launch_app(name: str) -> str:
    """Launch a desktop app by name."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", "-a", name])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", name])
        elif system == "Windows":
            os.startfile(name)
        else:
            return f"Unsupported OS: {system}"
        return f"Launched {name}"
    except Exception as exc:
        return f"Could not launch {name}: {exc}"


def play_media(path: str) -> str:
    """Play audio/video with default system player."""
    filepath = Path(path).expanduser().resolve()
    if not filepath.is_file():
        return f"File not found: {filepath}"

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", str(filepath)])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", str(filepath)])
        elif system == "Windows":
            os.startfile(str(filepath))
        return f"Playing {filepath.name}"
    except Exception as exc:
        return f"Could not play: {exc}"


def send_message(to: str = "", body: str = "") -> str:
    """Send Telegram text message."""
    from .messaging import send_text
    return send_text(to, body)


def send_voice_note(to: str = "", text: str = "") -> str:
    """Generate voice note from text and send via Telegram."""
    from .speech import text_to_wav
    from .messaging import send_voice

    wav_path = text_to_wav(text)
    return send_voice(to, wav_path)


def analyse_video_action(path: str) -> str:
    """Analyse a video and return summary."""
    from .video import analyse_video
    return analyse_video(path)


def set_reminder(text: str, seconds: int = 60) -> str:
    """Set a reminder — speaks + sends Telegram notification when fires."""
    from .speech import speak
    from .messaging import notify

    def _fire():
        msg = f"⏰ Reminder: {text}"
        print(f"\n[reminder] {msg}")
        speak(f"Reminder: {text}")
        notify(msg)

    run_at = datetime.now() + timedelta(seconds=int(seconds))
    _scheduler.add_job(_fire, "date", run_date=run_at)
    return f"Reminder set for {seconds} seconds: {text}"


def send_whatsapp(phone: str, message: str) -> str:
    """Send a WhatsApp message automatically, prioritizing the desktop app if installed."""
    import time
    try:
        import pyautogui
    except ImportError:
        return "pyautogui library is missing. Please run: pip install pyautogui"
        
    try:
        # Resolve contact name to phone number if it exists in config
        contact_name = phone.lower().strip()
        if contact_name in cfg.whatsapp_contacts:
            phone = cfg.whatsapp_contacts[contact_name]
            
        print(f"[action] Preparing to send WhatsApp message to {phone}...")
        
        # Clean phone number
        phone_clean = "".join(c for c in phone if c.isdigit() or c == "+")
        encoded_message = urllib.parse.quote(message)
        uri = f"whatsapp://send?phone={phone_clean}&text={encoded_message}"
        
        # 1. Try Desktop App using URI scheme
        opened_desktop = False
        system = platform.system()
        
        if system == "Darwin":
            result = subprocess.run(["open", uri], capture_output=True)
            if result.returncode == 0:
                opened_desktop = True
        elif system == "Windows":
            try:
                os.startfile(uri)
                opened_desktop = True
            except Exception:
                pass
        elif system == "Linux":
            result = subprocess.run(["xdg-open", uri], capture_output=True)
            if result.returncode == 0:
                opened_desktop = True
                
        if opened_desktop:
            print("[action] Opened WhatsApp Desktop App. Waiting 5 seconds to load...")
            time.sleep(5)  # wait for app to focus and draft to load
            pyautogui.press("enter")
            return f"WhatsApp message sent to {phone} (via Desktop App)"
            
        # 2. Fallback to Browser
        print("[action] Desktop app not found or failed. Falling back to Browser...")
        try:
            import pywhatkit
            pywhatkit.sendwhatmsg_instantly(phone_clean, message, wait_time=15, tab_close=True, close_time=3)
            return f"WhatsApp message sent to {phone} (via Browser)"
        except ImportError:
            return "Desktop App failed, and pywhatkit library is missing for browser fallback."
            
    except Exception as exc:
        return f"Could not send WhatsApp message: {exc}"


def get_time() -> str:
    """Gets the current date and time locally."""
    now = datetime.now().strftime("%I:%M %p, %A, %B %d, %Y")
    return f"The current time is {now}."


def search_web(query: str) -> str:
    """Search the web using duckduckgo-search and open the browser so the user can see."""
    try:
        # Open browser to show the user
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
            
        if not results:
            return f"I couldn't find any web results for {query}."
            
        # Get the first snippet
        snippet = results[0]['body']
        
        return f"According to the web: {snippet}"
    except ImportError:
        return "duckduckgo-search library is not installed."
    except Exception as exc:
        return f"Could not search the web: {exc}"


def read_clipboard() -> str:
    """Reads the current text from the clipboard."""
    try:
        import pyperclip
        text = pyperclip.paste()
        if not text.strip():
            return "The clipboard is empty."
        return f"Clipboard content: {text[:500]}"
    except ImportError:
        return "pyperclip library is not installed."
    except Exception as exc:
        return f"Could not read clipboard: {exc}"


def read_screen() -> str:
    """Takes a screenshot and reads the text on the screen using OCR."""
    try:
        from PIL import ImageGrab
        import pytesseract
        
        img = ImageGrab.grab()
        text = pytesseract.image_to_string(img)
        if not text.strip():
            return "No readable text found on the screen."
        return f"Screen text: {text[:1000]}"
    except ImportError:
        return "Pillow or pytesseract libraries are not installed."
    except Exception as exc:
        if "tesseract is not installed" in str(exc).lower():
            import platform
            sys_name = platform.system()
            if sys_name == "Darwin":
                return "Tesseract OCR is missing. Install it using: brew install tesseract"
            elif sys_name == "Windows":
                return "Tesseract OCR is missing. Please install it from https://github.com/UB-Mannheim/tesseract/wiki"
            else:
                return "Tesseract OCR is missing. Install it using: sudo apt install tesseract-ocr"
        return f"Could not read screen: {exc}"


# ═══════════════════════════════════════════════════
#  Dispatcher & Plugins
# ═══════════════════════════════════════════════════

_ACTION_MAP = {
    "open_url": open_url,
    "launch_app": launch_app,
    "play_media": play_media,
    "send_message": send_message,
    "send_voice_note": send_voice_note,
    "analyse_video": analyse_video_action,
    "set_reminder": set_reminder,
    "send_whatsapp": send_whatsapp,
    "search_web": search_web,
    "read_clipboard": read_clipboard,
    "read_screen": read_screen,
    "get_time": get_time,
}

_DYNAMIC_TOOL_SCHEMAS = []

def load_plugins():
    """Load user plugins from the plugins directory."""
    for file_path in cfg.plugins_dir.glob("*.py"):
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            if spec.loader:
                spec.loader.exec_module(module)
                
                if hasattr(module, "register_plugin"):
                    module.register_plugin(_ACTION_MAP, _DYNAMIC_TOOL_SCHEMAS)
                    print(f"[plugins] Loaded {file_path.name}")
        except Exception as exc:
            print(f"[plugins] Error loading {file_path.name}: {exc}")

# Load plugins on module import
load_plugins()


def run_action(action_data: dict) -> str:
    """
    Execute an action from LLM's JSON output.
    After completion, auto-sends Telegram notification.

    Parameters
    ----------
    action_data : dict
        {"action": "open_url", "args": {"url": "https://google.com"}}

    Returns
    -------
    str — result message (spoken back to user)
    """
    from .messaging import notify

    action_name = action_data.get("action", "")
    args = action_data.get("args", {})

    # Robustness: LLM sometimes puts arguments at the top level instead of inside "args"
    if not args:
        args = {k: v for k, v in action_data.items() if k not in ("action", "args")}

    func = _ACTION_MAP.get(action_name)
    if func is None:
        supported = ", ".join(sorted(_ACTION_MAP.keys()))
        return f"Unknown action: {action_name}. I can do: {supported}"

    try:
        print(f"[action] ▶ {action_name}({args})")
        result = func(**args)
        print(f"[action] ✓ {result}")

        # ── Auto‑notify on Telegram ──
        notify(f"✅ Task done: {action_name}\n{result}")

        return result

    except Exception as exc:
        err = f"Action {action_name} failed: {exc}"
        print(f"[action] ✗ {err}")

        # ── Notify failure too ──
        notify(f"❌ Task failed: {action_name}\n{exc}")

        return err
