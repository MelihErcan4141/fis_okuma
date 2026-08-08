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




def test_a101_company_is_canonicalized():
    regex_receipt = Receipt(
        company="A101 YEN] MAGAZACILIK A.S. M.Kodu:6848",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="A101 YEN] MAGAZACILIK A.S.",
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

    assert (
        result.receipt.company
        == "A101 YENİ MAĞAZACILIK A.Ş."
    )


def test_bim_ocr_error_is_canonicalized():
    regex_receipt = Receipt(
        company="BUR BURLESIY MASAZALAR A.S",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="BUR BURLESIY MASAZALAR A.S",
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

    assert (
        result.receipt.company
        == "BİM BİRLEŞİK MAĞAZALAR A.Ş."
    )



def test_unknown_company_is_not_changed():
    regex_receipt = Receipt(
        company="XYZ TEKNOLOJI LTD",
        receipt_no="0012",
        date="07-08-2026",
        time="15:30",
        kdv=20.50,
        total=250.00
    )

    ai_receipt = Receipt(
        company="XYZ TEKNOLOJI LTD",
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

    assert (
        result.receipt.company
        == "XYZ TEKNOLOJI LTD"
    )


def test_different_import_companies_are_not_merged():
    regex_receipt = Receipt(
        company="YABELES ITHALAT-IHRACAT LTD",
        receipt_no="0269",
        date="07-07-2026",
        time="18:17",
        kdv=12.85,
        total=623.16
    )

    ai_receipt = Receipt(
        company="YABELES ITHALAT-IHRACAT LTD",
        receipt_no="0269",
        date="07-07-2026",
        time="18:17",
        kdv=12.85,
        total=623.16
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    assert (
        result.receipt.company
        == "YABELES ITHALAT-IHRACAT LTD"
    )



def test_company_accented_i_is_normalized():
    regex_receipt = Receipt(
        company="KAS ITHALAT IHRACAT LÍMITED",
        receipt_no="00180",
        date="23/07/2026",
        time="19:03",
        kdv=121.84,
        total=869.99
    )

    ai_receipt = Receipt(
        company="KAS ITHALAT IHRACAT LÍMITED",
        receipt_no="00180",
        date="23/07/2026",
        time="19:03",
        kdv=121.84,
        total=869.99
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    assert (
        result.receipt.company
        == "KAS İTHALAT İHRACAT LİMİTED"
    )


def test_migros_short_name_is_canonicalized():
    regex_receipt = Receipt(
        company="MiGROS",
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=299.83,
        total=1799.00
    )

    ai_receipt = Receipt(
        company="MiGROS TICARET A.S. LIMAN AVM BANDIRMA SATIS MAGAZASI",
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=299.83,
        total=1799.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    assert (
        result.receipt.company
        == "MİGROS TİCARET A.Ş."
    )


def test_generic_company_words_do_not_cause_false_match():
    regex_receipt = Receipt(
        company="ABC ITHALAT IHRACAT LIMITED",
        receipt_no="123",
        date="07-08-2026",
        time="15:30",
        kdv=20.00,
        total=200.00
    )

    ai_receipt = Receipt(
        company="ABC ITHALAT IHRACAT LIMITED",
        receipt_no="123",
        date="07-08-2026",
        time="15:30",
        kdv=20.00,
        total=200.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    assert (
        result.receipt.company
        == "ABC ITHALAT IHRACAT LIMITED"
    )


def test_completely_different_company_is_not_canonicalized():
    regex_receipt = Receipt(
        company="MEHMET YILMAZ RESTORAN",
        receipt_no="55",
        date="07-08-2026",
        time="15:30",
        kdv=15.00,
        total=150.00
    )

    ai_receipt = Receipt(
        company="MEHMET YILMAZ RESTORAN",
        receipt_no="55",
        date="07-08-2026",
        time="15:30",
        kdv=15.00,
        total=150.00
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        make_parsed_fields()
    )

    assert (
        result.receipt.company
        == "MEHMET YILMAZ RESTORAN"
    )


def test_generic_company_name_does_not_override_real_ai_company():
    regex_receipt = Receipt(
        company="TiCARET A.S.",
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=299.83,
        total=1799.00
    )

    ai_receipt = Receipt(
        company=(
            "MiGROS TiCARET A.S. "
            "LiMAN AVM BANDIRMA SATIS MAGAZASI"
        ),
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=299.83,
        total=1799.00
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
        result.receipt.company
        == "MİGROS TİCARET A.Ş."
    )

    assert (
        company_field.status
        == ValidationStatus.VERIFIED_WITH_AI
    )



def test_generic_regex_company_uses_registry_verified_ai():
    regex_receipt = Receipt(
        company="TiCARET A.S.",
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=299.83,
        total=1799.00
    )

    ai_receipt = Receipt(
        company="MiGROS TiCARET A.S. LiMAN AVM BANDIRMA SATIS MAGAZASI",
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=299.83,
        total=1799.00
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
        result.receipt.company
        == "MİGROS TİCARET A.Ş."
    )

    assert (
        company_field.status
        == ValidationStatus.VERIFIED_WITH_AI
    )


def test_unknown_ai_company_requires_review_when_regex_is_generic():
    regex_receipt = Receipt(
        company="TiCARET A.S.",
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=20.00,
        total=200.00
    )

    ai_receipt = Receipt(
        company="HASAN YILMAZ GIDA LTD",
        receipt_no="0041",
        date="16/08/2024",
        time="17:15",
        kdv=20.00,
        total=200.00
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
        result.receipt.company
        == "HASAN YILMAZ GIDA LTD"
    )

    assert (
        company_field.status
        == ValidationStatus.NEEDS_REVIEW
    )

    assert result.requires_review is True



def test_kdv_with_strong_label_context_is_verified():
    regex_receipt = Receipt(
        company="ABC PETROL",
        receipt_no="0257",
        date="11-07-2025",
        time="01:09",
        kdv=718.29,
        total=4309.74
    )

    ai_receipt = Receipt(
        company="ABC PETROL",
        receipt_no="0257",
        date="11-07-2025",
        time="01:09",
        kdv=None,
        total=4309.74
    )

    parsed_fields = make_parsed_fields(
        kdv_conf=0.941
    )

    parsed_fields["kdv"].source_text = (
        "-718.29"
    )

    validator = ReceiptValidator()

    result = validator.validate(
        regex_receipt,
        ai_receipt,
        parsed_fields,
        ocr_texts=[
            "ABC PETROL",
            "KDV",
            "-718.29",
            "TOPLAM",
            "4.309,74",
        ]
    )

    kdv_field = get_field(
        result,
        "KDV"
    )

    assert (
        kdv_field.status
        == ValidationStatus.VERIFIED_WITH_OCR
    )

    assert kdv_field.final_value == 718.29
    assert result.requires_review is False