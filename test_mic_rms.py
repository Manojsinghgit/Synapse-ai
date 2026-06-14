import numpy as np
import sounddevice as sd
import time

def callback(indata, frames, time, status):
    rms = np.sqrt(np.mean(indata**2))
    print(f"RMS: {rms:.4f}")

with sd.InputStream(samplerate=16000, channels=1, dtype='float32', callback=callback):
    time.sleep(2)
