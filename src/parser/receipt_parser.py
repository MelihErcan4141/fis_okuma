import re

from models.receipt import Receipt
from models.parsed_field import ParsedField


def clean_amount(text):
    if text is None:
        return None

    text = str(text).strip()

    # Para dışı karakterleri temizle.
    text = (
        text
        .replace("*", "")
        .replace("TL", "")
        .replace("₺", "")
        .replace(" ", "")
    )

    # Sadece sayı, virgül, nokta ve eksi kalsın.
    text = re.sub(
        r"[^0-9,.\-]",
        "",
        text
    )

    if not text:
        return None

    try:
        # Hem nokta hem virgül varsa:
        # 1.800,00 -> 1800.00
        # 1,800.00 -> 1800.00
        if "," in text and "." in text:

            last_comma = text.rfind(",")
            last_dot = text.rfind(".")

            if last_comma > last_dot:
                # Türkçe format: 1.800,00
                text = text.replace(".", "")
                text = text.replace(",", ".")

            else:
                # İngilizce format: 1,800.00
                text = text.replace(",", "")

        elif "," in text:
            # 623,16 -> 623.16
            text = text.replace(",", ".")

        elif "." in text:
            parts = text.split(".")

            # 4.499 gibi tek nokta ve sonrasında 3 hane varsa
            # bunu binlik ayırıcı kabul et.
            if (
                len(parts) == 2
                and len(parts[1]) == 3
                and parts[0].lstrip("-").isdigit()
                and parts[1].isdigit()
            ):
                text = "".join(parts)

            # 1.800.000 gibi birden fazla binlik ayırıcı.
            elif (
                len(parts) > 2
                and all(
                    len(part) == 3
                    for part in parts[1:]
                )
            ):
                text = "".join(parts)

        value = float(text)

        return value

    except ValueError:
        return None

def find_company(ocr_document):
    if not ocr_document.lines:
        return ParsedField()

    ignored_phrases = {
        "E-ARSIV",
        "E ARSIV",
        "FATURA",
        "MALI DEGERI YOK",
        "MALİ DEĞERİ YOK",
        "FIS NO",
        "FİŞ NO",
        "TARIH",
        "TARİH",
        "SAAT",
        "V.NO",
        "V NO",
        "VERGI NO",
        "VERGİ NO",
        "TOPLAM",
        "KDV"
    }

    generic_lines = {
        "TICARET",
        "TİCARET",
        "TIC.",
        "TİC.",
        "TIC.A.S",
        "TİC.A.Ş",
        "LIMITED",
        "LTD",
        "LTD.",
        "A.S",
        "A.Ş",
        "SANAYI",
        "SANAYİ"
    }

    business_keywords = {
        "LTD",
        "LIMITED",
        "A.S",
        "A.Ş",
        "TICARET",
        "TİCARET",
        "MARKET",
        "MAGAZA",
        "MAĞAZA",
        "PETROL",
        "LOKANTA",
        "HIRDAVAT",
        "AKARYAKIT"
    }

    candidates = []

    for index, line in enumerate(ocr_document.lines[:10]):
        text = line.text.strip()

        if not text:
            continue

        upper = text.upper()

        if any(
            phrase in upper
            for phrase in ignored_phrases
        ):
            continue

        # Tek başına şirket türü/ek satırı olan şeyleri ele.
        if upper in generic_lines:
            continue

        letter_count = sum(
            character.isalpha()
            for character in text
        )

        if letter_count < 3:
            continue

        digit_count = sum(
            character.isdigit()
            for character in text
        )

        # Aşırı sayısal satır şirket adı değildir.
        if digit_count > letter_count:
            continue

        score = 0

        # Fişin ilk satırlarına çok daha güçlü öncelik.
        score += max(0, 20 - (index * 3))

        # Firma tipi kelimesi artı puan ama artık tek başına
        # yukarıdaki satırları ezmeyecek.
        if any(
            keyword in upper
            for keyword in business_keywords
        ):
            score += 5

        # Çok kısa/generic görünen satırları cezalandır.
        words = text.split()

        if len(words) == 1:
            score -= 3

        candidates.append(
            (score, line)
        )

    if not candidates:
        return ParsedField()

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_line = candidates[0][1]

    return ParsedField(
        value=best_line.text,
        source_text=best_line.text,
        confidence=best_line.confidence
    )

def find_receipt_no(ocr_document):
    lines = ocr_document.lines

    # 1. Önce güçlü ve açık fiş numarası etiketlerini ara.
    strong_patterns = [
        r"F[Iİ]S\s*NO\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",
        r"F[Iİ]Ş\s*NO\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",
        r"F[Iİ]SNO\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",
        r"F[Iİ]ŞNO\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",

        # OCR bazen O harfini 0 okuyabilir.
        r"F[Iİ]S\s*N[O0]\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",
        r"F[Iİ]Ş\s*N[O0]\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",

        # Bazı fişlerde kısa etiket olabilir.
        r"\bF\s*NO\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",
        r"\bF\.NO\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",

        # Belge numarası formatları.
        r"BELGE\s*NO\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",
        r"BELGE\s*NUMARASI\s*[:\-]?\s*([0-9]{1,12})(?![0-9])",
    ]

    for line in lines:
        text = line.text.strip()

        for pattern in strong_patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:
                return ParsedField(
                    value=match.group(1),
                    source_text=line.text,
                    confidence=line.confidence
                )

    # 2. Etiket ve sayı OCR tarafından iki ayrı satıra bölünmüş olabilir.
    #
    # Örnek:
    #
    # FIS NO
    # 0127
    #
    for i, line in enumerate(lines[:-1]):
        current = line.text.strip()

        if re.fullmatch(
            r"F[Iİ][SŞ]\s*N[O0]\s*[:\-]?",
            current,
            re.IGNORECASE
        ):
            next_line = lines[i + 1]

            match = re.fullmatch(
                r"\s*([0-9]{1,12})\s*",
                next_line.text
            )

            if match:
                confidence = min(
                    line.confidence,
                    next_line.confidence
                )

                return ParsedField(
                    value=match.group(1),
                    source_text=(
                        f"{line.text} {next_line.text}"
                    ),
                    confidence=confidence
                )

    # Bilerek genel "NO: 2", "NO: 58" gibi fallback kullanmıyoruz.
    # Çünkü bunlar adres/kapı numarası olabilir.

    return ParsedField()


def find_date(ocr_document):
    for line in ocr_document.lines:
        match = re.search(
            r"\b(\d{2}[-./]\d{2}[-./]\d{4})\b",
            line.text
        )

        if match:
            return ParsedField(
                value=match.group(1),
                source_text=line.text,
                confidence=line.confidence
            )

    return ParsedField()


def find_time(ocr_document):
    for line in ocr_document.lines:
        match = re.search(
            r"\b(\d{2}:\d{2})\b",
            line.text
        )

        if match:
            return ParsedField(
                value=match.group(1),
                source_text=line.text,
                confidence=line.confidence
            )

    return ParsedField()


def find_kdv(ocr_document, total_field):
    lines = ocr_document.lines

    # ---------------------------------------------------------
    # 1) En güvenilir durum:
    # TOPKDV / TOP KDV / TOPLAM KDV etiketinin hemen sonraki
    # satırında bulunan para tutarını KDV kabul et.
    # ---------------------------------------------------------

    for i, line in enumerate(lines):
        text = line.text.strip().upper()

        is_total_kdv_label = (
            text == "TOPKDV"
            or text == "TOP KDV"
            or text == "TOPLAM KDV"
        )

        if not is_total_kdv_label:
            continue

        # Etiketten sonra satır yoksa devam et.
        if i + 1 >= len(lines):
            continue

        amount_line = lines[i + 1]
        amount_text = amount_line.text.strip()

        # Örnekler:
        # *13,85
        # * 13,85
        # *183.00
        # *1,96
        match = re.fullmatch(
            r"\*?\s*([0-9]+(?:[.,][0-9]{1,2})?)",
            amount_text
        )

        if not match:
            continue

        raw_amount = match.group(1)

        # Virgül veya nokta ondalık ayracı olabilir.
        normalized_amount = raw_amount.replace(",", ".")

        try:
            value = float(normalized_amount)
        except ValueError:
            continue

        # KDV negatif veya sıfır olamaz.
        if value <= 0:
            continue

        # Toplam biliniyorsa KDV toplamdan büyük olamaz.
        if (
            total_field is not None
            and total_field.value is not None
            and value >= total_field.value
        ):
            continue

        return ParsedField(
            value=value,
            source_text=amount_line.text,
            confidence=amount_line.confidence
        )

    kdv_keywords = {
        "KDV",
        "TOPKDV",
        "TOP KDV",
        "TOPLAM KDV"
    }

    for i, line in enumerate(lines):
        normalized_text = line.text.strip().upper()

        if normalized_text not in kdv_keywords:
            continue

        candidates = []

        # KDV kelimesinden önceki satır
        if i > 0:
            previous_line = lines[i - 1]
            value = clean_amount(previous_line.text)

            if value is not None:
                candidates.append(
                    ParsedField(
                        value=value,
                        source_text=previous_line.text,
                        confidence=previous_line.confidence
                    )
                )

        # KDV kelimesinden sonraki satır
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            value = clean_amount(next_line.text)

            if value is not None:
                candidates.append(
                    ParsedField(
                        value=value,
                        source_text=next_line.text,
                        confidence=next_line.confidence
                    )
                )

        if not candidates:
            return ParsedField()

        # Toplama eşit olan değer büyük ihtimalle KDV değildir.
        if total_field.value is not None:
            valid_candidates = [
                candidate
                for candidate in candidates
                if candidate.value != total_field.value
                and candidate.value < total_field.value
            ]

            if len(valid_candidates) == 1:
                return valid_candidates[0]

        # Tek aday varsa güvenle onu döndür
        if len(candidates) == 1:
            return candidates[0]

        # İki aday arasında güvenilir karar veremiyorsak tahmin etme
        return ParsedField()

    return ParsedField()


def find_total(ocr_document):
    lines = ocr_document.lines

    total_keywords = {
        "TOPLAM",
        "GENEL TOPLAM",
        "ÖDENECEK",
        "ÖDENECEK TUTAR",
        "TOP"
    }

    for i, line in enumerate(lines):
        normalized_text = line.text.strip().upper()

        if normalized_text in total_keywords:

            # Önce TOPLAM kelimesinden sonraki satıra bak
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                value = clean_amount(next_line.text)

                if value is not None:
                    return ParsedField(
                        value=value,
                        source_text=next_line.text,
                        confidence=next_line.confidence
                    )

            # Sonraki satır sayı değilse önceki satıra bak
            if i > 0:
                previous_line = lines[i - 1]
                value = clean_amount(previous_line.text)

                if value is not None:
                    return ParsedField(
                        value=value,
                        source_text=previous_line.text,
                        confidence=previous_line.confidence
                    )

    return ParsedField()


def parse_receipt(ocr_document):
    company = find_company(ocr_document)
    receipt_no = find_receipt_no(ocr_document)
    date = find_date(ocr_document)
    time = find_time(ocr_document)
    total = find_total(ocr_document)
    kdv = find_kdv(ocr_document, total)

    receipt = Receipt(
        company=company.value,
        receipt_no=receipt_no.value,
        date=date.value,
        time=time.value,
        kdv=kdv.value,
        total=total.value
    )

    fields = {
        "company": company,
        "receipt_no": receipt_no,
        "date": date,
        "time": time,
        "kdv": kdv,
        "total": total
    }

    return receipt, fields