import time
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import whisper
import warnings
warnings.filterwarnings("ignore")

print("Loading model...")
t0 = time.time()
model = whisper.load_model("base")
print(f"Model loaded in {time.time()-t0:.2f}s")

# Transcribe a dummy silent audio to force initialization
import numpy as np
dummy_audio = np.zeros(16000 * 2, dtype=np.float32)
print("Warming up...")
t0 = time.time()
model.transcribe(dummy_audio, fp16=False)
print(f"Warmup done in {time.time()-t0:.2f}s")
