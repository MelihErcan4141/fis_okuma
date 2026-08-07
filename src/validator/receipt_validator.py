from models.receipt import Receipt


class ValidationResult:
    def __init__(self, receipt, warnings):
        self.receipt = receipt
        self.warnings = warnings


class ReceiptValidator:
    def validate(self, regex_receipt, ai_receipt):
        warnings = []

        company = self._choose(
            "Firma",
            regex_receipt.company,
            ai_receipt.company,
            warnings
        )

        receipt_no = self._choose(
            "Fiş No",
            regex_receipt.receipt_no,
            ai_receipt.receipt_no,
            warnings
        )

        date = self._choose(
            "Tarih",
            regex_receipt.date,
            ai_receipt.date,
            warnings,
            normalize_date=True
        )

        time = self._choose(
            "Saat",
            regex_receipt.time,
            ai_receipt.time,
            warnings
        )

        kdv = self._choose(
            "KDV",
            regex_receipt.kdv,
            ai_receipt.kdv,
            warnings
        )

        total = self._choose(
            "Toplam",
            regex_receipt.total,
            ai_receipt.total,
            warnings
        )

        final_receipt = Receipt(
            company=company,
            receipt_no=receipt_no,
            date=date,
            time=time,
            kdv=kdv,
            total=total
        )

        return ValidationResult(final_receipt, warnings)

    def _choose(
        self,
        field_name,
        regex_value,
        ai_value,
        warnings,
        normalize_date=False
    ):
        if regex_value is None and ai_value is None:
            warnings.append(
                f"{field_name}: Her iki parser da değer bulamadı."
            )
            return None

        if ai_value is None:
            return regex_value

        if regex_value is None:
            return ai_value

        regex_compare = regex_value
        ai_compare = ai_value

        if normalize_date:
            regex_compare = self._normalize_date(regex_value)
            ai_compare = self._normalize_date(ai_value)

        if regex_compare == ai_compare:
            return regex_value

        warnings.append(
            f"{field_name}: Regex={regex_value}, AI={ai_value}"
        )

        return regex_value

    def _normalize_date(self, value):
        if value is None:
            return None

        return (
            str(value)
            .replace(".", "-")
            .replace("/", "-")
        )