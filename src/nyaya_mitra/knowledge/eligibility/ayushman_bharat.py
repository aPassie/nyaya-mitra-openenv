"""eligibility checker for ayushman_bharat (pmjay). pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    secc = bool(profile.economic.get("secc_listed"))
    urban_occ = bool(profile.economic.get("urban_occupational_category"))

    if not (secc or urban_occ):
        return False, ["not in secc 2011 list and not in urban occupational category"]
    return True, ["secc-listed household or urban occupational beneficiary"]
