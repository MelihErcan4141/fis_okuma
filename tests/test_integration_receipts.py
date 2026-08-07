import pytest

from ocr.reader import OCRReader
from parser.receipt_parser import parse_receipt


@pytest.mark.integration
def test_real_receipt_1():
    image_path = "images/fis1_converted.jpg"

    reader = OCRReader()
    ocr_document = reader.read(image_path)

    receipt, parsed_fields = parse_receipt(ocr_document)

    assert receipt.company == "YABELES ITHALAT-IHRACAT LTD"
    assert receipt.receipt_no == "0269"
    assert receipt.date == "07-07-2026"
    assert receipt.time == "18:17"
    assert receipt.kdv == pytest.approx(12.85)
    assert receipt.total == pytest.approx(623.16)

    assert parsed_fields["kdv"].confidence >= 0.95
    assert parsed_fields["total"].confidence >= 0.95