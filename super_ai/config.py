"""
super_ai.config
───────────────
Auto-config. User ko kuch set nahi karna.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
import json
from dotenv import load_dotenv

# Models stored in ~/.superai/models/
DATA_DIR = Path.home() / ".superai"
MODELS_DIR = DATA_DIR / "models"

# Optional .env (for Telegram)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env", override=False)


@dataclass
class Config:
    """All settings with defaults — works out of the box."""

    # Paths
    data_dir: Path = field(default_factory=lambda: DATA_DIR)
    models_dir: Path = field(default_factory=lambda: MODELS_DIR)

    # Vosk
    vosk_model_url: str = "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"
    vosk_model_name: str = "vosk-model-small-en-in-0.4"

    # Ollama
    ollama_model: str = "llama3.2:1b"

    # Wake word
    wake_word: str = "hey ai"

    # TTS
    tts_rate: int = 150
    tts_voice_index: int = 0

    # Telegram (optional)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # WhatsApp Contacts (optional, JSON string in .env: {"name": "+91..."})
    whatsapp_contacts: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        contacts_str = os.getenv("WHATSAPP_CONTACTS", "{}")
        try:
            contacts = json.loads(contacts_str)
        except Exception:
            contacts = {}

        c = cls(
            wake_word=os.getenv("WAKE_WORD", "hey ai").lower(),
            tts_rate=int(os.getenv("TTS_RATE", "150")),
            tts_voice_index=int(os.getenv("TTS_VOICE_INDEX", "0")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            whatsapp_contacts=contacts,
        )
        c.data_dir.mkdir(parents=True, exist_ok=True)
        c.models_dir.mkdir(parents=True, exist_ok=True)
        return c

    @property
    def vosk_model_path(self) -> Path:
        return self.models_dir / self.vosk_model_name


cfg = Config.load()
