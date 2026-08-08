from pathlib import Path

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener


register_heif_opener()


class ImagePreprocessor:

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".heic",
        ".heif",
    }

    # OCR için gereksiz derecede büyük
    # telefon fotoğraflarını küçült.
    MAX_LONG_SIDE = 2200

    def prepare(self, image_path: str) -> str:
        """
        OCR'a gönderilecek görseli standart JPEG
        formatına dönüştürür.

        Büyük görseller OCR performansını düşürdüğü için
        en uzun kenar MAX_LONG_SIDE değerini geçiyorsa
        görüntü orantılı şekilde küçültülür.

        Orijinal dosyaya dokunmaz.
        """

        source_path = Path(image_path)

        if not source_path.exists():
            raise FileNotFoundError(
                f"Görsel bulunamadı: {source_path}"
            )

        extension = source_path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Desteklenmeyen görsel formatı: {extension}"
            )

        output_dir = (
            source_path.parent
            / "processed"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = (
            output_dir
            / f"{source_path.stem}_processed.jpg"
        )

        with Image.open(source_path) as image:

            # Telefon fotoğraflarındaki EXIF
            # orientation bilgisini uygula.
            image = ImageOps.exif_transpose(
                image
            )

            # JPEG alpha channel desteklemez.
            if image.mode != "RGB":
                image = image.convert("RGB")

            width, height = image.size

            longest_side = max(
                width,
                height
            )

            # Sadece gerçekten büyük görselleri
            # küçült. Küçük görselleri büyütme.
            if longest_side > self.MAX_LONG_SIDE:

                scale = (
                    self.MAX_LONG_SIDE
                    / longest_side
                )

                new_width = round(
                    width * scale
                )

                new_height = round(
                    height * scale
                )

                image = image.resize(
                    (
                        new_width,
                        new_height
                    ),
                    Image.Resampling.LANCZOS
                )

            image.save(
                output_path,
                format="JPEG",
                quality=90,
                optimize=True
            )

        return str(output_path)