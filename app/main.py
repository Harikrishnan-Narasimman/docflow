"""
FastAPI service exposing DocFlow, a multi-agent document processing pipeline.

Run with:
    uvicorn app.main:app --reload

Then:
    curl -X POST http://localhost:8000/process \
      -H "Content-Type: application/json" \
      -d '{"raw_text": "INVOICE\nVendor: Acme...\n..."}'
"""

from fastapi import FastAPI
from pydantic import BaseModel

from .orchestrator import process_document, pipeline_result_to_dict

app = FastAPI(title="DocFlow — Multi-Agent Document Processing Pipeline")


class DocumentRequest(BaseModel):
    raw_text: str


@app.post("/process")
def process(request: DocumentRequest):
    result = process_document(request.raw_text)
    return pipeline_result_to_dict(result)


@app.get("/health")
def health():
    return {"status": "ok"}