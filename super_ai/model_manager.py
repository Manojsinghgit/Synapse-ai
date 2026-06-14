"""
super_ai.model_manager
──────────────────────
Auto-installs & manages everything behind the scenes.
User ko kuch nahi karna — sab apne aap hota hai.

1. Ollama install (if missing)
1. Ollama install (if missing)
2. Ollama serve (background process)
3. Model pull (llama3.2)
4. Whisper model warmup
"""

import os
import sys
import time
import shutil
import signal
import atexit
import zipfile
import platform
import subprocess
import urllib.request
from pathlib import Path

from .config import cfg

# Track background ollama process so we can kill it on exit
_ollama_process = None


def _progress_hook(block_num, block_size, total_size):
    """Simple download progress bar."""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, downloaded * 100 // total_size)
        mb_done = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        bar = "█" * (percent // 2) + "░" * (50 - percent // 2)
        print(f"\r   [{bar}] {percent}% ({mb_done:.0f}/{mb_total:.0f} MB)", end="", flush=True)


# ═══════════════════════════════════════════════════
#  1. Whisper Speech Model
# ═══════════════════════════════════════════════════

def ensure_whisper_model():
    """Load and warm up the Whisper model."""
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
        
    print(f"\n🎤 Loading Speech Engine (Whisper)...")
    import whisper
    # Suppress warnings
    import warnings
    warnings.filterwarnings("ignore", module="whisper")
    
    # This will download if not present, and load into memory
    model = whisper.load_model(cfg.whisper_model)
    
    # Warmup with dummy audio
    import numpy as np
    dummy_audio = np.zeros(16000 * 2, dtype=np.float32)
    model.transcribe(dummy_audio, fp16=False)
    print("   ✓ Speech Engine ready")




# ═══════════════════════════════════════════════════
#  2. Ollama — Install
# ═══════════════════════════════════════════════════

def _is_ollama_installed() -> bool:
    """Check if ollama binary exists."""
    return shutil.which("ollama") is not None


def _install_ollama():
    """Auto-install Ollama based on OS. User sees progress, no input needed."""
    system = platform.system()

    if system == "Darwin":
        # macOS — try brew first, then curl installer
        print("\n🧠 Installing AI engine (one-time)...")
        if shutil.which("brew"):
            print("   Using Homebrew...")
            result = subprocess.run(
                ["brew", "install", "ollama"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("   ✓ AI engine installed via Homebrew")
                return
            # brew failed — try curl
        # curl install
        print("   Downloading installer...")
        result = subprocess.run(
            ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("   ✓ AI engine installed")
        else:
            raise RuntimeError(
                f"Could not install Ollama automatically.\n"
                f"Please install manually: https://ollama.com/download\n"
                f"Error: {result.stderr}"
            )

    elif system == "Linux":
        print("\n🧠 Installing AI engine (one-time)...")
        result = subprocess.run(
            ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("   ✓ AI engine installed")
        else:
            raise RuntimeError(
                f"Could not install Ollama.\n"
                f"Please install manually: https://ollama.com/download\n"
                f"Error: {result.stderr}"
            )

    elif system == "Windows":
        raise RuntimeError(
            "Windows auto-install not supported yet.\n"
            "Please download from: https://ollama.com/download/windows"
        )
    else:
        raise RuntimeError(f"Unsupported OS: {system}")


def ensure_ollama_installed():
    """Install Ollama if not present."""
    if _is_ollama_installed():
        return
    _install_ollama()
    # Verify
    if not _is_ollama_installed():
        raise RuntimeError("Ollama installation failed. Please install from https://ollama.com")


# ═══════════════════════════════════════════════════
#  3. Ollama — Serve (background)
# ═══════════════════════════════════════════════════

def _is_ollama_running() -> bool:
    """Check if Ollama server is already running."""
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False


def _cleanup_ollama():
    """Kill the background ollama process on exit."""
    global _ollama_process
    if _ollama_process and _ollama_process.poll() is None:
        _ollama_process.terminate()
        try:
            _ollama_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _ollama_process.kill()
        print("[cleanup] Ollama server stopped")


def ensure_ollama_serving():
    """Start Ollama server in background if not already running."""
    global _ollama_process

    if _is_ollama_running():
        return

    print("   Starting AI server in background...")
    _ollama_process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid if os.name != "nt" else None,
    )

    # Register cleanup so server stops when our app exits
    atexit.register(_cleanup_ollama)

    # Wait for server to be ready (max 30 seconds)
    for i in range(60):
        time.sleep(0.5)
        if _is_ollama_running():
            print("   ✓ AI server running")
            return

    raise RuntimeError("Ollama server failed to start within 30 seconds.")


# ═══════════════════════════════════════════════════
#  4. Ollama — Pull Model
# ═══════════════════════════════════════════════════

def _is_model_pulled() -> bool:
    """Check if the exact model is already downloaded."""
    try:
        result = subprocess.run(
            ["ollama", "show", cfg.ollama_model],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def ensure_model_pulled():
    """Pull the LLM model if not already present."""
    if _is_model_pulled():
        return

    print(f"\n🧠 Downloading AI Brain Engine (one-time, ~2.0 GB). Please wait...")
    import ollama
    
    try:
        # Stream the download progress
        for progress in ollama.pull(cfg.ollama_model, stream=True):
            if "total" in progress and "completed" in progress:
                total = progress["total"]
                completed = progress["completed"]
                if total > 0:
                    percent = int((completed / total) * 100)
                    mb_done = completed / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    bar = "█" * (percent // 2) + "░" * (50 - percent // 2)
                    print(f"\r   [{bar}] {percent}% ({mb_done:.0f}/{mb_total:.0f} MB)", end="", flush=True)
            elif "status" in progress:
                # Print status updates cleanly without overriding the bar if it exists
                status = progress["status"]
                if "pulling" not in status: # hide the raw pulling layer hashes
                    print(f"\r   {status.capitalize()}{' ' * 40}", end="", flush=True)
                    
        print("\n   ✓ AI brain ready")
    except Exception as exc:
        raise RuntimeError(f"Failed to download AI engine: {exc}")


# ═══════════════════════════════════════════════════
#  Master function — does everything
# ═══════════════════════════════════════════════════

def ensure_all_models():
    """
    One call to set up everything:
    1. Whisper model warmup
    2. Install Ollama (if missing)
    3. Start Ollama server (background)
    4. Pull LLM model (if missing)

    User sees progress bars. Subsequent runs skip all downloads.
    """
    ensure_whisper_model()
    ensure_ollama_installed()
    ensure_ollama_serving()
    ensure_model_pulled()
    print()
