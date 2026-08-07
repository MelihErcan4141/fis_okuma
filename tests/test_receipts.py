import pytest

from models.ocr_line import OCRLine
from models.ocr_document import OCRDocument
from parser.receipt_parser import parse_receipt


def make_document(lines):
    return OCRDocument(
        [
            OCRLine(text=text, confidence=confidence)
            for text, confidence in lines
        ]
    )


@pytest.mark.parametrize(
    "lines, expected",
    [
        (
            [
                ("YABELES ITHALAT-IHRACAT LTD", 0.978),
                ("FIS NO: 0269", 0.998),
                ("07-07-2026", 0.999),
                ("SAAT 18:17", 1.0),
                ("*623,16", 1.0),
                ("ARATOPLAM", 0.999),
                ("*12,85", 0.995),
                ("KDV", 1.0),
                ("*623,16", 0.998),
                ("*623,16", 1.0),
                ("TOP", 1.0),
                ("NAKIT", 1.0),
            ],
            {
                "company": "YABELES ITHALAT-IHRACAT LTD",
                "receipt_no": "0269",
                "date": "07-07-2026",
                "time": "18:17",
                "kdv": 12.85,
                "total": 623.16,
            }
        ),

        (
            [
                ("KAS İTHALAT IHRACAT LÍMITED", 0.930),
                ("FIS NO: 00180", 0.996),
                ("TARIH: 23/07/2026", 0.991),
                ("SAAT : 19:03:24", 0.986),
                ("*121,84", 0.999),
                ("TOPKDV", 1.0),
                ("*869,99", 1.0),
                ("TOPLAM", 1.0),
                ("*869,99", 1.0),
            ],
            {
                "company": "KAS İTHALAT IHRACAT LÍMITED",
                "receipt_no": "00180",
                "date": "23/07/2026",
                "time": "19:03",
                "kdv": 121.84,
                "total": 869.99,
            }
        ),

        (
            [
                ("KANAAT LOKANTASI", 1.0),
                ("09.07.2026", 1.0),
                ("Saat: 15:24", 0.921),
                ("Fis No: 0006", 0.989),
                ("*1.800,00", 0.999),
                ("KDV", 1.0),
                ("*163,64", 1.0),
                ("TOPLAM", 1.0),
                ("*1.800,00", 0.999),
            ],
            {
                "company": "KANAAT LOKANTASI",
                "receipt_no": "0006",
                "date": "09.07.2026",
                "time": "15:24",
                "kdv": 163.64,
                "total": 1800.0,
            }
        ),
    ]
)
def test_receipt_parser(lines, expected):
    document = make_document(lines)

    receipt, parsed_fields = parse_receipt(document)

    assert receipt.company == expected["company"]
    assert receipt.receipt_no == expected["receipt_no"]
    assert receipt.date == expected["date"]
    assert receipt.time == expected["time"]

    assert receipt.kdv == pytest.approx(expected["kdv"])
    assert receipt.total == pytest.approx(expected["total"])

    assert parsed_fields["company"].confidence is not None
    assert parsed_fields["receipt_no"].confidence is not None
    assert parsed_fields["date"].confidence is not None
    assert parsed_fields["time"].confidence is not None
    assert parsed_fields["kdv"].confidence is not None
    assert parsed_fields["total"].confidence is not None