"""eligibility checker for mgnrega. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    age = int(profile.demographics.get("age") or 0)
    rural = profile.demographics.get("residence") == "rural"
    willing = profile.economic.get("willing_unskilled_work")
    if willing is None:
        willing = True

    if age < 18:
        return False, ["under 18"]
    if not rural:
        return False, ["urban resident; mgnrega is rural only"]
    if not willing:
        return False, ["not willing to do unskilled manual work"]
    return True, ["adult rural resident willing to do unskilled work"]
