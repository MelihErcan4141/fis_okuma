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


@pytest.mark.integration
def test_real_receipt_2():
    image_path = "images/fis2_converted.jpg"

    reader = OCRReader()
    ocr_document = reader.read(image_path)

    receipt, parsed_fields = parse_receipt(ocr_document)

    assert receipt.company == "KAS İTHALAT IHRACAT LÍMITED"
    assert receipt.receipt_no == "00180"
    assert receipt.date == "23/07/2026"
    assert receipt.time == "19:03"
    assert receipt.kdv == pytest.approx(121.84)
    assert receipt.total == pytest.approx(869.99)

    assert parsed_fields["kdv"].confidence >= 0.95
    assert parsed_fields["total"].confidence >= 0.95


@pytest.mark.integration
def test_real_receipt_3():
    image_path = "images/fis4.jpeg"

    reader = OCRReader()
    ocr_document = reader.read(image_path)

    receipt, parsed_fields = parse_receipt(ocr_document)

    assert receipt.company == "KANAAT LOKANTASI"
    assert receipt.receipt_no == "0006"
    assert receipt.date == "09.07.2026"
    assert receipt.time == "15:24"
    assert receipt.kdv == pytest.approx(163.64)
    assert receipt.total == pytest.approx(1800.00)

    assert parsed_fields["kdv"].confidence >= 0.95
    assert parsed_fields["total"].confidence >= 0.95