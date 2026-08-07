import re

from models.receipt import Receipt


def find_company(texts):
    if texts:
        return texts[0]
    return None


def find_receipt_no(texts):
    for text in texts:
        match = re.search(
            r"F[Iİ]S\s*NO[:\s]*([0-9]+)",
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


def find_date(texts):
    for text in texts:
        match = re.search(
            r"\b(\d{2}[-./]\d{2}[-./]\d{4})\b",
            text
        )

        if match:
            return match.group(1)

    return None


def find_time(texts):
    for text in texts:
        match = re.search(
            r"\b(\d{2}:\d{2})\b",
            text
        )

        if match:
            return match.group(1)

    return None


def clean_amount(text):
    text = text.replace("*", "").replace(" ", "")
    text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def find_kdv(texts):
    for i, text in enumerate(texts):
        if text.strip().upper() == "KDV":
            if i > 0:
                return clean_amount(texts[i - 1])

    return None


def find_total(texts):
    for i, text in enumerate(texts):
        if text.strip().upper().startswith("TOP"):
            if i > 0:
                value = clean_amount(texts[i - 1])

                if value is not None:
                    return value

    return None


def parse_receipt(texts):
    return Receipt(
        company=find_company(texts),
        receipt_no=find_receipt_no(texts),
        date=find_date(texts),
        time=find_time(texts),
        kdv=find_kdv(texts),
        total=find_total(texts)
    )