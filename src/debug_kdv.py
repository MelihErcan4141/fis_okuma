from ocr.reader import OCRReader


IMAGE_PATHS = [
    "images/real_batch/fis10.jpg",
    "images/real_batch/fis12.jpg",
    "images/real_batch/fis14.jpg",
    "images/real_batch/fis20.jpg",
    "images/real_batch/fis21.jpg",
]


def main():
    reader = OCRReader()

    for image_path in IMAGE_PATHS:
        print("\n" + "=" * 80)
        print(f"DOSYA: {image_path}")
        print("=" * 80)

        document = reader.read(image_path)

        lines = document.lines

        for index, line in enumerate(lines):
            text = line.text.strip()

            if "KDV" not in text.upper():
                continue

            print(f"\nKDV ETİKETİ BULUNDU: [{index}] {text}")
            print("-" * 60)

            # KDV satırından önceki 5 ve sonraki 8 OCR satırını göster.
            start = max(0, index - 5)
            end = min(len(lines), index + 9)

            for i in range(start, end):
                current = lines[i]

                marker = ">>> " if i == index else "    "

                print(
                    f"{marker}"
                    f"[{i:02d}] "
                    f"{current.confidence:.3f} | "
                    f"{current.text}"
                )


if __name__ == "__main__":
    main()