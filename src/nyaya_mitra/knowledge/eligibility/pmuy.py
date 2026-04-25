"""eligibility checker for pmuy. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    is_woman = profile.demographics.get("gender") == "female"
    age = int(profile.demographics.get("age") or 0)
    bpl = bool(profile.economic.get("bpl_household"))
    has_lpg = bool(profile.economic.get("existing_lpg_in_family"))

    if not is_woman:
        return False, ["pmuy is for women"]
    if age < 18:
        return False, ["under 18"]
    if not bpl:
        return False, ["not in bpl household"]
    if has_lpg:
        return False, ["family already has lpg connection"]
    return True, ["adult woman in bpl household with no existing lpg"]
