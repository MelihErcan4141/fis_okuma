import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


COMPANY_DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "companies.json"
)

GENERIC_COMPANY_WORDS = {
    "AS",
    "LTD",
    "LIMITED",
    "TICARET",
    "SANAYI",
    "SAN",
    "TIC",
    "ITHALAT",
    "IHRACAT",
    "MAGAZALAR",
    "MAGAZA",
    "MAGAZASI",
    "MARKET",
    "GIDA",
    "VE",
}


def get_distinctive_words(value):
    normalized = normalize_text(value)

    if not normalized:
        return set()

    return {
        word
        for word in normalized.split()
        if (
            len(word) >= 3
            and word
            not in GENERIC_COMPANY_WORDS
        )
    }

def normalize_text(value):
    if value is None:
        return None

    text = str(value).upper().strip()

    # Türkçe karakterleri önce açıkça normalize et
    replacements = {
        "İ": "I",
        "İ": "I",
        "Ş": "S",
        "Ğ": "G",
        "Ü": "U",
        "Ö": "O",
        "Ç": "C",

        # OCR'ın sık ürettiği aksanlı Latin karakterler
        "Í": "I",
        "Ì": "I",
        "Î": "I",
        "Ï": "I",

        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ä": "A",

        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ë": "E",

        "Ó": "O",
        "Ò": "O",
        "Ô": "O",

        "Ú": "U",
        "Ù": "U",
        "Û": "U",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new
        )

    # Kalan accent işaretlerini kaldır
    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        ch
        for ch in text
        if not unicodedata.combining(ch)
    )

    text = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text

def load_company_registry():
    if not COMPANY_DATA_PATH.exists():
        return []

    with open(
        COMPANY_DATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    return data.get(
        "companies",
        []
    )


def _similarity(left, right):
    if not left or not right:
        return 0.0

    return SequenceMatcher(
        None,
        left,
        right
    ).ratio()


def canonicalize_company(
    value,
    threshold=0.90
):
    if value is None:
        return None

    normalized_value = normalize_text(
        value
    )

    if not normalized_value:
        return value

    companies = load_company_registry()

    best_name = None
    best_score = 0.0

    source_words = get_distinctive_words(
        normalized_value
    )

    for company in companies:
        canonical_name = company.get(
            "canonical_name"
        )

        aliases = company.get(
            "aliases",
            []
        )

        candidates = [
            canonical_name,
            *aliases
        ]

        for candidate in candidates:
            normalized_candidate = (
                normalize_text(candidate)
            )

            if not normalized_candidate:
                continue

            candidate_words = (
                get_distinctive_words(
                    normalized_candidate
                )
            )

            # Önce exact normalize edilmiş eşleşme.
            # Bu durumda distinctive kelime şartı aramıyoruz.
            # 1) Normalize edilmiş değerler tamamen aynıysa
            # doğrudan canonical ismi döndür.
            if (
                normalized_value
                == normalized_candidate
            ):
                return canonical_name


            # 2) Registry'deki ayırt edici kelimelerin tamamı
            # OCR/AI tarafından bulunan uzun firma metninin
            # içerisinde geçiyorsa güvenli eşleşme kabul et.
            #
            # Örnek:
            # MİGROS TİCARET A.Ş.
            #          ↓
            # {"MIGROS"}
            #
            # MiGROS TICARET A.S. LIMAN AVM BANDIRMA...
            #          ↓
            # {"MIGROS", "LIMAN", "AVM", ...}
            #
            # MIGROS ortak olduğu için canonical Migros'a gider.
            if (
                candidate_words
                and candidate_words.issubset(
                    source_words
                )
            ):
                return canonical_name


            # 3) Yukarıdaki güçlü kurallar tutmadıysa
            # fuzzy matching'e geç.
            has_distinctive_overlap = bool(
                source_words
                & candidate_words
            )

            if not has_distinctive_overlap:
                continue

            score = _similarity(
                normalized_value,
                normalized_candidate
            )

            if score > best_score:
                best_score = score
                best_name = canonical_name

    if (
        best_name is not None
        and best_score >= threshold
    ):
        return best_name

    # ÇOK ÖNEMLİ:
    # Registry'de güvenilir eşleşme bulamazsak
    # firmayı silme/değiştirme.
    return value
