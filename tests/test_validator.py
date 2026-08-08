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
        make_parsed_fields(kdv_conf=None),
        ocr_texts=[
            "ABC MARKET",
            "KDV",
            "TOPLAM",
            "250,00"
        ]
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

def test_negative_amount_is_invalid():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=-430974.0,
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
        make_parsed_fields()
    )

    kdv_field = get_field(result, "KDV")

    assert kdv_field.status == ValidationStatus.INVALID
    assert kdv_field.final_value is None
    assert result.requires_review is True


def test_invalid_time_is_invalid():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time="37:82",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="07-08-2026",
        time=None,
        kdv=20.50,
        total=250.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    time_field = get_field(result, "Saat")

    assert time_field.status == ValidationStatus.INVALID
    assert time_field.final_value is None


def test_invalid_date_is_invalid():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date="211277062",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0012",
        date=None,
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

    date_field = get_field(result, "Tarih")

    assert date_field.status == ValidationStatus.INVALID
    assert date_field.final_value is None


def test_extremely_long_receipt_number_is_invalid():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="05020011308301870047",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no=None,
        date="07-08-2026",
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

    receipt_no_field = get_field(result, "Fiş No")

    assert receipt_no_field.status == ValidationStatus.INVALID
    assert receipt_no_field.final_value is None

def test_kdv_greater_than_total_is_invalid():
        regex_receipt = Receipt(
            company="ABC MARKET",
            receipt_no="0012",
            date="07-08-2026",
            time="15:30",
            kdv=300.00,
            total=250.00
        )

        ai_receipt = Receipt(
            company="ABC MARKET",
            receipt_no="0012",
            date="07-08-2026",
            time="15:30",
            kdv=300.00,
            total=250.00
        )

        validator = ReceiptValidator()

        result = validator.validate(
            regex_receipt,
            ai_receipt,
            make_parsed_fields()
        )

        kdv_field = get_field(result, "KDV")

        assert kdv_field.status == ValidationStatus.INVALID
        assert kdv_field.final_value is None
        assert result.requires_review is True

def test_ai_only_short_receipt_number_is_verified():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no=None,
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="0127",
        date="07-08-2026",
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

    receipt_no_field = get_field(
        result,
        "Fiş No"
    )

    assert (
        receipt_no_field.status
        == ValidationStatus.VERIFIED_WITH_AI
    )

    assert (
        receipt_no_field.final_value
        == "0127"
    )



def test_ai_only_long_receipt_number_requires_review():
    regex_receipt = Receipt(
        company="ABC MARKET",
        receipt_no=None,
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="ABC MARKET",
        receipt_no="05020011308301870047",
        date="07-08-2026",
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

    receipt_no_field = get_field(
        result,
        "Fiş No"
    )

    assert (
        receipt_no_field.status
        != ValidationStatus.VERIFIED_WITH_AI
    )

    assert (
        receipt_no_field.final_value
        is None
    )


def test_missing_kdv_without_label_is_not_present():
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
        make_parsed_fields(kdv_conf=None),
        ocr_texts=[
            "ABC MARKET",
            "FIS NO: 0012",
            "TOPLAM",
            "250,00"
        ]
    )

    kdv_field = get_field(
        result,
        "KDV"
    )

    assert (
        kdv_field.status
        == ValidationStatus.NOT_PRESENT
    )

    assert result.requires_review is False




def test_missing_kdv_with_label_still_requires_review():
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
        make_parsed_fields(kdv_conf=None),
        ocr_texts=[
            "ABC MARKET",
            "KDV",
            "TOPLAM",
            "250,00"
        ]
    )

    kdv_field = get_field(
        result,
        "KDV"
    )

    assert (
        kdv_field.status
        == ValidationStatus.MISSING
    )

    assert result.requires_review is True


def test_total_scale_difference_is_verified():
        regex_receipt = Receipt(
            company="ABC MARKET",
            receipt_no="0012",
            date="07-08-2026",
            time="15:30",
            kdv=20.50,
            total=1.7
        )

        ai_receipt = Receipt(
            company="ABC MARKET",
            receipt_no="0012",
            date="07-08-2026",
            time="15:30",
            kdv=20.50,
            total=170.0
        )

        validator = ReceiptValidator()

        result = validator.validate(
            regex_receipt,
            ai_receipt,
            make_parsed_fields()
        )

        total_field = get_field(
            result,
            "Toplam"
        )

        assert (
            total_field.status
            == ValidationStatus.VERIFIED
        )

        assert (
            total_field.final_value
            == 170.0
        )



def test_company_short_and_long_name_match():
        regex_receipt = Receipt(
            company="MIGROS",
            receipt_no="0012",
            date="07-08-2026",
            time="15:30",
            kdv=20.50,
            total=250.00
        )

        ai_receipt = Receipt(
            company="MIGROS TICARET A.S.",
            receipt_no="0012",
            date="07-08-2026",
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

        company_field = get_field(
            result,
            "Firma"
        )

        assert (
            company_field.status
            == ValidationStatus.VERIFIED
        )

        assert (
            company_field.final_value
            == "MIGROS"
        )