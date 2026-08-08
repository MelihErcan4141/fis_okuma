import time

from image.preprocessor import ImagePreprocessor
from ocr.reader import OCRReader
from parser.receipt_parser import parse_receipt
from ai.local_parser import (
    LocalAIParser,
    ReceiptAIResult,
)
from validator.receipt_validator import ReceiptValidator


class ReceiptProcessor:

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.ocr_reader = OCRReader()
        self.ai_parser = LocalAIParser()
        self.validator = ReceiptValidator()
        
    def _can_skip_ai(
            self,
            regex_receipt,
            parsed_fields,
            ocr_texts
        ):
            """
            Regex + OCR sonucu tek başına çok güçlü ise
            Local AI çağrısını atlamaya izin verir.

            Bu kontrol bilinçli olarak konservatiftir.
            Şüpheli tek bir alan varsa AI çalışır.
            """

            min_confidence = 0.95

            required_fields = {
                "company": regex_receipt.company,
                "receipt_no": regex_receipt.receipt_no,
                "date": regex_receipt.date,
                "time": regex_receipt.time,
                "total": regex_receipt.total,
            }

            # Firma, fiş no, tarih, saat ve toplamın
            # tamamı regex tarafından bulunmuş olmalı.
            for field_name, value in required_fields.items():
                if value is None:
                    return False

                parsed_field = parsed_fields.get(
                    field_name
                )

                if parsed_field is None:
                    return False

                confidence = parsed_field.confidence

                if (
                    confidence is None
                    or confidence < min_confidence
                ):
                    return False

            # Validator'ın zaten kullandığı temel
            # format kontrollerini burada da uyguluyoruz.
            if not self.validator._is_valid_company(
                regex_receipt.company
            ):
                return False

            if not self.validator._is_valid_receipt_no(
                regex_receipt.receipt_no
            ):
                return False

            if not self.validator._is_valid_date(
                regex_receipt.date
            ):
                return False

            if not self.validator._is_valid_time(
                regex_receipt.time
            ):
                return False

            if not self.validator._is_valid_amount(
                regex_receipt.total
            ):
                return False

            if regex_receipt.total <= 0:
                return False

            # Fişte gerçekten KDV etiketi var mı?
            has_kdv_label = any(
                "KDV" in str(text).upper()
                for text in ocr_texts
            )

            if has_kdv_label:
                # Etiket varsa regex KDV'yi de
                # güvenli biçimde bulmuş olmalı.
                if regex_receipt.kdv is None:
                    return False

                kdv_field = parsed_fields.get(
                    "kdv"
                )

                if kdv_field is None:
                    return False

                if (
                    kdv_field.confidence is None
                    or kdv_field.confidence
                    < min_confidence
                ):
                    return False

                if not self.validator._is_valid_amount(
                    regex_receipt.kdv
                ):
                    return False

                # Cross-field güvenlik kontrolü.
                if (
                    regex_receipt.kdv
                    > regex_receipt.total
                ):
                    return False

            return True
        

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
        # 4. Local AI
        step_start = time.perf_counter()

        ai_skipped = self._can_skip_ai(
            regex_receipt,
            parsed_fields,
            ocr_document.texts
        )

        if ai_skipped:
            # AI gerçekten çalışmadığı için boş bir
            # AI sonucu gönderiyoruz.
            #
            # Validator böylece regex değerlerini
            # yalnızca yüksek OCR confidence varsa
            # VERIFIED_WITH_OCR kabul edecek.
            ai_result = ReceiptAIResult()

        else:
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

        ai_status = (
            "SKIP"
            if ai_skipped
            else "RUN"
        )

        print(
            f"AI         : "
            f"{ai_time:.2f} sn "
            f"[{ai_status}]"
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