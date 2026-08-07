class OCRDocument:

    def __init__(self, lines):
        self.lines = lines

    @property
    def texts(self):
        return [line.text for line in self.lines]

    @property
    def confidences(self):
        return [line.confidence for line in self.lines]

    def average_confidence(self):
        if not self.lines:
            return 0

        return sum(
            line.confidence
            for line in self.lines
        ) / len(self.lines)