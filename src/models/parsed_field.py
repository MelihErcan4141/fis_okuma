class ParsedField:
    def __init__(
        self,
        value=None,
        source_text=None,
        confidence=None
    ):
        self.value = value
        self.source_text = source_text
        self.confidence = confidence