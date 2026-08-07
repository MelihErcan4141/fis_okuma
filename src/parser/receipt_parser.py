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


def find_kdv(ocr_document):
    lines = ocr_document.lines

    for i, line in enumerate(lines):
        if line.text.strip().upper() == "KDV":
            if i > 0:
                value_line = lines[i - 1]
                value = clean_amount(value_line.text)

                if value is not None:
                    return ParsedField(
                        value=value,
                        source_text=value_line.text,
                        confidence=value_line.confidence
                    )

    return ParsedField()


def find_total(ocr_document):
    lines = ocr_document.lines

    for i, line in enumerate(lines):
        if line.text.strip().upper().startswith("TOP"):
            if i > 0:
                value_line = lines[i - 1]
                value = clean_amount(value_line.text)

                if value is not None:
                    return ParsedField(
                        value=value,
                        source_text=value_line.text,
                        confidence=value_line.confidence
                    )

    return ParsedField()


def parse_receipt(ocr_document):
    company = find_company(ocr_document)
    receipt_no = find_receipt_no(ocr_document)
    date = find_date(ocr_document)
    time = find_time(ocr_document)
    kdv = find_kdv(ocr_document)
    total = find_total(ocr_document)

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