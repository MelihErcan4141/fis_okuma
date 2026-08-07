from services.batch_receipt_processor import BatchReceiptProcessor


def main():
    folder_path = "images/batch_test"

    processor = BatchReceiptProcessor()

    print("\n--- BATCH PROCESSING BAŞLADI ---\n")

    results = processor.process_folder(folder_path)

    print(f"Toplam bulunan fiş: {len(results)}\n")

    success_count = 0
    failed_count = 0
    review_count = 0

    for item in results:
        print("=" * 60)
        print(f"Dosya: {item['file']}")

        if not item["success"]:
            failed_count += 1

            print("Durum: ❌ HATA")
            print(f"Hata : {item['error']}")
            continue

        success_count += 1

        result = item["result"]

        print("\n--- FINAL RECEIPT ---")
        print(result.receipt)

        if result.requires_review:
            review_count += 1
            print("\nDurum: ⚠ KULLANICI KONTROLÜ GEREKİYOR")
        else:
            print("\nDurum: ✅ DOĞRULANDI")

    print("\n" + "=" * 60)
    print("--- BATCH ÖZETİ ---")
    print(f"Toplam       : {len(results)}")
    print(f"İşlenen      : {success_count}")
    print(f"Hatalı       : {failed_count}")
    print(f"Kontrol gerek: {review_count}")


if __name__ == "__main__":
    main()