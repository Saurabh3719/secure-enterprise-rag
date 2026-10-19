"""Load the committed watsonxDocsQA Parquet files into application models."""

import os
from pathlib import Path
from typing import Iterable, Mapping, Optional, Tuple

import pyarrow as pa
import pyarrow.parquet as pq

from secure_rag.ingestion.models import DatasetBundle, Document, QuestionAnswer


DATASET_DIRECTORY_ENVIRONMENT_VARIABLE = "SECURE_RAG_DATASET_DIR"

DOCUMENT_COLUMNS = frozenset(
    {"doc_id", "url", "title", "document", "md_document", "html_document"}
)
QUESTION_COLUMNS = frozenset(
    {
        "question_id",
        "question",
        "correct_answer",
        "correct_answer_document_ids",
        "ground_truths_contexts",
    }
)


class DatasetLoadError(RuntimeError):
    """Raised when a dataset file is missing, unreadable, or has the wrong schema."""


class WatsonxDocsQALoader:
    """Translate the external IBM schema into stable internal Python models."""

    def __init__(self, dataset_directory: Optional[Path] = None) -> None:
        self.dataset_directory = (
            Path(dataset_directory)
            if dataset_directory is not None
            else self._default_dataset_directory()
        )

    @staticmethod
    def _default_dataset_directory() -> Path:
        configured = os.environ.get(DATASET_DIRECTORY_ENVIRONMENT_VARIABLE)
        if configured:
            return Path(configured).expanduser()

        working_tree_data = Path.cwd() / "data" / "watsonx_docs_qa"
        if working_tree_data.is_dir():
            return working_tree_data

        source_tree_data = (
            Path(__file__).resolve().parents[3] / "data" / "watsonx_docs_qa"
        )
        if source_tree_data.is_dir():
            return source_tree_data

        return working_tree_data

    @property
    def corpus_path(self) -> Path:
        return self.dataset_directory / "corpus" / "train-00000-of-00001.parquet"

    @property
    def training_questions_path(self) -> Path:
        return (
            self.dataset_directory
            / "question_answers"
            / "train-00000-of-00001.parquet"
        )

    @property
    def test_questions_path(self) -> Path:
        return (
            self.dataset_directory
            / "question_answers"
            / "test-00000-of-00001.parquet"
        )

    def _read_rows(
        self,
        path: Path,
        expected_columns: Iterable[str],
    ) -> Tuple[Mapping[str, object], ...]:
        if not path.is_file():
            raise DatasetLoadError(f"Dataset file does not exist: {path}")

        try:
            table = pq.read_table(path)
        except (OSError, pa.ArrowException) as error:
            raise DatasetLoadError(f"Could not read Parquet file: {path}") from error

        expected = frozenset(expected_columns)
        actual = frozenset(table.column_names)
        if actual != expected:
            missing = sorted(expected - actual)
            unexpected = sorted(actual - expected)
            raise DatasetLoadError(
                f"Unexpected schema in {path}; missing={missing}, unexpected={unexpected}"
            )

        return tuple(table.to_pylist())

    @staticmethod
    def _required_text(row: Mapping[str, object], column: str) -> str:
        value = row.get(column)
        if not isinstance(value, str):
            raise DatasetLoadError(f"Column {column!r} must contain text")
        return value

    def load_documents(self) -> Tuple[Document, ...]:
        rows = self._read_rows(self.corpus_path, DOCUMENT_COLUMNS)
        return tuple(
            Document(
                document_id=self._required_text(row, "doc_id"),
                url=self._required_text(row, "url"),
                title=self._required_text(row, "title"),
                content=self._required_text(row, "document"),
                markdown_content=self._required_text(row, "md_document"),
                html_content=self._required_text(row, "html_document"),
            )
            for row in rows
        )

    def _load_questions(self, path: Path) -> Tuple[QuestionAnswer, ...]:
        rows = self._read_rows(path, QUESTION_COLUMNS)
        return tuple(
            QuestionAnswer(
                question_id=self._required_text(row, "question_id"),
                question=self._required_text(row, "question"),
                correct_answer=self._required_text(row, "correct_answer"),
                correct_document_id=self._required_text(
                    row, "correct_answer_document_ids"
                ),
                ground_truth_context=self._required_text(
                    row, "ground_truths_contexts"
                ),
            )
            for row in rows
        )

    def load_training_questions(self) -> Tuple[QuestionAnswer, ...]:
        return self._load_questions(self.training_questions_path)

    def load_test_questions(self) -> Tuple[QuestionAnswer, ...]:
        return self._load_questions(self.test_questions_path)

    def load(self) -> DatasetBundle:
        """Load the complete corpus while preserving the benchmark split."""

        return DatasetBundle(
            documents=self.load_documents(),
            training_questions=self.load_training_questions(),
            test_questions=self.load_test_questions(),
        )

