import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from secure_rag.ingestion import (
    DatasetBundle,
    DatasetLoadError,
    Document,
    QuestionAnswer,
    WatsonxDocsQALoader,
    validate_dataset,
)
from secure_rag.cli.inspect_dataset import print_questions


def document(document_id: str = "doc-1", content: str = "Useful text") -> Document:
    return Document(
        document_id=document_id,
        url="https://example.test/document",
        title="Example document",
        content=content,
        markdown_content=content,
        html_content=f"<p>{content}</p>",
    )


def question(question_id: str = "question-1", document_id: str = "doc-1") -> QuestionAnswer:
    return QuestionAnswer(
        question_id=question_id,
        question="What does the document say?",
        correct_answer="Useful text",
        correct_document_id=document_id,
        ground_truth_context="Useful text",
    )


class WatsonxDocsQALoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = WatsonxDocsQALoader().load()

    def test_loads_expected_snapshot_counts(self) -> None:
        self.assertEqual(len(self.dataset.documents), 1144)
        self.assertEqual(len(self.dataset.training_questions), 45)
        self.assertEqual(len(self.dataset.test_questions), 30)

    def test_maps_external_columns_to_internal_models(self) -> None:
        first = self.dataset.documents[0]

        self.assertTrue(first.document_id)
        self.assertTrue(first.title)
        self.assertTrue(first.content)
        self.assertTrue(first.url.startswith("https://"))

    def test_real_snapshot_passes_validation(self) -> None:
        report = validate_dataset(self.dataset)

        self.assertTrue(report.is_valid, report.errors)
        self.assertEqual(report.summary.duplicate_document_ids, 0)
        self.assertEqual(report.summary.duplicate_question_ids, 0)
        self.assertEqual(report.summary.empty_documents, 0)
        self.assertEqual(report.summary.empty_questions, 0)
        self.assertEqual(report.summary.broken_document_references, 0)

    def test_missing_dataset_file_has_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            loader = WatsonxDocsQALoader(Path(temporary_directory))

            with self.assertRaisesRegex(DatasetLoadError, "does not exist"):
                loader.load_documents()


class DatasetValidatorTests(unittest.TestCase):
    def test_detects_broken_document_reference(self) -> None:
        dataset = DatasetBundle(
            documents=(document(),) * 1144,
            training_questions=(question(document_id="missing"),) * 45,
            test_questions=(question(question_id="test-1"),) * 30,
        )

        report = validate_dataset(dataset)

        self.assertFalse(report.is_valid)
        self.assertEqual(report.summary.broken_document_references, 45)

    def test_detects_duplicate_ids_and_train_test_overlap(self) -> None:
        dataset = DatasetBundle(
            documents=tuple(document() for _ in range(1144)),
            training_questions=tuple(question() for _ in range(45)),
            test_questions=tuple(question() for _ in range(30)),
        )

        report = validate_dataset(dataset)

        self.assertFalse(report.is_valid)
        self.assertGreater(report.summary.duplicate_document_ids, 0)
        self.assertGreater(report.summary.duplicate_question_ids, 0)
        self.assertTrue(any("both train and test" in error for error in report.errors))

    def test_detects_empty_document_content(self) -> None:
        valid_documents = [document(f"doc-{index}") for index in range(1143)]
        valid_documents.append(document("empty-doc", content="   "))
        training = tuple(
            question(f"train-{index}", document_id="doc-0") for index in range(45)
        )
        testing = tuple(
            question(f"test-{index}", document_id="doc-0") for index in range(30)
        )
        dataset = DatasetBundle(
            documents=tuple(valid_documents),
            training_questions=training,
            test_questions=testing,
        )

        report = validate_dataset(dataset)

        self.assertFalse(report.is_valid)
        self.assertEqual(report.summary.empty_documents, 1)


class DatasetInspectorTests(unittest.TestCase):
    def test_test_labels_are_hidden_when_not_requested(self) -> None:
        output = io.StringIO()
        held_out = question(question_id="test-secret")

        with redirect_stdout(output):
            print_questions("test", (held_out,), sample_count=1, show_labels=False)

        rendered = output.getvalue()
        self.assertIn("[hidden test label]", rendered)
        self.assertNotIn(held_out.correct_answer, rendered)
        self.assertNotIn(held_out.correct_document_id, rendered)

    def test_training_labels_can_be_displayed(self) -> None:
        output = io.StringIO()
        training = question(question_id="train-visible")

        with redirect_stdout(output):
            print_questions("training", (training,), sample_count=1, show_labels=True)

        rendered = output.getvalue()
        self.assertIn(training.correct_answer, rendered)
        self.assertIn(training.correct_document_id, rendered)


if __name__ == "__main__":
    unittest.main()
