from dataclasses import dataclass, field
from typing import List, Optional, Literal

DocumentType = Literal["invoice", "receipt", "purchase_order", "unknown"]

@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float
    reasoning: str

@dataclass
class LineItem:
    description: str
    quantity: float
    unit_price: float
    line_total: float

@dataclass
class ExtractedDocument:
    document_type: DocumentType
    vendor_name: Optional[str] = None
    document_date: Optional[str] = None
    document_number: Optional[str] = None
    line_items: List[LineItem] = field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None

@dataclass
class ValidationIssue:
    field: str
    problem: str

@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

@dataclass
class PipelineResult:
    raw_text: str
    classification: Optional[ClassificationResult] = None
    extracted: Optional[ExtractedDocument] = None
    validation: Optional[ValidationResult] = None
    attempts: int = 0
    success: bool = False
    log: List[str] = field(default_factory=list)