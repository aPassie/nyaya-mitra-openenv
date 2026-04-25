"""applicability checker for the maternity benefit act, 1961. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    is_woman = profile.demographics.get("gender") == "female"
    employed = bool(profile.economic.get("formally_employed"))
    facts = profile.situation_specific.hidden_facts or {}
    pregnant_or_postpartum = bool(facts.get("pregnant") or facts.get("recent_delivery"))
    denied = bool(facts.get("denied_maternity_benefit"))

    if not is_woman:
        return False, ["maternity benefit act covers women employees"]
    if not employed:
        return False, ["not formally employed"]
    if not pregnant_or_postpartum:
        return False, ["not pregnant or postpartum"]
    if not denied:
        return False, ["no denial of maternity benefit reported"]
    return True, ["pregnant or postpartum woman employee denied maternity benefit"]
