"""
super_ai.config
───────────────
Auto-config. User ko kuch set nahi karna.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field

# Models stored in ~/.superai/models/
DATA_DIR = Path.home() / ".superai"
MODELS_DIR = DATA_DIR / "models"
PLUGINS_DIR = DATA_DIR / "plugins"
CONFIG_FILE = DATA_DIR / "config.json"


@dataclass
class Config:
    """All settings with defaults — works out of the box."""

    # Paths
    data_dir: Path = field(default_factory=lambda: DATA_DIR)
    models_dir: Path = field(default_factory=lambda: MODELS_DIR)
    plugins_dir: Path = field(default_factory=lambda: PLUGINS_DIR)

    # Speech Model
    vosk_model_url: str = "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"
    vosk_model_name: str = "vosk-model-small-en-in-0.4"

    # AI Brain
    ollama_model: str = "llama3.2:1b"

    # Wake word
    wake_word: str = "hey ai"

    # TTS
    tts_rate: int = 150
    tts_voice_index: int = 0

    # Telegram (optional)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # WhatsApp Contacts (optional: {"name": "+91..."})
    whatsapp_contacts: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

        c = cls()
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                c.wake_word = data.get("wake_word", c.wake_word)
                c.tts_rate = data.get("tts_rate", c.tts_rate)
                c.tts_voice_index = data.get("tts_voice_index", c.tts_voice_index)
                c.telegram_bot_token = data.get("telegram_bot_token", c.telegram_bot_token)
                c.telegram_chat_id = data.get("telegram_chat_id", c.telegram_chat_id)
                c.whatsapp_contacts = data.get("whatsapp_contacts", c.whatsapp_contacts)
            except Exception:
                pass
        return c

    def save(self):
        data = {
            "wake_word": self.wake_word,
            "tts_rate": self.tts_rate,
            "tts_voice_index": self.tts_voice_index,
            "telegram_bot_token": self.telegram_bot_token,
            "telegram_chat_id": self.telegram_chat_id,
            "whatsapp_contacts": self.whatsapp_contacts,
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @property
    def vosk_model_path(self) -> Path:
        return self.models_dir / self.vosk_model_name


cfg = Config.load()

def interactive_setup():
    """Prompt user for setup if not done yet."""
    if CONFIG_FILE.exists():
        return
        
    print("\n" + "="*50)
    print("🚀 Welcome to Super-AI Setup!")
    print("="*50)
    
    # AI Name
    print("\n1. Name your AI")
    print("What should the AI respond to? (e.g., Jarvis, Friday, or Hey AI)")
    name = input(f"Enter name [Default: {cfg.wake_word}]: ").strip()
    if name:
        cfg.wake_word = name.lower()
        
    # Telegram
    print("\n2. Telegram Notifications (Optional)")
    print("Do you want to receive notifications on your phone when tasks are done?")
    tg_choice = input("Enter y/n [Default: n]: ").strip().lower()
    if tg_choice == 'y':
        print("\n--- Telegram Setup Guide ---")
        print("a. Open Telegram app and search for '@BotFather'")
        print("b. Send '/newbot' and follow steps to get your HTTP API Token.")
        cfg.telegram_bot_token = input("Paste your Bot Token here: ").strip()
        
        print("\nc. Now search for '@userinfobot' on Telegram and send '/start'.")
        print("d. It will reply with your 'Id'.")
        cfg.telegram_chat_id = input("Paste your ID here: ").strip()
        print("----------------------------")
    
    cfg.save()
    print("\n✅ Setup complete! Settings saved.\n")
