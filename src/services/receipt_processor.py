import time

from image.preprocessor import ImagePreprocessor
from ocr.reader import OCRReader
from parser.receipt_parser import parse_receipt
from ai.local_parser import LocalAIParser
from validator.receipt_validator import ReceiptValidator


class ReceiptProcessor:

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.ocr_reader = OCRReader()
        self.ai_parser = LocalAIParser()
        self.validator = ReceiptValidator()

    def process(self, image_path):
        total_start = time.perf_counter()

        # 1. Görseli OCR'a hazırla
        step_start = time.perf_counter()

        processed_image_path = (
            self.preprocessor.prepare(
                image_path
            )
        )

        preprocess_time = (
            time.perf_counter()
            - step_start
        )

        # 2. OCR
        step_start = time.perf_counter()

        ocr_document = self.ocr_reader.read(
            processed_image_path
        )

        ocr_time = (
            time.perf_counter()
            - step_start
        )

        # 3. Regex parser
        step_start = time.perf_counter()

        regex_receipt, parsed_fields = (
            parse_receipt(
                ocr_document
            )
        )

        regex_time = (
            time.perf_counter()
            - step_start
        )

        # 4. Local AI
        step_start = time.perf_counter()

        ai_result = self.ai_parser.parse(
            ocr_document.texts
        )

        ai_time = (
            time.perf_counter()
            - step_start
        )

        # 5. Validator
        step_start = time.perf_counter()

        validation_result = (
            self.validator.validate(
                regex_receipt,
                ai_result,
                parsed_fields,
                ocr_texts=ocr_document.texts
            )
        )

        validation_time = (
            time.perf_counter()
            - step_start
        )

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            "\n--- PERFORMANS ---"
        )

        print(
            f"Preprocess : "
            f"{preprocess_time:.2f} sn"
        )

        print(
            f"OCR        : "
            f"{ocr_time:.2f} sn"
        )

        print(
            f"Regex      : "
            f"{regex_time:.4f} sn"
        )

        print(
            f"AI         : "
            f"{ai_time:.2f} sn"
        )

        print(
            f"Validator  : "
            f"{validation_time:.4f} sn"
        )

        print(
            f"TOPLAM     : "
            f"{total_time:.2f} sn"
        )

        return validation_result