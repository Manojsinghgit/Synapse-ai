import spacy
from transformers import pipeline
import logging

# Load a small spaCy model for multilingual NER (fallback to en_core_web_sm if not available)
try:
    nlp = spacy.load("xx_ent_wiki_sm")
except OSError:
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        import spacy.cli
        logging.warning("Downloading spaCy model 'en_core_web_sm'...")
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")

# Emotion detection using a HuggingFace text classification pipeline (fallback to "distilbert-base-uncased-finetuned-sst-2-english")
try:
    emotion_classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")
except Exception:
    emotion_classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

def detect_intent(text: str) -> str:
    """Very naive intent detection: classify text as 'command', 'question', or 'statement'."""
    lowered = text.lower()
    if any(word in lowered for word in ["play", "open", "search", "show", "send", "call", "launch"]):
        return "command"
    if lowered.endswith("?") or lowered.startswith("what") or lowered.startswith("how") or lowered.startswith("is"):
        return "question"
    return "statement"

def detect_emotion(text: str) -> str:
    """Return the top emotion label from the classifier, lower‑cased."""
    try:
        result = emotion_classifier(text, top_k=1)[0]
        return result["label"].lower()
    except Exception as e:
        logging.warning(f"Emotion detection failed: {e}")
        return "neutral"
