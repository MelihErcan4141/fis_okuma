import hashlib
import json
from pathlib import Path

from models.ocr_document import OCRDocument
from models.ocr_line import OCRLine


class OCRCache:

    def __init__(self, cache_dir="cache/ocr"):
        self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def _calculate_hash(self, image_path):
        hasher = hashlib.sha256()

        with open(image_path, "rb") as file:
            while True:
                chunk = file.read(1024 * 1024)

                if not chunk:
                    break

                hasher.update(chunk)

        return hasher.hexdigest()

    def _get_cache_path(self, image_path):
        image_hash = self._calculate_hash(
            image_path
        )

        return (
            self.cache_dir
            / f"{image_hash}.json"
        )

    def load(self, image_path):
        cache_path = self._get_cache_path(
            image_path
        )

        if not cache_path.exists():
            return None

        try:
            with open(
                cache_path,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):
            return None

        lines = []

        for item in data.get("lines", []):
            lines.append(
                OCRLine(
                    text=item["text"],
                    confidence=float(
                        item["confidence"]
                    )
                )
            )

        return OCRDocument(lines)

    def save(
        self,
        image_path,
        document
    ):
        cache_path = self._get_cache_path(
            image_path
        )

        data = {
            "lines": [
                {
                    "text": line.text,
                    "confidence": (
                        line.confidence
                    )
                }
                for line in document.lines
            ]
        }

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