from services.ai_cache import AICache


def test_ai_cache_save_and_load(
    tmp_path
):
    cache = AICache(
        cache_dir=tmp_path / "ai_cache"
    )

    texts = [
        "BIM BIRLESIK MAGAZALAR A.S.",
        "FIS NO: 0127",
        "TOPLAM",
        "432,25",
    ]

    data = {
        "company": (
            "BIM BIRLESIK MAGAZALAR A.S."
        ),
        "receipt_no": "0127",
        "date": None,
        "time": None,
        "kdv": None,
        "total": 432.25,
    }

    cache.save(
        model_name="qwen3:4b",
        prompt_version="v1",
        texts=texts,
        data=data
    )

    loaded = cache.load(
        model_name="qwen3:4b",
        prompt_version="v1",
        texts=texts
    )

    assert loaded == data


def test_ai_cache_changes_with_prompt_version(
    tmp_path
):
    cache = AICache(
        cache_dir=tmp_path / "ai_cache"
    )

    texts = [
        "TEST MARKET",
        "TOPLAM 100,00",
    ]

    cache.save(
        model_name="qwen3:4b",
        prompt_version="v1",
        texts=texts,
        data={
            "company": "TEST MARKET"
        }
    )

    loaded = cache.load(
        model_name="qwen3:4b",
        prompt_version="v2",
        texts=texts
    )

    assert loaded is None