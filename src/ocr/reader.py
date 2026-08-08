from paddleocr import PaddleOCR
from models.ocr_line import OCRLine
from models.ocr_document import OCRDocument
from services.ocr_cache import OCRCache

class OCRReader:
    def __init__(self):
        self.ocr = PaddleOCR(
            lang="tr",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )
        self.cache = OCRCache()
        self.cache_hits = 0
        self.cache_misses = 0

    def read(self, image_path):

        cached_document = self.cache.load(
            image_path
        )

        if cached_document is not None:
            self.cache_hits += 1

            return cached_document

        self.cache_misses += 1

        results = self.ocr.predict(
            image_path
        )

        lines = []

        for result in results:
            texts = result["rec_texts"]
            scores = result["rec_scores"]

            for text, score in zip(
                texts,
                scores
            ):
                lines.append(
                    OCRLine(
                        text=text,
                        confidence=float(score)
                    )
                )

        document = OCRDocument(lines)

        self.cache.save(
            image_path,
            document
        )

        return document