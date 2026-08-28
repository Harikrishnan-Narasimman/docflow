"""
Agent 3: Validator.

Deliberately NOT an LLM call. This agent checks the extracted data against
concrete business rules using plain code -- an LLM is the wrong tool for
"does 4.99 * 3 equal 14.97", and using deterministic checks here means
validation results are 100% reproducible, unlike another LLM call would be.

This is a design choice worth defending in an interview: not every step
in an "agentic" pipeline needs to be an LLM call. Use the LLM where
judgment/language understanding is required (classify, extract) and plain
code where a deterministic check will do (validate).
"""

from ..models import ExtractedDocument, ValidationResult, ValidationIssue

TOLERANCE = 0.02  # allow small floating-point/rounding differences


def validate_extraction(doc: ExtractedDocument) -> ValidationResult:
    issues = []

    if not doc.vendor_name:
        issues.append(ValidationIssue(field="vendor_name", problem="Missing vendor name."))

    if not doc.document_date:
        issues.append(ValidationIssue(field="document_date", problem="Missing document date."))

    if not doc.line_items:
        issues.append(ValidationIssue(field="line_items", problem="No line items were extracted."))

    for i, item in enumerate(doc.line_items):
        expected_total = round(item.quantity * item.unit_price, 2)
        if abs(expected_total - item.line_total) > TOLERANCE:
            issues.append(
                ValidationIssue(
                    field=f"line_items[{i}]",
                    problem=(
                        f"Line total {item.line_total} does not match "
                        f"quantity ({item.quantity}) x unit_price ({item.unit_price}) "
                        f"= {expected_total}."
                    ),
                )
            )

    if doc.line_items and doc.subtotal is not None:
        computed_subtotal = round(sum(item.line_total for item in doc.line_items), 2)
        if abs(computed_subtotal - doc.subtotal) > TOLERANCE:
            issues.append(
                ValidationIssue(
                    field="subtotal",
                    problem=(
                        f"Subtotal {doc.subtotal} does not match sum of line items "
                        f"({computed_subtotal})."
                    ),
                )
            )

    if doc.subtotal is not None and doc.total is not None:
        tax = doc.tax or 0.0
        expected_total = round(doc.subtotal + tax, 2)
        if abs(expected_total - doc.total) > TOLERANCE:
            issues.append(
                ValidationIssue(
                    field="total",
                    problem=(
                        f"Total {doc.total} does not match subtotal ({doc.subtotal}) "
                        f"+ tax ({tax}) = {expected_total}."
                    ),
                )
            )

    return ValidationResult(is_valid=(len(issues) == 0), issues=issues)


def format_issues_for_feedback(validation: ValidationResult) -> str:
    """Turns validation issues into a plain-text block the extractor agent
    can use as retry feedback."""
    return "\n".join(f"- {issue.field}: {issue.problem}" for issue in validation.issues)