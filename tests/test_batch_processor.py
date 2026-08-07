from pathlib import Path
from unittest.mock import Mock

import pytest

from services.batch_receipt_processor import BatchReceiptProcessor


def test_missing_folder_raises_error(tmp_path):
    processor = BatchReceiptProcessor()

    missing_folder = tmp_path / "yok"

    with pytest.raises(FileNotFoundError):
        processor.process_folder(missing_folder)


def test_file_path_instead_of_folder_raises_error(tmp_path):
    processor = BatchReceiptProcessor()

    file_path = tmp_path / "test.jpg"
    file_path.write_text("test")

    with pytest.raises(NotADirectoryError):
        processor.process_folder(file_path)


def test_unsupported_files_are_ignored(tmp_path):
    processor = BatchReceiptProcessor()

    unsupported_file = tmp_path / "notes.txt"
    unsupported_file.write_text("test")

    results = processor.process_folder(tmp_path)

    assert results == []


def test_supported_files_are_processed(tmp_path):
    processor = BatchReceiptProcessor()

    image1 = tmp_path / "fis1.jpg"
    image2 = tmp_path / "fis2.png"

    image1.write_bytes(b"fake")
    image2.write_bytes(b"fake")

    fake_result = Mock()
    fake_result.requires_review = False

    processor.processor.process = Mock(
        return_value=fake_result
    )

    results = processor.process_folder(tmp_path)

    assert len(results) == 2

    assert results[0]["success"] is True
    assert results[1]["success"] is True

    assert processor.processor.process.call_count == 2


def test_one_failed_receipt_does_not_stop_batch(tmp_path):
    processor = BatchReceiptProcessor()

    image1 = tmp_path / "fis1.jpg"
    image2 = tmp_path / "fis2.jpg"
    image3 = tmp_path / "fis3.jpg"

    image1.write_bytes(b"fake")
    image2.write_bytes(b"fake")
    image3.write_bytes(b"fake")

    fake_result = Mock()
    fake_result.requires_review = False

    processor.processor.process = Mock(
        side_effect=[
            fake_result,
            RuntimeError("Bozuk fiş"),
            fake_result
        ]
    )

    results = processor.process_folder(tmp_path)

    assert len(results) == 3

    assert results[0]["success"] is True

    assert results[1]["success"] is False
    assert results[1]["result"] is None
    assert "Bozuk fiş" in results[1]["error"]

    assert results[2]["success"] is True