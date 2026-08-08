from models.ocr_line import OCRLine
from models.ocr_document import OCRDocument
from parser.receipt_parser import parse_receipt
from services.receipt_processor import ReceiptProcessor
from validator.receipt_validator import ReceiptValidator


def make_document(lines):
    return OCRDocument(
        [
            OCRLine(
                text=text,
                confidence=confidence
            )
            for text, confidence in lines
        ]
    )


def make_processor():
    processor = ReceiptProcessor.__new__(
        ReceiptProcessor
    )
    processor.validator = ReceiptValidator()
    return processor


def test_ai_can_be_skipped_for_strong_regex_result():
    document = make_document(
        [
            ("YABELES ITHALAT-IHRACAT LTD", 0.99),
            ("FIS NO: 0269", 0.99),
            ("07-07-2026", 0.99),
            ("SAAT 18:17", 0.99),
            ("*12,85", 0.99),
            ("KDV", 1.0),
            ("*623,16", 0.99),
            ("TOP", 1.0),
            ("NAKIT", 1.0),
        ]
    )

    receipt, parsed_fields = parse_receipt(
        document
    )

    processor = make_processor()

    result = processor._can_skip_ai(
        receipt,
        parsed_fields,
        document.texts
    )

    assert result is True



def test_ai_is_not_skipped_when_receipt_no_missing():
    document = make_document(
        [
            ("YABELES ITHALAT-IHRACAT LTD", 0.99),
            ("07-07-2026", 0.99),
            ("SAAT 18:17", 0.99),
            ("*12,85", 0.99),
            ("KDV", 1.0),
            ("*623,16", 0.99),
            ("TOP", 1.0),
            ("NAKIT", 1.0),
        ]
    )

    receipt, parsed_fields = parse_receipt(
        document
    )

    assert receipt.receipt_no is None

    processor = make_processor()

    result = processor._can_skip_ai(
        receipt,
        parsed_fields,
        document.texts
    )

    assert result is False
    document = make_document(
        [
            ("YABELES ITHALAT-IHRACAT LTD", 0.99),
            ("07-07-2026", 0.99),
            ("SAAT 18:17", 0.99),
            ("*12,85", 0.99),
            ("KDV", 1.0),
            ("*623,16", 0.99),
            ("TOP", 1.0),
            ("NAKIT", 1.0),
        ]
    )

    receipt, parsed_fields = parse_receipt(
        document
    )

    assert receipt.receipt_no is None

    result = processor._can_skip_ai(
        receipt,
        parsed_fields,
        document.texts
    )

    assert result is False