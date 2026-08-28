# DocFlow

A multi-agent pipeline that processes invoices, receipts, and purchase
orders using three specialized agents that hand work off to each other,
rather than one model doing everything in a single call.

## Architecture

```
raw document text
       |
       v
[1. Classifier Agent]  --> decides: invoice / receipt / purchase_order / unknown
       |
       v
[2. Extractor Agent]   --> pulls structured fields (vendor, date, line items, total)
       |
       v
[3. Validator Agent]   --> checks extraction against business rules (NOT an LLM call)
       |
       +-- valid? --> done
       |
       +-- invalid? --> feedback sent back to Extractor Agent, retry (up to 3x)
```

**Why three agents instead of one big prompt:** each agent has a single,
narrow responsibility. The classifier only classifies. The extractor only
extracts, and can be re-run with specific feedback without re-doing
classification. The validator only checks rules. This mirrors how you'd
design a real pipeline with a human in each role, and it means a failure
in one stage doesn't require re-running the whole thing from scratch.

**Why the validator is plain code, not an LLM call:** checking whether
`quantity x unit_price == line_total` is a deterministic arithmetic
question. An LLM is the wrong tool for this -- it can occasionally get
math wrong, is slower and more expensive than a comparison operator, and
adds non-determinism to a check that should always give the same answer.
Use the LLM where judgment and language understanding are genuinely
needed (classification, extraction) and plain code where a deterministic
check will do (validation).

## Setup

```bash
cd DocFlow
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt

echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Then:

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "raw_text": "INVOICE\nVendor: Acme Office Supplies Inc.\nInvoice Number: INV-2024-0472\nDate: 2024-03-15\n\nDescription       Qty  Unit Price  Line Total\nCopy Paper (Case) 10   12.50       125.00\n\nSubtotal: 125.00\nTax: 10.00\nTotal: 135.00"
}
EOF
```

Response includes the classification, extracted fields, validation result,
number of attempts, and a log of what happened at each step.

## Run the evaluation

```bash
python -m app.evaluate
```

## Results

Tested against 22 documents: clean invoices/receipts/purchase orders,
plus edge cases covering non-USD currency, duplicate and negative-quantity
line items, non-US date formats, large item counts, zero tax, rounding,
severe OCR noise, stacked discounts, missing required fields, multi-page
formatting, ambiguous document types, and near-empty input.

| Outcome | Count |
|---|---|
| Correctly processed | 16/22 |
| Correctly declined (missing data, out-of-scope, degenerate input) | 3/22 |

**Correct-outcome rate: 19/22 (86%)** when counting honest refusals as
correct behavior rather than failures. The pipeline declined to
hallucinate a missing vendor name, correctly rejected an unrelated
internal memo, and correctly refused to fabricate data for a near-empty
document rather than guessing.

## Project structure

```
app/
  agents/
    classifier.py   # Agent 1: determines document type
    extractor.py     # Agent 2: pulls structured fields, accepts retry feedback
    validator.py      # Agent 3: rule-based checks, no LLM call
  llm_client.py        # shared Claude API wrapper used by classifier + extractor
  models.py           # shared dataclasses passed between agents
  orchestrator.py      # coordinates the handoff and retry loop between agents
  main.py              # FastAPI endpoint
  evaluate.py          # test harness against sample documents
sample_docs/           # sample invoice/receipt/PO text files, including edge cases
```

## Extending this project

- **Real OCR input**: swap the raw text input for actual OCR output
  (e.g., via `pytesseract` or a cloud OCR API) so the pipeline handles
  scanned documents, not just clean text.
- **MCP-based ingestion**: instead of accepting raw text via the API,
  pull documents from an external source (email inbox, cloud storage
  folder) using the Model Context Protocol, so the pipeline can process
  a live stream of incoming documents rather than manually submitted text.