import re

from models.receipt import Receipt
from models.parsed_field import ParsedField


def clean_amount(text):
    text = text.replace("*", "").replace(" ", "")
    text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def find_company(ocr_document):
    if not ocr_document.lines:
        return ParsedField()

    line = ocr_document.lines[0]

    return ParsedField(
        value=line.text,
        source_text=line.text,
        confidence=line.confidence
    )


def find_receipt_no(ocr_document):
    for line in ocr_document.lines:
        match = re.search(
            r"F[Iİ]S\s*NO[:\s]*([0-9]+)",
            line.text,
            re.IGNORECASE
        )

        if match:
            return ParsedField(
                value=match.group(1),
                source_text=line.text,
                confidence=line.confidence
            )

    return ParsedField()


def find_date(ocr_document):
    for line in ocr_document.lines:
        match = re.search(
            r"\b(\d{2}[-./]\d{2}[-./]\d{4})\b",
            line.text
        )

        if match:
            return ParsedField(
                value=match.group(1),
                source_text=line.text,
                confidence=line.confidence
            )

    return ParsedField()


def find_time(ocr_document):
    for line in ocr_document.lines:
        match = re.search(
            r"\b(\d{2}:\d{2})\b",
            line.text
        )

        if match:
            return ParsedField(
                value=match.group(1),
                source_text=line.text,
                confidence=line.confidence
            )

    return ParsedField()


def find_kdv(ocr_document, total_field):
    lines = ocr_document.lines

    kdv_keywords = {
        "KDV",
        "TOPKDV",
        "TOP KDV",
        "TOPLAM KDV"
    }

    for i, line in enumerate(lines):
        normalized_text = line.text.strip().upper()

        if normalized_text not in kdv_keywords:
            continue

        candidates = []

        # KDV kelimesinden önceki satır
        if i > 0:
            previous_line = lines[i - 1]
            value = clean_amount(previous_line.text)

            if value is not None:
                candidates.append(
                    ParsedField(
                        value=value,
                        source_text=previous_line.text,
                        confidence=previous_line.confidence
                    )
                )

        # KDV kelimesinden sonraki satır
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            value = clean_amount(next_line.text)

            if value is not None:
                candidates.append(
                    ParsedField(
                        value=value,
                        source_text=next_line.text,
                        confidence=next_line.confidence
                    )
                )

        if not candidates:
            return ParsedField()

        # Toplama eşit olan değer büyük ihtimalle KDV değildir.
        if total_field.value is not None:
            valid_candidates = [
                candidate
                for candidate in candidates
                if candidate.value != total_field.value
                and candidate.value < total_field.value
            ]

            if len(valid_candidates) == 1:
                return valid_candidates[0]

        # Tek aday varsa güvenle onu döndür
        if len(candidates) == 1:
            return candidates[0]

        # İki aday arasında güvenilir karar veremiyorsak tahmin etme
        return ParsedField()

    return ParsedField()


def find_total(ocr_document):
    lines = ocr_document.lines

    total_keywords = {
        "TOPLAM",
        "GENEL TOPLAM",
        "ÖDENECEK",
        "ÖDENECEK TUTAR",
        "TOP"
    }

    for i, line in enumerate(lines):
        normalized_text = line.text.strip().upper()

        if normalized_text in total_keywords:

            # Önce TOPLAM kelimesinden sonraki satıra bak
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                value = clean_amount(next_line.text)

                if value is not None:
                    return ParsedField(
                        value=value,
                        source_text=next_line.text,
                        confidence=next_line.confidence
                    )

            # Sonraki satır sayı değilse önceki satıra bak
            if i > 0:
                previous_line = lines[i - 1]
                value = clean_amount(previous_line.text)

                if value is not None:
                    return ParsedField(
                        value=value,
                        source_text=previous_line.text,
                        confidence=previous_line.confidence
                    )

    return ParsedField()


def parse_receipt(ocr_document):
    company = find_company(ocr_document)
    receipt_no = find_receipt_no(ocr_document)
    date = find_date(ocr_document)
    time = find_time(ocr_document)
    total = find_total(ocr_document)
    kdv = find_kdv(ocr_document, total)

    receipt = Receipt(
        company=company.value,
        receipt_no=receipt_no.value,
        date=date.value,
        time=time.value,
        kdv=kdv.value,
        total=total.value
    )

    fields = {
        "company": company,
        "receipt_no": receipt_no,
        "date": date,
        "time": time,
        "kdv": kdv,
        "total": total
    }

    return receipt, fields