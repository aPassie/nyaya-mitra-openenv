"""applicability checker for the minimum wages act, 1948. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    is_worker = bool(profile.economic.get("is_wage_worker"))
    facts = profile.situation_specific.hidden_facts or {}
    underpaid = bool(facts.get("wages_below_minimum"))

    if not is_worker:
        return False, ["not a wage worker in a scheduled employment"]
    if not underpaid:
        return False, ["wages not reported below the minimum wage"]
    return True, ["wage worker paid below the notified minimum wage"]
