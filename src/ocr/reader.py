from paddleocr import PaddleOCR
from models.ocr_line import OCRLine
from models.ocr_document import OCRDocument

class OCRReader:
    def __init__(self):
        self.ocr = PaddleOCR(
            lang="tr",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )

    def read(self, image_path):
        results = self.ocr.predict(image_path)

        lines = []

        for result in results:
            texts = result["rec_texts"]
            scores = result["rec_scores"]

            for text, score in zip(texts, scores):
                lines.append(
                    OCRLine(
                        text=text,
                        confidence=float(score)
                    )
                )

        return OCRDocument(lines)