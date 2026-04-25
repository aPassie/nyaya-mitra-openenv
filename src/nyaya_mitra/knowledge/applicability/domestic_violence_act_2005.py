"""applicability checker for the domestic violence act, 2005. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    is_woman = profile.demographics.get("gender") == "female"
    facts = profile.situation_specific.sensitive_facts or {}
    has_dv = bool(facts.get("dv_history") or facts.get("dv_present"))

    if not is_woman:
        return False, ["dv act protects women"]
    if not has_dv:
        return False, ["no domestic violence reported"]
    return True, ["woman experiencing domestic violence"]
