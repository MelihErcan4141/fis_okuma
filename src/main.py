from services.receipt_processor import ReceiptProcessor


def main():
    image_path = "images/fis1_converted.jpg"

    processor = ReceiptProcessor()

    result = processor.process(image_path)

    print("\n--- FINAL RECEIPT ---\n")
    print(result.receipt)

    print("\n--- VALIDATION REPORT ---\n")

    for field in result.fields:
            print(f"{field.field_name}:")
            print(f"  Regex : {field.regex_value}")
            print(f"  AI    : {field.ai_value}")
            print(f"  Final : {field.final_value}")
            print(f"  Status: {field.status.value}")
            print(f"  Mesaj : {field.message}")
            print()

    if result.requires_review:
        print("⚠ Bu fişte kullanıcı kontrolü gereken alanlar var.")
    else:
        print(" Tüm alanlar doğrulandı.")


if __name__ == "__main__":
    main()