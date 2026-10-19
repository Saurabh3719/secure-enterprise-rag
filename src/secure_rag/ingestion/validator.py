"""Validate dataset integrity before chunking or indexing."""

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from secure_rag.ingestion.models import DatasetBundle


EXPECTED_DOCUMENT_COUNT = 1144
EXPECTED_TRAINING_QUESTION_COUNT = 45
EXPECTED_TEST_QUESTION_COUNT = 30


@dataclass(frozen=True)
class DatasetSummary:
    document_count: int
    training_question_count: int
    test_question_count: int
    duplicate_document_ids: int
    duplicate_question_ids: int
    empty_documents: int
    empty_questions: int
    broken_document_references: int


@dataclass(frozen=True)
class DatasetValidationReport:
    summary: DatasetSummary
    errors: Tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def raise_for_errors(self) -> None:
        if self.errors:
            raise ValueError("Dataset validation failed: " + "; ".join(self.errors))


def _duplicate_count(values: Iterable[str]) -> int:
    items = tuple(values)
    return len(items) - len(set(items))


def _blank(value: str) -> bool:
    return not value.strip()


def validate_dataset(dataset: DatasetBundle) -> DatasetValidationReport:
    """Check snapshot counts, required text, uniqueness, and QA references."""

    errors: List[str] = []
    documents = dataset.documents
    questions = dataset.training_questions + dataset.test_questions

    document_ids = tuple(document.document_id for document in documents)
    question_ids = tuple(question.question_id for question in questions)
    known_document_ids = set(document_ids)

    duplicate_document_ids = _duplicate_count(document_ids)
    duplicate_question_ids = _duplicate_count(question_ids)
    empty_documents = sum(
        _blank(document.document_id)
        or _blank(document.title)
        or _blank(document.content)
        for document in documents
    )
    empty_questions = sum(
        _blank(question.question_id)
        or _blank(question.question)
        or _blank(question.correct_answer)
        or _blank(question.correct_document_id)
        or _blank(question.ground_truth_context)
        for question in questions
    )
    broken_document_references = sum(
        question.correct_document_id not in known_document_ids for question in questions
    )
    split_overlap = {
        question.question_id for question in dataset.training_questions
    }.intersection(question.question_id for question in dataset.test_questions)

    expected_counts = (
        ("documents", len(documents), EXPECTED_DOCUMENT_COUNT),
        (
            "training questions",
            len(dataset.training_questions),
            EXPECTED_TRAINING_QUESTION_COUNT,
        ),
        ("test questions", len(dataset.test_questions), EXPECTED_TEST_QUESTION_COUNT),
    )
    for label, actual, expected in expected_counts:
        if actual != expected:
            errors.append(f"Expected {expected} {label}, found {actual}")

    if duplicate_document_ids:
        errors.append(f"Found {duplicate_document_ids} duplicate document IDs")
    if duplicate_question_ids:
        errors.append(f"Found {duplicate_question_ids} duplicate question IDs")
    if empty_documents:
        errors.append(f"Found {empty_documents} documents with empty required fields")
    if empty_questions:
        errors.append(f"Found {empty_questions} questions with empty required fields")
    if broken_document_references:
        errors.append(
            f"Found {broken_document_references} questions with missing source documents"
        )
    if split_overlap:
        errors.append(
            f"Found {len(split_overlap)} question IDs in both train and test splits"
        )

    summary = DatasetSummary(
        document_count=len(documents),
        training_question_count=len(dataset.training_questions),
        test_question_count=len(dataset.test_questions),
        duplicate_document_ids=duplicate_document_ids,
        duplicate_question_ids=duplicate_question_ids,
        empty_documents=empty_documents,
        empty_questions=empty_questions,
        broken_document_references=broken_document_references,
    )
    return DatasetValidationReport(summary=summary, errors=tuple(errors))

