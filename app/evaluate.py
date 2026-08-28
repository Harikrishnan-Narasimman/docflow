"""
Runs the pipeline against sample documents and reports results,
including whether the retry loop successfully catches and corrects
an intentional math error.

Run with:
    python -m app.evaluate
"""

import os
import json
from .orchestrator import process_document, pipeline_result_to_dict

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_docs")

TEST_FILES = [
    # Original set
    "clean_invoice.txt",
    "clean_receipt.txt",
    "math_error_invoice.txt",
    "purchase_order.txt",
    "discount_invoice.txt",
    "missing_vendor_invoice.txt",
    "messy_ocr_receipt.txt",
    "unrelated_memo.txt",

    # Expanded edge-case set
    "edge_currency_eur.txt",
    "edge_duplicate_lineitem.txt",
    "edge_negative_quantity.txt",
    "edge_date_format_uk.txt",
    "edge_many_line_items.txt",
    "edge_zero_tax.txt",
    "edge_rounding.txt",
    "edge_severe_ocr_noise.txt",
    "edge_multiple_discounts.txt",
    "edge_missing_total.txt",
    "edge_multipage_style.txt",
    "edge_missing_po_number.txt",
    "edge_ambiguous_type.txt",
    "edge_near_empty.txt",
]


def run_eval():
    results = []

    for filename in TEST_FILES:
        path = os.path.join(SAMPLE_DIR, filename)
        with open(path, "r") as f:
            raw_text = f.read()

        print("=" * 60)
        print(f"FILE: {filename}")
        print("=" * 60)

        result = process_document(raw_text)

        for line in result.log:
            print(f"  {line}")

        print(f"\n  Final success: {result.success} (after {result.attempts} attempt(s))")
        if result.extracted:
            print(f"  Extracted total: {result.extracted.total}")
        print()

        results.append(
            {
                "file": filename,
                "success": result.success,
                "attempts": result.attempts,
                "document_type": result.classification.document_type if result.classification else None,
            }
        )

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successes = sum(1 for r in results if r["success"])
    print(f"{successes}/{len(results)} documents processed successfully.")
    for r in results:
        status = "OK" if r["success"] else "FAILED"
        print(f"  [{status}] {r['file']} -> type={r['document_type']}, attempts={r['attempts']}")

    return results


if __name__ == "__main__":
    run_eval()
