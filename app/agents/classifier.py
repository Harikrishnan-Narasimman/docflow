"""
Agent 1: Classifier.

Given raw document text, decides what kind of document it is. This runs
first so the extraction agent knows which fields to look for -- an
invoice and a purchase order don't have identical structure, so guessing
the type wrong cascades into bad extraction.
"""

from ..llm_client import call_llm_json
from ..models import ClassificationResult

SYSTEM_PROMPT = """You are a document classification assistant. Given raw
text extracted from a business document, classify it into exactly one of:
"invoice", "receipt", "purchase_order", or "unknown" (use "unknown" if it
clearly doesn't fit the other three or the text is too garbled to tell).

Respond with ONLY a JSON object in this exact shape, no markdown, no
explanation outside the JSON:

{
  "document_type": "invoice" | "receipt" | "purchase_order" | "unknown",
  "confidence": <float between 0 and 1>,
  "reasoning": "<one short sentence explaining the classification>"
}
"""


def classify_document(raw_text: str) -> ClassificationResult:
    result = call_llm_json(SYSTEM_PROMPT, raw_text)
    return ClassificationResult(
        document_type=result.get("document_type", "unknown"),
        confidence=float(result.get("confidence", 0.0)),
        reasoning=result.get("reasoning", ""),
    )