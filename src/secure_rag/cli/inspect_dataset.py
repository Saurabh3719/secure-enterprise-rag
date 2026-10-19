"""Display a readable summary and representative watsonxDocsQA records."""

import argparse
import re
from pathlib import Path
from typing import Iterable

from secure_rag.ingestion import QuestionAnswer, WatsonxDocsQALoader, validate_dataset
from secure_rag.ingestion.models import Document


def preview(value: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def print_documents(documents: Iterable[Document], sample_count: int) -> None:
    print("\nSample documents")
    print("----------------")
    for index, document in enumerate(documents):
        if index >= sample_count:
            break
        print(f"[{index + 1}] {document.title}")
        print(f"    ID: {document.document_id}")
        print(f"    URL: {document.url}")
        print(f"    Text: {preview(document.content)}")


def print_questions(
    label: str,
    questions: Iterable[QuestionAnswer],
    sample_count: int,
    show_labels: bool,
) -> None:
    print(f"\nSample {label} questions")
    print("-" * (17 + len(label)))
    for index, question in enumerate(questions):
        if index >= sample_count:
            break
        print(f"[{index + 1}] {question.question}")
        if show_labels:
            print(f"    Expected document: {question.correct_document_id}")
            print(f"    Answer: {preview(question.correct_answer)}")
        else:
            print("    Expected document: [hidden test label]")
            print("    Answer: [hidden test label]")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples",
        type=int,
        default=3,
        help="number of records to show from each section (default: 3)",
    )
    parser.add_argument(
        "--dataset-directory",
        type=Path,
        help="watsonxDocsQA directory (default: ./data/watsonx_docs_qa)",
    )
    parser.add_argument(
        "--show-test-labels",
        action="store_true",
        help="display held-out test answers and source IDs (normally hidden)",
    )
    arguments = parser.parse_args()
    if arguments.samples < 0:
        parser.error("--samples must be zero or greater")

    dataset = WatsonxDocsQALoader(arguments.dataset_directory).load()
    report = validate_dataset(dataset)
    summary = report.summary

    print("IBM watsonxDocsQA")
    print("=================")
    print(f"Documents:          {summary.document_count}")
    print(f"Training questions: {summary.training_question_count}")
    print(f"Test questions:     {summary.test_question_count}")
    print(f"Duplicate doc IDs:  {summary.duplicate_document_ids}")
    print(f"Duplicate QA IDs:   {summary.duplicate_question_ids}")
    print(f"Empty documents:    {summary.empty_documents}")
    print(f"Empty questions:    {summary.empty_questions}")
    print(f"Broken references:  {summary.broken_document_references}")
    print(f"Validation:         {'PASS' if report.is_valid else 'FAIL'}")

    if report.errors:
        print("\nValidation errors")
        for error in report.errors:
            print(f"- {error}")
        return 1

    if arguments.samples:
        print_documents(dataset.documents, arguments.samples)
        print_questions(
            "training", dataset.training_questions, arguments.samples, show_labels=True
        )
        print_questions(
            "test",
            dataset.test_questions,
            arguments.samples,
            show_labels=arguments.show_test_labels,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

