from validator.receipt_validator import ReceiptValidator
from ocr.reader import OCRReader
from ai.local_parser import LocalAIParser
from parser.receipt_parser import parse_receipt



image_path = "images/fis1_converted.jpg"

reader = OCRReader()

ocr_document = reader.read(image_path)

print("\n--- HAM OCR METİNLERİ ---\n")

for line in ocr_document.lines:
    print(f"{line.confidence:.3f} | {line.text}")

receipt, parsed_fields = parse_receipt(ocr_document)


print("\n--- REGEX PARSER SONUCU ---\n")
print(receipt)


print("\n--- PARSED FIELD CONFIDENCE ---\n")

for name, field in parsed_fields.items():
    print(f"{name}:")
    print(f"  Değer      : {field.value}")
    print(f"  Kaynak     : {field.source_text}")

    if field.confidence is not None:
        print(f"  Confidence : {field.confidence:.2%}")
    else:
        print("  Confidence : None")

    print()

ai_parser = LocalAIParser()
ai_result = ai_parser.parse(ocr_document.texts)




print("\n--- LOCAL AI PARSER SONUCU ---\n")
print("Firma:", ai_result.company)
print("Fiş No:", ai_result.receipt_no)
print("Tarih:", ai_result.date)
print("Saat:", ai_result.time)
print("KDV:", ai_result.kdv)
print("Toplam:", ai_result.total)

validator = ReceiptValidator()

validation_result = validator.validate(
    receipt,
    ai_result,
    parsed_fields
)

print("\n--- VALIDATION REPORT ---\n")

for field in validation_result.fields:

    print(f"{field.field_name}:")

    print(f"  Regex : {field.regex_value}")

    print(f"  AI    : {field.ai_value}")

    print(f"  Final : {field.final_value}")

    print(f"  Status: {field.status.value}")

    print(f"  Mesaj : {field.message}")

    print()

print("--- FINAL RECEIPT ---\n")

print(validation_result.receipt)

if validation_result.requires_review:

    print(

        "\n⚠ Bu fişte kullanıcı kontrolü gereken alanlar var."

    )

else:

    print(

        "\nTüm alanlar doğrulandı."

    )

print("\nOCR Ortalama Güven:")

print(
    f"{ocr_document.average_confidence():.2%}"
)

