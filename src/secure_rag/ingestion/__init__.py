"""Dataset loading and validation for the RAG ingestion pipeline."""

from secure_rag.ingestion.loader import DatasetLoadError, WatsonxDocsQALoader
from secure_rag.ingestion.models import DatasetBundle, Document, QuestionAnswer
from secure_rag.ingestion.validator import (
    DatasetSummary,
    DatasetValidationReport,
    validate_dataset,
)

__all__ = [
    "DatasetBundle",
    "DatasetLoadError",
    "DatasetSummary",
    "DatasetValidationReport",
    "Document",
    "QuestionAnswer",
    "WatsonxDocsQALoader",
    "validate_dataset",
]

