from paddleocr import PaddleOCR


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

        texts = []

        for result in results:
            texts.extend(result["rec_texts"])

        return texts