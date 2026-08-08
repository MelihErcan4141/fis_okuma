from services.batch_receipt_processor import BatchReceiptProcessor


def main():
    folder_path = "images/real_batch"

    processor = BatchReceiptProcessor()

    print("\n--- BATCH PROCESSING BAŞLADI ---\n")

    results = processor.process_folder(folder_path)

    total_count = len(results)
    success_count = 0
    failed_count = 0
    review_count = 0
    verified_count = 0

    field_stats = {}

    for item in results:
        print("\n" + "=" * 70)
        print(f"Dosya: {item['file']}")

        if not item["success"]:
            failed_count += 1

            print("Durum: ❌ İŞLEME HATASI")
            print(f"Hata : {item['error']}")

            continue

        success_count += 1

        result = item["result"]

        print("\n--- FINAL RECEIPT ---")
        print(result.receipt)

        print("\n--- ALAN DURUMLARI ---")

        for field in result.fields:
            print(
                f"{field.field_name:<12} "
                f"{field.status.value:<20} "
                f"Regex: {field.regex_value!r} | "
                f"AI: {field.ai_value!r} | "
                f"Final: {field.final_value!r}"
            )

            if field.field_name not in field_stats:
                field_stats[field.field_name] = {
                    "safe": 0,
                    "review": 0
                }

            if field.status.value in {
                "VERIFIED",
                "VERIFIED_WITH_OCR",
                "VERIFIED_WITH_AI",
                "NOT_PRESENT"
            }:
                field_stats[field.field_name]["safe"] += 1

            else:
                field_stats[field.field_name]["review"] += 1

        if result.requires_review:
            review_count += 1

            print(
                "\n⚠ KULLANICI KONTROLÜ GEREKİYOR"
            )

        else:
            verified_count += 1

            print(
                "\n✅ TAMAMEN DOĞRULANDI"
            )

    print("\n" + "=" * 70)

    print("--- BATCH ÖZETİ ---")

    print(
        f"Toplam fiş          : {total_count}"
    )

    print(
        f"Başarıyla işlendi   : {success_count}"
    )

    print(
        f"Tam doğrulanan      : {verified_count}"
    )

    print(
        f"Kontrol gereken     : {review_count}"
    )

    print(
        f"İşleme hatası       : {failed_count}"
    )

    if total_count > 0:
        verification_rate = (
            verified_count
            / total_count
            * 100
        )

        print(
            f"Tam doğrulama oranı : "
            f"%{verification_rate:.2f}"
        )

    print("\n--- ALAN BAŞARI ORANLARI ---")

    for field_name, stats in field_stats.items():
        total = (
            stats["safe"]
            + stats["review"]
        )

        rate = (
            stats["safe"]
            / total
            * 100
            if total > 0
            else 0
        )

        print(
            f"{field_name:<12}: "
            f"{stats['safe']}/{total} "
            f"(%{rate:.2f})"
        )


if __name__ == "__main__":
    main()