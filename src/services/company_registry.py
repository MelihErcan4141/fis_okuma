import json
from pathlib import Path

from services.company_normalizer import (
    COMPANY_DATA_PATH,
    normalize_text,
)


class CompanyRegistry:
    def __init__(self, data_path=None):
        self.data_path = (
            Path(data_path)
            if data_path is not None
            else COMPANY_DATA_PATH
        )

    def _load_data(self):
        if not self.data_path.exists():
            return {
                "companies": []
            }

        with open(
            self.data_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def _save_data(self, data):
        self.data_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            self.data_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

    def add_alias(
        self,
        canonical_name,
        alias
    ):
        if not canonical_name:
            raise ValueError(
                "canonical_name boş olamaz."
            )

        if not alias:
            raise ValueError(
                "alias boş olamaz."
            )

        canonical_normalized = normalize_text(
            canonical_name
        )

        alias_normalized = normalize_text(
            alias
        )

        data = self._load_data()

        companies = data.setdefault(
            "companies",
            []
        )

        # -------------------------------------------------
        # 1. Aynı alias başka şirkete bağlı mı?
        # -------------------------------------------------

        for company in companies:
            current_canonical = company.get(
                "canonical_name"
            )

            aliases = company.get(
                "aliases",
                []
            )

            candidates = [
                current_canonical,
                *aliases
            ]

            for candidate in candidates:
                if (
                    normalize_text(candidate)
                    == alias_normalized
                ):
                    if (
                        normalize_text(
                            current_canonical
                        )
                        != canonical_normalized
                    ):
                        raise ValueError(
                            (
                                f"'{alias}' alias'ı zaten "
                                f"'{current_canonical}' "
                                "firmasına bağlı."
                            )
                        )

                    # Zaten aynı firmaya bağlıysa
                    # tekrar ekleme.
                    return False

        # -------------------------------------------------
        # 2. Canonical firma registry'de var mı?
        # -------------------------------------------------

        target_company = None

        for company in companies:
            current_canonical = company.get(
                "canonical_name"
            )

            if (
                normalize_text(
                    current_canonical
                )
                == canonical_normalized
            ):
                target_company = company
                break

        # -------------------------------------------------
        # 3. Firma yoksa yeni kayıt oluştur
        # -------------------------------------------------

        if target_company is None:
            target_company = {
                "canonical_name": canonical_name,
                "aliases": []
            }

            companies.append(
                target_company
            )

        aliases = target_company.setdefault(
            "aliases",
            []
        )

        # Canonical adın aynısını alias olarak ekleme.
        if (
            alias_normalized
            == canonical_normalized
        ):
            return False

        aliases.append(alias)

        self._save_data(data)

        return True