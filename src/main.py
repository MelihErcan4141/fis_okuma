from validator.receipt_validator import ReceiptValidator
from ocr.reader import OCRReader
from ai.local_parser import LocalAIParser
from parser.receipt_parser import parse_receipt


image_path = "images/fis1_converted.jpg"

reader = OCRReader()

texts = reader.read(image_path)

print("\n--- HAM OCR METİNLERİ ---\n")

for text in texts:
    print(text)

receipt = parse_receipt(texts)
print("\n--- REGEX PARSER SONUCU ---\n")
print(receipt)

ai_parser = LocalAIParser()
ai_result = ai_parser.parse(texts)

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
    ai_result
)

print("\n--- FINAL RECEIPT ---\n")
print(validation_result.receipt)

print("\n--- UYARILAR ---\n")

if validation_result.warnings:
    for warning in validation_result.warnings:
        print("⚠", warning)
else:
    print("Her şey tutarlı.")

