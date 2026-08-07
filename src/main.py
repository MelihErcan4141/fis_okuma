import re
from paddleocr import PaddleOCR
from models.receipt import Receipt

image_path = "images/fis1_converted.jpg"

ocr = PaddleOCR(

    lang="tr",

    use_doc_orientation_classify=False,

    use_doc_unwarping=False,

    use_textline_orientation=False

)

results = ocr.predict(image_path)
texts = []

for result in results:

    texts.extend(result["rec_texts"])

print("\n--- HAM OCR METİNLERİ ---\n")

for text in texts:

    print(text)

def find_receipt_no(texts):

    for text in texts:

        match = re.search(r"F[Iİ]S\s*NO[:\s]*([0-9]+)", text, re.IGNORECASE)

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

receipt_no = find_receipt_no(texts)

date = find_date(texts)

time = find_time(texts)

def find_company(texts):
    if texts:
        return texts[0]
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
        upper_text = text.strip().upper()

        if upper_text.startswith("TOP"):
            if i > 0:
                value = clean_amount(texts[i - 1])

                if value is not None:
                    return value

    return None


receipt = Receipt(

    company=find_company(texts),

    receipt_no=find_receipt_no(texts),

    date=find_date(texts),

    time=find_time(texts),

    kdv=find_kdv(texts),

    total=find_total(texts)

)

print("\n--- ÇIKARILAN BİLGİLER ---\n")

print(receipt)