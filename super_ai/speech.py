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
import platform
import subprocess
from pathlib import Path

import numpy as np
import sounddevice as sd
import pyttsx3

from .config import cfg

# ═══════════════════════════════════════════════════
#  Speech‑to‑Text (Whisper + VAD)
# ═══════════════════════════════════════════════════

_whisper_model = None
_audio_q: queue.Queue = queue.Queue()

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.05  # Increased energy threshold for speech (ignores bg noise)
SILENCE_DURATION = 1.2    # Seconds of silence to consider speech finished

def _ensure_whisper():
    """Lazy‑load Whisper model."""
    global _whisper_model
    if _whisper_model is not None:
        return
        
    import ssl
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
        
    import warnings
    warnings.filterwarnings("ignore", module="whisper")
    import whisper

    print(f"[speech] Loading Speech Engine (Whisper {cfg.whisper_model})...")
    _whisper_model = whisper.load_model(cfg.whisper_model)
    
    # Warmup
    dummy_audio = np.zeros(16000 * 1, dtype=np.float32)
    _whisper_model.transcribe(dummy_audio, fp16=False)
    print("[speech] ✓ Speech recognition ready")

def _mic_callback(indata, frames, time_info, status):
    """sounddevice callback — raw PCM float32 into queue."""
    if status:
        pass
    _audio_q.put(indata.copy())

def listen(timeout: float = 15.0) -> str | None:
    """
    Open mic, use VAD to record a sentence, and transcribe using Whisper.
    """
    _ensure_whisper()

    # Drain stale audio
    while not _audio_q.empty():
        _audio_q.get_nowait()

    print("[speech] Listening...")
    
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=4000, # 0.25 seconds chunks
        dtype="float32",
        channels=1,
        callback=_mic_callback,
    ):
        start_time = time.time()
        recording = False
        silence_frames = 0
        audio_buffer = []
        pre_roll = []  # Store last 2 chunks (0.5s) of background audio
        
        while True:
            if time.time() - start_time > timeout and not recording:
                return None
                
            try:
                chunk = _audio_q.get(timeout=1.0)
            except queue.Empty:
                continue

            # Calculate RMS energy
            rms = np.sqrt(np.mean(chunk**2))
            
            if rms > SILENCE_THRESHOLD:
                # User is speaking
                if not recording:
                    recording = True
                    # Add pre-roll so we don't lose the quiet start of the first word (like "T" in "Tom")
                    audio_buffer.extend(pre_roll)
                audio_buffer.append(chunk)
                silence_frames = 0
            elif recording:
                # User is quiet, but we are recording
                audio_buffer.append(chunk)
                silence_frames += 1
                
                # Check if silence duration exceeded
                # 4000 samples @ 16000Hz = 0.25s per chunk. 1.0s = 4 chunks
                if silence_frames >= (SILENCE_DURATION / 0.25):
                    break
            else:
                # Not recording yet, keep a rolling buffer of 2 chunks
                pre_roll.append(chunk)
                if len(pre_roll) > 2:
                    pre_roll.pop(0)

        if not audio_buffer:
            return None

        # Process recorded audio
        audio_data = np.concatenate(audio_buffer).flatten()
        
        # Whisper transcription
        # We pass the wake word as the initial_prompt so Whisper expects it
        # and doesn't filter it out as background noise/stutter.
        prompt = f"{cfg.wake_word}, "
        result = _whisper_model.transcribe(audio_data, fp16=False, initial_prompt=prompt)
        text = result.get("text", "").strip()
        
        if text:
            print(f"[speech] Heard: \"{text}\"")
            return text
            
    return None

def check_wake_word(text: str) -> str | None:
    """
    If text starts with wake word (ignoring punctuation), return the command.
    """
    import string
    # Remove punctuation for cleaner matching
    clean_text = text.translate(str.maketrans('', '', string.punctuation)).lower().strip()
    wake = cfg.wake_word.lower().strip()

    if clean_text.startswith(wake):
        # The actual text might have punctuation, we try to strip wake word roughly
        words = text.split()
        if len(words) > 0 and wake in words[0].lower():
            command = " ".join(words[1:]).strip()
            return command if command else None
        # Fallback
        command = clean_text[len(wake):].strip()
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
    print(f"[ai] {text}")
    
    if platform.system() == "Darwin":
        try:
            # Use macOS native 'say' command for natural Siri voice
            subprocess.run(["say", text])
            return
        except Exception:
            pass # fallback to pyttsx3

    _ensure_tts()
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
