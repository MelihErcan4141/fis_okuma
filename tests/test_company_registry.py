import json

import pytest

from services.company_registry import (
    CompanyRegistry
)


def create_registry_file(tmp_path):
    path = tmp_path / "companies.json"

    data = {
        "companies": [
            {
                "canonical_name":
                    "BİM BİRLEŞİK MAĞAZALAR A.Ş.",
                "aliases": [
                    "BIM BIRLESIK MAGAZALAR AS"
                ]
            }
        ]
    }

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    return path


def test_add_alias_to_existing_company(
    tmp_path
):
    path = create_registry_file(
        tmp_path
    )

    registry = CompanyRegistry(
        data_path=path
    )

    added = registry.add_alias(
        "BİM BİRLEŞİK MAĞAZALAR A.Ş.",
        "BUR BURLESIY MASAZALAR A.S"
    )

    assert added is True

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    aliases = (
        data["companies"][0]["aliases"]
    )

    assert (
        "BUR BURLESIY MASAZALAR A.S"
        in aliases
    )


def test_duplicate_alias_is_not_added(
    tmp_path
):
    path = create_registry_file(
        tmp_path
    )

    registry = CompanyRegistry(
        data_path=path
    )

    first = registry.add_alias(
        "BİM BİRLEŞİK MAĞAZALAR A.Ş.",
        "BUR BURLESIY MASAZALAR A.S"
    )

    second = registry.add_alias(
        "BİM BİRLEŞİK MAĞAZALAR A.Ş.",
        "BUR BURLESIY MASAZALAR A.S"
    )

    assert first is True
    assert second is False


def test_alias_cannot_belong_to_two_companies(
    tmp_path
):
    path = create_registry_file(
        tmp_path
    )

    registry = CompanyRegistry(
        data_path=path
    )

    registry.add_alias(
        "BİM BİRLEŞİK MAĞAZALAR A.Ş.",
        "BUR BURLESIY MASAZALAR A.S"
    )

    with pytest.raises(ValueError):
        registry.add_alias(
            "XYZ MARKET",
            "BUR BURLESIY MASAZALAR A.S"
        )


def test_new_company_can_be_created(
    tmp_path
):
    path = create_registry_file(
        tmp_path
    )

    registry = CompanyRegistry(
        data_path=path
    )

    added = registry.add_alias(
        "KANAAT LOKANTASI",
        "KANAAT LOKANTAS1"
    )

    assert added is True

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    kanaat = next(
        company
        for company in data["companies"]
        if (
            company["canonical_name"]
            == "KANAAT LOKANTASI"
        )
    )

    assert (
        "KANAAT LOKANTAS1"
        in kanaat["aliases"]
    )


def test_same_as_canonical_is_not_added_as_alias(
    tmp_path
):
    path = create_registry_file(
        tmp_path
    )

    registry = CompanyRegistry(
        data_path=path
    )

    added = registry.add_alias(
        "BİM BİRLEŞİK MAĞAZALAR A.Ş.",
        "BİM BİRLEŞİK MAĞAZALAR A.Ş."
    )

    assert added is False