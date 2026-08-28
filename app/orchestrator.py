"""
Orchestrator: coordinates the handoff between the three agents.

Flow:
  1. Classifier agent determines document type.
  2. Extractor agent pulls structured fields, given the type.
  3. Validator agent (plain code, not an LLM) checks the extraction
     against business rules.
  4. If validation fails, the issues are handed back to the extractor
     as feedback and it retries (up to MAX_ATTEMPTS times).

This is the "multi-agent" part: each agent has a narrow, well-defined
job, and the orchestrator manages the handoff and retry logic --
distinct from the text-to-SQL project, where a single agent retried its
own output. Here, one agent's output becomes another agent's input, and
a third agent's judgment sends work back for another pass.
"""

from dataclasses import asdict
from .agents.classifier import classify_document
from .agents.extractor import extract_fields
from .agents.validator import validate_extraction, format_issues_for_feedback
from .models import PipelineResult

MAX_ATTEMPTS = 3


def process_document(raw_text: str) -> PipelineResult:
    result = PipelineResult(raw_text=raw_text)

    # Step 1: Classify
    classification = classify_document(raw_text)
    result.classification = classification
    result.log.append(
        f"Classified as '{classification.document_type}' "
        f"(confidence {classification.confidence:.2f}): {classification.reasoning}"
    )

    if classification.document_type == "unknown":
        result.log.append("Classifier could not confidently identify document type. Stopping.")
        result.success = False
        return result

    # Step 2 & 3: Extract, then validate, with retry on failure
    feedback = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result.attempts = attempt

        extracted = extract_fields(raw_text, classification.document_type, feedback=feedback)
        result.extracted = extracted

        validation = validate_extraction(extracted)
        result.validation = validation

        if validation.is_valid:
            result.log.append(f"Attempt {attempt}: validation passed.")
            result.success = True
            return result

        issues_text = format_issues_for_feedback(validation)
        result.log.append(f"Attempt {attempt}: validation failed.\n{issues_text}")
        feedback = issues_text

    result.success = False
    result.log.append(f"Gave up after {MAX_ATTEMPTS} attempts. Final issues remain unresolved.")
    return result


def pipeline_result_to_dict(result: PipelineResult) -> dict:
    """Converts the dataclass tree into a plain dict for JSON responses."""
    return {
        "success": result.success,
        "attempts": result.attempts,
        "classification": asdict(result.classification) if result.classification else None,
        "extracted": asdict(result.extracted) if result.extracted else None,
        "validation": asdict(result.validation) if result.validation else None,
        "log": result.log,
    }