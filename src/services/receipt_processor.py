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
        # 1. Görseli OCR'a hazırla
        processed_image_path = self.preprocessor.prepare(image_path)

        # 2. OCR
        ocr_document = self.ocr_reader.read(
            processed_image_path
        )

        # 3. Regex parser
        regex_receipt, parsed_fields = parse_receipt(
            ocr_document
        )

        # 4. Local AI
        ai_result = self.ai_parser.parse(
            ocr_document.texts
        )

        # 5. Validator
        validation_result = self.validator.validate(
            regex_receipt,
            ai_result,
            parsed_fields,
            ocr_texts=ocr_document.texts
        )

        return validation_result