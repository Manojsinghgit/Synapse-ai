"""
super_ai.speech
───────────────
Voice Input  : OpenAI Whisper (offline, auto-downloads model)
Voice Output : macOS `say` command (natural Siri voice) with pyttsx3 fallback
"""

import json
import queue
import time
import os
import tempfile
import platform
import subprocess
import threading
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
SILENCE_THRESHOLD = 0.04   # RMS energy threshold (slightly lower to catch soft "Tom")
SILENCE_DURATION = 1.5     # Seconds of silence to consider speech done
MIN_AUDIO_LENGTH = 0.5     # Minimum seconds of audio to bother transcribing

# Flag to pause listening while the AI is speaking (prevent echo)
_speaking = False


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

    # Warmup with silent audio
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
    Open mic, use VAD to detect speech, and transcribe using Whisper.
    Returns transcribed text or None if nothing heard.
    """
    global _speaking
    _ensure_whisper()

    # Drain stale audio from previous rounds
    while not _audio_q.empty():
        _audio_q.get_nowait()

    print("[speech] Listening...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=4000,  # 0.25 second chunks
        dtype="float32",
        channels=1,
        callback=_mic_callback,
    ):
        start_time = time.time()
        recording = False
        silence_frames = 0
        audio_buffer = []
        pre_roll = []  # Rolling buffer: last 3 chunks (0.75s) to catch soft starts

        while True:
            # Timeout only applies when NOT actively recording
            if time.time() - start_time > timeout and not recording:
                return None

            try:
                chunk = _audio_q.get(timeout=1.0)
            except queue.Empty:
                continue

            # Skip audio while the assistant is speaking (prevents echo loops)
            if _speaking:
                continue

            # Calculate RMS energy
            rms = np.sqrt(np.mean(chunk**2))

            if rms > SILENCE_THRESHOLD:
                # Speech detected
                if not recording:
                    recording = True
                    # Prepend the pre-roll buffer so we capture the soft start
                    # of words like "Tom" where the "T" is quiet
                    audio_buffer.extend(pre_roll)
                audio_buffer.append(chunk)
                silence_frames = 0
            elif recording:
                # Still recording, but this chunk is silence
                audio_buffer.append(chunk)
                silence_frames += 1

                # 4000 samples @ 16000Hz = 0.25s per chunk
                chunks_for_silence = int(SILENCE_DURATION / 0.25)
                if silence_frames >= chunks_for_silence:
                    break
            else:
                # Not recording yet — maintain rolling pre-roll buffer
                pre_roll.append(chunk)
                if len(pre_roll) > 3:
                    pre_roll.pop(0)

        if not audio_buffer:
            return None

        # Check minimum audio length
        audio_data = np.concatenate(audio_buffer).flatten()
        duration = len(audio_data) / SAMPLE_RATE
        if duration < MIN_AUDIO_LENGTH:
            return None

        # ── Whisper transcription ──
        # initial_prompt biases Whisper to expect the wake word
        prompt = f"{cfg.wake_word}, "
        result = _whisper_model.transcribe(
            audio_data,
            fp16=False,
            initial_prompt=prompt,
            language="en",  # Primary language (Whisper still handles Hindi phonetics)
        )
        text = result.get("text", "").strip()

        # Filter out Whisper hallucinations (common with short/noisy audio)
        _hallucinations = {
            "thanks for watching", "thank you", "thank you.", "thanks for watching!",
            "you", "bye", "the end", "subtitle", "subtitles",
            ".", "", "...", "uh", "um",
        }
        if text.lower().strip(".,!? ") in _hallucinations:
            return None

        if text:
            print(f'[speech] Heard: "{text}"')
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
#  Text‑to‑Speech (macOS `say` + pyttsx3 fallback)
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
    """Speak text aloud. Sets _speaking flag to prevent echo pickup."""
    global _speaking
    print(f"[ai] {text}")

    _speaking = True  # Mute the mic listener during speech

    try:
        if platform.system() == "Darwin":
            try:
                # Use macOS native 'say' for natural Siri-quality voice
                subprocess.run(["say", text], check=False)
                return
            except Exception:
                pass  # fallback to pyttsx3

        _ensure_tts()
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    finally:
        # Small delay to let echo dissipate before re-enabling mic
        time.sleep(0.3)
        _speaking = False


def text_to_wav(text: str, output_path: str | None = None) -> str:
    """Render text to WAV file, return path. Used for voice notes."""
    _ensure_tts()
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "superai_voice.wav")

    _tts_engine.save_to_file(text, output_path)
    _tts_engine.runAndWait()
    return output_path
