from models.receipt import Receipt
from models.parsed_field import ParsedField
from validator.receipt_validator import (
    ReceiptValidator,
    ValidationStatus
)


def make_parsed_fields(
    company_conf=0.99,
    receipt_no_conf=0.99,
    date_conf=0.99,
    time_conf=0.99,
    kdv_conf=0.99,
    total_conf=0.99
):
    return {
        "company": ParsedField(confidence=company_conf),
        "receipt_no": ParsedField(confidence=receipt_no_conf),
        "date": ParsedField(confidence=date_conf),
        "time": ParsedField(confidence=time_conf),
        "kdv": ParsedField(confidence=kdv_conf),
        "total": ParsedField(confidence=total_conf),
    }


def get_field(result, field_name):
    for field in result.fields:
        if field.field_name == field_name:
            return field

    raise AssertionError(f"{field_name} bulunamadı.")


def test_all_fields_verified():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07.08.2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    assert result.requires_review is False

    for field in result.fields:
        assert field.status == ValidationStatus.VERIFIED


def test_verified_with_high_ocr_confidence():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=None,
        total=250.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields(kdv_conf=0.99)
    )

    kdv_field = get_field(result, "KDV")

    assert kdv_field.status == ValidationStatus.VERIFIED_WITH_OCR
    assert kdv_field.final_value == 20.50
    assert result.requires_review is False


def test_low_ocr_confidence_requires_review():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=None,
        total=250.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields(kdv_conf=0.60)
    )

    kdv_field = get_field(result, "KDV")

    assert kdv_field.status == ValidationStatus.NEEDS_REVIEW
    assert result.requires_review is True


def test_conflict_requires_human_review():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=35.00,
        total=250.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields(kdv_conf=0.999)
    )

    kdv_field = get_field(result, "KDV")

    assert kdv_field.status == ValidationStatus.CONFLICT
    assert kdv_field.final_value is None
    assert result.requires_review is True


def test_missing_field_requires_review():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=None,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=None,
        total=250.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields(kdv_conf=None)
    )

    kdv_field = get_field(result, "KDV")

    assert kdv_field.status == ValidationStatus.MISSING
    assert kdv_field.final_value is None
    assert result.requires_review is True


def test_float_values_are_compared_safely():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=623.16
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=623.1600000000001
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    total_field = get_field(result, "Toplam")

    assert total_field.status == ValidationStatus.VERIFIED
    assert total_field.final_value == 623.16