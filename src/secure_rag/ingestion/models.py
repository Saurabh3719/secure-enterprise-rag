"""Application models that isolate the rest of the system from Parquet rows."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Document:
    """One source document before chunking or RBAC enrichment."""

    document_id: str
    url: str
    title: str
    content: str
    markdown_content: str
    html_content: str


@dataclass(frozen=True)
class QuestionAnswer:
    """One benchmark question with its expected answer and source document."""

    question_id: str
    question: str
    correct_answer: str
    correct_document_id: str
    ground_truth_context: str


@dataclass(frozen=True)
class DatasetBundle:
    """The complete dataset with development and final evaluation kept separate."""

    documents: Tuple[Document, ...]
    training_questions: Tuple[QuestionAnswer, ...]
    test_questions: Tuple[QuestionAnswer, ...]

