import hashlib
import json
from pathlib import Path

from services.app_paths import user_cache_dir


class AICache:

    def __init__(
        self,
        cache_dir=None
    ):
        self.cache_dir = (
            Path(cache_dir)
            if cache_dir is not None
            else user_cache_dir() / "ai"
        )

        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def _create_key(
        self,
        model_name,
        prompt_version,
        texts
    ):
        content = "\n".join(
            [
                model_name,
                prompt_version,
                *texts
            ]
        )

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    def _get_cache_path(
        self,
        model_name,
        prompt_version,
        texts
    ):
        key = self._create_key(
            model_name,
            prompt_version,
            texts
        )

        return (
            self.cache_dir
            / f"{key}.json"
        )

    def load(
        self,
        model_name,
        prompt_version,
        texts
    ):
        cache_path = self._get_cache_path(
            model_name,
            prompt_version,
            texts
        )

        if not cache_path.exists():
            return None

        try:
            with open(
                cache_path,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):
            return None

    def save(
        self,
        model_name,
        prompt_version,
        texts,
        data
    ):
        cache_path = self._get_cache_path(
            model_name,
            prompt_version,
            texts
        )

        with open(
            cache_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )
