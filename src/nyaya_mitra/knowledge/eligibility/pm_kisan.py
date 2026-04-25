"""eligibility checker for pm_kisan. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile

EXCLUDED_OCCUPATIONS = {
    "doctor",
    "engineer",
    "lawyer",
    "chartered accountant",
    "architect",
    "income_tax_payer",
}


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    occ = (profile.economic.get("occupation") or "").lower()
    holds_land = bool(profile.economic.get("holds_cultivable_land"))
    is_pro = profile.economic.get("is_professional") or occ in EXCLUDED_OCCUPATIONS
    is_taxpayer = bool(profile.economic.get("income_tax_payer"))

    if is_pro:
        return False, ["excluded as professional"]
    if is_taxpayer:
        return False, ["excluded as income-tax payer"]
    if "farmer" not in occ and "kisan" not in occ:
        return False, ["not a farmer"]
    if not holds_land:
        return False, ["does not hold cultivable land"]
    return True, ["farmer with cultivable land"]
