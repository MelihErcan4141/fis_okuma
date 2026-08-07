from pathlib import Path

from services.receipt_processor import ReceiptProcessor


class BatchReceiptProcessor:

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".heic",
        ".heif",
    }

    def __init__(self):
        self.processor = ReceiptProcessor()

    def process_folder(self, folder_path):
        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(
                f"Klasör bulunamadı: {folder}"
            )

        if not folder.is_dir():
            raise NotADirectoryError(
                f"Bu yol bir klasör değil: {folder}"
            )

        results = []

        for file_path in sorted(folder.iterdir()):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            try:
                validation_result = self.processor.process(
                    str(file_path)
                )

                results.append(
                    {
                        "file": str(file_path),
                        "success": True,
                        "result": validation_result,
                        "error": None
                    }
                )

            except Exception as error:
                results.append(
                    {
                        "file": str(file_path),
                        "success": False,
                        "result": None,
                        "error": str(error)
                    }
                )

        return results