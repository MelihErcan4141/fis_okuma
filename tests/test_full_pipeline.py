import pytest

from ocr.reader import OCRReader
from parser.receipt_parser import parse_receipt
from ai.local_parser import LocalAIParser
from validator.receipt_validator import ReceiptValidator


@pytest.mark.full_pipeline
def test_full_pipeline_receipt_1():

    # 1. Gerçek fotoğraf
    image_path = "images/fis1_converted.jpg"

    # 2. OCR
    reader = OCRReader()
    ocr_document = reader.read(image_path)

    # 3. Regex parser
    regex_receipt, parsed_fields = parse_receipt(ocr_document)

    # 4. Local AI
    ai_parser = LocalAIParser()
    ai_result = ai_parser.parse(ocr_document.texts)

    # 5. Validator
    validator = ReceiptValidator()

    validation_result = validator.validate(
        regex_receipt,
        ai_result,
        parsed_fields
    )

    # 6. Final receipt
    final_receipt = validation_result.receipt

    assert final_receipt.company == "YABELES ITHALAT-IHRACAT LTD"
    assert final_receipt.receipt_no == "0269"
    assert final_receipt.date == "07-07-2026"
    assert final_receipt.time == "18:17"

    assert final_receipt.kdv == pytest.approx(12.85)
    assert final_receipt.total == pytest.approx(623.16)

    assert validation_result.requires_review is False


@pytest.mark.full_pipeline
def test_full_pipeline_receipt_2():

    image_path = "images/fis2_converted.jpg"

    reader = OCRReader()
    ocr_document = reader.read(image_path)

    regex_receipt, parsed_fields = parse_receipt(ocr_document)

    ai_parser = LocalAIParser()
    ai_result = ai_parser.parse(ocr_document.texts)

    validator = ReceiptValidator()

    validation_result = validator.validate(
        regex_receipt,
        ai_result,
        parsed_fields
    )

    final_receipt = validation_result.receipt

    assert final_receipt.company == "KAS İTHALAT IHRACAT LÍMITED"
    assert final_receipt.receipt_no == "00180"
    assert final_receipt.date == "23/07/2026"
    assert final_receipt.time == "19:03"

    assert final_receipt.kdv == pytest.approx(121.84)
    assert final_receipt.total == pytest.approx(869.99)

    assert validation_result.requires_review is False


@pytest.mark.full_pipeline
def test_full_pipeline_receipt_3():

    image_path = "images/fis4.jpeg"

    reader = OCRReader()
    ocr_document = reader.read(image_path)

    regex_receipt, parsed_fields = parse_receipt(ocr_document)

    ai_parser = LocalAIParser()
    ai_result = ai_parser.parse(ocr_document.texts)

    validator = ReceiptValidator()

    validation_result = validator.validate(
        regex_receipt,
        ai_result,
        parsed_fields
    )

    final_receipt = validation_result.receipt

    assert final_receipt.company == "KANAAT LOKANTASI"
    assert final_receipt.receipt_no == "0006"
    assert final_receipt.date == "09.07.2026"
    assert final_receipt.time == "15:24"

    assert final_receipt.kdv == pytest.approx(163.64)
    assert final_receipt.total == pytest.approx(1800.00)

    assert validation_result.requires_review is False