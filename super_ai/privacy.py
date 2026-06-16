from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import logging

# Suppress annoying "language is not supported by registry" warnings
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)

# Initialize Presidio globally (lightweight, runs locally)
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def sanitize_text(text: str) -> str:
    """Detect and redact PII in *text* using Microsoft Presidio.
    Returns the sanitized string.
    """
    try:
        results = analyzer.analyze(text, language="en")
        if not results:
            return text
        # Create a dict of entities to anonymize
        anonymize_ops = {r.entity_type: {"type": "replace", "new_value": "[REDACTED]"} for r in results}
        sanitized = anonymizer.anonymize(text=text, analyzer_results=results, operators=anonymize_ops)
        return sanitized.text
    except Exception as e:
        logging.warning(f"Presidio sanitization failed: {e}")
        return text
