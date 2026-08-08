from enum import Enum
import math
import re

from models.receipt import Receipt
from services.company_normalizer import canonicalize_company


MIN_HIGH_CONFIDENCE = 0.95


class ValidationStatus(Enum):
    VERIFIED = "VERIFIED"
    VERIFIED_WITH_OCR = "VERIFIED_WITH_OCR"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFLICT = "CONFLICT"
    MISSING = "MISSING"
    INVALID = "INVALID"
    VERIFIED_WITH_AI = "VERIFIED_WITH_AI"
    NOT_PRESENT = "NOT_PRESENT"


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
            ValidationStatus.VERIFIED_WITH_AI,
            ValidationStatus.VERIFIED,
            ValidationStatus.VERIFIED_WITH_OCR,
            ValidationStatus.NOT_PRESENT
        }

        return any(
            field.status not in safe_statuses
            for field in self.fields
        )


class ReceiptValidator:
    def _apply_cross_field_checks(self, fields):
        field_map = {
            field.field_name: field
            for field in fields
        }

        kdv_field = field_map.get("KDV")
        total_field = field_map.get("Toplam")

        if (
            kdv_field is None
            or total_field is None
        ):
            return

        kdv = kdv_field.final_value
        total = total_field.final_value

        # İkisinden biri güvenli final değere ulaşmadıysa
        # matematiksel karşılaştırma yapma.
        if kdv is None or total is None:
            return

        # KDV toplamdan büyük olamaz.
        if kdv > total:
            kdv_field.final_value = None
            kdv_field.status = ValidationStatus.INVALID
            kdv_field.message = (
                f"KDV ({kdv}) toplam tutardan "
                f"({total}) büyük olamaz."
            )

    def validate(
        self,
        regex_receipt,
        ai_receipt,
        parsed_fields,
        ocr_texts=None
    ):
        fields = []
        if ocr_texts is None:
            ocr_texts = []

        kdv_keywords = {
            "KDV",
            "TOPKDV",
            "TOP KDV",
            "TOPLAM KDV"
        }

        has_kdv_label = False

        for text in ocr_texts:
            normalized = str(text).upper().strip()

            if any(
                keyword in normalized
                for keyword in kdv_keywords
            ):
                has_kdv_label = True
                break

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

        if (
            regex_receipt.kdv is None
            and ai_receipt.kdv is None
            and not has_kdv_label
        ):
            fields.append(
                FieldValidation(
                    "KDV",
                    None,
                    None,
                    None,
                    ValidationStatus.NOT_PRESENT,
                    "Fişte KDV etiketi bulunmadı."
                )
            )

        else:
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
        self._apply_cross_field_checks(fields)

        values = {
            field.field_name: field.final_value
            for field in fields
        }
        values["Firma"] = canonicalize_company(
            values["Firma"]
        )

        receipt = Receipt(
            company=values["Firma"],
            receipt_no=values["Fiş No"],
            date=values["Tarih"],
            time=values["Saat"],
            kdv=values["KDV"],
            total=values["Toplam"]
        )

        return ValidationResult(
            receipt,
            fields
        )

    def _validate_field(
        self,
        field_name,
        regex_value,
        ai_value,
        ocr_confidence,
        normalize=False,
        normalize_time=False
    ):

        # Önce açıkça geçersiz değerleri kontrol et.
        invalid_reason = self._get_invalid_reason(
            field_name,
            regex_value
        )

        if invalid_reason:

            # Firma regex sonucu kötü olabilir ama
            # AI tarafında güvenilir bir firma adı bulunmuş olabilir.
            if (
                field_name == "Firma"
                and ai_value is not None
                and self._is_valid_company(ai_value)
            ):
                canonical_ai = canonicalize_company(
                    ai_value
                )

                # Registry gerçekten bir canonical isim bulduysa
                # AI sonucunu güvenli kabul et.
                if canonical_ai != ai_value:
                    return FieldValidation(
                        field_name,
                        regex_value,
                        ai_value,
                        canonical_ai,
                        ValidationStatus.VERIFIED_WITH_AI,
                        (
                            "Regex firma sonucu geçersiz/genel bulundu, "
                            "AI sonucu registry ile doğrulandı."
                        )
                    )

                # Registry doğrulayamıyorsa kullanıcı kontrolüne bırak.
                return FieldValidation(
                    field_name,
                    regex_value,
                    ai_value,
                    ai_value,
                    ValidationStatus.NEEDS_REVIEW,
                    (
                        "Regex firma sonucu geçersiz/genel bulundu. "
                        "AI geçerli görünüyor ancak registry ile doğrulanamadı."
                    )
                )

            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                None,
                ValidationStatus.INVALID,
                invalid_reason
            )

        # AI'ın ürettiği değer de açıkça geçersiz olabilir.
        ai_invalid_reason = self._get_invalid_reason(
            field_name,
            ai_value
        )

        if ai_invalid_reason:
            # Regex geçerliyse AI'nın saçma sonucu
            # final değeri bozmasın ama yine de review isteyelim.
            if regex_value is not None:
                return FieldValidation(
                    field_name,
                    regex_value,
                    ai_value,
                    regex_value,
                    ValidationStatus.NEEDS_REVIEW,
                    (
                        "AI geçersiz bir değer üretti: "
                        f"{ai_value}"
                    )
                )

            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                None,
                ValidationStatus.INVALID,
                ai_invalid_reason
            )

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
        # Güvenlik nedeniyle AI'yı doğrudan final yapmıyoruz.
        if regex_value is None:
            if (
                field_name == "Fiş No"
                and ai_value is not None
                and self._is_valid_receipt_no(ai_value)
            ):
                text = str(ai_value).strip()

                if (
                    text.isdigit()
                    and 1 <= len(text) <= 6
                ):
                    return FieldValidation(
                        field_name,
                        regex_value,
                        ai_value,
                        text,
                        ValidationStatus.VERIFIED_WITH_AI,
                        (
                            "Fiş numarası yalnızca AI tarafından bulundu "
                            "ancak formatı güvenli sınırlar içinde."
                        )
                    )

            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                None,
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
                        "yüksek OCR güveniyle destekleniyor "
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
        
        if field_name == "Firma":
            regex_compare = self._normalize_company(regex_value)
            ai_compare = self._normalize_company(ai_value)

            if regex_compare and ai_compare:
                shorter = min(
                    (regex_compare, ai_compare),
                    key=len
                )

                longer = max(
                    (regex_compare, ai_compare),
                    key=len
                )

                if (
                    len(shorter) >= 6
                    and longer.startswith(shorter)
                ):
                    return FieldValidation(
                        field_name,
                        regex_value,
                        ai_value,
                        regex_value,
                        ValidationStatus.VERIFIED,
                        (
                            "Firma adları aynı temel isimle başlıyor. "
                            "Daha kısa OCR değeri final olarak kullanıldı."
                        )
                    )

        if normalize:
            regex_compare = self._normalize_date(
                regex_value
            )

            ai_compare = self._normalize_date(
                ai_value
            )

        if normalize_time:
            regex_compare = self._normalize_time(
                regex_value
            )

            ai_compare = self._normalize_time(
                ai_value
            )

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

            # Özellikle Toplam alanında OCR bazen ondalık basamağı
            # yanlış yere koyabiliyor:
            # 1.7   <-> 170.0
            # 4.32  <-> 432.0
            #
            # Sadece 10x veya 100x ölçek farkını ve yalnızca
            # "Toplam" alanında kontrol ediyoruz.
            if (
                not values_match
                and field_name == "Toplam"
                and regex_compare > 0
                and ai_compare > 0
            ):
                scale_candidates = [
                    regex_compare * 10,
                    regex_compare * 100,
                    regex_compare / 10,
                    regex_compare / 100,
                ]

                values_match = any(
                    math.isclose(
                        candidate,
                        ai_compare,
                        rel_tol=1e-9,
                        abs_tol=0.01
                    )
                    for candidate in scale_candidates
                )

        else:
            if field_name == "Firma":
                # Tam eşleşme
                if regex_compare == ai_compare:
                    values_match = True

                # Kısa isim uzun ismin başında/ortasında geçiyorsa
                elif (
                    regex_compare
                    and ai_compare
                    and (
                        regex_compare in ai_compare
                        or ai_compare in regex_compare
                    )
                ):
                    # Çok kısa anlamsız parçaları kabul etmiyoruz.
                    shorter = min(
                        len(regex_compare),
                        len(ai_compare)
                    )

                    values_match = shorter >= 6

                else:
                    values_match = False

            else:
                values_match = (
                    regex_compare == ai_compare
                )

        if values_match:
            final_value = regex_value

            # Toplam alanında ölçek farkı varsa,
            # daha büyük olan değeri seçiyoruz.
            if (
                field_name == "Toplam"
                and isinstance(regex_value, (int, float))
                and isinstance(ai_value, (int, float))
                and not math.isclose(
                    regex_value,
                    ai_value,
                    rel_tol=1e-9,
                    abs_tol=0.001
                )
            ):
                final_value = max(
                    regex_value,
                    ai_value
                )

            return FieldValidation(
                field_name,
                regex_value,
                ai_value,
                final_value,
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

    def _get_invalid_reason(
        self,
        field_name,
        value
    ):
        if value is None:
            return None
        if field_name == "Firma":
            if not self._is_valid_company(value):
                return (
                    f"Geçersiz veya fazla genel firma adı: {value}"
                )

        elif field_name == "Tarih":
            if not self._is_valid_date(value):
                return (
                    f"Geçersiz tarih değeri: {value}"
                )

        elif field_name == "Saat":
            if not self._is_valid_time(value):
                return (
                    f"Geçersiz saat değeri: {value}"
                )

        elif field_name == "KDV":
            if not self._is_valid_amount(value):
                return (
                    f"Geçersiz KDV tutarı: {value}"
                )

        elif field_name == "Toplam":
            if not self._is_valid_amount(value):
                return (
                    f"Geçersiz toplam tutarı: {value}"
                )

            if value <= 0:
                return (
                    f"Toplam sıfırdan büyük olmalıdır: {value}"
                )

        elif field_name == "Fiş No":
            if not self._is_valid_receipt_no(value):
                return (
                    f"Geçersiz fiş numarası: {value}"
                )

        return None
    
    def _is_valid_date(self, value):
        text = str(value).strip()

        match = re.fullmatch(
            r"(\d{2})[-./](\d{2})[-./](\d{4})",
            text
        )

        if not match:
            return False

        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))

        if not 1 <= month <= 12:
            return False

        if not 1 <= day <= 31:
            return False

        if not 1900 <= year <= 2100:
            return False

        return True

    def _is_valid_time(self, value):
        text = str(value).strip()

        match = re.fullmatch(
            r"(\d{2}):(\d{2})(?::(\d{2}))?",
            text
        )

        if not match:
            return False

        hour = int(match.group(1))
        minute = int(match.group(2))

        second = (
            int(match.group(3))
            if match.group(3)
            else 0
        )

        return (
            0 <= hour <= 23
            and 0 <= minute <= 59
            and 0 <= second <= 59
        )

    def _is_valid_amount(self, value):
        if not isinstance(
            value,
            (int, float)
        ):
            return False

        if not math.isfinite(value):
            return False

        return value >= 0
    


    def _is_valid_company(self, value):
        if value is None:
            return False

        normalized = self._normalize_company(
            value
        )

        if not normalized:
            return False

        words = normalized.split()

        # Firma adı tamamen anlamsız veya çok kısa olmasın.
        if len(normalized) < 3:
            return False

        generic_words = {
            "TICARET",
            "SANAYI",
            "SAN",
            "TIC",

            # A.Ş. normalize edilince "A S" oluyor.
            "A",
            "S",
            "AS",

            "LTD",
            "LIMITED",

            # ŞTİ. normalize edilince "STI" olabilir.
            "STI",
            "SIRKETI",

            "MAGAZA",
            "MAGAZASI",

            # Tek başına ayırt edici olmayan bağlaçlar
            "VE",
        }

        meaningful_words = [
            word
            for word in words
            if word not in generic_words
        ]

        # Örneğin:
        # "TICARET A.S."
        # "SAN TIC LTD"
        # gibi isimler gerçek firma adı olarak
        # yeterince ayırt edici değil.
        if not meaningful_words:
            return False

        return True

    def _is_valid_receipt_no(self, value):
        text = str(value).strip()

        if not text:
            return False

        # Şimdilik çok uzun değerleri fiş no kabul etmiyoruz.
        if len(text) > 12:
            return False

        return True

    def _normalize_time(self, value):
        if value is None:
            return None

        value = str(value).strip()

        parts = value.split(":")

        if len(parts) >= 2:
            return (
                f"{parts[0]}:{parts[1]}"
            )

        return value
    

    def _normalize_date(self, value):
        if value is None:
            return None

        return (
            str(value)
            .replace(".", "-")
            .replace("/", "-")
        )
    
    def _normalize_company(self, value):
        if value is None:
            return None

        import unicodedata

        text = str(value).upper().strip()

        replacements = {
            "İ": "I",
            "Ş": "S",
            "Ğ": "G",
            "Ü": "U",
            "Ö": "O",
            "Ç": "C",

            "Í": "I",
            "Ì": "I",
            "Î": "I",
            "Ï": "I",

            "Á": "A",
            "À": "A",
            "Â": "A",

            "É": "E",
            "È": "E",
            "Ê": "E",

            "Ó": "O",
            "Ò": "O",
            "Ô": "O",

            "Ú": "U",
            "Ù": "U",
            "Û": "U",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = unicodedata.normalize(
            "NFKD",
            text
        )

        text = "".join(
            ch
            for ch in text
            if not unicodedata.combining(ch)
        )

        text = re.sub(
            r"[^A-Z0-9 ]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return text