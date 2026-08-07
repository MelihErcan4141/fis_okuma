from ocr.reader import OCRReader
from parser.receipt_parser import parse_receipt


image_path = "images/fis1_converted.jpg"

reader = OCRReader()

texts = reader.read(image_path)

print("\n--- HAM OCR METİNLERİ ---\n")

for text in texts:
    print(text)

receipt = parse_receipt(texts)

print("\n--- ÇIKARILAN BİLGİLER ---\n")
print(receipt)