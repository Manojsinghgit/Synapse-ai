"""
super_ai.video
──────────────
Optional video analysis:
  1. Extract key frames with OpenCV
  2. Object detection with YOLOv8‑nano (TFLite / ONNX, ~6 MB)
  3. Text extraction with Tesseract OCR
  4. Return a human‑readable summary
"""

import os
from pathlib import Path

import cv2
import numpy as np


def _extract_frames(video_path: str, every_n_seconds: int = 2) -> list[np.ndarray]:
    """
    Extract one frame every *every_n_seconds* from the video.
    Returns a list of BGR numpy arrays.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    interval = int(fps * every_n_seconds)
    frames: list[np.ndarray] = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % interval == 0:
            frames.append(frame)
        idx += 1

    cap.release()
    print(f"[video] Extracted {len(frames)} frames from {video_path}")
    return frames


def _detect_objects(frames: list[np.ndarray]) -> list[dict]:
    """
    Run YOLOv8‑nano on each frame.
    Returns a list of {"frame": i, "objects": [...]} dicts.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[video] ultralytics not installed — skipping object detection")
        return []

    model = YOLO("yolov8n.pt")  # auto‑downloads ~6 MB on first run
    results_list = []

    for i, frame in enumerate(frames):
        results = model.predict(source=frame, conf=0.30, verbose=False)
        objects = []
        for r in results:
            for box in r.boxes:
                objects.append({
                    "class": model.names[int(box.cls)],
                    "confidence": round(float(box.conf), 2),
                })
        if objects:
            results_list.append({"frame": i, "objects": objects})

    return results_list


def _extract_text(frames: list[np.ndarray]) -> list[str]:
    """
    Run Tesseract OCR on each frame to find on‑screen text.
    """
    try:
        import pytesseract
    except ImportError:
        print("[video] pytesseract not installed — skipping OCR")
        return []

    texts = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray).strip()
        if text:
            texts.append(text)
    return texts


def analyse_video(path: str) -> str:
    """
    Full pipeline: frames → YOLO detection → OCR → human‑readable summary.
    """
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return f"Video file not found: {path}"

    print(f"[video] Analysing {path} …")

    frames = _extract_frames(path)
    if not frames:
        return "Could not extract any frames from the video."

    # Object detection
    detections = _detect_objects(frames)

    # OCR
    texts = _extract_text(frames[:5])  # limit OCR to first 5 frames for speed

    # Build summary
    summary_parts = []

    if detections:
        # Unique objects across all frames
        all_objects = set()
        for d in detections:
            for obj in d["objects"]:
                all_objects.add(obj["class"])
        summary_parts.append(
            f"Objects detected: {', '.join(sorted(all_objects))}."
        )

    if texts:
        # Deduplicate and take first few unique texts
        unique_texts = list(dict.fromkeys(texts))[:3]
        summary_parts.append(
            f"Text found on screen: {' | '.join(unique_texts)}"
        )

    if not summary_parts:
        return "I analysed the video but didn't find any recognisable objects or text."

    summary = " ".join(summary_parts)
    print(f"[video] Summary: {summary}")
    return summary
