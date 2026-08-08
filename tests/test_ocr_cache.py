from pathlib import Path

from models.ocr_document import OCRDocument
from models.ocr_line import OCRLine
from services.ocr_cache import OCRCache


def test_ocr_cache_save_and_load(tmp_path):
    image_path = tmp_path / "receipt.jpg"
    image_path.write_bytes(b"fake-image-content")

    cache = OCRCache(
        cache_dir=tmp_path / "ocr_cache"
    )

    original_document = OCRDocument(
        [
            OCRLine(
                text="TEST MARKET",
                confidence=0.99
            ),
            OCRLine(
                text="TOPLAM",
                confidence=0.98
            ),
        ]
    )

    cache.save(
        image_path,
        original_document
    )

    loaded_document = cache.load(
        image_path
    )

    assert loaded_document is not None
    assert len(loaded_document.lines) == 2

    assert (
        loaded_document.lines[0].text
        == "TEST MARKET"
    )

    assert (
        loaded_document.lines[0].confidence
        == 0.99
    )


def test_ocr_cache_changes_when_file_content_changes(
    tmp_path
):
    image_path = tmp_path / "receipt.jpg"

    cache = OCRCache(
        cache_dir=tmp_path / "ocr_cache"
    )

    image_path.write_bytes(
        b"first-image"
    )

    first_document = OCRDocument(
        [
            OCRLine(
                text="FIRST",
                confidence=0.99
            )
        ]
    )

    cache.save(
        image_path,
        first_document
    )

    assert cache.load(
        image_path
    ) is not None

    # Aynı dosya adı ama farklı içerik.
    image_path.write_bytes(
        b"second-image"
    )

    # Hash değişeceği için eski cache
    # kullanılmamalı.
    assert cache.load(
        image_path
    ) is None