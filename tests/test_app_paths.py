from pathlib import Path

from services.ai_cache import AICache
from services.ocr_cache import OCRCache


def test_default_caches_are_absolute_and_separate(tmp_path, monkeypatch):
    cache_root = tmp_path / "ReceiptReader"
    monkeypatch.setenv("RECEIPTREADER_CACHE_DIR", str(cache_root))
    ocr_cache = OCRCache()
    ai_cache = AICache()

    assert ocr_cache.cache_dir.is_absolute()
    assert ai_cache.cache_dir.is_absolute()
    assert ocr_cache.cache_dir.name == "ocr"
    assert ai_cache.cache_dir.name == "ai"
    assert ocr_cache.cache_dir.parent == ai_cache.cache_dir.parent
    assert ocr_cache.cache_dir.parent.name == "ReceiptReader"
    assert isinstance(ocr_cache.cache_dir, Path)
