"""eligibility checker for pm_awas_grameen. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    rural = profile.demographics.get("residence") == "rural"
    secc = bool(profile.economic.get("secc_listed"))
    owns_pucca = bool(profile.economic.get("owns_pucca_house"))
    kuccha_or_houseless = bool(
        profile.economic.get("kuccha_house") or profile.economic.get("houseless")
    )

    if not rural:
        return False, ["urban resident; pmayg is rural"]
    if not secc:
        return False, ["not in secc 2011 deprivation list"]
    if owns_pucca:
        return False, ["already owns a pucca house"]
    if not kuccha_or_houseless:
        return False, ["not in kuccha-house or houseless category"]
    return True, ["rural secc-listed household in kuccha or houseless category"]
