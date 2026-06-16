# Dependency manager for super_ai
# Automatically installs missing Python packages at runtime.
# This is invoked from super_ai/__init__.py during import.

import subprocess
import sys
from importlib import import_module

def ensure_package(package_name: str, import_name: str | None = None) -> None:
    """Attempt to import a package, and if it fails, install it via pip.

    Args:
        package_name: The name to pass to pip install.
        import_name: The module name to import (may differ from package name).
    """
    mod_name = import_name or package_name
    try:
        import_module(mod_name)
    except ImportError:
        print(f"[dependency_manager] Installing missing package: {package_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        # Verify import after installation
        try:
            import_module(mod_name)
        except ImportError as exc:
            print(f"[dependency_manager] Failed to import {mod_name} after installation: {exc}")
            raise

def ensure_all() -> None:
    """Ensure all required third‑party dependencies are present.
    Add any new packages to the list below.
    """
    packages = [
        ("qdrant-client", "qdrant_client"),
        ("fastembed", None),
        ("spacy", None),
        ("transformers", None),
        ("sentence-transformers", "sentence_transformers"),
        ("presidio-analyzer", "presidio_analyzer"),
        ("presidio-anonymizer", "presidio_anonymizer"),
        ("ollama", None),
        ("sounddevice", None),
        ("pyttsx3", None),
        ("opencv-python", "cv2"),
        ("thefuzz", None),
        ("numpy", None),
        ("psutil", None),
        ("pynput", None),
        ("openai-whisper", "whisper"),
        ("apscheduler", None),
    ]
    for pkg, imp in packages:
        ensure_package(pkg, imp)
