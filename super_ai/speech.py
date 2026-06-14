"""
super_ai.speech
───────────────
Voice Input  : Vosk (offline, auto‑downloads model)
Voice Output : pyttsx3 (system TTS, zero setup)
"""

import json
import queue
import time
import os
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import pyttsx3

from .config import cfg

# ═══════════════════════════════════════════════════
#  Speech‑to‑Text (Vosk)
# ═══════════════════════════════════════════════════

_vosk_model: Model | None = None
_recognizer: KaldiRecognizer | None = None
_audio_q: queue.Queue = queue.Queue()

SAMPLE_RATE = 16000


def _ensure_vosk():
    """Lazy‑load Vosk — auto‑downloads model on first call."""
    global _vosk_model, _recognizer
    if _vosk_model is not None:
        return

    from .model_manager import ensure_vosk_model
    model_path = ensure_vosk_model()

    print(f"[speech] Loading speech model...")
    _vosk_model = Model(str(model_path))
    _recognizer = KaldiRecognizer(_vosk_model, SAMPLE_RATE)
    _recognizer.SetWords(True)
    print("[speech] ✓ Speech recognition ready")


def _mic_callback(indata, frames, time_info, status):
    """sounddevice callback — raw PCM bytes into queue."""
    if status:
        print(f"[mic] {status}")
    _audio_q.put(bytes(indata))


def listen(timeout: float = 15.0) -> str | None:
    """
    Open mic, record until Vosk hears a complete sentence
    (or timeout). Returns transcribed text or None.
    """
    _ensure_vosk()

    # Drain stale audio
    while not _audio_q.empty():
        _audio_q.get_nowait()

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=_mic_callback,
    ):
        start = time.time()
        while True:
            try:
                data = _audio_q.get(timeout=1.0)
            except queue.Empty:
                if time.time() - start > timeout:
                    return None
                continue

            if _recognizer.AcceptWaveform(data):
                result = json.loads(_recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    print(f"[speech] Heard: \"{text}\"")
                    return text

            if time.time() - start > timeout:
                partial = json.loads(_recognizer.PartialResult())
                text = partial.get("partial", "").strip()
                return text or None

    return None


def check_wake_word(text: str) -> str | None:
    """
    If text starts with wake word, strip it and return the command.
    Otherwise return None.

    Example:
        check_wake_word("hey ai open google")  →  "open google"
        check_wake_word("what time is it")      →  None
    """
    lower = text.lower().strip()
    wake = cfg.wake_word.lower().strip()

    if lower.startswith(wake):
        command = lower[len(wake):].strip()
        return command if command else None
    return None


# ═══════════════════════════════════════════════════
#  Text‑to‑Speech (pyttsx3 — zero setup)
# ═══════════════════════════════════════════════════

_tts_engine: pyttsx3.Engine | None = None


def _ensure_tts():
    """Lazy‑init pyttsx3."""
    global _tts_engine
    if _tts_engine is not None:
        return

    _tts_engine = pyttsx3.init()
    _tts_engine.setProperty("rate", cfg.tts_rate)

    voices = _tts_engine.getProperty("voices")
    if voices and cfg.tts_voice_index < len(voices):
        _tts_engine.setProperty("voice", voices[cfg.tts_voice_index].id)

    print("[speech] ✓ Voice output ready")


def speak(text: str):
    """Speak text aloud (blocking)."""
    _ensure_tts()
    print(f"[ai] {text}")
    _tts_engine.say(text)
    _tts_engine.runAndWait()


def text_to_wav(text: str, output_path: str | None = None) -> str:
    """Render text to WAV file, return path. Used for voice notes."""
    _ensure_tts()
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "superai_voice.wav")

    _tts_engine.save_to_file(text, output_path)
    _tts_engine.runAndWait()
    return output_path
