"""
Agent 2: Extractor.

Given the raw text AND the document type from the classifier, pulls out
structured fields into the ExtractedDocument schema. Accepts optional
feedback from the validation agent so it can retry with corrections
instead of blindly repeating the same mistake.
"""

from typing import Optional
from ..llm_client import call_llm_json
from ..models import ExtractedDocument, LineItem, DocumentType

SYSTEM_PROMPT_TEMPLATE = """You are a document field extraction assistant.
The document below has already been classified as a "{document_type}".

Extract the following fields and respond with ONLY a JSON object in this
exact shape, no markdown, no explanation outside the JSON. Use null for
any field you cannot find -- never invent a value.

{{
  "vendor_name": "<string or null>",
  "document_date": "<YYYY-MM-DD string or null>",
  "document_number": "<string or null>",
  "line_items": [
    {{"description": "<string>", "quantity": <number>, "unit_price": <number>, "line_total": <number>}}
  ],
  "subtotal": <number or null>,
  "tax": <number or null>,
  "total": <number or null>
}}
"""

RETRY_ADDENDUM = """

Your previous extraction had the following issues that must be fixed:
{issues}

Re-extract the fields, correcting these specific problems.
"""


def extract_fields(
    raw_text: str,
    document_type: DocumentType,
    feedback: Optional[str] = None,
) -> ExtractedDocument:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(document_type=document_type)
    if feedback:
        system_prompt += RETRY_ADDENDUM.format(issues=feedback)

    result = call_llm_json(system_prompt, raw_text)

    def _safe_float(value, default=0.0):
        """Converts to float, treating None (explicit JSON null) the same as
        a missing key -- .get()'s default only covers missing keys, not
        keys present with a null value."""
        if value is None:
            return default
        return float(value)


    line_items = [
        LineItem(
            description=item.get("description") or "",
            quantity=_safe_float(item.get("quantity")),
            unit_price=_safe_float(item.get("unit_price")),
            line_total=_safe_float(item.get("line_total")),
        )
        for item in result.get("line_items", [])
    ]

    return ExtractedDocument(
        document_type=document_type,
        vendor_name=result.get("vendor_name"),
        document_date=result.get("document_date"),
        document_number=result.get("document_number"),
        line_items=line_items,
        subtotal=result.get("subtotal"),
        tax=result.get("tax"),
        total=result.get("total"),
    )