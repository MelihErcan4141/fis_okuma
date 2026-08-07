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

    def prepare(self, image_path: str) -> str:
        """
        OCR'a gönderilecek görseli standart JPEG formatına dönüştürür.

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

        output_dir = source_path.parent / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{source_path.stem}_processed.jpg"

        with Image.open(source_path) as image:

            # Telefon fotoğraflarındaki EXIF orientation bilgisini uygula.
            image = ImageOps.exif_transpose(image)

            # JPEG alpha channel desteklemez.
            if image.mode != "RGB":
                image = image.convert("RGB")

            image.save(
                output_path,
                format="JPEG",
                quality=95
            )

        return str(output_path)