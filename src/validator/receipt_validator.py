from enum import Enum
from models.receipt import Receipt
import math

MIN_HIGH_CONFIDENCE = 0.95


class ValidationStatus(Enum):
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFLICT = "CONFLICT"
    MISSING = "MISSING"

class ValidationStatus(Enum):
    VERIFIED = "VERIFIED"
    VERIFIED_WITH_OCR = "VERIFIED_WITH_OCR"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFLICT = "CONFLICT"
    MISSING = "MISSING"


class FieldValidation:
    def __init__(
        self,
        field_name,
        regex_value,
        ai_value,
        final_value,
        status,
        message
    ):
        self.field_name = field_name
        self.regex_value = regex_value
        self.ai_value = ai_value
        self.final_value = final_value
        self.status = status
        self.message = message


class ValidationResult:
    def __init__(self, receipt, fields):
        self.receipt = receipt
        self.fields = fields

    @property
    def requires_review(self):

        safe_statuses = {

            ValidationStatus.VERIFIED,

            ValidationStatus.VERIFIED_WITH_OCR

        }

        return any(

            field.status not in safe_statuses

            for field in self.fields

        )


class ReceiptValidator:
    def _normalize_time(self, value):
        if value is None:
            return None

        value = str(value).strip()

        parts = value.split(":")

        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}"

        return value

    def validate(self, regex_receipt, ai_receipt,parsed_fields):

        fields = []

        fields.append(
            self._validate_field(
                "Firma",
                regex_receipt.company,
                ai_receipt.company,
                parsed_fields["company"].confidence
            )
        )

        fields.append(
            self._validate_field(
                "Fiş No",
                regex_receipt.receipt_no,
                ai_receipt.receipt_no,
                parsed_fields["receipt_no"].confidence
            )
        )

        fields.append(
            self._validate_field(
                "Tarih",
                regex_receipt.date,
                ai_receipt.date,
                parsed_fields["date"].confidence,
                normalize=True
            )
        )

        fields.append(
            self._validate_field(
                "Saat",
                regex_receipt.time,
                ai_receipt.time,
                parsed_fields["time"].confidence,
                normalize_time=True
            )
        )

        fields.append(
            self._validate_field(
                "KDV",
                regex_receipt.kdv,
                ai_receipt.kdv,
                parsed_fields["kdv"].confidence
            )
        )

        fields.append(
            self._validate_field(
                "Toplam",
                regex_receipt.total,
                ai_receipt.total,
                parsed_fields["total"].confidence
            )
        )

        values = {
            field.field_name: field.final_value
            for field in fields
        }

        receipt = Receipt(
            company=values["Firma"],
            receipt_no=values["Fiş No"],
            date=values["Tarih"],
            time=values["Saat"],
            kdv=values["KDV"],
            total=values["Toplam"]
        )

        return ValidationResult(receipt, fields)

    def _validate_field(
        self,
        field_name,
        regex_value,
        ai_value,
        ocr_confidence,
        normalize=False,
        normalize_time=False
    ):

        # İkisi de hiçbir şey bulamadı.
        if regex_value is None and ai_value is None:
            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                None,
                ValidationStatus.MISSING,
                "Her iki parser da değer bulamadı."
            )

        # Regex bulamadı ama AI buldu.
        if regex_value is None:
            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                ai_value,
                ValidationStatus.NEEDS_REVIEW,
                "Değer yalnızca AI tarafından bulundu."
            )

        # AI bulamadı ama regex buldu.
        if ai_value is None:

            if (
                ocr_confidence is not None
                and ocr_confidence >= MIN_HIGH_CONFIDENCE
            ):
                return FieldValidation(
                    field_name,
                    regex_value,
                    ai_value,
                    regex_value,
                    ValidationStatus.VERIFIED_WITH_OCR,
                    (
                        "AI değer bulamadı ancak regex sonucu "
                        f"yüksek OCR güveniyle destekleniyor "
                        f"({ocr_confidence:.2%})."
                    )
                )

            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                regex_value,
                ValidationStatus.NEEDS_REVIEW,
                (
                    "Değer yalnızca regex parser tarafından bulundu "
                    "ve OCR güveni yeterince yüksek değil."
                )
            )

        regex_compare = regex_value
        ai_compare = ai_value

        if normalize:
            regex_compare = self._normalize_date(regex_value)
            ai_compare = self._normalize_date(ai_value)

        if normalize_time:
            regex_compare = self._normalize_time(regex_value)
            ai_compare = self._normalize_time(ai_value)

        # İki parser aynı şeyi söylüyor.
        if (
            isinstance(regex_compare, (int, float))
            and isinstance(ai_compare, (int, float))
        ):
            values_match = math.isclose(
                regex_compare,
                ai_compare,
                rel_tol=1e-9,
                abs_tol=0.001
            )
        else:
            values_match = regex_compare == ai_compare

        if values_match:
            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                regex_value,
                ValidationStatus.VERIFIED,
                "Regex ve AI sonuçları eşleşiyor."
            )

        # İki parser farklı şeyler söylüyor.
        return FieldValidation(
            field_name,
            regex_value,
            ai_value,
            None,
            ValidationStatus.CONFLICT,
            "Regex ve AI sonuçları birbiriyle uyuşmuyor."
        )

    def _normalize_date(self, value):

        if value is None:
            return None

        return (
            str(value)
            .replace(".", "-")
            .replace("/", "-")
        )